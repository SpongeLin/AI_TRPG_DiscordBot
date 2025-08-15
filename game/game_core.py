from game.func_tool import perform_d100_check, read_system_prompt
from request.google_chat import google_request
from request.model import ChatRequest


class GameCore:
    def __init__(self):
        pass
    
    async def process_command(self, ctx, func, args):
        print(f"func: {func}, args: {args}")
        
        if func == "DICE":
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
        elif func == "Damage":
            self.damage(args)
        else:
            await ctx.send(f"發現擲骰指令，但未使用DICE")
            
    def damage(self, args: str):
        target, damage = args.split(",")
        print(f"target: {target}, damage: {damage}")
        pass
            
game_core = GameCore()