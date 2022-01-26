from nextcord.ext import commands
from core.cog_append import Cog

from .help_method import BotHelpCommand

class Help(Cog):
	def __init__(self, bot: commands.Bot):
		self._original_help_command = bot.help_command
		bot.help_command = BotHelpCommand()
		bot.help_command.cog = self

	def cog_unload(self):
		self.bot.help_command = self._original_help_command

def setup(bot: commands.Bot):
	bot.add_cog(Help(bot))