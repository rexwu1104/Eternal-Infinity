from ..Music import MTranslator
from ..Imports import await_run

from datetime import datetime
from discord import Color, Embed
from discord.ext import commands
from typing import Set

__all__ = (
    'command_embed',
    'help_embed',
)

async def command_embed(command: commands.Command, translator: MTranslator, help: commands.HelpCommand) -> Embed:
    ctx: commands.Context = help.context
    embed = Embed(color=Color.random(),
                  title=command.name,
                  timestamp=datetime.now())
    
    embed.add_field(name=translator.translate('usage'), value=f'''```\n{
        command.help.format(translator.translate("or"), translator.translate("example"), help.bot)
    }\n```''')
    
    embed.set_author(name=ctx.author.name,
                     icon_url=ctx.author.avatar.url)
    
    return embed
    
async def help_embed(mapping: dict[commands.Cog, Set[commands.Command]], translator: MTranslator, help: commands.HelpCommand)-> Embed:
    ctx: commands.Context = help.context
    embed = Embed(color=Color.random(),
                  title=translator.translate('Command list'),
                  timestamp=datetime.now())
    
    for cog, command_set in mapping.items():
        filtered = await help.filter_commands(command_set, sort=True)
        if not filtered:
            continue
        
        name = cog.qualified_name if cog else 'No Category'
        
        command_count = 0
        result = '```\n'
        for command in filtered:
            command_count += 1
            result += f'{command.name}, '
            
            if command_count % 3 == 0:
                result = result[:-2] + '\n'
                
        value = (result[:-3] if result[-1] == '\n' else result[:-2]) + '\n```'
        embed.add_field(name=name, value=value)
    
    embed.set_author(name=ctx.author.name,
                     icon_url=ctx.author.avatar.url)
    
    return embed