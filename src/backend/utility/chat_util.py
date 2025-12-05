from typing import Optional
from fastapi import WebSocket

# Keep track of active websockets so background tasks can push messages into chat
active_websockets: dict[str, Optional[WebSocket]] = {}


async def push_chat_message(user_id: str, text: str):
    """
    Push an assistant-style message into the user's chat over WebSocket,
    if there is an active connection.
    """
    ws = active_websockets.get(user_id)
    if not ws:
        return

    try:
        # Stream as a single "message" + "done" pair
        await ws.send_json({
            "type": "message",
            "role": "chatbot",
            "content": text,
        })
        await ws.send_json({
            "type": "done",
            "full_response": text,
        })
    except Exception as e:
        # If sending fails, we just drop it; connection may have closed
        print(f"Failed to push chat message for user {user_id}: {e}")

