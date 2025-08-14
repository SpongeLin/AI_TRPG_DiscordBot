import os
import httpx
import json
from typing import Optional, Any, Dict, List, Literal

# Local modules
from request.memory import conversation_store, ConversationTurn
from request.config import get_default_model, get_timeout_seconds, get_max_retries, get_retry_backoff_base
from request.logger_setup import logger
from request.utils_http import post_json_with_retries
from request.model import ChatRequest # 確保你的 ChatRequest 模型能接受額外欄位

# REVISED: 在 ChatRequest 中增加 function_name 欄位
# 你需要在你的 model.py 中修改 ChatRequest
# from pydantic import BaseModel
# class ChatRequest(BaseModel):
#     ...
#     toolReturn: Optional[bool] = False
#     function_name: Optional[str] = None # <-- 新增此行

# 安全設定保持不變
UNCENSORED_CATEGORIES = [
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
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


# REVISED: 大幅修改此函式以正確處理儲存的新結構
def _build_history_contents(history: List[ConversationTurn]) -> List[Dict[str, Any]]:
    contents: List[Dict[str, Any]] = []
    for turn in history:
        role = turn.get("role")
        part = {} # 初始化一個空的 Part 物件

        if role == "user":
            part = {"text": turn.get("text", "")}
            contents.append({"role": "user", "parts": [part]})

        elif role == "model":
            if "text" in turn:
                part = {"text": turn.get("text", "")}
            elif "function_call" in turn:
                # 正確的邏輯：只提取 function_call 物件，而不是整個 turn
                part = {"function_call": turn.get("function_call")}
            else:
                continue # 如果是空的 model turn，跳過

            contents.append({"role": "model", "parts": [part]})

        elif role == "tool":
            if "function_response" in turn:
                # 正確的邏輯：只提取 function_response 物件，而不是整個 turn
                part = {"function_response": turn.get("function_response")}
            else:
                continue # 如果是空的 tool turn，跳過
            
            contents.append({"role": "tool", "parts": [part]})

    return contents

# REVISED: 重構核心請求和儲存邏輯
async def google_request(req: ChatRequest):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("GOOGLE_API_KEY is not set")

    model = req.model or get_default_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    # 清除 session (如果需要)
    if req.clear_session and req.session_id:
        conversation_store.clear_session(req.session_id)

    # 1. 準備歷史對話
    contents: List[Dict[str, Any]] = []
    if req.use_history and req.session_id:
        history = conversation_store.get_recent(req.session_id, max_turns=int(req.history_turns or 8))
        # 注意：這裡的建構函式是舊的，我們將在下面處理完整的 contents
        # contents.extend(_build_history_contents(history)) # 我們將把所有 turn 放在一起處理

    # 2. 處理並儲存當前回合 (可能是 user 或 tool)
    if req.session_id:
        if req.toolReturn:
            # 這是工具的回應
            if not req.function_name:
                raise ValueError("toolReturn is True, but function_name is not provided.")
            
            try:
                # req.prompt 應該是 JSON 字串，我們需要解析它
                response_data = json.loads(req.prompt)
            except json.JSONDecodeError:
                raise ValueError("toolReturn is True, but the prompt is not a valid JSON string.")

            # 存入歷史
            conversation_store.add_tool_response(req.session_id, req.function_name, response_data)

        else:
            # 這是一個普通的使用者訊息
            conversation_store.add_turn(req.session_id, role="user", text=req.prompt)

    # 3. 重新從 store 獲取完整的、包含當前回合的歷史，並建構 contents
    if req.use_history and req.session_id:
         # 獲取包含剛剛新增回合的最新歷史
        final_history = conversation_store.get_recent(req.session_id, max_turns=int(req.history_turns or 8) + 1)
        contents = _build_history_contents(final_history)
    else:
        # 如果不使用歷史，只處理當前回合
        if req.toolReturn:
            # 邏輯上 toolReturn 不應該在沒有歷史的情況下發生，但為了完整性做處理
            response_data = json.loads(req.prompt)
            contents.append({"role": "tool", "parts": [{"function_response": {"name": req.function_name, "response": response_data}}]})
        else:
            contents.append({"role": "user", "parts": [{"text": req.prompt}]})

    body: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": int(req.max_output_tokens or 1024),
            "temperature": float(req.temperature or 0.7),
        },
        "safetySettings": UNCENSORED_CATEGORIES
    }

    if req.system_prompt:
        body["systemInstruction"] = {"parts": [{"text": req.system_prompt}]}
        
    if req.tools_declaration:
        body["tools"] = req.tools_declaration

    timeout_seconds = get_timeout_seconds()
    max_retries = get_max_retries()
    backoff_base = get_retry_backoff_base()

    # 為了 debug，打印出最終發送的 body
    logger.info("Sending request body to Gemini: %s", json.dumps(body, indent=2, ensure_ascii=False))

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        r = await post_json_with_retries(client, url, json=body, headers={"content-type": "application/json"}, max_retries=max_retries, backoff_base=backoff_base)

    if r.status_code != 200:
        logger.warning("google_chat non-200 status=%s body=%s", r.status_code, r.text)
        raise Exception(r.text)

    data = r.json()
    
    func_call = detect_tools_declaration(data)
    text = _extract_text_from_gl_response(data)

    # 4. 儲存模型的回應 (可能是文字或 function call)
    if req.session_id:
        if text:
            conversation_store.add_turn(req.session_id, role="model", text=text)
        if func_call:
            conversation_store.add_func_call(req.session_id, func_call["function_name"], func_call["function_args"])

    # 準備最終的回應
    resp: Dict[str, Any] = {"text": text, "model": model}
    if req.session_id:
        resp["session_id"] = req.session_id
    if req.return_raw:
        resp["raw"] = data
    if func_call:
        resp["function_call"] = func_call
    return resp