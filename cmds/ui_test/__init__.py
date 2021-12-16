import nextcord as nc
from nextcord.ext import commands
from core.cog_append import Cog

class Dropdown(nc.ui.Select):
	def __init__(self):
		options = [
			nc.SelectOption(label='Red', description='Your favourite colour is red', emoji='🟥'),
			nc.SelectOption(label='Green', description='Your favourite colour is green', emoji='🟩'),
			nc.SelectOption(label='Blue', description='Your favourite colour is blue', emoji='🟦')
		]

		super().__init__(placeholder='Choose your favourite colour...', min_values=1, max_values=1, options=options)

	async def callback(self, interaction: nc.Interaction):
		await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')

class Viewer(nc.ui.View):
	def __init__(self):
		super().__init__()

	def add(self, item):
		self.add_item(item())

class UI_Test(Cog):

	@commands.command()
	async def test(self, ctx: commands.Context):
		view = Viewer()
		view.add(Dropdown)

		await ctx.send('Pick your favourite colour:', view=view)

def setup(bot: commands.Bot):
	bot.add_cog(UI_Test(bot))