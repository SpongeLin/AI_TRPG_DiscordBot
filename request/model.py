from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_output_tokens: Optional[int] = 12800
    temperature: Optional[float] = 0.7

    toolReturn: Optional[bool] = False

    # New optional fields
    session_id: Optional[str] = None
    use_history: Optional[bool] = True
    history_turns: Optional[int] = 10
    system_prompt: Optional[str] = None
    return_raw: Optional[bool] = False
    clear_session: Optional[bool] = False
    tools_declaration: Optional[object] = None
    function_name: Optional[str] = None