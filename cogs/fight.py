from discord.ext import commands
from request.google_chat import google_request
from request.model import ChatRequest
from game.fight_manager import fight_manager


class Fight(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command()
    async def roll(self, ctx, *, message: str | None = None):
        if not message:
            await ctx.send('用法: $roll 你的訊息')
            return
        
        await fight_manager.roll_dice(ctx, message)

    @commands.command()
    async def f1(self, ctx, *, message: str | None = None):
        if not message:
            await ctx.send('用法: $fight 你的訊息')
            return
        
        fight_manager.enter_message("001", message)
        #fight_manager.enter_message(ctx.author.id, message)

    @commands.command()
    async def f2(self, ctx, *, message: str | None = None):
        if not message:
            await ctx.send('用法: $fight 你的訊息')
            return
        
        fight_manager.enter_message("002", message)
        #fight_manager.enter_message(ctx.author.id, message)

async def setup(bot):
    await bot.add_cog(Fight(bot))