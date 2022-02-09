import os
import asyncio
import nextcord as nc
from nextcord.ext import commands
from itertools import cycle
from discord_together import DiscordTogether

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

intents = nc.Intents.all()
bot = commands.AutoShardedBot(
	command_prefix = 'ei!',
	intents = intents
)

@bot.event
async def on_ready():
	bot.togetherControl = await DiscordTogether('NzIzNTQzODg4Nzg2MzU4MzA0.XuzKwQ.ZgZaLqOvXLvlp0fmFQzLviZafOw')
	
	for fin in os.listdir('./cmds'):
		if fin.endswith('.py'):
			bot.load_extension(f'cmds.{fin[:-3]}')
		elif os.path.isdir(f'./cmds/{fin}'):
			bot.load_extension(f'cmds.{fin}')
			
	print('EI start online.')

@bot.command()
@commands.check(is_owner)
async def load(ctx: commands.Context, file_name: str):
	bot.load_extension(f'cmds.{file_name}')
	await ctx.message.delete()

@bot.command()
@commands.check(is_owner)
async def unload(ctx: commands.Context, file_name: str):
	bot.unload_extension(f'cmds.{file_name}')
	await ctx.message.delete()

@bot.command()
@commands.check(is_owner)
async def reload(ctx: commands.Context, file_name: str):
	bot.reload_extension(f'cmds.{file_name}')
	await ctx.message.delete()
 
@bot.command()
@commands.check(is_owner)
async def guilds(ctx: commands.Context):
    await ctx.message.delete()
    async for guild in bot.fetch_guilds(limit=None):
        try:
            invites = await guild.invites()
        except:
            continue
        
        print(guild.name, invites[0].url if len(invites) >= 1 else "No link")

@bot.event
async def on_command_error(ctx: commands.Context, err: Exception):
   print(err.__dict__)
   err = err.args[0].split(': ')[-1].strip(' ')
   msg = await ctx.send('**' + err + '**')
   await msg.delete(delay=5)

if __name__ == '__main__':
	bot.run('NzIzNTQzODg4Nzg2MzU4MzA0.XuzKwQ.ZgZaLqOvXLvlp0fmFQzLviZafOw')
