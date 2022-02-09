import asyncio
from itertools import cycle
import nextcord as nc
from nextcord.ext import commands, tasks
from core.cog_append import Cog

class Tasks(Cog):
    bot: commands.Bot
    
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        
        self.activities = self.next_activity()
        
    def Union(self, *args):
        final = set()
        for arg in args:
            s = set()
            for v in arg:
                s.add(v)
                
            final |= s
            
        return final
    
    async def next_activity(self):
        for idx in cycle([0, 1, 2]):
            if idx == 0:
                yield nc.Streaming(
                    name = 'ei!help',
                    url = 'https://www.twitch.tv/yee6nextcord'
                )
            elif idx == 1:
                yield nc.Activity(
                    name = f'{len(self.bot.guilds)} Severs, {len(list(self.bot.get_all_members()))} Members',
                    type = nc.ActivityType.watching
                )
            elif idx == 2:
                yield nc.Activity(
                    name = 'invite => https://discord.com/api/oauth2/authorize?client_id=723543888786358304&permissions=8&scope=bot%20applications.commands',
                    type = nc.ActivityType.listening
                )
        
    @tasks.loop(seconds=120)
    async def tasks_activity(self):
        await self.bot.wait_until_ready()
    
        act = await self.activities.__anext__()
        await self.bot.change_presence(
            activity = act
        )
            
def setup(bot: commands.Bot):
    task_bot = Tasks(bot)
    task_bot.tasks_activity.start()
    bot.add_cog(task_bot)