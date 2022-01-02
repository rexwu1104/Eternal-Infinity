from nextcord.ext import commands

class Cog(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot: commands.Bot = bot

def setup(bot: commands.Bot):
	bot.add_cog(Cog(bot))