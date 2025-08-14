from __future__ import annotations

from typing import TypedDict, Literal, List, Dict
from datetime import datetime
from threading import RLock


class ConversationTurn(TypedDict):
    role: Literal["user", "model"]
    text: str
    ts: float


class ConversationStore:
    def __init__(self, max_history_per_session: int = 40) -> None:
        self._store: Dict[str, List[ConversationTurn]] = {}
        self._lock = RLock()
        self._max = max_history_per_session

    def add_turn(self, session_id: str, role: Literal["user", "model"], text: str) -> None:
        if not session_id:
            return
        with self._lock:
            turns = self._store.setdefault(session_id, [])
            turns.append({
                "role": role,
                "text": text,
                "ts": datetime.utcnow().timestamp(),
            })
            if len(turns) > self._max:
                self._store[session_id] = turns[-self._max :]

    def get_recent(self, session_id: str, max_turns: int) -> List[ConversationTurn]:
        if not session_id or max_turns <= 0:
            return []
        with self._lock:
            turns = self._store.get(session_id, [])
            return turns[-max_turns:]

    def clear_session(self, session_id: str) -> None:
        if not session_id:
            return
        with self._lock:
            self._store.pop(session_id, None)


conversation_store = ConversationStore()



