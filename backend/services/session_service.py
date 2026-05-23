from datetime import datetime, timedelta


class SessionStore:
    """内存会话存储"""

    def __init__(self):
        self._sessions: dict[str, datetime] = {}

    def create(self) -> str:
        from uuid import uuid4
        thread_id = str(uuid4())
        self._sessions[thread_id] = datetime.now()
        return thread_id

    def exists(self, thread_id: str) -> bool:
        return thread_id in self._sessions

    def remove(self, thread_id: str):
        self._sessions.pop(thread_id, None)


session_store = SessionStore()
