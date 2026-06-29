import asyncio
from uuid import UUID

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
import socketio
from fastapi import APIRouter
from langchain_openai import ChatOpenAI
from langfuse import get_client
from loguru import logger

from backend.config import (
    config,
    root_question_prompt,
    node_no_question_prompt,
    node_repeat_question_prompt,
    subnode_no_question_prompt,
    subnode_repeat_question_prompt,
)
from backend.endpoints.graph import (
    user_graph_contexts,
    _default_user_graph_context,
    fetch_subnode_stream,
    SUBNODE_MAP,
)
from backend.models.session import Session as ChatSession
from backend.models.session import SessionMessage
from backend.models.chat_message import ChatMessage
from backend.stores.postgres import DEFAULT_SESSION_NAME, postgres_store
from backend.stores.redis import redis_store
from backend.utility.log_util import end_session, start_session
from backend.utility.session_store import (
    ACTIVE_SESSION_KEY,
    get_active_session_id,
    parse_session_id,
    set_active_session_id,
)
from backend.utility.chat_util import (
    push_chat_message,
    register_socketio,
    bind_user,
    stream_agent_events,
    unbind_sid,
    push_chat_message_stream,
    sid_connections,
)

cors_origins = [config["base_url"]]

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    cors_credentials=True,
)

register_socketio(sio)

socket_app = socketio.ASGIApp(sio)
chat_router = APIRouter()


async def _resolve_active_session(
    user_id: str,
    session_state: dict | None = None,
    create: bool = False,
) -> ChatSession | None:
    session_id = get_active_session_id(user_id)
    active_session = None

    if session_id is not None:
        active_session = await postgres_store.get_session(user_id, session_id)

    if active_session is None and session_state is not None:
        session_id = parse_session_id(session_state.get(ACTIVE_SESSION_KEY))
        if session_id is not None:
            active_session = await postgres_store.get_session(user_id, session_id)

    if active_session is None:
        active_session = await postgres_store.get_latest_session(user_id)

    if active_session is None and create:
        active_session = await postgres_store.create_session(user_id)

    if active_session is not None:
        set_active_session_id(user_id, active_session.session_id)

    return active_session


def _format_history_text(messages: list[SessionMessage]) -> str:
    labels = {"ai": "AI", "user": "User"}
    return "\n".join(
        f"{labels.get(item.role, item.role)}: {item.content}" for item in messages
    )


def _fallback_session_title(user_msg: str) -> str:
    title = " ".join(user_msg.split())
    if not title:
        return DEFAULT_SESSION_NAME
    if len(title) > 80:
        return f"{title[:77].rstrip()}..."
    return title


def _sanitize_session_title(raw_title: object) -> str | None:
    if isinstance(raw_title, list):
        raw_title = " ".join(str(item) for item in raw_title)

    title = " ".join(str(raw_title).split()).strip(" \"'")
    if title.lower().startswith("title:"):
        title = title[6:].strip()
    title = title.rstrip(".")

    if not title:
        return None
    if len(title) > 80:
        title = f"{title[:77].rstrip()}..."
    return title


async def _generate_session_title(user_msg: str) -> str | None:
    llm = ChatOpenAI(
        model=config["llm_model"],
        base_url=config["openai_host"],
    )
    result = await llm.ainvoke(
        "Create a concise title for this chat session.\n"
        "Rules: maximum 6 words, no quotation marks, no trailing punctuation, "
        "and no extra text.\n\n"
        f"First user message:\n{user_msg}"
    )
    return _sanitize_session_title(result.content)


async def _update_session_title(
    user_id: str,
    session_id: UUID,
    user_msg: str,
) -> None:
    title = _fallback_session_title(user_msg)
    try:
        generated_title = await _generate_session_title(user_msg)
        if generated_title:
            title = generated_title
    except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
        logger.warning(f"Temporary OpenAI failure while generating session title: {exc}")
    except (
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        PermissionDeniedError,
    ) as exc:
        logger.error(f"OpenAI configuration error while generating session title: {exc}")
    except Exception as exc:
        logger.warning(f"Unexpected failure while generating AI session title: {exc}")

    try:
        await postgres_store.update_session_name(user_id, session_id, title)
    except Exception as exc:
        logger.warning(f"Failed to update session title: {exc}")


def _schedule_session_title(user_id: str, session_id: UUID, user_msg: str) -> None:
    asyncio.create_task(_update_session_title(user_id, session_id, user_msg))


async def _store_chat_message(
    user_id: str,
    session_id: UUID,
    role: str,
    content: str,
) -> None:
    session_role = "ai" if role == "ai" else "user"
    redis_role = "assistant" if session_role == "ai" else "user"

    await postgres_store.add_message(user_id, session_id, session_role, content)
    await redis_store.store_message(
        str(session_id),
        ChatMessage(role=redis_role, message=content),
    )


@sio.event
async def connect(sid, environ, auth):
    """
    Called when a client initiates a Socket.IO connection.
    Loads user from ASGI session (already decoded by SessionMiddleware).
    """
    scope = environ.get("asgi.scope") or {}
    session = scope.get("session") or {}
    user = session.get("user")

    if not user:
        print("❌ Rejecting socket: no user in session")
        raise ConnectionRefusedError("unauthorized")

    user_id = user["sub"]
    bind_user(user_id, sid)
    await _resolve_active_session(user_id, session, create=False)
    user_graph_contexts[user_id] = _default_user_graph_context()
    start_session(user_id, sid)
    print(f"✓ Socket connected: {sid} user={user_id}")


@sio.event
async def disconnect(sid):
    user_id = unbind_sid(sid)
    end_session(user_id, sid)
    print(f"⚠ Socket disconnected sid={sid} user={user_id}")


@sio.event
async def send_message(sid, data):
    user_id = sid_connections.get(sid)
    if not user_id:
        return

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return

    active_session = await _resolve_active_session(user_id, create=True)
    if active_session is None:
        return

    durable_session_id = active_session.session_id
    durable_session_id_str = str(durable_session_id)

    # --------------------------------------------------
    # Create a single Langfuse trace for this chat turn
    # --------------------------------------------------
    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    print(f"[TRACE] send_message trace_id={trace_id} user={user_id}")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="chat_turn",
        trace_context={"trace_id": trace_id},
    ) as root_span:
        root_span.update_trace(
            name="chat_turn",
            user_id=user_id,
            session_id=durable_session_id_str,
            input={"message": user_msg},
        )
        root_span.update(input={"message": user_msg})

        limit = int(config.get("chat_history_limit", 0))
        history_items = await postgres_store.list_messages(
            user_id,
            durable_session_id,
            limit,
        )
        history_text = _format_history_text(history_items)
        is_first_message = not history_items
        await _store_chat_message(user_id, durable_session_id, "user", user_msg)

        if active_session.name == DEFAULT_SESSION_NAME and is_first_message:
            _schedule_session_title(user_id, durable_session_id, user_msg)

        ctx = user_graph_contexts[user_id]

        selected_subnode = ctx.get("selected_subnode", "root")
        dialogue_state_asked = bool(ctx.get("dialogue_state_asked", False))
        prefetched = (ctx.get("prefetched") or {}).get(selected_subnode)

        full_response = ""

        if dialogue_state_asked:
            try:
                if user_msg.lower() == "yes":
                    # Use prefetched if available
                    if prefetched:
                        full_response = prefetched
                        await _store_chat_message(
                            user_id,
                            durable_session_id,
                            "ai",
                            full_response,
                        )
                        await push_chat_message_stream(
                            user_id,
                            "on_chat_model_stream",
                            prefetched,
                            selected_subnode,
                        )
                        await push_chat_message_stream(
                            user_id,
                            "done",
                            prefetched,
                            selected_subnode,
                        )
                        root_span.update(output={"response": full_response})
                        root_span.update_trace(output={"response": full_response})
                        langfuse.flush()
                        return

                    question = ctx.get("latest_question") or ctx.get("previous_question")
                else:
                    ctx["latest_question"] = user_msg
                    ctx["prefetched"] = {}
                    question = ctx["latest_question"]

                await fetch_subnode_stream(
                    user_id,
                    question,
                    selected_subnode,
                    history_text=history_text,
                    trace_id=trace_id,
                    session_id=durable_session_id_str,
                )
                full_response = ctx.get("prefetched", {}).get(selected_subnode, "")
                await _store_chat_message(
                    user_id,
                    durable_session_id,
                    "ai",
                    full_response,
                )
                await push_chat_message_stream(
                    user_id,
                    "done",
                    full_response,
                    selected_subnode,
                )
                root_span.update(output={"response": full_response})
                root_span.update_trace(output={"response": full_response})
                langfuse.flush()
                return

            finally:
                ctx["dialogue_state_asked"] = False

        # --------------------------------------------------
        # NORMAL ROOT WORKFLOW (user asked a new question in chat)
        # --------------------------------------------------
        ctx["previous_question"] = ctx.get("latest_question")
        ctx["latest_question"] = user_msg
        ctx["selected_subnode"] = "root"
        ctx["dialogue_state_asked"] = False

        synthetic_prompt = root_question_prompt(user_msg, history_text)

        async for evt in stream_agent_events(
            synthetic_prompt, user_id=user_id, trace_id=trace_id,
            session_id=durable_session_id_str,
        ):
            event_type = evt["type"]
            event_data = evt["data"]

            if event_type != "on_chat_model_stream":
                await push_chat_message_stream(user_id, event_type, event_data, "root")
                continue

            if event_data:
                await push_chat_message_stream(
                    user_id, "on_chat_model_stream", event_data, "root"
                )
                full_response += event_data

        # --------------------------------------------------
        # FINALIZE ROOT RESPONSE
        # --------------------------------------------------
        await _store_chat_message(user_id, durable_session_id, "ai", full_response)
        ctx.setdefault("prefetched", {})["root"] = full_response

        root_span.update(output={"response": full_response})
        root_span.update_trace(output={"response": full_response})

        await push_chat_message_stream(user_id, "done", full_response, "root")

    langfuse.flush()


@sio.event
async def select_node(sid, data):
    user_id = sid_connections.get(sid)
    if not user_id:
        return

    node_id = int(data.get("node_id", 0))
    ctx = user_graph_contexts[user_id]
    question = ctx.get("latest_question")

    if node_id == 1:
        ctx["selected_subnode"] = "root"
        ctx["dialogue_state_asked"] = False

        if not question:
            await push_chat_message(
                user_id,
                node_no_question_prompt(),
                "system_prompt",  # ← was missing
            )
        else:
            await push_chat_message(
                user_id,
                node_repeat_question_prompt(question),
                "system_prompt",  # ← was missing
            )
        ctx["dialogue_state_asked"] = True
        ctx["previous_question"] = question
        return

    if node_id in SUBNODE_MAP:
        subnode = SUBNODE_MAP[node_id]
        ctx["selected_subnode"] = subnode
        ctx["dialogue_state_asked"] = False

        if not question:
            await push_chat_message(
                user_id,
                subnode_no_question_prompt(subnode),
                "system_prompt",
            )
        else:
            await push_chat_message(
                user_id,
                subnode_repeat_question_prompt(subnode, question),
                "system_prompt",
            )

        ctx["dialogue_state_asked"] = True
        ctx["previous_question"] = question
