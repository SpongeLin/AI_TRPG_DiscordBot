# This example requires the 'message_content' intent.

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
async def setup_hook():
    await bot.load_extension('cogs.hello')
    await bot.load_extension('cogs.fight')
bot.setup_hook = setup_hook

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))