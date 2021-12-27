import nextcord
from nextcord.ext import (
	commands
)
from .embeds import (
	info_embed
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
		controller.lengthen()

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