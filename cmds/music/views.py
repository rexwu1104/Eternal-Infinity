from nextcord import (
	Interaction,
	ButtonStyle
)
from nextcord.ext import (
	commands
)
from nextcord.ui import (
	select,
	button,
	View,
	Select,
	Button
)

class ControlBoard(View):
	def __init__(self):
		super().__init__(timeout=None)

	@button(custom_id='first', style=ButtonStyle.secondary, emoji='⏮️', row=0)
	async def first(self, button: button, interaction: Interaction):
		...

	@button(custom_id='prev', style=ButtonStyle.secondary, emoji='⏪', row=0)
	async def prev(self, button: button, interaction: Interaction):
		...

	@button(custom_id='play_or_pause', style=ButtonStyle.secondary, emoji='⏯️', row=0)
	async def play_or_pause(self, button: button, interaction: Interaction):
		...

	@button(custom_id='next', style=ButtonStyle.secondary, emoji='⏩', row=0)
	async def next(self, button: button, interaction: Interaction):
		...

	@button(custom_id='last', style=ButtonStyle.secondary, emoji='⏭️', row=0)
	async def last(self, button: button, interaction: Interaction):
		...

	@button(custom_id='whisper', style=ButtonStyle.secondary, emoji='🔉', row=1)
	async def whisper(self, button: button, interaction: Interaction):
		...

	@button(custom_id='suffle', style=ButtonStyle.secondary, emoji='🔀', row=1)
	async def suffle(self, button: button, interaction: Interaction):
		...

	@button(custom_id='stop', style=ButtonStyle.secondary, emoji='⏹️', row=1)
	async def stop(self, button: button, interaction: Interaction):
		...

	# 🔁🔂
	@button(custom_id='loop', style=ButtonStyle.secondary, emoji='➡️', row=1)
	async def loop(self, button: button, interaction: Interaction):
		...

	@button(custom_id='lounder', style=ButtonStyle.secondary, emoji='🔊', row=1)
	async def lounder(self, button: button, interaction: Interaction):
		...