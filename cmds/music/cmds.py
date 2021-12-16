import re
import orjson
import asyncio
import nextcord as nc
from nextcord.ext import commands
from functools import partial
from itertools import cycle
from .dl import (
	get_youtube,
	get_youtube_list
)
from .module import (
	search_view,
	queue_embed,
	parse_obj,
	cycle_to_list,
	jump_to_position,
	TimeLogPCMAudio as TLPCMA,
	nowplay_embed
)
from .database import DB

urls = [
	re.compile(r'(?:https?://)?open\.spotify\.com/(album|playlist)/([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/playlist\?(?:.+&)*list=)([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?open\.spotify\.com/track/([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
]
OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

db = DB()
with open('./cmds/music/music_template.json', 'r', encoding='utf8') as mt:
	template = orjson.loads(mt.read())

async def _play(self, ctx: commands.Context, *, q: str, t: str):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.in_sequence and voice_controller.vchannel != ctx.author.voice.channel:
		await ctx.send('**Excuse me, the music is not playing over.**\n**I cannot join your channel.**')
		return

	if voice_controller.queue_loop:
		await ctx.send('**now in queue-loop mode, cannot add song**')
		return
		
	if voice_controller.client is None:
		voice_controller.client = \
			await ctx.author.voice.channel.connect()
		voice_controller.vchannel = \
			voice_controller.client.channel
		voice_controller.tchannel = \
			ctx.channel
		await ctx.send(template['Join'] % (
			voice_controller.vchannel.name,
			voice_controller.tchannel.name
		))
		
	is_url = 1 in map(
		lambda r: 1 if r.search(q) else 0,
		urls
	)

	if is_url:
		voice_controller.tmp_queue.append(
			[
				q,
				ctx.author
			]
		)
		await voice_controller.load()
		voice_controller.queue_info.append({
			'id': voice_controller.queue[0][0] \
				.id,
			'title': voice_controller.queue[0][0] \
				.title,
			'length': voice_controller.queue[0][0] \
				.duration,
			'thumbnail': voice_controller.queue[0][0] \
				.thumbnail,
			'author': voice_controller.queue[0][0] \
				.author
		}) if len(voice_controller.queue_info) == 0 \
			or type(voice_controller.tmp_queue[0]) == str \
			else None
	elif not is_url and t == 'play':
		await ctx.send(template['Search']['Odd'] % (q))
		url, data_info = await get_youtube(q)

		voice_controller.tmp_queue.append(
			[
				url,
				ctx.author
			]
		)
		await voice_controller.load()
		voice_controller.queue_info.append(data_info)
	elif t == 'search':
		youtube_list = await get_youtube_list(q)
		view = search_view(youtube_list)

		await ctx.send('take a choice~~', view=view)
		if not await view.wait():
			select = view.children[0]
			index = int(select.values[0])
			view.stop()

		voice_controller.tmp_queue.append(
			[
				parse_obj(
					youtube_list[index]
				),
				ctx.author
			]
		)
		await voice_controller.load()
		voice_controller.queue_info.append(youtube_list[index])

	if not voice_controller.in_sequence:
		info = voice_controller.queue[0][0]
		nowinfo = voice_controller.queue_info[0]
		source = nc.PCMVolumeTransformer(
			TLPCMA(voice_controller, info.voice_url, **OPTIONS),
			voice_controller.volume
		)
		voice_controller.source = source
		voice_controller.nowplay = info
		voice_controller.now_info = nowinfo
		loop = voice_controller.client.loop

		def handle_error(async_func, loop, error):
			asyncio.run_coroutine_threadsafe(async_func(error), loop)

		async def play_next(err: Exception):
			if err is not None:
				print(err)
				
			await voice_controller.load()
			if voice_controller.song_loop:
				info = voice_controller.queue[0][0]
				nowinfo = voice_controller.queue_info[0]
				new_source = nc.PCMVolumeTransformer(
					TLPCMA(voice_controller, info.voice_url, **OPTIONS),
					voice_controller.volume
				)
			elif voice_controller.queue_loop:
				info = next(voice_controller.queue)[0]
				nowinfo = next(voice_controller.queue_info)
				new_source = nc.PCMVolumeTransformer(
					TLPCMA(voice_controller, info.voice_url, **OPTIONS),
					voice_controller.volume
				)
			else:
				voice_controller.queue.pop(0)
				voice_controller.queue_info.pop(0)
				if len(voice_controller.queue) == 0:
					voice_controller.client.cleanup()
					await voice_controller.client.disconnect()
					await ctx.send(template['Leave'])
					voice_controller.reset()
				info = voice_controller.queue[0][0]
				nowinfo = voice_controller.queue_info[0]
				new_source = nc.PCMVolumeTransformer(
					TLPCMA(voice_controller, info.voice_url, **OPTIONS),
					voice_controller.volume
				)

			voice_controller.source = new_source
			voice_controller.nowplay = info
			voice_controller.now_info = nowinfo

			voice_controller.client.play(new_source, after=partial(handle_error, play_next, loop))
			if not voice_controller.song_loop:
				await ctx.send(template['Play'] % (info.title))

		voice_controller.client.play(source, after=partial(handle_error, play_next, loop))
		await ctx.send(template['Play'] % (info.title))
		voice_controller.in_sequence = True
	else:
		info = voice_controller.queue[-1][0]
		await ctx.send(template['Add'] % (info.title))

async def _loop(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.client is not None and voice_controller.vchannel != ctx.author.voice.channel:
		await ctx.send(template['NotInChannel']['In'])
		return
	elif voice_controller.client is None:
		await ctx.send(template['NotInChannel']['Out'])
		return

	if voice_controller.queue_loop and not voice_controller.song_loop:
		voice_controller.queue_loop = False
		voice_controller.song_loop = True
		voice_controller.queue = cycle_to_list(voice_controller.queue)
		voice_controller.queue_info = cycle_to_list(voice_controller.queue_info)
		await ctx.send(template['Loop']['Enable'])
	elif voice_controller.song_loop:
		voice_controller.song_loop = False
		await ctx.send(template['Loop']['Disable'])
	else:
		voice_controller.song_loop = True
		await ctx.send(template['Loop']['Enable'])

async def _queueloop(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.client is not None and voice_controller.vchannel != ctx.author.voice.channel:
		await ctx.send(template['NotInChannel']['In'])
		return
	elif voice_controller.client is None:
		await ctx.send(template['NotInChannel']['Out'])
		return
		
	if not voice_controller.queue_loop and voice_controller.song_loop:
		voice_controller.queue_loop = True
		voice_controller.song_loop = False
		voice_controller.queue = cycle(voice_controller.queue)
		voice_controller.queue_info = cycle(voice_controller.queue_info)
		await ctx.send(template['QueueLoop']['Enable'])
	elif voice_controller.queue_loop:
		voice_controller.queue_loop = False
		voice_controller.queue = cycle_to_list(voice_controller.queue)
		voice_controller.queue_info = cycle_to_list(voice_controller.queue_info)
		await ctx.send(template['QueueLoop']['Disable'])
	else:
		voice_controller.queue_loop = True
		voice_controller.queue = cycle(voice_controller.queue)
		voice_controller.queue_info = cycle(voice_controller.queue_info)
		await ctx.send(template['QueueLoop']['Enable'])

async def _volume(self, ctx: commands.Context, vol: float):
	voice_controller = self.guilds[ctx.guild.id]
	voice_controller.volume = vol
	if voice_controller.source is not None:
		voice_controller.source.volume = vol

	await ctx.send('**Volume is change to** `{}%`'.format(vol*100))

async def _queue(self, ctx: commands.Context, page: int):
	voice_controller = self.guilds[ctx.guild.id]
	queue_info = voice_controller.queue_info \
		if type(voice_controller.queue_info) != cycle \
		else cycle_to_list(voice_controller.queue_info)

	await ctx.send(
		embed=queue_embed(
			ctx,
			queue_info,
			page if len(queue_info) else 0
		)
	)

async def _skip(self, ctx: commands.Context, pos: int):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.queue_loop:
		await ctx.send('**In queue-loop mode cannot use skip!!!**')
		return
		
	queue_info = voice_controller.queue_info
	queue = voice_controller.queue + \
		voice_controller.tmp_queue

	if (len(queue_info) - 1 < pos or len(queue) - 1 < pos) and pos != 1:
		await ctx.send('**index out of range!!!**')
		return

	if (len(queue_info) == 1 and len(queue) == 1) and pos == 1:
		await ctx.send(template['Skip'])
		client = voice_controller.client
		voice_controller.reset()
		client.stop()
		client.cleanup()
		await client.disconnect()
		await ctx.send(template['Leave'])
		return

	queue_info = jump_to_position(queue_info, pos)
	queue = jump_to_position(queue, pos)

	voice_controller.queue_info = queue_info
	voice_controller.queue = []
	voice_controller.tmp_queue = queue
	await voice_controller.load()

	await ctx.send(template['Skip'])
	voice_controller.client.stop()

async def _join(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.in_sequence and voice_controller.vchannel != ctx.author.voice.channel:
		await ctx.send('**Excuse me, the music is not playing over.**\n**I cannot join your channel.**')
		return

	if voice_controller.client is None:
		voice_controller.client = \
			await ctx.author.voice.channel.connect()
		voice_controller.vchannel = \
			voice_controller.client.channel
		voice_controller.tchannel = \
			ctx.channel
		await ctx.send(template['Join'] % (
			voice_controller.vchannel.name,
			voice_controller.tchannel.name
		))
	elif voice_controller.vchannel != ctx.author.voice.channel:
		voice_controller.client = \
			await ctx.author.voice.channel.connect()
		voice_controller.vchannel = \
			voice_controller.client.channel
		await ctx.send(template['Join'] % (
			voice_controller.vchannel.name,
			voice_controller.tchannel.name
		))

async def _leave(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	# if ctx.author not in voice_controller.DJ:
	# 	await ctx.send('**You cannot let bot leave this channel.**\
	# 	\n**You are not the DJ!!!**')

	if voice_controller.client is None:
		await ctx.send(template['NotInChannel']['In'])
		return

	voice_controller.client.stop()
	voice_controller.client.cleanup()
	await voice_controller.client.disconnect()
	voice_controller.reset()
	await ctx.send(template['Leave'])

async def _nowplay(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	if len(voice_controller.queue_info) == 0:
		await ctx.send('**There is not any song in queue!!!**')
		return
		
	embed = nowplay_embed(
		ctx,
		voice_controller.now_info,
		int(voice_controller.time)
	)

	await ctx.send(embed=embed)

async def _stop(self, ctx: commands.Context):
	voice_controller = self.guilds[ctx.guild.id]
	if voice_controller.client is None:
		await ctx.send(template['NotInChannel']['In'])
		return 

	voice_controller.client.pause()
	await ctx.send(template['Pause'])

def _create_dj(self, ctx: commands.Context):
	...