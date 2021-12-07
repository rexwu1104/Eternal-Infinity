import NPytdl
import orjson
from core.cog_append import Cog
from nextcord.ext import commands
from nextcord import (
	VoiceClient,
	VoiceChannel,
	TextChannel,
	PCMVolumeTransformer,
	Member, User
)
from typing import (
	List,
	Dict,
	Union
)
from .cmds import (
	play
)

ysdl = NPytdl.Pytdl()
with open('./cmds/music/music_template.json', 'r', encoding='utf8') as mt:
	template = orjson.loads(mt.read())

class VoiceController:
	def __init__(self):
		self.queue_loop : bool = False
		self.song_loop : bool = False
		self.queue : List[[NPytdl.YoutubeVideo, Union[Member, User]]] = []
		self.tmp_queue : List[[Union[str, NPytdl.YoutubeVideo], Union[Member, User]]] = []
		self.nowplay : NPytdl.YoutubeVideo = None
		self.source : PCMVolumeTransformer = None
		self.client : VoiceClient = None
		self.vchannel : VoiceChannel = None
		self.tchannel : TextChannel = None
		self.in_sequence : bool = False
		self.DJ : List[Union[Member, User]] = []

	async def load(self):
		item = self.tmp_queue.pop(0)
		if type(item[0]) == str:
			info = await ysdl.info(item[0])
		else:
			info = item[0]
		if type(info) == NPytdl.YoutubeVideo:
			await info.create()
			self.queue.append([info, item[1]])
		elif type(info) == NPytdl.YoutubeVideos:
			await info.create()
			first = info.videoList.pop(0)
			self.tmp_queue = [[i, item[1]]for i in info.videoList] + self.tmp_queue
			await first.create()
			self.queue.append([first, item[1]])
		# elif type(info) == NPytdl.SpotifyMusic:
		# elif type(info) == NPytdl.SpotifyMusics:

class Music(Cog):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.guilds : Dict[int, VoiceController] = {}
		for guild in self.bot.guilds:
			self.guilds[guild.id] = VoiceController()

	@commands.command(aliases=['p'])
	async def play(self, ctx : commands.Context, *, q : str = ''):
		voice_controller = self.guilds[ctx.guild.id]
		if ctx.author.voice is None:
			await ctx.send(template['NotInChannel']['Out'])
			return
		if q == '' and not voice_controller.in_sequence:
			await ctx.send(':x: **query cannot be empty!!!**')
			return
		elif q == '':
			voice_controller.client.resume()
			return
		await play(self, ctx, q=q, t='play')

	@commands.command()
	async def search(self, ctx : commands.Context, *, q : str = ''):
		if ctx.author.voice is None:
			await ctx.send(template['NotInChannel']['Out'])
			return
		if q == '':
			await ctx.send(':x: **query cannot be empty!!!**')
			return
		await play(self, ctx, q=q, t='search')

def setup(bot : commands.Bot):
	bot.add_cog(Music(bot))