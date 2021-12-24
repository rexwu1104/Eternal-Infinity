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

def parse_obj(obj: Dict) -> str:
	return 'https://youtu.be/' + obj['id']

def _second_to_duration(time: int):
	h: int = time // 3600
	m: int = (time - h * 3600) // 60
	s: int = (time - h * 3600) - m * 60
	result: str = ''

	if h < 10:
		result += '0' + str(h)
	else:
		result += str(h)
	result += ':'
	if m < 10:
		result += '0' + str(m)
	else:
		result += str(m)
	result += ':'
	if s < 10:
		result += '0' + str(s)
	else:
		result += str(s)

	return result

def _duration_to_second(d: str):
	dl = d.split(':')
	s: int = 0
	for idx in range(0, len(dl)):
		s += s * 60 + int(dl[idx])

	return s

class SearchSelect(nc.ui.Select):
	def __init__(self, youtube_list: List[Dict]):
		self._options = youtube_list
		options = [
			nc.SelectOption(
				label=value['title'],
				description=f'https://youtu.be/{value["id"]}',
				value=youtube_list.index(value)
			) for value in youtube_list
		]

		super().__init__(
			placeholder='Choose one...',
			min_values=1,
			max_values=1,
			options=options
		)

	async def callback(self, interaction: nc.Interaction):
		interaction.response._responded = True
		self.view.stop()

class SearchView(nc.ui.View):
	def __init__(self, *args):
		super().__init__()

		self.add_item(SearchSelect(*args))

	async def interaction_check(self, interaction: nc.Interaction):
		await interaction.message.delete()
		return True

class MusicControlBoard(nc.ui.View):
	@nc.ui.button(style=nc.ButtonStyle.blurple, label='|---Loop---|', row=0)
	async def loop_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.green, label='|Volume Up|', row=0)
	async def volume_up_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.blurple, label='|Queue Loop|', row=0)
	async def queue_loop_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.green, label='|-Previous-|', row=1)
	async def prev_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.green, label='|--Pause--|', row=1)
	async def resume_and_pause_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.green, label='|--Next--|', row=1)
	async def next_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.blurple, label='|--Queue--|', row=2)
	async def queue_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.green, label='|Volume Down|', row=2)
	async def volume_down_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	@nc.ui.button(style=nc.ButtonStyle.blurple, label='|--Info--|', row=2)
	async def info_button(self, button: nc.ui.Button, interaction: nc.Interaction):
		...

	def __init__(self, vc, **funcs):
		super().__init__(timeout=None)

def queue_embed(ctx: commands.command, queue_info: List[Dict], page: int) -> nc.Embed:
	description: str = ''
	try:
		nowplay: Dict = queue_info[0]
		index: int = 12 * (page - 1)

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
			info: Dict = queue_info[index + idx]
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

def nowplay_embed(ctx: commands.Context, now_info: Dict, time: int):
	progress = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
	d = _second_to_duration(time)
	description = '[%s](%s)\n\n' % (
		now_info['title'],
		parse_obj(now_info)
	)
	t = _duration_to_second(now_info['length'])
	description += '`' + progress[:int(time/t*29)] +\
		'🔘' +\
		progress[int(time/t*29):] + '`\n\n'
	description += '`' + \
		d + \
		'/' + \
		_second_to_duration(
			_duration_to_second(now_info['length'])
		) + \
		'`'
	description += template['Queue']['Request'] % (
		ctx.author.name + ctx.author.discriminator
	)

	embed = nc.Embed(
		color=nc.Colour.random(),
		description=description,
		title='Now playing'
	)
	embed.set_thumbnail(now_info['thumbnail'][-1])
	return embed

def cycle_to_list(cycle, saved: List = []) -> List:
	while e := next(cycle):
		if e in saved:
			break

		saved.append(e)

	return saved

class TimeLogPCMAudio(nc.FFmpegPCMAudio):
	def __init__(self, vc: VC, source: Generic[AT], **kwargs):
		super().__init__(source, **kwargs)
		self.VC = vc

	def read(self):
		ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
		if len(ret) != OpusEncoder.FRAME_SIZE:
			self.VC.time = 0.0
			return b''
		self.VC.time += 0.02
		return ret