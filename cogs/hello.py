from discord.ext import commands
import json

from request.google_chat import google_request
from request.model import ChatRequest

class Hello(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command()
    async def hello(self, ctx):
        await ctx.send('Hello!')
        
    @commands.command()
    async def chat(self, ctx, *, message: str | None = None):
        if not message:
            await ctx.send('用法: $chat 你的訊息')
            return
        
        print(f"傳送message給模型: {message}")
        req = ChatRequest(
            prompt=message,
            session_id=str(ctx.author.id),
            system_prompt="請全程使用中文輸出模型內容。",
        )
        resp = await google_request(req)
        print(f"模型回傳: {resp}")
        text = resp.get("text") or ""
        await ctx.send(text or "（無回覆）")
        
async def setup(bot):
    await bot.add_cog(Hello(bot))