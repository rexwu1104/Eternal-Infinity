import nextcord
from nextcord.ext import (
	commands
)
from .embeds import (
	info_embed
)
from .views import (
	ControlBoard
)

async def play_(self, ctx: commands.Context, q: str, t: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel: # user not in any channel
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel: # user not in music-playing channel
		return

	if not controller.client:
		controller.channel = ctx.author.voice.channel
		controller.client = await controller.channel.connect()

	if controller.is_url(q):
		"""
		q is a url, maybe a youtube video url, youtube playlist
		url, spotify track url, spotify playlist url or spotify
		album url
		"""
		controller.tmps.append([
			q, ctx.author
		])
		await controller.load(-1)
	else:
		"""
		q is not a url, just a query, let me to search result
		"""
		await controller.search(q, ctx)
		await controller.load(-1)

	msg = await ctx.send(
		embed=info_embed(controller),
		view=ControlBoard(controller)
	)
	controller.message = msg
	
	controller.play()