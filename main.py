import os
import nextcord as nc
from nextcord.ext import commands
from discord_together import DiscordTogether

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

intents = nc.Intents.all()
bot = commands.AutoShardedBot(
	command_prefix = 'ei!',
	intents = intents
)
# bot.remove_command('help')

@bot.event
async def on_ready():
	bot.togetherControl = await DiscordTogether(os.environ['token'])
	await bot.change_presence(
		activity = nc.Streaming(
			name = 'ei!help',
			url = 'https://www.twitch.tv/yee6nextcord'
		)
	)

	if bot.loop.is_running():
		from multiprocessing import Process
		from web.backend import start_server
		proc = Process(
			target = start_server,
			daemon = True
		)
		proc.start()
	
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

if __name__ == '__main__':
	bot.run(os.environ['token'])