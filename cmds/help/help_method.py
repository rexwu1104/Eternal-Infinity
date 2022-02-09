from email.headerregistry import Group
from typing import List, Optional, Set
from nextcord.ext import commands
from nextcord.ui import View, Select, Button, button
from nextcord import Embed, Color, SelectOption, Interaction, ButtonStyle

class BotHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self.context, command)
    
    async def _help_view(
        self,
        mapping: Optional[dict] = None,
        command_set: Optional[Set[commands.Command]] = None,
        choices: Optional[List[str]] = None
    ):
        class HelpSelect(Select):
            cho = choices
            cmd = command_set
            mpi = mapping
            
            def __init__(selfi, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                
            async def callback(selfi, interaction: Interaction):
                if selfi.cho:
                    mapping = self.get_bot_mapping()
                    embed = await self._help_embed(
                        title="Commands",
                        description=self.context.bot.description,
                        mapping=mapping)
                    view = await self._help_view(mapping=mapping)
                elif selfi.cmd:
                    command = self.context.bot.get_command(selfi.values[0])
                    embed = await self._help_embed(
                        title=command.qualified_name,
                        description=command.help,
                        command_set=command.commands if isinstance(command, commands.Group) else None)
                    choices = ["home"]
                    view = await self._help_view(choices=choices)
                elif selfi.mpi:
                    cog = self.context.bot.get_cog(selfi.values[0])
                    embed = await self._help_embed(
                        title=cog.qualified_name,
                        description=cog.description,
                        command_set=cog.get_commands())
                    view = await self._help_view(command_set=cog.get_commands())
                    
                await interaction.message.edit(embed=embed, view=view)
                await interaction.response.defer()
                
            @classmethod
            async def create(cls):
                options = []
                if cls.cho:
                    for choice in cls.cho:
                        options.append(
                            SelectOption(
                                label=choice,
                                value=choice))
                elif cls.cmd:
                    filtered = await self.filter_commands(cls.cmd, sort=True)
                    for command in filtered:
                        label = command.name
                        
                        options.append(
                            SelectOption(
                                label=label,
                                value=label))
                elif cls.mpi:
                    for cog, command_set in mapping.items():
                        filtered = await self.filter_commands(command_set, sort=True)
                        if not filtered:
                            continue
                        
                        label = cog.qualified_name if cog else False
                        if not label:
                            continue
                        
                        options.append(
                            SelectOption(
                                label=label,
                                value=label))
                        
                return cls(placeholder="Choose a command", options=options, row=0)
                
        class HelpView(View):
            def __init__(selfi) -> None:
                super().__init__(timeout=None)
                
            @button(label='cancel', emoji='❌', custom_id='close', style=ButtonStyle.grey, row=1)
            async def close(selfi, button: Button, interaction: Interaction):
                button.view.stop()

                await interaction.message.delete()
                await interaction.response.defer()
                
            @button(label='home', emoji='🏠', custom_id='home', style=ButtonStyle.grey, row=1)
            async def home(selfi, button: Button, interaction: Interaction):
                mapping = self.get_bot_mapping()
                embed = await self._help_embed(
                    title="Commands",
                    description=self.context.bot.description,
                    mapping=mapping)
                view = await self._help_view(mapping=mapping)
        
                await interaction.message.edit(embed=embed, view=view)
                await interaction.response.defer()
                
            @classmethod
            async def create(cls):
                ret = cls()
                ret.add_item(
                    await HelpSelect.create()
                )
                
                return ret
            
        return await HelpView.create()
    
    async def _help_embed(
        self,
        title: str,
        description: Optional[str] = None,
        mapping: Optional[dict] = None,
        command_set: Optional[Set[commands.Command]] = None
    ):
        embed = Embed(
            title=title,
            color=Color.random())
        
        if description:
            embed.description = f"{description}"
            
        if command_set:
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=f"Use `{self.context.clean_prefix}help {command.name}` to get help", inline=True)
        elif mapping:
            for cog, command_set in mapping.items():
                filtered = await self.filter_commands(command_set, sort=True)
                if not filtered:
                    continue
                
                name = cog.qualified_name if cog else "No Category"
                value = (
                    f"{cog.description}\n"
                    if cog
                    else "The command only for developer"
                )
                
                embed.add_field(name=name, value=value)
                
        return embed
     
    async def send_bot_help(self, mapping: dict):
        embed = await self._help_embed(
            title="Commands",
            description=self.context.bot.description,
            mapping=mapping)
        view = await self._help_view(mapping=mapping)
        
        await self.context.message.delete()        
        await self.get_destination().send(embed=embed, view=view)
        
    async def send_command_help(self, command: commands.Command):
        embed = await self._help_embed(
            title=command.qualified_name,
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None)
        choices = ["home"]
        view = await self._help_view(choices=choices)
        
        await self.get_destination().send(embed=embed, view=view)
    
    async def send_cog_help(self, cog: commands.Cog):
        embed = await self._help_embed(
            title=cog.qualified_name,
            description=cog.description,
            command_set=cog.get_commands())
        view = await self._help_view(command_set=cog.get_commands())
        
        await self.get_destination().send(embed=embed, view=view)
    
    send_group_help = send_command_help