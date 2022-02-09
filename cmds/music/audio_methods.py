import nextcord
from nextcord.ext import (
	commands
)
from pysondb import db
from .embeds import (
	info_embed,
	queue_embed,
	now_embed
)
from .views import (
	ControlBoard,
	SelectMenu,
	ResultSelect
)

guild_db = db.getDb('./cmds/music/guilds.json')
member_db = db.getDb('./cmds/music/members.json')

def check(member, controller):
	return controller.queue[controller.now_pos][1] == member and member.voice is not None

def check_dj(member, controller):
	return member in controller.DJs or len(member.voice.channel.members) == 2

async def play_(self, ctx: commands.Context, q: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.client:
		controller.channel = ctx.author.voice.channel
		controller.client = await controller.channel.connect()

	if not controller.message:
		msg = await ctx.send("**loading...**")
		controller.message = msg

	if q.find('choice>') != -1:
		choices = q.split(' ')

		if choices[-1].isdigit():
			alias = choices[1]
			idx = int(choices[-1])

			data = member_db.getBy({'member_id': ctx.author.id})
			if len(data) == 0:
				return

			q = data[0]['aliases'][alias][idx]
		else:
			alias = choices[1]
			idx = 0

			data = member_db.getBy({'member_id': ctx.author.id})
			if len(data) == 0:
				return

			q = data[0]['aliases'][alias][idx]

	if controller.is_url(q):
		controller.tmps.append([
			q, ctx.author
		])
	else:
		await controller.search(q, ctx)

	if not controller.in_sequence:
		await controller.load(-1)
		controller.play(command=True)
	else:
		old_pos = controller.now_pos
		await controller.load(-1)
		await controller.load(old_pos, loaded=True)

	await controller.message.edit(
		view=ControlBoard(controller),
		embed=info_embed(controller),
		content=None
	)

async def search_(self, ctx: commands.Context, q: str):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.client:
		controller.channel = ctx.author.voice.channel
		controller.client = await controller.channel.connect()

	await ctx.send(
		'**take a choice~~**',
		view=ResultSelect(
			controller,
			await SelectMenu.create(controller, q)
		)
	)

async def queue_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	await controller.message.edit(embed=queue_embed(
		controller, ctx.author
	))

async def nowplay_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	await controller.message.edit(embed=now_embed(
		controller, ctx.author
	))

async def loop_(self, ctx: commands.Context, t: str):
	controller = self.controllers[ctx.guild.id]

	if not check_dj(ctx.author, controller):
		return

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	if t is None:
		if controller.loop_range is None:
			controller.loop_range = controller.now_pos
		else:
			controller.loop_range = None
	elif t.lower() == 'all':
		controller.loop_range = [0, len(controller.tmps) - 1]
	elif t.lower() == 'random':
		controller.loop_range = 'random'
	elif (t.find('-') != -1 and t.count('-') == 1):
		if controller.now_pos > controller.loop_range[1]:
			await controller.skip(0)
		elif controller.now_pos < controller.loop_range[0]:
			await controller.prev(0)

		controller.loop_range = list(map(
			lambda v: int(v) - 1,
			t.split('-')
		))
	elif (t.find('~') != -1 and t.count('~') == 1):
		if controller.now_pos > controller.loop_range[1]:
			await controller.skip(0)
		elif controller.now_pos < controller.loop_range[0]:
			await controller.prev(0)

		controller.loop_range = list(map(
			lambda v: int(v) - 1,
			t.split('~')
		))

	await controller.message.edit(
		view=ControlBoard(controller),
		embed=info_embed(controller)
	)

async def volume_(self, ctx: commands.Context, vol: float):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	controller.vol(vol)

	await controller.message.edit(
		view=ControlBoard(controller),
		embed=info_embed(controller)
	)

async def skip_(self, ctx: commands.Context, pos: int):
	controller = self.controllers[ctx.guild.id]
	
	if not check_dj(ctx.author, controller) or (not check(ctx.author, controller) and pos == controller.now_pos + 1):
		return

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	if pos - 1 > len(controller.tmps) or pos - 1 < 1:
		return

	if pos - 1 > controller.now_pos:
		await controller.skip(pos - 1 - controller.now_pos)
	elif pos - 1 < controller.now_pos:
		await controller.prev(controller.now_pos - pos + 1)
	else:
		await controller.skip(0)

async def join_(self, ctx: commands.Context, channel: nextcord.VoiceChannel):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.client:
		if channel is not None:
			controller.channel = channel
		else:
			controller.channel = ctx.author.voice.channel
			
		controller.client = await controller.channel.connect()

async def leave_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not ctx.author.voice.channel:
		return

	if ctx.author.voice.channel != controller.channel:
		return

	await controller.client.disconnect()
	await controller.message.delete()
	controller.client.stop()

	controller.reset()

async def stop_(self, ctx: commands.Context):
	controller = self.controllers[ctx.guild.id]

	if not check_dj(ctx.author, controller) or not check(ctx.author, controller):
		return

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return

	controller.client.pause()

	await controller.message.edit(
		view=ControlBoard(controller)
	)

async def create_dj_(self, ctx: commands.Context, name: str):
	data = guild_db.getBy({'guild_id': ctx.guild.id})

	if len(data) == 0:
		role = await ctx.guild.create_role(
			name=name,
			mentionable=False
		)

		data = {
			'dj_role_id': role.id,
			'name': name,
			'guild_id': ctx.guild.id
		}
		guild_db.add(data)

async def remove_(self, ctx: commands.Context, pos: int):
	controller = self.controllers[ctx.guild.id]

	if not check_dj(ctx.author, controller) or not check(ctx.author, controller):
		return

	if not ctx.author.voice.channel:
		return

	if not controller.in_sequence and ctx.author.voice.channel != controller.channel:
		return

	if not controller.message:
		return
	
	controller.tmps.pop(pos - 1)
	controller.queue.pop(pos - 1)
	controller.information.pop(pos - 1)

	if pos - 1 == controller.now_pos:
		await controller.skip(0)

	await controller.message.edit(
		view=ControlBoard(controller),
		embed=info_embed(controller)
	)

async def alias_(self, ctx: commands.Context, alias: str, sub: str):
	data = member_db.getBy({'member_id': ctx.author.id})

	if len(data) == 0:
		data = {
			'member_id': ctx.author.id,
			'aliases': {
				alias: [sub]
			}
		}
		member_db.add(data)
	else:
		data = data[0]
		data['aliases'][alias].append(sub)
		member_db.add(data)

async def custom_(self, ctx: commands.Context, option: str, action: str = None):
	...

async def insert_(self, ctx: commands.Context, pos: int, msg: str):
	...

async def together_(self, ctx: commands.Context):
	link = await self.bot.togetherControl.create_link(ctx.author.voice.channel.id, 'youtube')
	await ctx.send("__click this!!!__\n{}".format(link))