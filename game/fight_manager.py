
import random
from typing import Any, Callable, Dict
import inspect
import json

from request.google_chat import google_request
from request.model import ChatRequest

def perform_d100_check(success_rate: int) -> str:
    """
    Performs a D100 check, including rules for critical success and failure.

    - A roll of 1 is a 'Critical Failure'.
    - A roll of 100 is a 'Critical Success'.
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

    # Priority check for critical failure and success
    if roll_result == 1:
        status = "Critical Failure"
    elif roll_result == 100:
        status = "Critical Success"
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
        
        tools_declaration = [
            {
                "function_declarations": [
                    {
                        "name": "perform_d100_check",
                        "description": "Performs a 100-sided die (d100) check against a given success rate. If the user does not provide a specific success rate and asks the AI to decide, you MUST invent a plausible success rate based on the story's context before calling this function. Then, call the function with the rate you decided on.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "success_rate": {
                                    "type": "NUMBER",
                                    "description": "An integer between 1 and 100 representing the probability of success. If the user does not specify this value, you are responsible for determining a reasonable value based on the narrative context (e.g., a skilled hero has a higher rate, a difficult task has a lower rate)."
                                }
                            },
                            "required": ["success_rate"]
                        }
                    }
                ]
            }
        ]
        
        req = ChatRequest(
            prompt=message,
            session_id="fixed_003",
            system_prompt="請全程使用中文輸出模型內容。你是一位經驗豐富的TRPG遊戲主持人(GM)。當玩家的行動需要透過工具(Function)進行技能檢定，但玩家沒有提供具體的數值(例如成功率)時，你有責任和權力根據當前的故事情境，主動為玩家設定一個合理的數值，然後直接使用該工具來推動故事發展。不要向玩家詢問數值，要自信地做出決定。",
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





