from ..Music import MTranslator

from .Embeds import *

from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Select, View, button
from discord.ext import commands
from discord.ext.commands import AutoShardedBot

__all__ = (
    'CommandsSelect',
    'HelpView',
)

class HelpView(View):
    bot: AutoShardedBot
    translator: MTranslator
    now_action: dict[str, str] = None
    prev_actions: list[dict[str, str]] = []
    after_actions: list[dict[str, str]] = []
    
    def __init__(self, translator: MTranslator, bot: AutoShardedBot, now_action: dict):
        super().__init__(timeout=None)
        
        self.bot = bot
        self.translator = translator
        self.now_action = now_action
        
        self.add_item(CommandsSelect(bot))
        
    @button(custom_id='back', emoji='⬅️', disabled=True, row=1)
    async def _back(self, interaction: Interaction, _: Button):
        context: commands.Context = await self.bot.get_context(interaction.message)
        context.message.author = interaction.user
        await self.bot.help_command._set_context(context, interaction=True)
        
        self.after_actions.append(self.now_action)
        self.now_action = self.prev_actions.pop()
        
        if self._next.disabled:
            self._next.disabled = False
            
        if len(self.prev_actions) == 0:
            self._back.disabled = True
        
        await interaction.message.edit(view=self)
        if 'command' in self.now_action:
            param = self.bot.get_command(self.now_action['command'])
            await self.bot.help_command.send_command_help(param, interaction.message)
        else:
            param = self.bot.help_command.get_bot_mapping()
            await self.bot.help_command.send_bot_help(param, interaction.message)
            
        await interaction.response.defer()
        
    @button(custom_id='next', emoji='➡️', disabled=True, row=1)
    async def _next(self, interaction: Interaction, _: Button):
        context: commands.Context = await self.bot.get_context(interaction.message)
        context.message.author = interaction.user
        await self.bot.help_command._set_context(context, interaction=True)
        
        self.prev_actions.append(self.now_action)
        self.now_action = self.after_actions.pop()
        
        if self._back.disabled:
            self._back.disabled = False
            
        if len(self.after_actions) == 0:
            self._next.disabled = True
        
        await interaction.message.edit(view=self)
        if 'command' in self.now_action:
            param = self.bot.get_command(self.now_action['command'])
            await self.bot.help_command.send_command_help(param, interaction.message)
        else:
            param = self.bot.help_command.get_bot_mapping()
            await self.bot.help_command.send_bot_help(param, interaction.message)
            
        await interaction.response.defer()
        
    @button(custom_id='home', emoji='🏠', row=1)
    async def _home(self, interaction: Interaction, _: Button):
        context: commands.Context = await self.bot.get_context(interaction.message)
        context.message.author = interaction.user
        await self.bot.help_command._set_context(context, interaction=True)
        
        self.prev_actions.append(self.now_action)
        self.now_action = {'bot': 'mapping'}
        
        if self._back.disabled:
            self._back.disabled = False
        
        await interaction.message.edit(view=self)
        await self.bot.help_command.send_bot_help(self.bot.help_command.get_bot_mapping(), interaction.message)
        
        await interaction.response.defer()
        
    @button(custom_id='close', emoji='❌', style=ButtonStyle.red, row=1)
    async def _close(self, interaction: Interaction, _: Button):
        self.stop()
        await interaction.message.delete()
        
class CommandsSelect(Select):
    bot: AutoShardedBot
    view: HelpView
    
    def __init__(self, bot: AutoShardedBot) -> None:
        self.bot = bot
        
        def decorate(l: list):
            return str(l).replace('\'', '').replace('[', '').replace(']', '')
        
        options: list[SelectOption] = []
        for command in bot.walk_commands():
            if isinstance(command.parent, commands.Group):
                continue
            
            options.append(SelectOption(label='Command: ' + command.name,
                                        value=command.name,
                                        description=decorate(command.aliases)))
            
        options.sort(key=lambda v: v.label)
            
        super().__init__(placeholder='Choose a command...',
                         options=options,
                         row=0)
        
    async def callback(self, interaction: Interaction) -> None:
        context: commands.Context = await self.bot.get_context(interaction.message)
        context.message.author = interaction.user
        await self.bot.help_command._set_context(context, interaction=True)
        
        self.view.prev_actions.append(self.view.now_action)
        self.view.after_actions.clear()
        if self.view._back.disabled:
            self.view._back.disabled = False
            
        if not self.view._next.disabled:
            self.view._next.disabled = True
        
        await interaction.message.edit(view=self.view)
        
        if command := self.bot.get_command(self.values[0]):
            self.view.now_action = {'command': command.name}
            await self.bot.help_command.send_command_help(command, interaction.message)
        
        await interaction.response.defer()