from typing import Optional, Dict
import socketio

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


# =====================================================
# Emitting Messages
# =====================================================

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
        "mode": "replace",   # 🔥 DIT is de sleutel
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

