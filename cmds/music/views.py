import asyncio
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
from .embeds import (
	info_embed
)

style = ButtonStyle.grey

class FindView(View):
	def find(self, condition):
		return [value for idx, value in enumerate(self.children) if condition(value)]

class ControlBoard(FindView):
	def __init__(self, controller):
		self.controller = controller
		super().__init__(timeout=None)

	def check(self, member):
		return self.controller.queue[self.controller.now_pos][1] == member

	@button(custom_id='first', style=style, emoji='⏮️', row=0)
	async def first_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return

		await self.controller.prev(self.controller.now_pos)
		self.find(lambda i: i.custom_id == 'play_or_pause')[0].emoji = '⏸️'

		await interaction.response.edit_message(view=self)

	@button(custom_id='prev', style=style, emoji='⏪', row=0)
	async def prev_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		await self.controller.prev(1)
		self.find(lambda i: i.custom_id == 'play_or_pause')[0].emoji = '⏸️'

		await interaction.response.edit_message(view=self)

	@button(custom_id='play_or_pause', style=style, emoji='⏸️', row=0)
	async def play_or_pause_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		if self.controller.client.is_paused():
			button.emoji = '⏸️'
			self.controller.client.resume()
		else:
			button.emoji = '▶️'
			self.controller.client.pause()

		await interaction.response.edit_message(view=self)

	@button(custom_id='next', style=style, emoji='⏩', row=0)
	async def next_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		await self.controller.skip(1)
		self.find(lambda i: i.custom_id == 'play_or_pause')[0].emoji = '⏸️'

		await interaction.response.edit_message(view=self)

	@button(custom_id='last', style=style, emoji='⏭️', row=0)
	async def last_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		await self.controller.skip(len(self.controller.tmps) - self.controller.now_pos - 1)
		self.find(lambda i: i.custom_id == 'play_or_pause')[0].emoji = '⏸️'

		await interaction.response.edit_message(view=self)

	@button(custom_id='whisper', style=style, emoji='🔉', row=1)
	async def whisper_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		self.controller.vol(self.controller.volume - 0.1)

		if self.controller.volume == 0.0:
			button.disabled = True

		if self.controller.volume < 2.0:
			self.find(lambda i: i.custom_id == 'lounder')[0].disabled = False

		await interaction.response.edit_message(
			view=self,
			embed=info_embed(self.controller)
		)

	@button(custom_id='suffle', style=style, emoji='🔀', row=1)
	async def suffle_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		if self.controller.loop_range != 'random':
			self.controller.loop_range = 'random'
			self.find(lambda i: i.custom_id == 'loop')[0].emoji = '➡️'
		else:
			self.controller.loop_range = None
			interaction.response._responded = True

		await interaction.response.edit_message(
			view=self,
			embed=info_embed(self.controller)
		)

	@button(custom_id='stop', style=style, emoji='⏹️', row=1)
	async def stop_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		self.stop()
		await interaction.message.delete()
		await self.controller.client.disconnect()
		self.controller.reset()

	@button(custom_id='loop', style=style, emoji='➡️', row=1)
	async def loop_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		if self.controller.loop_range is None:
			button.emoji = '🔂'
			self.controller.loop_range = self.controller.now_pos
		elif type(self.controller.loop_range) == int:
			button.emoji = '🔁'
			self.controller.loop_range = [0, len(self.controller.tmps)-1]
		elif type(self.controller.loop_range) == list or \
				 type(self.controller.loop_range) == str:
			button.emoji = '➡️'
			self.controller.loop_range = None

		await interaction.response.edit_message(
			view=self,
			embed=info_embed(self.controller)
		)

	@button(custom_id='lounder', style=style, emoji='🔊', row=1)
	async def lounder_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user):
			return
			
		self.controller.vol(self.controller.volume + 0.1)

		if self.controller.volume == 2.0:
			button.disabled = True

		if self.controller.volume > 0.0:
			self.find(lambda i: i.custom_id == 'whisper')[0].disabled = False

		await interaction.response.edit_message(
			view=self,
			embed=info_embed(self.controller)
		)

	@button(custom_id='search', style=style, emoji='🔍', row=2)
	async def search_(self, button: Button, interaction: Interaction):
		...

	@button(custom_id='queue', style=style, emoji='📜', row=2)
	async def queue_(self, button: Button, interaction: Interaction):
		...

	@button(custom_id='home', style=style, label='🏠', row=2)
	async def home_(self, button: Button, interaction: Interaction):
		...

	@button(custom_id='info', style=style, emoji='📄', row=2)
	async def info_(self, button: Button, interaction: Interaction):
		...

	@button(custom_id='play', style=style, emoji='🔎', row=2)
	async def play_(self, button: Button, interaction: Interaction):
		...

class SelectMenu(Select):
	def __init__(self, controller, options):
		self.controller = controller
		super().__init__(placeholder='choose one music...', custom_id='selectmenu', row=0, options=options)

	@classmethod
	async def create(cls, controller, q: str):
		return cls(
			controller,
			await controller.select_options(q)
		)

	async def callback(self, interaction: Interaction):
		self.controller.tmps.append([
			self.values[0], interaction.user
		])
		
		if self.controller.message is None:
			self.controller.message = interaction.message

			if not self.controller.in_sequence:
				await self.controller.load(-1)
				self.controller.play(command=True)

			await self.controller.message.edit(
				content=None,
				embed=info_embed(self.controller),
				view=ControlBoard(self.controller)
			)
		else:
			await interaction.message.delete()

			await self.controller.message.edit(
				embed=info_embed(self.controller),
				view=ControlBoard(self.controller)
			)

		await interaction.response.pong()
		self.view.stop()

class ResultSelect(FindView):
	def __init__(self, controller, select_menu):
		self.controller = controller
		super().__init__(timeout=None)

		self.add_item(select_menu)