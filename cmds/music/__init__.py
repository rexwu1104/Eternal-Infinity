from http.server import executable
import re
import random
import NPytdl
import asyncio
from core.cog_append import Cog
from functools import (
	partial,
	wraps
)
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

	def find_id(self, uri: str):
		regex = re.compile(r'(?:https?://)?(?:youtu\.be/|(?:(?:m|www)\.)*youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
		match = re.match(regex, uri)

		id = match.group(1)
		print(id)

		return id

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
					self.find_id(data[0].url)
				))[0]
			elif not self.information[pos]:
				self.information += [(await ysdl.resultList(
					self.find_id(data[0].url)
				))[0]]

			self.now_info = self.information[pos]

			self.queue[pos] = data
			self.source = PCMVolumeTransformer(TimeSource(
					self, data[0].voice_url, executable="C:\\Users\\rexwu\AppData\Roaming\\ffmpeg\\bin\\ffmpeg.exe", **OPTIONS
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
					self, loaded[0].voice_url, executable="C:\\Users\\rexwu\AppData\Roaming\\ffmpeg\\bin\\ffmpeg.exe", **OPTIONS
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
					self, loaded[0].voice_url, executable="C:\\Users\\rexwu\AppData\Roaming\\ffmpeg\\bin\\ffmpeg.exe", **OPTIONS
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
					self, loaded[0].voice_url, executable="C:\\Users\\rexwu\AppData\Roaming\\ffmpeg\\bin\\ffmpeg.exe", **OPTIONS
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
					self, self.queue[pos][0].voice_url, executable="C:\\Users\\rexwu\AppData\Roaming\\ffmpeg\\bin\\ffmpeg.exe", **OPTIONS
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

NoneType = type(None)
def check_voice(ctx: commands.Context):
	if ctx.author.voice:
		return True

	if type(ctx.kwargs.get('command', 1)) in [str, NoneType]:
		return True

	asyncio.run_coroutine_threadsafe(
		ctx.message.delete(),
		ctx.bot.loop
	)
	asyncio.run_coroutine_threadsafe(
		ctx.send("**You must to join a voice channel.**"),
		ctx.bot.loop
	)

	return False

class Music(Cog):
	"""The music functions for control music convience"""
    
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

	@commands.check(check_voice)
	@commands.command(aliases=['p'])
	async def play(self, ctx: commands.Context, *, msg: str):
		"""Play a song with query or url"""
		await ctx.message.delete()
		await play_(self, ctx, msg)

	@commands.check(check_voice)
	@commands.command()
	async def search(self, ctx: commands.Context, *, query: str):
		"""Search with query and send a select menu"""
		await ctx.message.delete()
		await search_(self, ctx, query)

	@commands.check(check_voice)
	@commands.command(aliases=['q'])
	async def queue(self, ctx: commands.Context):
		"""The queue of songs after now playing"""
		await ctx.message.delete()
		await queue_(self, ctx)

	@commands.check(check_voice)
	@commands.command(aliases=['np'])
	async def nowplay(self, ctx: commands.Context):
		"""The song which is playing now"""
		await ctx.message.delete()
		await nowplay_(self, ctx)

	@commands.check(check_voice)
	@commands.command()
	async def loop(self, ctx: commands.Context, t: str = None):
		"""Loop the song, queue or a range"""
		await ctx.message.delete()
		await loop_(self, ctx, t)

	@commands.check(check_voice)
	@commands.command(aliases=['vol'])
	async def volume(self, ctx: commands.Context, vol: float):
		"""Adjust the volume"""
		await ctx.message.delete()
		await volume_(self, ctx, vol)

	@commands.check(check_voice)
	@commands.command(aliases=['s'])
	async def skip(self, ctx: commands.Context, pos: int = 1):
		"""Skip the song and jump to the position"""
		await ctx.message.delete()
		await skip_(self, ctx, pos)

	@commands.check(check_voice)
	@commands.command(aliases=['j', 'connect'])
	async def join(self, ctx: commands.Context, channel: VoiceChannel = None):
		"""Join to a voice channel"""
		await ctx.message.delete()
		await join_(self, ctx, channel)

	@commands.check(check_voice)
	@commands.command(aliases=['dc', 'disconnect'])
	async def leave(self, ctx: commands.Context):
		"""Leave the voice channel"""
		await ctx.message.delete()
		await leave_(self, ctx)

	@commands.check(check_voice)
	@commands.command(aliases=['pause'])
	async def stop(self, ctx: commands.Context):
		"""Pause the song"""
		await ctx.message.delete()
		await stop_(self, ctx)

	@commands.check(check_voice)
	@commands.command(aliases=['cd'])
	async def createdj(self, ctx: commands.Context, *, name: str = 'DJ'):
		"""Create the dj role"""
		await ctx.message.delete()
		await create_dj_(self, ctx, name)

	@commands.check(check_voice)
	@commands.command()
	async def remove(self, ctx: commands.Context, pos: int):
		"""Remove the song of the position"""
		await ctx.message.delete()
		await remove_(self, ctx, pos)

	@commands.check(check_voice)
	@commands.command(aliases=['a'])
	async def alias(self, ctx: commands.Context, alias: str, *, sub: str):
		"""Create a alias to play music"""
		await ctx.message.delete()
		await alias_(self, ctx, alias, sub)

	@commands.check(check_voice)
	@commands.command(aliases=['t'])
	async def together(self, ctx: commands.Context):
		"""Create a 'watch together' link"""
		await ctx.message.delete()
		await together_(self, ctx)

	@commands.check(check_voice)
	@commands.command()
	async def fix(self, ctx: commands.Context):
		"""Fix some error"""
		await ctx.message.delete()
		controller = self.controllers[ctx.guild.id]

		controller.reset()

	@commands.check(check_voice)
	@commands.command()
	async def cc(self, ctx: commands.Context, sub: str = None):
		controller = self.controllers[ctx.guild.id]
		if sub is None:
			pprint(controller.__dict__)
		elif sub in controller.__dict__:
			pprint(controller.__dict__[sub])

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))