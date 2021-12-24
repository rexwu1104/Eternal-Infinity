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