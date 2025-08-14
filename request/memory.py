from __future__ import annotations

from typing import Any, Dict, List, Literal
from threading import RLock

# ConversationTurn 現在是一個更通用的字典，因為每個角色的結構都不同
ConversationTurn = Dict[str, Any]


class ConversationStore:
    def __init__(self, max_history_per_session: int = 40) -> None:
        self._store: Dict[str, List[ConversationTurn]] = {}
        self._lock = RLock()
        self._max = max_history_per_session

    def add_turn(self, session_id: str, role: Literal["user", "model"], text: str) -> None:
        """儲存使用者輸入或模型的文字回應"""
        if not session_id:
            return
        with self._lock:
            turns = self._store.setdefault(session_id, [])
            # 儲存的結構直接對應 API 的 parts 結構
            turns.append({
                "role": role,
                "text": text
            })
            if len(turns) > self._max:
                self._store[session_id] = turns[-self._max:]

    def add_func_call(self, session_id: str, func_name: str, func_args: Dict[str, Any]) -> None:
        """儲存模型發出的函式呼叫請求"""
        if not session_id:
            return
        with self._lock:
            turns = self._store.setdefault(session_id, [])
            # 儲存完整的 function_call 物件，角色是 model
            turns.append({
                "role": "model",
                "function_call": {
                    "name": func_name,
                    "args": func_args
                }
            })
            if len(turns) > self._max:
                self._store[session_id] = turns[-self._max:]

    def add_tool_response(self, session_id: str, func_name: str, response_data: Any) -> None:
        """儲存工具執行後的回應"""
        if not session_id:
            return
        with self._lock:
            turns = self._store.setdefault(session_id, [])
            # 儲存完整的 function_response 物件，角色是 tool
            turns.append({
                "role": "tool",
                "function_response": {
                    "name": func_name,
                    "response": response_data
                }
            })
            if len(turns) > self._max:
                self._store[session_id] = turns[-self._max:]

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