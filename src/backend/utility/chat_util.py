import time
from typing import Optional, Dict, AsyncGenerator
 
import os
import socketio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from mcp_use import MCPAgent, MCPClient
from mcp_use.client.config import load_config_file

load_dotenv()

# =====================================================
# Socket.IO broker state
# =====================================================

sio: Optional[socketio.AsyncServer] = None

# user_id → sid
user_connections: Dict[str, str] = {}

# sid → user_id
sid_connections: Dict[str, str] = {}


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

def bind_user(user_id: str, sid: str):
    """
    Record mapping between authenticated user_id and Socket.IO sid.
    """
    user_connections[user_id] = sid
    sid_connections[sid] = user_id
    print(f"[BIND] user={user_id} ↔ sid={sid}")


def unbind_sid(sid: str) -> Optional[str]:
    """
    Remove sid and reverse-mapping when client disconnects.
    """
    user_id = sid_connections.pop(sid, None)
    if user_id:
        user_connections.pop(user_id, None)

    print(f"[UNBIND] sid={sid} user={user_id}")
    return user_id


async def _create_agent() -> MCPAgent:
    config = load_config_file(os.getenv("MCP_TOOL_CONFIG_PATH", ""))
    client = MCPClient(config)
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", ""),
        base_url=os.getenv("OPENAI_HOST", ""),
    )
    return MCPAgent(
        llm=llm,
        client=client,
        max_steps=30,
        callbacks=[CallbackHandler()],
    )

async def run_agent(message: str, user_id: str | None = None) -> str:
    """
    Run the agent to completion and return the full response string.
    """
    langfuse = get_client()
    agent = await _create_agent()
    try:
        return await agent.run(message)
    finally:
        langfuse.flush()
 


async def stream_agent_events(
    message: str, user_id: str | None = None
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields parsed event dicts:
      {"type": str, "data": str, "timestamp": float}
    """
    langfuse = get_client()
    agent = await _create_agent()
    try:
        async for event in agent.stream_events(message):
            event_type = event.get("event", "")
            data = ""
            if event_type == "on_chat_model_stream":
                data = event["data"]["chunk"].content or ""
            yield {
                "type": event_type,
                "data": data,
                "timestamp": time.time(),
            }
    finally:
        langfuse.flush()
 

async def emit_to_user(user_id: str, event: str, payload: dict):
    """
    Emit a named event to a specific user if connected.
    """
    if sio is None:
        print("[emit_to_user] Socket.IO not registered")
        return

    sid = user_connections.get(user_id)
    if not sid:
        print(f"[emit_to_user] No active sid for user={user_id}")
        return

    try:
        await sio.emit(event, payload, to=sid)
    except Exception as e:
        print(f"[emit_to_user] ERROR sending to user={user_id}: {e}")


async def push_chat_message(
    user_id: str,
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
        "role": "chatbot",
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
        "role": "chatbot",
        "content": message,
        "mode": "replace", 
        "subnode": subnode,
    }

    try:
        if(event_type == "done"):
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
                    "role": "chatbot",
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
