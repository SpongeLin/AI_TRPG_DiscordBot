from game.func_tool import perform_d100_check, read_system_prompt, send_to_google_ai
from request.google_chat import google_request
from request.model import ChatRequest
import re
from typing import Dict

from game.fight_manager import fight_manager

class GameCore:
    def __init__(self):
        pass
    
    # 預編譯的指令樣式正則，避免每次呼叫重編譯
    COMMAND_PATTERN = re.compile(r"☆([A-Za-z_][A-Za-z0-9_]*)\:\{([^}]*)\}☆")
        
    def enter_message(self, user_id, message):
        print(f"user_id: {user_id}, message: {message}")
        
    async def send_message(self, ctx, message, session_id):        
        resp = await send_to_google_ai(message, session_id)
        text = resp.get("text") or ""
        
        command_result = self.parse_command_result(text)
        text = self.remove_command_text(text)
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
    
    async def process_command(self, ctx, func, args):
        print(f"func: {func}, args: {args}")
        
        if func == "DICE":
            await self.dice(ctx, args)
        elif func == "Damage":
            await self.damage(ctx, args)
        else:
            await ctx.send(f"發現擲骰指令，但未使用DICE")
    
    async def dice(self, ctx, args: str):
        dice_message = perform_d100_check(int(args))
        print(f"D100檢定結果: {dice_message}")
        
        await ctx.send(dice_message)
            
        req = ChatRequest(
            prompt=dice_message,
            session_id="fixed_003",
            system_prompt=read_system_prompt()
        )
        resp = await google_request(req)
        
        print(f"模型回傳: {resp}")
        
        text = resp.get("text") or ""
        await ctx.send(f"{text}" or "ai say nothing")
            
    async def damage(self, ctx, args: str):
        target, damage = args.split(",")
        result = fight_manager.damage(target, int(damage))
        
        if result["status"] == "dead":
            print(result["result"])
            await ctx.send(result["result"])
            #給模型結束請求做收尾
        elif result["status"] == "damage":
            print(result["result"])
        else:
            print(f"發現傷害指令，但Damage指令錯誤, {result['result']}")
            
game_core = GameCore()