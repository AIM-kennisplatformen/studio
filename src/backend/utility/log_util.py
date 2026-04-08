from langfuse import get_client

active_trace_ids: dict[str, str] = {}


def _log_session_event(
    *,
    trace_id: str,
    name: str,
    event: str,
    user_id: str | None,
    sid: str,
    message: str,
):
    langfuse = get_client()

    with langfuse.start_as_current_observation(
        as_type="span",
        name=name,
        trace_context={"trace_id": trace_id},
    ) as observation:
        observation.update(
            input={"event": event, "user_id": user_id, "sid": sid},
            output={"status": event, "message": message},
        )
        observation.update_trace(
            user_id=user_id,
            session_id=sid,
            metadata={"message": message},
        )

    langfuse.flush()


def start_session(user_id: str, sid: str) -> str:
    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    active_trace_ids[sid] = trace_id

    _log_session_event(
        trace_id=trace_id,
        name="session_start",
        event="connect",
        user_id=user_id,
        sid=sid,
        message="User connected via Socket.IO",
    )

    return trace_id


def end_session(user_id: str | None, sid: str):
    trace_id = active_trace_ids.pop(sid, None)
    if not trace_id:
        return

    _log_session_event(
        trace_id=trace_id,
        name="session_end",
        event="disconnect",
        user_id=user_id,
        sid=sid,
        message="User disconnected / socket closed",
    )
