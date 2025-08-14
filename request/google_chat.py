from typing import Optional, Any, Dict, List, Literal

import os
import asyncio
import httpx
from pydantic import BaseModel

# Local modules
from request.memory import conversation_store, ConversationTurn
from request.config import (
    get_default_model,
    get_timeout_seconds,
    get_max_retries,
    get_retry_backoff_base,
)
from request.logger_setup import logger
from request.utils_http import post_json_with_retries
from request.model import ChatRequest

# Safety settings to disable category blocking
UNCENSORED_CATEGORIES = [
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_CIVIC_INTEGRITY",
        "threshold": "BLOCK_NONE",
    },
]

def detect_tools_declaration(data: Dict[str, Any]):
    try:
        candidates = data.get('candidates') or []
        if not candidates or not isinstance(candidates[0], dict):
            return None

        content = candidates[0].get('content') or {}
        if not isinstance(content, dict):
            return None

        parts = content.get('parts') or []
        if not parts or not isinstance(parts[0], dict):
            return None

        function_call = parts[0].get('functionCall')
        if not isinstance(function_call, dict):
            return None

        function_name = function_call.get('name')
        function_args = function_call.get('args', {})
        if not function_name:
            return None

        print(f"🤖 AI 回應: 偵測到需要呼叫函式 '{function_name}'")
        print(f"   - 函式參數: {function_args}")
        return {"function_name": function_name, "function_args": function_args}
    except Exception:
        return None

def _extract_text_from_gl_response(data: Dict[str, Any]) -> str:
    try:
        candidates: List[Dict[str, Any]] = data.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        texts: List[str] = []
        for p in parts:
            if isinstance(p, dict) and p.get("text"):
                texts.append(p["text"])
        return "\n".join(texts)
    except Exception:
        return ""


def _build_history_contents(history: List[ConversationTurn]) -> List[Dict[str, Any]]:
    contents: List[Dict[str, Any]] = []
    for turn in history:
        role: Literal["user", "model"] = turn["role"]
        text: str = turn["text"]
        contents.append({
            "role": role,
            "parts": [{"text": text}],
        })
    return contents

async def google_request(req: ChatRequest):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("GOOGLE_API_KEY is not set")

    model = req.model or get_default_model()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    )

    # Prepare conversation contents
    contents: List[Dict[str, Any]] = []
    if req.clear_session and req.session_id:
        conversation_store.clear_session(req.session_id)

    if req.use_history and req.session_id:
        history = conversation_store.get_recent(req.session_id, max_turns=int(req.history_turns or 8))
        contents.extend(_build_history_contents(history))

    # Append current user turn
    contents.append({
        "role": "user",
        "parts": [{"text": req.prompt}],
    })
    

    body: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": int(req.max_output_tokens or 1024),
            "temperature": float(req.temperature or 0.7),
        },
        "safetySettings": UNCENSORED_CATEGORIES
    }

    if req.system_prompt:
        body["systemInstruction"] = {
            "parts": [{"text": req.system_prompt}]
        }
        
    if req.tools_declaration:
        body["tools"] = req.tools_declaration

    timeout_seconds = get_timeout_seconds()
    max_retries = get_max_retries()
    backoff_base = get_retry_backoff_base()

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        r = await post_json_with_retries(
            client=client,
            url=url,
            json=body,
            headers={"content-type": "application/json"},
            max_retries=max_retries,
            backoff_base=backoff_base,
        )

    if r.status_code != 200:
        logger.warning("google_chat non-200 status=%s body=%s", r.status_code, r.text)
        raise Exception(r.text)

    data = r.json()
    
    func_call = detect_tools_declaration(data)
    
    text = _extract_text_from_gl_response(data)

    # Persist turns when session_id is present
    if req.session_id:
        conversation_store.add_turn(req.session_id, role="user", text=req.prompt)
        if text:
            conversation_store.add_turn(req.session_id, role="model", text=text)

    resp: Dict[str, Any] = {"text": text, "model": model}
    if req.session_id:
        resp["session_id"] = req.session_id
    if req.return_raw:
        resp["raw"] = data
    if func_call:
        resp["function_call"] = func_call
    return resp