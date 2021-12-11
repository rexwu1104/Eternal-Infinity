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
	_play,
	_loop,
	_queueloop,
	_volume
)
from pprint import pprint

ysdl = NPytdl.Pytdl()
with open('./cmds/music/music_template.json', 'r', encoding='utf8') as mt:
	template = orjson.loads(mt.read())

class VoiceController:
	def __init__(self):
		self.volume = 1.0
		self.queue_loop : bool = False
		self.song_loop : bool = False
		self.queue : List[[NPytdl.YoutubeVideo, Union[Member, User]]] = []
		self.queue_info : List[Dict] = []
		self.tmp_queue : List[[Union[str, NPytdl.YoutubeVideo], Union[Member, User]]] = []
		self.nowplay : NPytdl.YoutubeVideo = None
		self.now_info : Dict = {}
		self.source : PCMVolumeTransformer = None
		self.client : VoiceClient = None
		self.vchannel : VoiceChannel = None
		self.tchannel : TextChannel = None
		self.in_sequence : bool = False
		self.DJ : List[Union[Member, User]] = []

	async def load(self):
		if len(self.tmp_queue) == 0:
			return

		item = self.tmp_queue.pop(0)
		if type(item[0]) == str:
			info = await ysdl.info(item[0])
		else:
			info = item[0]
			
		await info.create()
		if type(info) == NPytdl.YoutubeVideo:
			self.queue.append([info, item[1]])
		elif type(info) == NPytdl.YoutubeVideos:
			data_info = await ysdl.playList(
				info.url.split('=')[1]
			)
			self.queue_info += data_info
			first = info.videoList.pop(0)
			self.tmp_queue = [[i, item[1]] for i in info.videoList] + self.tmp_queue
			await first.create()
			self.queue.append([first, item[1]])
		elif type(info) == NPytdl.SpotifyMusic:
			data_info = await ysdl.spotifyTrack(
				info.url.split('/')[4]
			)
			self.queue_info += data_info
			first = info.music
			await first.create()
			self.queue.append([first, item[1]])
		elif type(info) == NPytdl.SpotifyMusics:
			if info.url.find('album') != -1:
				data_info = await ysdl.spotifyResultList(
					info.url
				)
			else:
				data_info = await ysdl.spotifyPlayList(
					info.url.split('/')[4]
				)

			self.queue_info += data_info
			first = info.musicList.pop(0)
			self.tmp_queue = [[i, item[1]] for i in info.musicList] + self.tmp_queue

	def reset(self):
		self.queue_loop : bool = False
		self.song_loop : bool = False
		self.queue : List[[NPytdl.YoutubeVideo, Union[Member, User]]] = []
		self.queue_info : List[Dict] = []
		self.tmp_queue : List[[Union[str, NPytdl.YoutubeVideo], Union[Member, User]]] = []
		self.nowplay : NPytdl.YoutubeVideo = None
		self.source : PCMVolumeTransformer = None
		self.client : VoiceClient = None
		self.vchannel : VoiceChannel = None
		self.tchannel : TextChannel = None
		self.in_sequence : bool = False

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
		await _play(self, ctx, q=q, t='play')

	@commands.command()
	async def search(self, ctx : commands.Context, *, q : str = ''):
		if ctx.author.voice is None:
			await ctx.send(template['NotInChannel']['Out'])
			return
		if q == '':
			await ctx.send(':x: **query cannot be empty!!!**')
			return
		await _play(self, ctx, q=q, t='search')

	@commands.command()
	async def cc(self, ctx : commands.Context):
		voice_controller = self.guilds[ctx.guild.id]
		pprint(voice_controller.__dict__, indent=1)

	@commands.command()
	async def loop(self, ctx : commands.Context):
		if ctx.author.voice is None:
			await ctx.send(template['NotInChannel']['Out'])
			return
		await _loop(self, ctx)
	
	@commands.command()
	async def queueloop(self, ctx : commands.Context):
		if ctx.author.voice is None:
			await ctx.send(template['NotInChannel']['Out'])
			return
		await _queueloop(self, ctx)

	@commands.command()
	async def volume(self, ctx : commands.Context, vol : float):
		await _volume(self, ctx, vol)

def setup(bot : commands.Bot):
	bot.add_cog(Music(bot))