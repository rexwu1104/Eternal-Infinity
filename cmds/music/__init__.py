import re
import random
import NPytdl
import orjson
import asyncio
from core.cog_append import Cog
from functools import partial
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
# from .methods import ()
# from .embeds import ()

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}
guild_db = db.getDb('./cmds/music/guilds.json')

def is_owner(ctx: commands.Context) -> bool:
	return ctx.author.id == 606472364271599621

class Music(cog_append):
	...

def setup(bot: commands.Bot):
	bot.add_cog(Music(bot))