import re
import math
import orjson
import asyncio
import nextcord as nc
from nextcord.opus import Encoder as OpusEncoder
from nextcord.ext import commands
from typing import (
	List,
	Dict,
	Union,
	TypeVar,
	Generic
)

AT = TypeVar('AT', bound='AudioSource')
VC = TypeVar('VC', bound='VoiceController')

with open('./cmds/music/music_template.json', 'r', encoding='utf8') as mt:
	template = orjson.loads(mt.read())

async def get_number(bot : commands.Bot, ctx : commands.Context) -> Union[int, str]:
	def check(m : nc.Message):
		return m.content.isdigit() or m.content == 'cancel'

	sr : nc.Message = await ctx.send('**Type a number to make a choice. Type** `cancel` **to exit**')

	try:
		m : nc.Message = await bot.wait_for('message', check=check, timeout=60.0)
		await sr.delete()
	except asyncio.TimeoutError:
		await ctx.send('**timeout!!!**')
		return None

	return int(m.content) if m.content.isdigit() else m.content

def search_embed(youtube_list : List[Dict]) -> nc.Embed:
	description : str = ''
	for item in youtube_list:
		title : str = item['title']
		description += f'{youtube_list.index(item)+1}. [{title}](https://youtu.be/{item["id"]})\n\n'

	embed = nc.Embed(
		color=nc.Colour.random(),
		description=description
	)
	return embed

def queue_embed(ctx : commands.command, queue_info : List[Dict], page : int) -> nc.Embed:
	description : str = ''
	try:
		nowplay : Dict = queue_info[0]
		index : int = 12 * (page - 1)

		description += template['Queue']['Now'] \
			% (
				nowplay['title'] \
					.replace('(', '\(') \
					.replace(')', '\)'),
				'https://youtu.be/' + nowplay['id']
			)
	except:
		description += template['Queue']['NoSong']

	for idx in range(1, 13):
		try:
			info : Dict = queue_info[index + idx]
			if idx == 1:
				description += template['Queue']['Next']
		except:
			break

		description += template['Queue']['Item'] \
			% (
				index + idx,
				info['title'] \
					.replace('(', '\(') \
					.replace(')', '\)'),
				'https://youtu.be/' + info['id']
			)

	if description != template['Queue']['NoSong']:
		description += template['Queue']['Page'] % (
			page,
			math.ceil((len(queue_info) - 1) / 12) \
				if math.ceil((len(queue_info) - 1) / 12) > 0 \
				else 1
		)

	description += template['Queue']['Request'] % (
		ctx.author.name + ctx.author.discriminator
	)

	embed = nc.Embed(
		color=nc.Colour.random(),
		description=description
	)
	return embed

def nowplay_embed(ctx : commands.Context, now_info : Dict, time : int):
	...

def parse_obj(obj : Dict) -> str:
	return 'https://youtu.be/' + obj['id']

def cycle_to_list(cycle, saved : List = []) -> List:
	while e := next(cycle):
		if e in saved:
			break

		saved.append(e)

	return saved

def jump_to_position(queue : List, pos : int):
	return queue[pos - 1:]

class CustomSource(nc.FFmpegPCMAudio):
	def __init__(self, vc : VC, source : Generic[AT], **kwargs):
		super().__init__(source, **kwargs)
		self.VC = vc

	def read(self):
		ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
		if len(ret) != OpusEncoder.FRAME_SIZE:
			return b''
		self.VC.time += 0.02
		return ret