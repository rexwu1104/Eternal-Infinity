from .Music import *
from .Help import *

from discord.ext import commands

async def setup(bot: commands.AutoShardedBot):
    music_bot = Music(bot)
    await music_bot.init()
    await bot.add_cog(music_bot)
    
    await bot.add_cog(Help(bot))