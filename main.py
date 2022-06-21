try:
    import discord
except:
    __import__('os').system('bash ./install_discord.py.sh')

from Commands.Music import ModeConverter
from config import *

import asyncio
import discord_together

from typing import Optional, Union
from discord import Intents, Interaction, Object, StageChannel, VoiceChannel
from discord.ext import commands
from discord.app_commands import CommandTree

bot = commands.AutoShardedBot(application_id=928250356494913567, command_prefix="t!", intents=Intents.all())
bot._connection._command_tree = None
Applications = CommandTree(bot)

# @bot.event
# async def on_ready():
#     await bot.tree.sync(guild=Object(id=723162132082065501))
    
# @bot.tree.command()
# async def play(interaction: Interaction, url: str):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].play, url=url)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def search(interaction: Interaction, query: str):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].search, query=query)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def join(interaction: Interaction, channel: Optional[Union[VoiceChannel, StageChannel]] = None):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].join, channel=channel)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def leave(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].leave)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def loop(interaction: Interaction, rang: str = None):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].loop, rang=await ModeConverter.convert(rang))
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def shuffle(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].shuffle)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def skip(interaction: Interaction, position: int = None):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].skip, position=position)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def pause(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].pause)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def volume(interaction: Interaction, volume: float):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].volume, vol=volume)
#     await interaction.response.defer()

# @bot.tree.command()
# async def nowinfo(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].nowinfo)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def queue(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].queue)
#     await interaction.response.defer()

# @bot.tree.command()
# async def remove(interaction: Interaction, position: int):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].remove, position=position)
#     await interaction.response.defer()
    
# @bot.tree.command()
# async def together(interaction: Interaction):
#     context: commands.Context = await bot.get_context(interaction.message)
        
#     await context.invoke(bot.cogs['Music'].together)
#     await interaction.response.defer()

async def main():
    await bot.load_extension('Commands')
    async with bot:
        bot.togetherControl = await discord_together.DiscordTogether(token)
        
        await bot.start(token)
        print('new version!!!')
    
asyncio.run(main())