import re
import random
import NPytdl
import orjson
import asyncio
from core.cog_append import Cog
from functools import (
	partial,
	wraps
)
from pyppeteer import launch
from pprint import pprint
from pysondb import db
from nextcord.ext import commands
from nextcord.ui import (
	View
)
from nextcord import (
	Guild,
	VoiceChannel,
	FFmpegPCMAudio,
	PCMVolumeTransformer,
	SelectOption
)
from typing import (
	List,
	Dict,
	Union,
	Any
)
from .audio_methods import (
	play_,
	search_,
	queue_,
	nowplay_,
	loop_,
	volume_,
	skip_,
	join_,
	leave_,
	stop_,
	create_dj_,
	remove_,
	alias_,
	custom_,
	insert_,
	together_
)
from .embeds import (
	info_embed
)
from .functions import (
	_duration_to_second
)

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}
guild_db = db.getDb('./cmds/music/guilds.json')

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

class AudioVoiceController:
	def __init__(self, mbot, **funcs):
		self.bot = mbot
		self.funcs = funcs
		self.queue = []
		self.tmps = []
		self.information = []
		self.message = None
		self.DJs = []
		self.now_info = None
		self.volume = 1.0
		self.client = None
		self.channel = None
		self.loop_range = None
		self.in_sequence = False
		self.now_pos = None
		self.source = None
		self.time = 0.0
		self.jump = False

	def load_dj(self, guild):
		data = guild_db.getBy({'guild_id': guild.id})

		if len(data) == 0:
			return

		dj_id = data[0]['dj_role_id']

		for member in guild.members:
			if member.get_role(dj_id) is not None:
				self.DJs.append(member)

	def is_url(self, url: str):
		return 1 in map(
			lambda r: 1 if r.search(url) else 0,
			[
				re.compile(r'(?:https?://)?open\.spotify\.com/(album|playlist)/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|(?:(?:m|www)\.)*youtube\.com/playlist\?(?:.+&)*list=)([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?open\.spotify\.com/track/([\w\-]+)(?:[?&].+)*'),
				re.compile(r'(?:https?://)?(?:youtu\.be/|(?:(?:m|www)\.)*youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
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

	async def load(self, pos: int, loaded=False):
		ysdl = NPytdl.Pytdl()
		data = self.replace(pos)

		self.lengthen()

		if type(data[0]) == str:
			data[0] = await ysdl.info(data[0])

		if type(data[0]) == NPytdl.YoutubeVideo:
			await data[0].create(cookie_file='./cookie.txt')
		else:
			await data[0].create()

		if type(data[0]) == NPytdl.YoutubeVideo:
			if type(self.information[pos]) == Empty:
				self.information[pos] = (await ysdl.resultList(
					data[0].url
				))[0]
			elif not self.information[pos]:
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
			await loaded[0].create(cookie_file='./cookie.txt')

			self.queue[pos] = loaded
			self.tmps += data
			self.source = PCMVolumeTransformer(TimeSource(
					self, loaded[0].voice_url, **OPTIONS
				), self.volume
			)

		elif type(data[0]) == NPytdl.SpotifyMusic:
			self.information.pop(len(self.information) - 1)
			l = len(self.information)
			self.information += await ysdl.spotifyTrack(
				data[0].url.split('/')[4]
			)

			self.now_info = self.information[l]

			data = list(map(
				lambda v: [v, data[1]],
				data[0].music
			))

			loaded = data.pop(0)
			await loaded[0].create(cookie_file='./cookie.txt')

			self.queue[pos] = loaded
			self.tmps += data
			self.source = PCMVolumeTransformer(TimeSource(
					self, loaded[0].voice_url, **OPTIONS
				), self.volume
			)
			
		elif type(data[0]) == NPytdl.SpotifyMusics:
			self.information.pop(len(self.information) - 1)
			l = len(self.information)
			self.information += await ysdl.spotifyPlayList(
				data[0].url.split('/')[4]
			)

			self.now_info = self.information[l]

			data = list(map(
				lambda v: [v, data[1]],
				data[0].musicList
			))

			loaded = data.pop(0)
			await loaded[0].create(cookie_file='./cookie.txt')

			self.queue[pos] = loaded
			self.tmps += data
			self.source = PCMVolumeTransformer(TimeSource(
					self, loaded[0].voice_url, **OPTIONS
				), self.volume
			)

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
		self.source.cleanup()

		if self.jump and (self.loop_range is None or type(self.loop_range) == list):
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

		loop_range = self.loop_range
		if type(loop_range) == int:
			await self.load(self.now_pos)
		elif type(loop_range) == list:
			if self.now_pos + num > loop_range[1]:
				await self.load(loop_range[1])
			else:
				await self.load(self.now_pos + num)
		elif type(loop_range) == str:
			pass
		else:
			await self.load(self.now_pos + num)

		self.client.stop()

	async def prev(self, num):
		self.jump = True

		loop_range = self.loop_range
		if type(loop_range) == int:
			await self.load(self.now_pos)
		elif type(loop_range) == list:
			if self.now_pos - num < loop_range[0]:
				await self.load(loop_range[0])
			else:
				await self.load(self.now_pos - num)
		elif type(loop_range) == str:
			pass
		else:
			await self.load(self.now_pos - num)

		self.client.stop()

	def vol(self, volume):
		if volume >= 1.0:
			self.volume = min(2.0, volume)
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
		self.now_pos = None
		self.source = None
		self.time = 0.0
		self.jump = False

class VideoVoiceController:
	def __init__(self):
		self.queue = []
		self.tmps = []
		self.information = []
		self.now_info = None
		self.client = None
		self.channel = None
		self.now_pos = None
		self.jump = False

class Music(Cog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.controllers = {}
		self.vcontrollers = {}
		for guild in self.bot.guilds:
			self.controllers[guild.id] = AudioVoiceController(self, **{
				'play': play_,
				'search': search_,
				'queue': queue_,
				'nowplay': nowplay_,
				'loop': loop_,
				'volume': volume_,
				'skip': skip_,
				'join': join_,
				'leave': leave_,
				'stop': stop_,
				'create_dj': create_dj_
			})
			self.controllers[guild.id].load_dj(guild)
			self.vcontrollers[guild.id] = VideoVoiceController()

	@commands.Cog.listener()
	async def on_guild_join(self, guild: Guild):
		self.controllers[guild.id] = AudioVoiceController(self, **{
			'play': play_,
			'search': search_,
			'queue': queue_,
			'nowplay': nowplay_,
			'loop': loop_,
			'volume': volume_,
			'skip': skip_,
			'join': join_,
			'leave': leave_,
			'stop': stop_,
			'create_dj': create_dj_
		})
		self.vcontrollers[guild.id] = VideoVoiceController()

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		data = guild_db.getBy({'guild_id': after.guild.id})

		if len(data) == 0:
			return

		dj_id = data[0]['dj_role_id']

		if before.get_role(dj_id) and not after.get_role(dj_id):
			self.controllers[after.guild.id].DJs.pop(
				self.controllers[after.guild.id].DJs.index(after)
			)
		elif not before.get_role(dj_id) and after.get_role(dj_id):
			self.controllers[after.guild.id].DJs.append(after)

	@commands.group()
	async def music(self, ctx: commands.Context):
		...

	@music.command(aliases=['p'])
	async def play(self, ctx: commands.Context, *, msg: str):
		await ctx.message.delete()
		await play_(self, ctx, msg)

	@music.command()
	async def search(self, ctx: commands.Context, *, query: str):
		await ctx.message.delete()
		await search_(self, ctx, query)

	@music.command(aliases=['q'])
	async def queue(self, ctx: commands.Context):
		await ctx.message.delete()
		await queue_(self, ctx)

	@music.command(aliases=['np'])
	async def nowplay(self, ctx: commands.Context):
		await ctx.message.delete()
		await nowplay_(self, ctx)

	@music.command()
	async def loop(self, ctx: commands.Context, t: str = None):
		await ctx.message.delete()
		await loop_(self, ctx, t)

	@music.command(aliases=['vol'])
	async def volume(self, ctx: commands.Context, vol: float):
		await ctx.message.delete()
		await volume_(self, ctx, vol)

	@music.command(aliases=['s'])
	async def skip(self, ctx: commands.Context, pos: int = 1):
		await ctx.message.delete()
		await skip_(self, ctx, pos)

	@music.command(aliases=['j', 'connect'])
	async def join(self, ctx: commands.Context, channel: VoiceChannel = None):
		await ctx.message.delete()
		await join_(self, ctx, channel)

	@music.command(aliases=['dc', 'disconnect'])
	async def leave(self, ctx: commands.Context):
		await ctx.message.delete()
		await leave_(self, ctx)

	@music.command()
	async def stop(self, ctx: commands.Context):
		await ctx.message.delete()
		await stop_(self, ctx)

	@music.command(aliases=['cd'])
	async def createdj(self, ctx: commands.Context, *, name: str = 'DJ'):
		await ctx.message.delete()
		await create_dj_(self, ctx, name)

	@music.command()
	async def remove(self, ctx: commands.Context, pos: int):
		await ctx.message.delete()
		await remove_(self, ctx, pos)

	@music.command(aliases=['a'])
	async def alias(self, ctx: commands.Context, alias: str, *, sub: str):
		await ctx.message.delete()
		await alias_(self, ctx, alias, sub)

	@music.command(aliases=['t'])
	async def together(self, ctx: commands.Context):
		await ctx.message.delete()
		await together_(self, ctx)

	@music.command()
	async def fix(self, ctx: commands.Context):
		await ctx.message.delete()
		controller = self.controllers[ctx.guild.id]

		controller.reset()

	@commands.group()
	async def video(self, ctx: commands.Context):
		...

	@video.command()
	async def play(self, ctx: commands.Context, *, msg: str):
		await ctx.message.delete()

	@video.command()
	async def test(self, ctx: commands.Context):
		controller = self.vcontrollers[ctx.guild.id]
		browser = await launch(headless=False, userDataDir="./cmds/music/data")

		page = await browser.newPage()

	@commands.command(aliases=['p'])
	async def play(self, ctx: commands.Context, *, msg: str):
		await ctx.message.delete()
		await play_(self, ctx, msg)

	@commands.command()
	async def search(self, ctx: commands.Context, *, query: str):
		await ctx.message.delete()
		await search_(self, ctx, query)

	@commands.command(aliases=['q'])
	async def queue(self, ctx: commands.Context):
		await ctx.message.delete()
		await queue_(self, ctx)

	@commands.command(aliases=['np'])
	async def nowplay(self, ctx: commands.Context):
		await ctx.message.delete()
		await nowplay_(self, ctx)

	@commands.command()
	async def loop(self, ctx: commands.Context, t: str = None):
		await ctx.message.delete()
		await loop_(self, ctx, t)

	@commands.command(aliases=['vol'])
	async def volume(self, ctx: commands.Context, vol: float):
		await ctx.message.delete()
		await volume_(self, ctx, vol)

	@commands.command(aliases=['s'])
	async def skip(self, ctx: commands.Context, pos: int = 1):
		await ctx.message.delete()
		await skip_(self, ctx, pos)

	@commands.command(aliases=['j', 'connect'])
	async def join(self, ctx: commands.Context, channel: VoiceChannel = None):
		await ctx.message.delete()
		await join_(self, ctx, channel)

	@commands.command(aliases=['dc', 'disconnect'])
	async def leave(self, ctx: commands.Context):
		await ctx.message.delete()
		await leave_(self, ctx)

	@commands.command()
	async def stop(self, ctx: commands.Context):
		await ctx.message.delete()
		await stop_(self, ctx)

	@commands.command(aliases=['cd'])
	async def createdj(self, ctx: commands.Context, *, name: str = 'DJ'):
		await ctx.message.delete()
		await create_dj_(self, ctx, name)

	@commands.command()
	async def remove(self, ctx: commands.Context, pos: int):
		await ctx.message.delete()
		await remove_(self, ctx, pos)

	@commands.command(aliases=['a'])
	async def alias(self, ctx: commands.Context, alias: str, *, sub: str):
		await ctx.message.delete()
		await alias_(self, ctx, alias, sub)

	@commands.command()
	async def together(self, ctx: commands.Context):
		await ctx.message.delete()
		await together_(self, ctx)

	@commands.command()
	async def fix(self, ctx: commands.Context):
		await ctx.message.delete()
		controller = self.controllers[ctx.guild.id]

		controller.reset()

	@commands.command()
	async def cc(self, ctx: commands.Context, sub: str = None):
		controller = self.controllers[ctx.guild.id]
		if sub is None:
			pprint(controller.__dict__)
		elif sub in controller.__dict__:
			pprint(controller.__dict__[sub])

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))