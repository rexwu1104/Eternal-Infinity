import discord
from Classes import *

from discord import Message
from discord.ext import commands
from discord.ext.commands import AutoShardedBot

__all__ = (
    'Help',
)

event = commands.Cog.listener()
command = commands.command
group = commands.group

class HelpCommand(commands.HelpCommand):
    bot: AutoShardedBot
    controller: MController
    
    def __init__(self, bot: AutoShardedBot, controller: MController) -> None:
        super().__init__()
        
        self.bot = bot
        self.controller = controller
        
    @property
    def help(self):
        return '{2.command_prefix}help [command]\n\n{1}:\n{2.command_prefix}help\n{2.command_prefix}help play'
    
    @help.setter
    def help(self, _): ...
        
    async def _set_context(self, context: commands.Context, *args: tuple, **kwargs: dict) -> None:
        commands.help._context.set(context)
        
        if 'interaction' not in kwargs:
            return await self.command_callback(context, *args, **kwargs)
    
    async def send_bot_help(self, mapping: dict, message: Message = None) -> None:
        channel: discord.abc.MessageableChannel = self.get_destination()
        container = self.controller.containers[channel.guild.id]
        if message:
            return await message.edit(embed=await help_embed(
                mapping,
                container.translater,
                self))
        else:
            await self.context.message.delete()
            return await channel.send(
                view=HelpView(container.translater,
                              self.bot,
                              {'bot': 'mapping'}),
                embed=await help_embed(mapping,
                                       container.translater,
                                       self))
    
    async def send_command_help(self, command: commands.Command, message: Message = None) -> None:
        channel: discord.abc.MessageableChannel = self.get_destination()
        container = self.controller.containers[channel.guild.id]
        if message:
            return await message.edit(embed=await command_embed(
                command,
                container.translater,
                self))
        else:
            await self.context.message.delete()
            return await channel.send(
                view=HelpView(container.translater,
                              self.bot,
                              {'command': command.name}),
                embed=await command_embed(command,
                                          container.translater,
                                          self))
        
class Help(commands.Cog):
    'The help command.'
    
    _original_help_command: HelpCommand
    
    help_command: HelpCommand
    bot: AutoShardedBot
    controller: MController
    
    def __init__(self, bot: AutoShardedBot) -> None:
        super().__init__()
        
        self.controller = bot.cogs.get('Music').controller
        
        self._original_help_command = bot.help_command
        bot.help_command = HelpCommand(bot, self.controller)
        bot.help_command.cog = self
        
        self.bot = bot