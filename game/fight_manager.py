from typing import Any, Callable, Dict
import inspect
import json
import os
from pathlib import Path

import re

from game.game_core import game_core
from request.logger_setup import logger
from game.func_tool import perform_d100_check, send_to_google_ai

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
    # 預編譯的指令樣式正則，避免每次呼叫重編譯
    COMMAND_PATTERN = re.compile(r"☆([A-Za-z_][A-Za-z0-9_]*)\:\{([^}]*)\}☆")
    def __init__(self):
        self.fight_list = []
        
        
    def enter_message(self, user_id, message):
        print(f"user_id: {user_id}, message: {message}")
        
    async def send_message(self, ctx, message, session_id):        
        resp = await send_to_google_ai(message, session_id)
        text = resp.get("text") or ""
        
        command_result = self.parse_command_result(text)
        text = self.remove_command_text(text)
        print(f"text: {text}")
        await ctx.send(f"{text}" or "ai say nothing")

        if command_result:
            await game_core.process_command(ctx, command_result["func"], command_result["args"])
        
    def parse_command_result(self, text: str) -> Dict[str, str]:
        m = self.COMMAND_PATTERN.search(text)
        if m:
            func = m.group(1)
            args = m.group(2).strip()
            return {"func": func, "args": args}
        return None
    
    def remove_command_text(self, text: str) -> str:
        return self.COMMAND_PATTERN.sub("", text)
    
fight_manager = FightManager()





