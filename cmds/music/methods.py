import lavapy
import asyncio
from lavapy.ext import spotify
from nextcord import (
	VoiceChannel
)
from nextcord.ext import commands
from .cls import (
	Player
)

async def join_(self, ctx: commands.Context, channel: VoiceChannel, nodeInit):
	controller = self.controllers[ctx.guild.id]

	if not channel:
		try:
			channel = ctx.author.voice.channel
		except AttributeError:
			return

	await nodeInit(channel)
	print(lavapy.NodePool.nodes())
	await asyncio.sleep(1)

	player = await channel.connect(cls=Player)
	player.ctx = ctx

	controller.player = player

async def leave_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.voice_client:
		return

	node = controller.player.node
	await controller.player.destroy()
	await node.disconnect()
	controller.reset()

async def play_(self, ctx: commands.Context, q: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.voice_client:
		await ctx.invoke(self.join, play=True)

	player = controller.player
	if not player:
		return

	if q.find('spotify.com') != -1:
		t = spotify.decodeSpotifyQuery(q)
	else:
		t = lavapy.decodeQuery(q)

	result = await t.search(q)
	if result is None:
		return

	controller.parse(result, ctx.author)
	if player.isPlaying:
		return

	await controller.play()