import nextcord
from nextcord.ext import (
	commands
)
from .embeds import (
	info_embed,
	queue_embed,
	now_embed
)
from .views import (
	ControlBoard,
	SelectMenu,
	ResultSelect
)

async def play_(self, ctx: commands.Context, q: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.client:
		controller.channel = ctx.author.voice.channel
		controller.client = await controller.channel.connect()

	if controller.is_url(q):
		controller.tmps.append([
			q, ctx.author
		])
	else:
		await controller.search(q, ctx)

	if not controller.in_sequence:
		await controller.load(-1)
		controller.play(command=True)
	else:
		old_pos = controller.now_pos
		await controller.load(-1)
		await controller.load(old_pos, loaded=True)

	if controller.message is None:
		msg = await ctx.send(
			embed=info_embed(controller),
			view=ControlBoard(controller)
		)
		controller.message = msg
	else:
		await controller.message.edit(embed=info_embed(controller))

async def search_(self, ctx: commands.Context, q: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.client:
		controller.channel = ctx.author.voice.channel
		controller.client = await controller.channel.connect()

	await ctx.send(
		'**take a choice~~**',
		view=ResultSelect(
			controller,
			await SelectMenu.create(controller, q)
		)
	)

async def queue_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	await controller.message.edit(embed=queue_embed(
		controller, ctx.author
	))

async def nowplay_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	await controller.message.edit(embed=now_embed(
		controller, ctx.author
	))

async def loop_(self, ctx: commands.Context, t: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	if t is None:
		if controller.loop_range is None:
			controller.loop_range = controller.now_pos
		else:
			controller.loop_range = None
	elif t.lower() == 'all':
		controller.loop_range = [0, len(controller.tmps) - 1]
	elif t.lower() == 'random':
		controller.loop_range = 'random'
	elif (t.find('-') != -1 and t.count('-') == 1):
		if controller.now_pos > loop_range[1]:
			await controller.skip(0)
		elif controller.now_pos < loop_range[0]:
			await controller.prev(0)

		controller.loop_range = list(map(
			lambda v: int(v) - 1,
			t.split('-')
		))
	elif (t.find('~') != -1 and t.count('~') == 1):
		if controller.now_pos > loop_range[1]:
			await controller.skip(0)
		elif controller.now_pos < loop_range[0]:
			await controller.prev(0)

		controller.loop_range = list(map(
			lambda v: int(v) - 1,
			t.split('~')
		))

	await controller.message.edit(
		view=ControlBoard(controller),
		embed=info_embed(
			controller
		)
	)