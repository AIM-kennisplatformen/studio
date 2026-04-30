
import socketio
from fastapi import APIRouter
from langfuse import get_client

from backend.config import config, root_question_prompt
from backend.endpoints.graph import (
    user_graph_contexts,
    _default_user_graph_context,
    fetch_subnode_stream,
    SUBNODE_MAP,
)
from backend.models.chat_message import ChatMessage
from backend.stores.redis import redis_store
from backend.utility.log_util import end_session, start_session
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
            session_id=sid,
            input={"message": user_msg},
        )
        root_span.update(input={"message": user_msg})

        limit = config.get("chat_history_limit")
        history_items = await redis_store.get_history(sid, limit)
            
        history_text = "\n".join([f"{item.role.capitalize()}: {item.message}" for item in history_items])

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
                    user_id, question, selected_subnode,
                    trace_id=trace_id, session_id=sid,
                )
                full_response = ctx.get("prefetched", {}).get(selected_subnode, "")
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
        await redis_store.store_message(sid, ChatMessage(role="user", message=user_msg))

        ctx["previous_question"] = ctx.get("latest_question")
        ctx["latest_question"] = user_msg
        ctx["selected_subnode"] = "root"
        ctx["dialogue_state_asked"] = False

        synthetic_prompt = root_question_prompt(user_msg, history_text)

        async for evt in stream_agent_events(
            synthetic_prompt, user_id=user_id, trace_id=trace_id,
            session_id=sid,
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
        await redis_store.store_message(sid, ChatMessage(role="assistant", message=full_response))
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
                "Do you want to ask an question, answered by the full body of literature? "
                "Please proceed, by asking me your question?",
            )
        else:
            await push_chat_message(
                user_id,
                "Answer a question by using the full body of literature "
                f"Would you like to ask a different question than: '{question}'? "
                "**Respond with another question** or type **yes** to repeat the previous question.",
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
                f"You've selected subset {subnode}. Please ask me your question.",
            )
        else:
            await push_chat_message(
                user_id,
                f"You've selected subset {subnode}. Please ask me your question using this subset. "
                f"If you want to repeat your previous question: `{question}` "
                "type **yes**, otherwise **respond with another question**.",
            )

        ctx["dialogue_state_asked"] = True
        ctx["previous_question"] = question
        return
