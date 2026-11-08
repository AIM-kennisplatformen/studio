import time
from collections.abc import AsyncGenerator

import socketio
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

# py.typed is not shipped, but typed properly, so proper ignore here
from mcp_use import MCPAgent, MCPClient  # pyright: ignore[reportMissingTypeStubs]
from mcp_use.client.config import load_config_file  # pyright: ignore[reportMissingTypeStubs]

from src.config import config
from src.models.chat_event import AgentEvent

# =====================================================
# Socket.IO broker state
# =====================================================

sio: socketio.AsyncServer | None = None

# user_id → sid (primary, last-connected)
user_connections: dict[str, str] = {}

# sid → user_id
sid_connections: dict[str, str] = {}

# user_id → set[sid] (multi-tab support)
user_sids: dict[str, set[str]] = {}


# =====================================================
# Registration
# =====================================================


def register_socketio(server: socketio.AsyncServer):
    """Register global Socket.IO instance (called once in chat.py)."""
    global sio
    sio = server


# =====================================================
# Connection Mapping
# =====================================================


def bind_user(user_id: str, sid: str) -> None:
    """
    Record mapping between authenticated user_id and Socket.IO sid.
    """
    user_connections[user_id] = sid
    sid_connections[sid] = user_id
    user_sids.setdefault(user_id, set()).add(sid)
    print(f"[BIND] user={user_id} ↔ sid={sid}")


def unbind_sid(sid: str) -> str | None:
    """
    Remove sid and reverse-mapping when client disconnects.
    """
    user_id = sid_connections.pop(sid, None)
    if not user_id:
        print(f"[UNBIND] sid={sid} user=None")
        return None

    _ = user_connections.pop(user_id, None)
    sids = user_sids.get(user_id)
    if sids:
        sids.discard(sid)
        if not sids:
            del user_sids[user_id]

    print(f"[UNBIND] sid={sid} user={user_id}")
    return user_id


async def _create_agent() -> MCPAgent:
    mcp_config = load_config_file(config["mcp_tool_config_path"])
    client = MCPClient(mcp_config)
    llm = ChatOpenAI(
        model=config["llm_model"],
        base_url=config["openai_host"],
    )
    return MCPAgent(
        llm=llm,
        client=client,
        max_steps=30,
        callbacks=[CallbackHandler()],
    )


async def run_agent(
    message: str,
    user_id: str | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
) -> str:
    """
    Run the agent to completion and return the full response string.

    When *trace_id* is supplied the entire agent execution is recorded
    under that existing Langfuse trace (the CallbackHandler created
    inside ``_create_agent`` automatically joins the current observation
    context).
    """
    langfuse = get_client()

    if trace_id is not None:
        with (
            langfuse.start_as_current_observation(
                as_type="span",
                name="run_agent",
                trace_context={"trace_id": trace_id},
            ),
            propagate_attributes(user_id=user_id, session_id=session_id),
        ):
            agent = await _create_agent()
            result = await agent.run(message)
        langfuse.flush()
        return result

    # Fallback: no trace_id provided — original behaviour
    agent = await _create_agent()
    try:
        return await agent.run(message)
    finally:
        langfuse.flush()


async def stream_agent_events(
    message: str,
    user_id: str | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
) -> AsyncGenerator[AgentEvent, None]:
    """
    Async generator that yields parsed event dicts:
      {"type": str, "data": str, "timestamp": float}

    When *trace_id* is supplied the streaming execution is recorded
    under that existing Langfuse trace.
    """
    langfuse = get_client()

    if trace_id is not None:
        with (
            langfuse.start_as_current_observation(
                as_type="span",
                name="stream_agent_events",
                trace_context={"trace_id": trace_id},
            ),
            propagate_attributes(user_id=user_id, session_id=session_id),
        ):
            agent = await _create_agent()
            async for event in agent.stream_events(message):
                event_type = event.get("event", "")
                data = ""
                if event_type == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if isinstance(chunk, AIMessageChunk):
                        data = chunk.content if isinstance(chunk.content, str) else ""
                yield {
                    "type": event_type,
                    "data": data,
                    "timestamp": time.time(),
                }
        langfuse.flush()
        return

    # Fallback: no trace_id provided — original behaviour
    agent = await _create_agent()
    try:
        async for event in agent.stream_events(message):
            event_type = event.get("event", "")
            data = ""
            if event_type == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if isinstance(chunk, AIMessageChunk):
                    data = chunk.content if isinstance(chunk.content, str) else ""
            yield {
                "type": event_type,
                "data": data,
                "timestamp": time.time(),
            }
    finally:
        langfuse.flush()


type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)


async def emit_to_user(user_id: str, event: str, payload: dict[str, JsonValue]):
    """
    Emit a named event to all sockets for a specific user.
    """
    if sio is None:
        print("[emit_to_user] Socket.IO not registered")
        return

    sids = user_sids.get(user_id)
    if not sids:
        print(f"[emit_to_user] No active sids for user={user_id}")
        return

    for sid in sids:
        try:
            await sio.emit(event, payload, to=sid)
        except Exception as e:
            print(f"[emit_to_user] ERROR sending to user={user_id} sid={sid}: {e}")


async def push_chat_message(
    user_id: str,
    message: str,
    subnode: str | None = None,
    message_type: str | None = None,
):
    """
    Sends a full assistant message (non-streamed) to the user.
    Explicitly marked as FINAL/REPLACE to avoid streaming confusion.
    """
    if sio is None:
        print("⚠ push_chat_message: Socket.IO not registered")
        return

    sid = user_connections.get(user_id)
    print(f"[PUSH] user={user_id}, sid={sid}")

    if not sid:
        return

    payload = {
        "role": "ai",
        "content": message,
        "mode": "replace",
        "subnode": subnode,
    }

    try:
        await sio.emit("message", payload, to=sid)
        await sio.emit(
            "done",
            {
                "full_response": message,
                "mode": "replace",
                "subnode": subnode,
                "message_kind": message_type,
            },
            to=sid,
        )
    except Exception as e:
        print(f"❌ push_chat_message ERROR for user={user_id}: {e}")


async def push_chat_message_stream(
    user_id: str,
    event_type: str,
    message: str,
    subnode: str | None = None,
):
    """
    Sends a full assistant message (non-streamed) to the user.
    Explicitly marked as FINAL/REPLACE to avoid streaming confusion.
    """
    if sio is None:
        print("⚠ push_chat_message: Socket.IO not registered")
        return

    sid = user_connections.get(user_id)
    print(f"[PUSH] user={user_id}, sid={sid}")

    if not sid:
        return

    payload = {
        "role": "ai",
        "content": message,
        "mode": "replace",
        "subnode": subnode,
    }

    try:
        if event_type == "done":
            await sio.emit(
                "done",
                {"full_response": message},
                to=sid,
            )
        # ALSO emit chat messages for chat UI
        elif event_type == "on_chat_model_stream" and message:
            await sio.emit(
                "message",
                {
                    "role": "ai",
                    "content": message,
                },
                to=sid,
            )
        else:
            await sio.emit(
                "event",
                {
                    "type": event_type,
                    "data": message,
                    "timestamp": payload.get("timestamp"),
                },
                to=sid,
            )

    except Exception as e:
        print(f"❌ push_chat_message ERROR for user={user_id}: {e}")
