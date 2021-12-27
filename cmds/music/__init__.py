import re
import random
import NPytdl
import orjson
import asyncio
from core.cog_append import Cog
from functools import partial
from pprint import pprint
from nextcord.ext import commands
from nextcord.opus import Encoder as OpusEncoder
from nextcord.ui import (
	View
)
from nextcord import (
	VoiceClient,
	VoiceChannel,
	TextChannel,
	FFmpegPCMAudio,
	PCMVolumeTransformer,
	Member, User,
	SelectOption
)
from typing import (
	List,
	Dict,
	Union,
	Any
)
from .methods import (
	play_,
	search_
)
from .embeds import (
	info_embed
)

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

class Empty:
	def __repr__(self):
		return '(nothing)'

	async def create(self):
		"????????"

class TimeSource(FFmpegPCMAudio):
	def __init__(self, controller, source, **kwargs):
		super().__init__(source, **kwargs)
		self.controller = controller

	def read(self):
		ret = super().read()
		self.controller.time += 0.02

		return ret

class VoiceController:
	def __init__(self):
		self.queue = []
		self.tmps = []
		self.information = []
		self.message = None
		self.DJ = []
		self.now_info = None
		self.volume = 1.0
		self.client = None
		self.channel = None
		self.loop_range = None
		self.in_sequence = False
		self.position = None
		self.source = None
		self.time = 0.0
		self.jump = False

	def is_url(self, url: str):
		return 1 in map(
			lambda r: 1 if r.search(url) else 0,
			[
				re.compile(r'(?:https?://)?open\.spotify\.com/(album|playlist)/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|((?:m|www)\.)*youtube\.com/playlist\?(?:.+&)*list=)([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?open\.spotify\.com/track/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|((?:m|www)\.)*youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
			]
		)
	
	async def select_options(self, q: str):
		options = []
		ysdl = NPytdl.Pytdl()
		obj_list = await ysdl.resultList(q)

		for obj in obj_list:
			options.append(SelectOption(
					label=obj['title'],
					description='https://youtu.be/' + obj['id'],
					value='https://youtu.be/' + obj['id']
				)
			)

		return options

	async def search(self, q: str, ctx: commands.Context):
		ysdl = NPytdl.Pytdl()
		obj = (await ysdl.resultList(q))[0]
		url = self.parse_obj(obj)

		self.tmps.append([
			url, ctx.author
		])

	def parse_obj(self, obj):
		return 'https://youtu.be/' + obj['id']

	def replace(self, pos: int):
		def safe_get(l, idx, default):
			try:
				return l[idx]
			except IndexError:
				return default

		data = safe_get(self.tmps, pos, Empty())
		if type(data) == Empty:
			return [data]

		self.tmps[pos] = Empty()
		return data

	def lengthen(self):
		self.queue += [Empty()] * (len(self.tmps) - len(self.queue))
		self.information += [Empty()] * (len(self.tmps) - len(self.information))

	async def load(self, pos: int):
		ysdl = NPytdl.Pytdl()
		data = self.replace(pos)

		self.lengthen()

		if type(data[0]) == str:
			data[0] = await ysdl.info(data[0])

		await data[0].create()
		if type(data[0]) == NPytdl.YoutubeVideo:
			if type(self.information[pos]) == Empty:
				self.information[pos] = (await ysdl.resultList(
					data[0].url
				))[0]
			else:
				self.information += [(await ysdl.resultList(
					data[0].url
				))[0]]

			self.now_info = self.information[pos]

			self.queue[pos] = data
			self.source = PCMVolumeTransformer(TimeSource(
					self, data[0].voice_url, **OPTIONS
				), self.volume
			)

		elif type(data[0]) == NPytdl.YoutubeVideos:
			self.information.pop(len(self.information) - 1)
			l = len(self.information)
			self.information += await ysdl.playList(
				data[0].url.split('=')[1]
			)

			self.now_info = self.information[l]

			data = list(map(
				lambda v: [v, data[1]],
				data[0].videoList
			))

			loaded = data.pop(0)
			await loaded[0].create()

			self.queue[pos] = loaded
			self.tmps += data
			self.source = PCMVolumeTransformer(TimeSource(
					self, loaded[0].voice_url, **OPTIONS
				), self.volume
			)

		elif type(data[0]) == NPytdl.SpotifyMusic:
			...
			
		elif type(data[0]) == NPytdl.SpotifyMusics:
			...

		else:
			if pos > len(self.tmps) and pos != -1:
				return
			elif pos == len(self.tmps):
				await self.client.disconnect()

				view = View.from_message(self.message)
				view.stop()
				await self.message.delete()

				return False

			self.now_info = self.information[pos]
			self.source = PCMVolumeTransformer(TimeSource(
					self, self.queue[pos][0].voice_url, **OPTIONS
				), self.volume
			)

		self.now_pos = self.queue.index(self.queue[pos])
		self.lengthen()

	def play(self, *, command=False):
		if not self.in_sequence:
			self.client.play(self.source, after=partial(
				self.handle_next, self.next, self.client.loop
			))

		if not command:
			asyncio.run_coroutine_threadsafe(
				self.message.edit(embed=info_embed(self)),
				self.client.loop
			)

		self.in_sequence = True

	def handle_next(self, n, l, e):
		asyncio.run_coroutine_threadsafe(n(e), l)

	async def next(self, err):
		if err:
			print(err)
			
		self.time = 0.0
		self.in_sequence = False

		print(self.now_pos, self.loop_range)
		if self.jump:
			self.now_pos -= 1
			self.jump = False
		
		if self.loop_range is None:
			s = await self.load(self.now_pos + 1)
			if s is False:
				self.reset()
				return
		elif type(self.loop_range) == str:
			await self.load(random.choice([idx for idx, _ in enumerate(self.tmps)]))
		elif type(self.loop_range) == int:
			await self.load(self.now_pos)
		elif type(self.loop_range) == list:
			if self.now_pos < self.loop_range[1]:
				await self.load(self.now_pos + 1)
			else:
				await self.load(self.loop_range[0])

		self.play()

	async def skip(self, num):
		self.jump = True
		await self.load(self.now_pos + num)
		self.client.stop()

	async def prev(self, num):
		self.jump = True
		await self.load(self.now_pos - num)
		self.client.stop()

	def vol(self, volume):
		if volume > 1.0:
			self.volume = min(2.0, volume)
		elif volume == 1.0:
			self.volume = 1.0
		else:
			self.volume = max(0.0, volume)
			
		self.source.volume = self.volume

	def reset(self):
		self.queue = []
		self.tmps = []
		self.information = []
		self.message = None
		self.now_info = None
		self.volume = 1.0
		self.client = None
		self.channel = None
		self.loop_range = None
		self.in_sequence = False
		self.position = None
		self.source = None
		self.time = 0.0
		self.jump = False

class Music(Cog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.controllers = {}
		for guild in self.bot.guilds:
			self.controllers[guild.id] = VoiceController()

	@commands.command(aliases=['p'])
	async def play(self, ctx: commands.Context, *, msg: str):
		await ctx.message.delete()
		await play_(self, ctx, msg)

	@commands.command()
	async def search(self, ctx: commands.Context, *, query: str):
		await ctx.message.delete()
		await search_(self, ctx, query)

	@commands.command()
	async def cc(self, ctx: commands.Context):
		controller = self.controllers[ctx.guild.id]
		pprint(controller.__dict__)

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))