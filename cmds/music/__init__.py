import lavapy
from lavapy.ext import spotify
from core.cog_append import Cog
from pysondb import db
from pprint import pprint
from nextcord.ext import commands
from nextcord import (
	VoiceChannel,
	SelectOption
)
from typing import (
	Dict
)
from .methods import (
	play_,
	join_,
	leave_
)
from .embeds import (
	info_embed
)
from .views import (
	ControlBoard
)
from .cls import (
	VoiceController,
	Player
)

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}
guild_db = db.getDb('./cmds/music/guilds.json')

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

class Music(Cog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.controllers: Dict[int, VoiceController] = {}

		for guild in self.bot.guilds:
			self.controllers[guild.id] = VoiceController(self, **{
				'play': play_
			})

	async def initialiseNodes(self, channel):
		try:
			print(f'{channel.id} -> {channel.rtc_region}')
			node = await lavapy.NodePool.createNode(
				client=self.bot,
				host='lavalink-server-node-js.herokuapp.com',
				port=443,
				password='password',
				region=channel.rtc_region,
				spotifyClient=spotify.SpotifyClient(
					clientID='clientid',
					clientSecret='clientsecret'
				),
				identifier=f'{channel.rtc_region} node',
				secure=True
			)
		except:
			...

	@commands.Cog.listener()
	async def on_lavapy_track_start(self, player, track):
		controller = self.controllers[player.guild.id]

		if not controller.in_sequence:
			controller.in_sequence = True
			controller.message = await player.ctx.send(
				embed=info_embed(controller),
				view=ControlBoard(controller)
			)
		else:
			await controller.message.edit(
				embed=info_embed(controller)
			)

	@commands.Cog.listener()
	async def on_lavapy_track_end(self, player, track, reason):
		controller = self.controllers[player.guild.id]

		if controller.use_ui:
			controller.use_ui = False
		else:
			await controller.skip(1)

	@commands.command()
	async def join(self, ctx: commands.Context, channel: VoiceChannel = None, play: bool = False):
		if not play:
			await ctx.message.delete()

		await join_(self, ctx, channel, self.initialiseNodes)

	@commands.command()
	async def leave(self, ctx, play: bool = False):
		if not play:
			await ctx.message.delete()

		await leave_(self, ctx)

	@commands.command()
	async def play(self, ctx: commands.Context, *, query: str):
		await ctx.message.delete()
		await play_(self, ctx, query)

	@commands.command()
	@commands.check(is_owner)
	async def cc(self, ctx: commands.Context, sub: str = None):
		controller = self.controllers[ctx.guild.id]
		if sub is None:
			pprint(controller.__dict__)
		elif sub in controller.__dict__:
			pprint(controller.__dict__[sub])

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))