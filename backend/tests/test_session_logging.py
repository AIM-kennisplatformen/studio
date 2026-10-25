from src.utility.log_util import active_trace_ids, end_session, start_session


def test_session_logging_uses_current_langfuse_api():
    sid = "test-session"

    try:
        trace_id = start_session("test-user", sid)
        assert active_trace_ids[sid] == trace_id

        end_session("test-user", sid)
        assert sid not in active_trace_ids
    finally:
        active_trace_ids.pop(sid, None)
