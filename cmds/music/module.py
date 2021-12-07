import nextcord as nc
import asyncio
from nextcord.ext import commands
from typing import (
	List,
	Dict,
	Union
)

async def get_place(bot : commands.Bot, ctx : commands.Context) -> str:
	def check(m : nc.Message):
		return m.content in ['spotify', 'youtube']

	sr = await ctx.send('where do you want search?')

	try:
		m = bot.wait_for('message', check=check, timeout=60.0)
	except asyncio.TimeoutError:
		await ctx.send('**timeout!!!**')
		return None

	await sr.delete()
	return m.content

async def get_number(bot : commands.Bot, ctx : commands.Context) -> Union[int, str]:
	def check(m : nc.Message):
		return m.content.isdigit() or m.content == 'cancel'

	sr = await ctx.send('**Type a number to make a choice. Type** `cancel` **to exit**')

	try:
		m = bot.wait_for('message', check=check, timeout=60.0)
	except asyncio.TimeoutError:
		await ctx.send('**timeout!!!**')
		return None

	await sr.delete()
	return int(m.content) if m.content.isdigit() else m.content

async def search_embed(youtube_list : List[Dict]) -> nc.Embed:
	description : str = ''
	for item in youtube_list:
		title = item['title']
		description += f'{youtube_list.index(item)+1}. [{title}](https://youtu.be/{item["id"]})\n\n'

	embed = nc.Embed(
		color=nc.Colour.random,
		description=description
	)
	return embed

def parse_obj(obj : Dict):
	return 'https://youtu.be/' + obj['id']
