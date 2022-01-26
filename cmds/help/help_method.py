from email.headerregistry import Group
from typing import Optional, Set
from discord import Color
from nextcord.ext import commands
from nextcord.ui import View
from nextcord import Embed

class BotHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self.context, command)
    
    async def _help_view(self):
        class HelpView(View):
            def __init__(self) -> None:
                super().__init__(timeout=None)
                
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
            embed.description = description
            
        if command_set:
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.help, inline=False)
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
        
        await self.get_destination().send("test", embed=embed)
        
    async def send_command_help(self, command: commands.Command):
        embed = await self._help_embed(
            title=command.qualified_name,
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None)
        
        await self.get_destination().send("test", embed=embed)
    
    async def send_cog_help(self, cog: commands.Cog):
        embed = await self._help_embed(
            title=cog.qualified_name,
            description=cog.description,
            command_set=cog.get_commands())
        
        await self.get_destination().send("test", embed=embed)
    
    send_group_help = send_command_help