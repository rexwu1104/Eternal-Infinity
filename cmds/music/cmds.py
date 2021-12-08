import re
import orjson
import asyncio
import nextcord as nc
from nextcord.ext import commands
from functools import partial
from .dl import (
	get_youtube,
	get_youtube_list,
	get_spotify
)
from .module import (
	get_place,
	get_number,
	search_embed,
	parse_obj
)

urls = [
	re.compile(r'(?:https?://)?open\.spotify\.com/(album|playlist)/([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/playlist\?(?:.+&)*list=)([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?open\.spotify\.com/track/([\w\-]+)(?:[?&].+)*'),
	re.compile(r'(?:https?://)?(?:youtu\.be/|(?:m|www)\.youtube\.com/watch\?(?:.+&)*v=)([\w\-]+)(?:[?&].+)*')
]
OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

with open('./cmds/music/music_template.json', 'r', encoding='utf8') as mt:
	template = orjson.loads(mt.read())

async def play(self, ctx : commands.Context, *, q : str, t : str):
	voice_controller = self.guilds[ctx.guild.id]
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
			q,
			ctx.author
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
		})
	elif not is_url and t == 'play':
		t = await get_place(self.bot, ctx)
		if t is None:
			return

		await ctx.send(template['Odd'] % (q))
		if t == 'youtube':
			url, data_info = await get_youtube(q)
		elif t == 'spotify':
			url, data_info = await get_spotify(q)

		voice_controller.tmp_queue.append(
			url,
			ctx.author
		)
		await voice_controller.load()
		voice_controller.queue_info.append(data_info)
	elif t == 'search':
		youtube_list = await get_youtube_list(q)
		embed = await search_embed(youtube_list)
		embed.set_author(
			name=ctx.author.name,
			icon_url=ctx.author.avatar.url
		)

		e = await ctx.send(embed=embed)
		index = await get_number(self.bot, ctx)

		if index is None or index == 'cancel':
			await e.delete()
			return

		if index < 1 or index > len(youtube_list):
			await e.delete()
			await ctx.send('**index out of range!!!**')
			return

		voice_controller.tmp_queue.append(
			[
				parse_obj(
					youtube_list[index]
				),
				ctx.author
			]
		)
		await voice_controller.load()
		voice_controller.queue_info.concat(youtube_list)

	if not voice_controller.in_sequence:
		info = voice_controller.queue[0][0]
		source = nc.PCMVolumeTransformer(nc.FFmpegPCMAudio(info.voice_url, **OPTIONS))
		voice_controller.source = source
		voice_controller.nowplay = info
		loop = voice_controller.client.loop

		def handle_error(async_func, loop, error):
			asyncio.run_coroutine_threadsafe(async_func(error), loop)

		async def play_next(err : Exception):
			await voice_controller.load()
			if voice_controller.song_loop:
				info = voice_controller.queue[0][0]
				new_source = nc.PCMVolumeTransformer(
					nc.FFmpegPCMAudio(info.voice_url, **OPTIONS)
				)
			elif voice_controller.queue_loop:
				info = next(voice_controller.queue)[0]
				new_source = nc.PCMVolumeTransformer(
					nc.FFmpegPCMAudio(info.voice_url, **OPTIONS)
				)
			else:
				voice_controller.queue.pop(0)
				voice_controller.queue_info.pop(0)
				if len(voice_controller.queue) == 0:
					await voice_controller.client.disconnect()
				info = voice_controller.queue[0][0]
				new_source = nc.PCMVolumeTransformer(
					nc.FFmpegPCMAudio(info.voice_url, **OPTIONS)
				)

			voice_controller.source = new_source
			voice_controller.nowplay = info

			voice_controller.client.play(new_source, after=(handle_error, play_next, loop))
			if not voice_controller.song_loop:
				await ctx.send(template['Play'] % (info.title))

		voice_controller.client.play(source, after=partial(handle_error, play_next, loop))
		await ctx.send(template['Play'] % (info.title))
		voice_controller.in_sequence = True
	else:
		info = voice_controller.queue[-1][0]
		await ctx.send(template['Add'] % (info.title))