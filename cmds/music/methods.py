import nextcord
from nextcord.ext import (
	commands
)

async def play_(self, ctx: commands.Context, q: str, t: str):
	controller = self.controllers[ctx.guild.id]

	if controller.is_url(q):
		"""
		q is a url, maybe a youtube video url, youtube playlist
		url, spotify track url, spotify playlist url or spotify
		album url
		"""
		controller.tmp_queue.append([
			q, ctx.author
		])
		await controller.load(0)
	else:
		await controller.search(q)
		await controller.load(0)

	controller.play()
	await ctx.send(embed=info_embed(controller), view=ControlBoard())