
import random
from typing import Any, Callable, Dict
import inspect
import json
import os
from pathlib import Path
from functools import lru_cache

from request.logger_setup import logger
from game.function_declarations import tools_declaration

from request.google_chat import google_request
from request.model import ChatRequest

#@lru_cache(maxsize=1)
def read_system_prompt() -> str:
    """Read system prompt text with robust path resolution and caching.

    Resolution order:
    1) Env var `SYSTEM_PROMPT_PATH` (absolute or relative to project root)
    2) Default: `<project_root>/prompt/desription.txt`
    """
    try:
        project_root = Path(__file__).resolve().parent.parent
        env_path = os.getenv("SYSTEM_PROMPT_PATH")

        if env_path:
            candidate_path = Path(env_path)
            if not candidate_path.is_absolute():
                candidate_path = project_root / candidate_path
        else:
            candidate_path = project_root / "prompt" / "description.txt"

        content = candidate_path.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning("System prompt file is empty: %s", candidate_path)
        else:
            logger.info("Loaded system prompt from: %s", candidate_path)
        return content
    except FileNotFoundError:
        logger.error("System prompt file not found. Set SYSTEM_PROMPT_PATH or ensure default exists at 'prompt/desription.txt'.")
        return ""
    except Exception as exc:
        logger.exception("Failed to read system prompt: %s", exc)
        return ""

def perform_d100_check(success_rate: int) -> str:
    """
    Performs a D100 check, including rules for critical success and failure.

    - A roll of 1 is a 'Critical Success'.
    - A roll of 100 is a 'Critical Failure'.
    - Otherwise, the result is determined by the success_rate.

    Args:
        success_rate: The probability of success (1-100).

    Returns:
        A JSON string containing the roll result, check status, and the success rate used.
    """
    if not 1 <= success_rate <= 100:
        return json.dumps({
            "error": "Success rate must be between 1 and 100."
        })

    roll_result = random.randint(1, 100)
    status = ""

    # Priority check for critical success and failure
    if roll_result == 1:
        status = "Critical Success"
    elif roll_result == 100:
        status = "Critical Failure"
    # Standard check if not a critical roll
    elif roll_result <= success_rate:
        status = "Success"
    else:
        status = "Failure"

    # Prepare the structured data for return
    result_data = {
        "roll": roll_result,
        "status": status,
        "success_rate_used": success_rate
    }
    
    # Convert the dictionary to a JSON string for the model to parse
    return json.dumps(result_data)

TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "perform_d100_check": perform_d100_check,
}

def call_tool(function_name: str, function_args: Dict[str, Any]) -> Any:
    func = TOOL_REGISTRY.get(function_name)
    if func is None:
        print(f"Unknown tool: {function_name}")
        return None

    # 可選：過濾多餘參數，避免 TypeError
    params = inspect.signature(func).parameters
    safe_args = {k: v for k, v in function_args.items() if k in params}

    return func(**safe_args)

class FightManager:
    def __init__(self):
        self.fight_list = []
        
        
    def enter_message(self, user_id, message):
        print(f"user_id: {user_id}, message: {message}")
        
    async def roll_dice(self, ctx, message, isToolReturn: bool = False):        
        req = ChatRequest(
            prompt=message,
            session_id="fixed_003",
            system_prompt=read_system_prompt(),
            tools_declaration=tools_declaration,
            toolReturn=isToolReturn,
            function_name = "perform_d100_check"
        )
        
        resp = await google_request(req)

        print(f"模型回傳: {resp}")
        
        func_call = resp.get("function_call")
        if func_call:
            result = call_tool(func_call["function_name"], func_call["function_args"])
            print(f"function_call結果: {result}")
            await ctx.send(result)
            await self.roll_dice(ctx, result, True)
            return
        
        text = resp.get("text") or ""
        await ctx.send(f"{text}" or "ai say nothing")
    
fight_manager = FightManager()





