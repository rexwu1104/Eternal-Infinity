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
	Union,
	Any
)
from .views import ControlBoard

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

class Empty:
	def __repr__(self):
		return '(nothing)'

class VoiceController:
	def __init__(self):
		self.queue = [] # loaded musics
		self.tmps = [] # waiting for load
		self.infomation = [] # the musics infomation
		self.ctx = None # use to edit the message content
		self.DJ = [] # the admin for music system
		self.now_info = None # the playing music's infomation
		self.volume = 1.0 # the client's volume
		self.client = None # the bot voiceClient
		self.vchannel = None # the channel of bot join
		self.loop_range = None # loop the music in this range
		self.in_sequence = False # is the client in channel?
		self.position = None # the position of the music in queue
		self.source = None # the source of music is playing
		self.time = 0.0 # the time of music

	def is_url(self, url: str):
		return 1 in map(
			lambda r: 1 if r.search(q) else 0,
			[
				re.compile(r'(?:https?://)?open\.spotify\.com/(album|playlist)/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/playlist\?(?:.+&)*list=)([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?open\.spotify\.com/track/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
			]
		)

	async def search(self, q: str, ctx: commands.Context):
		ydl = NPytdl.Pytdl()
		obj = await ydl.resultList(q)[0]
		url = self.parse_obj(obj)

		self.now_info = obj
		self.tmp_queue.append([
			url, ctx.author
		])

	def replace(self, pos: int):
		data = self.tmp_queue.get(pos, Empty())
		self.tmp_queue[pos] = Empty()
		return data

	def lengthen(self, size: int):
		self.queue += [Empty()] * size

	async def load(self, pos: int):
		data = self.replace(pos)

		if type(data) == Empty:
			return

		...

	async def play(self):
		...

class Music(Cog):
	@commands.command()
	async def test(self, ctx: commands.Context):
		await ctx.send('test', view=ControlBoard())

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))