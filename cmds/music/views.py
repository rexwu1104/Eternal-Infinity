from nextcord import (
	Interaction,
	ButtonStyle
)
from nextcord.ui import (
	button,
	View,
	Select,
	Button
)
from .embeds import (
	info_embed,
	queue_embed,
	now_embed
)

style = ButtonStyle.grey
class ControlBoard(View):
	def __init__(self, controller):
		self.controller = controller
		super().__init__(timeout=None)

		if self.controller.volume == 0.0:
			self.whisper_.disabled = True
		elif self.controller.volume == 2.0:
			self.lounder_.disabled = True

		if self.controller.client.is_paused():
			self.play_or_pause_.emoji = '▶️'
		else:
			self.play_or_pause_.emoji = '⏸️'

		if self.controller.loop_range is None or \
			 type(self.controller.loop_range) == str:
			self.loop_.emoji = '➡️'
		elif type(self.controller.loop_range) == int:
			self.loop_.emoji = '🔂'
		elif type(self.controller.loop_range) == list:
			self.loop_.emoji = '🔁'

	def check(self, member):
		return self.controller.queue[self.controller.now_pos][1] == member and member.voice is not None

	def check_dj(self, member):
		return member.voice is not None and (member in self.controller.DJs or len(member.voice.channel.members) == 2)

	@button(custom_id='first', style=style, emoji='⏮️', row=0)
	async def first_(self, button: Button, interaction: Interaction):
		if not self.check_dj(interaction.user):
			return

		await self.controller.prev(self.controller.now_pos)
		await interaction.response.defer()
		self.play_or_pause_.emoji = '⏸️'

		await self.controller.message.edit(view=self)

	@button(custom_id='prev', style=style, emoji='⏪', row=0)
	async def prev_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user) and not self.check_dj(interaction.user):
			return
			
		await self.controller.prev(1)
		await interaction.response.defer()
		self.play_or_pause_.emoji = '⏸️'

		await self.controller.message.edit(view=self)

	@button(custom_id='play_or_pause', style=style, emoji='⏸️', row=0)
	async def play_or_pause_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user) and not self.check_dj(interaction.user):
			return
			
		if self.controller.client.is_paused():
			button.emoji = '⏸️'
			self.controller.client.resume()
		else:
			button.emoji = '▶️'
			self.controller.client.pause()

		await self.controller.message.edit(view=self)

		await interaction.response.pong()

	@button(custom_id='next', style=style, emoji='⏩', row=0)
	async def next_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user) and not self.check_dj(interaction.user):
			return
			
		await self.controller.skip(1)
		await interaction.response.defer()
		self.play_or_pause_.emoji = '⏸️'

		await self.controller.message.edit(view=self)

	@button(custom_id='last', style=style, emoji='⏭️', row=0)
	async def last_(self, button: Button, interaction: Interaction):
		if not self.check_dj(interaction.user):
			return
			
		await self.controller.skip(len(self.controller.tmps) - self.controller.now_pos - 1)
		await interaction.response.defer()
		self.play_or_pause_.emoji = '⏸️'

		await self.controller.message.edit(view=self)

	@button(custom_id='whisper', style=style, emoji='🔉', row=1)
	async def whisper_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user) or not self.check_dj(interaction.user):
			return
			
		self.controller.vol(self.controller.volume - 0.1)

		if self.controller.volume == 0.0:
			button.disabled = True

		if self.controller.volume < 2.0:
			self.lounder_.disabled = False

		await self.controller.message.edit(
			view=self,
			embed=info_embed(self.controller)
		)

		await interaction.response.pong()

	@button(custom_id='suffle', style=style, emoji='🔀', row=1)
	async def suffle_(self, button: Button, interaction: Interaction):
		if not self.check_dj(interaction.user):
			return
			
		if self.controller.loop_range != 'random':
			self.controller.loop_range = 'random'
			self.loop_.emoji = '➡️'
		else:
			self.controller.loop_range = None

		await self.controller.message.edit(
			view=self,
			embed=info_embed(self.controller)
		)

		await interaction.response.pong()

	@button(custom_id='stop', style=style, emoji='⏹️', row=1)
	async def stop_(self, button: Button, interaction: Interaction):
		if not self.check_dj(interaction.user):
			return
			
		self.stop()
		await interaction.message.delete()
		await self.controller.client.disconnect()
		self.controller.reset()

		await interaction.response.pong()

	@button(custom_id='loop', style=style, emoji='➡️', row=1)
	async def loop_(self, button: Button, interaction: Interaction):
		if not self.check_dj(interaction.user):
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

		await self.controller.message.edit(
			view=self,
			embed=info_embed(self.controller)
		)

		await interaction.response.pong()

	@button(custom_id='lounder', style=style, emoji='🔊', row=1)
	async def lounder_(self, button: Button, interaction: Interaction):
		if not self.check(interaction.user) or not self.check_dj(interaction.user):
			return
			
		self.controller.vol(self.controller.volume + 0.1)

		if self.controller.volume == 2.0:
			button.disabled = True

		if self.controller.volume > 0.0:
			self.whisper_.disabled = False

		await self.controller.message.edit(
			view=self,
			embed=info_embed(self.controller)
		)

		await interaction.response.pong()

	@button(custom_id='search', style=style, emoji='🔍', row=2)
	async def search_(self, button: Button, interaction: Interaction):
		print(interaction.guild.id, interaction.guild.name)
		print(interaction.user.name)
		print("#-------------------------------")
		def check(m):
			return m.author == interaction.user

		ctx = await self.controller.bot.bot.get_context(
			self.controller.message
		)
		ctx.author = interaction.user

		await interaction.response.defer()

		s = await ctx.send('**please input any content**')
		m = await self.controller.bot.bot.wait_for('message', check=check)
		await s.delete()
		await m.delete()

		await self.controller.funcs['search'](
			self.controller.bot,
			ctx,
			m.content
		)

	@button(custom_id='queue', style=style, emoji='📜', row=2)
	async def queue_(self, button: Button, interaction: Interaction):
		await self.controller.message.edit(
			embed=queue_embed(self.controller, interaction.user)
		)

		await interaction.response.pong()

	@button(custom_id='home', style=style, label='🏠', row=2)
	async def home_(self, button: Button, interaction: Interaction):
		await self.controller.message.edit(
			embed=info_embed(self.controller)
		)

		await interaction.response.pong()

	@button(custom_id='info', style=style, emoji='📄', row=2)
	async def info_(self, button: Button, interaction: Interaction):
		await self.controller.message.edit(
			embed=now_embed(self.controller, interaction.user)
		)

		await interaction.response.pong()

	@button(custom_id='play', style=style, emoji='🔎', row=2)
	async def play_(self, button: Button, interaction: Interaction):
		print(interaction.guild.id, interaction.guild.name)
		print(interaction.user.name)
		print("#-------------------------------")
		def check(m):
			return m.author == interaction.user

		ctx = await self.controller.bot.bot.get_context(
			self.controller.message
		)
		ctx.author = interaction.user

		await interaction.response.defer()
		
		s = await ctx.send('**please input any content**')
		m = await self.controller.bot.bot.wait_for('message', check=check)
		await s.delete()
		await m.delete()

		await self.controller.funcs['play'](
			self.controller.bot,
			ctx,
			m.content
		)

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

			old_pos = self.controller.now_pos
			await self.controller.load(-1)
			await self.controller.load(old_pos, loaded=True)

			await self.controller.message.edit(
				embed=info_embed(self.controller),
				view=ControlBoard(self.controller)
			)

		await interaction.response.defer()
		self.view.stop()

class ResultSelect(View):
	def __init__(self, controller, select_menu):
		self.controller = controller
		super().__init__(timeout=None)

		self.add_item(select_menu)