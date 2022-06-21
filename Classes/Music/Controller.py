from ..Imports import Logger, MusicSource, await_run

from .Container import MContainer
from .Database import MDB
from .Translator import MTranslator
from .Enum import MPlayStatus, MPlayMode
from .View import MusicView

from discord.ext import commands
from discord import FFmpegPCMAudio, Member, User
from functools import partial
from typing import Union
from typing_extensions import Self

__all__ = (
    'MController',
)

OPTIONS = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3', 'options': '-vn'
}

class MController():
    bot: commands.AutoShardedBot
    containers: dict[int, MContainer] = {}
    db: MDB = MDB()
    dj_ids: dict[int, int] = {}
    translate_data: dict[int, str] = {}
    youtube_data: dict[int, bool] = {}
    youtube_enable_users: list[User] = []
    
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot = bot
        self.translate_data = dict([(int(k), v) for k, v in self.db.read('Classes/translate.json').items()])

        self.dj_ids = dj_ids = dict([(int(k), v) for k, v in self.db.read('Classes/dj_ids.json').items()])
        for guild in bot.guilds:
            Logger.log('guild[{0}] create'.format(guild.name))
            guild_id = guild.id
            if guild_id not in self.translate_data:
                self.translate_data[guild_id] = 'en-us'
                
            self.containers[guild_id] = MContainer(guild.id, MTranslator(self.translate_data[guild_id]))
            self.containers[guild_id].view = MusicView.ControlBoard(self)
            self.containers[guild_id].dj_role_id = dj_ids.get(guild_id, None)
            
        self.db.write('Classes/translate.json', self.translate_data)
        
        self.youtube_data = dict([(int(k), v) for k, v in self.db.read('Classes/youtube.json').items()])
        for k, v in self.youtube_data.items():
            if v:
                self.youtube_enable_users.append(self.bot.get_user(k))
    
    @classmethod        
    async def create(cls, bot: commands.AutoShardedBot) -> Self:
        await bot.wait_until_ready()
        return cls(bot)
    
    def check_dj(self, member: Member):
        container = self.containers[member.guild.id]
        dj_role = member.guild.get_role(container.dj_role_id)
        return True if dj_role in member.roles else False
            
    def play(self, guild_id: int, _ = None) -> None:
        container = self.containers[guild_id]
        Logger.debug(f'range is: {container.range}')
        Logger.debug(f'now_pos is: {container.now_pos}')
        
        if container.client is None and len(container):
            return Logger.error('Client is not joined the channel.')
        
        source = next(container)
        if source is None and container.client is not None:
            container.play_status = MPlayStatus.UnStarted
            
            await_run(container.client.disconnect(force=True), loop=self.bot.loop)
            await_run(container.sent_message.delete(), loop=self.bot.loop)
            
            container.clear()
            container.view._loop.emoji = '➡️'
            
            return None
        
        container.play_status = MPlayStatus.Play
        source.load(self.bot)
        Logger.log('guild[{0}] load source: {1}'.format(container.client.guild.name, source.info.title))
        
        container.source = MusicSource(FFmpegPCMAudio(source.audio_url, **OPTIONS), container.volume)
        container.client.play(container.source, after=partial(self.play, guild_id))
        Logger.log('guild[{0}] play source: {1}'.format(container.client.guild.name, source.info.title))
        
        container.view.page_position = MusicView.PagePosition.Info
        container.view._play_or_pause.emoji = '⏸️'
        if container.play_mode != MPlayMode.Odd:
            await_run(container.sent_message.edit(content=None,
                                                  embed=MusicView.information_embed(container),
                                                  view=container.view), loop=self.bot.loop)
        
    def pause(self, guild_id: int) -> None:
        container = self.containers[guild_id]
        
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        if container.client.is_playing():
            Logger.log('guild[{0}] pause'.format(container.client.guild.name))
            container.client.pause()
            
    def resume(self, guild_id: int) -> None:
        container = self.containers[guild_id]
        
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        if container.client.is_paused():
            Logger.log('guild[{0}] resume'.format(container.client.guild.name))
            container.client.resume()
            
    def stop(self, guild_id: int) -> None:
        container = self.containers[guild_id]
        
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        container.data.clear()
        container.client.stop()
        Logger.log('guild[{0}] stop'.format(container.client.guild.name))
            
    def jump_at(self, guild_id: int, pos: int) -> None:
        container = self.containers[guild_id]
        
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        match container.play_mode:
            case MPlayMode.Nothing:
                if pos == -1:
                    pos = 0
                elif pos >= len(container) or pos < 0:
                    return Logger.error('Pos is not in range.')
                
                container.now_pos = pos - 1
                container.client.stop()
            case MPlayMode.Plural:
                if pos == -1:
                    pos = container.range[1]
                elif pos >= container.range[1] or pos < container.range[0]:
                    return Logger.error('Pos is not in range.')
                
                container.now_pos = pos - 1
                container.client.stop()
            case MPlayMode.All:
                if pos == -1:
                    pos = len(container) - 1
                elif pos == len(container):
                    pos = 0
                elif pos > len(container) or pos < 0:
                    return Logger.error('Pos is not in range.')
                
                container.now_pos = pos - 1
                container.client.stop()
            case MPlayMode.Odd | MPlayMode.Shuffle:
                container.client.stop()
        
        Logger.log('guild[{0}] skip to {1}'.format(container.client.guild.name, pos))
        
    def remove_music(self, guild_id: int, position: int):
        container = self.containers[guild_id]
        if position < container.now_pos:
            container.now_pos -= 1
        elif position == container.now_pos:
            container.now_pos -= 2
            container.client.stop()
            
        container.data.pop(position)
        Logger.log('guild[{0}] remove position {1}'.format(container.client.guild.name, position))
                
    def set_volume(self, guild_id: int, volume: float) -> None:
        container = self.containers[guild_id]
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        container.source.volume = volume
        container.volume = container.source.volume
        Logger.log('guild[{0}] volume change: {1}'.format(container.client.guild.name, container.volume))
        
    def change_play_mode(self, guild_id: int, mode: MPlayMode) -> None:
        container = self.containers[guild_id]
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        container.play_mode = mode
        Logger.log('guild[{0}] play mode change: {1}'.format(container.client.guild.name, mode.name))
        
    def add_dj(self, guild_id: int, dj_id: int) -> None:
        self.dj_ids[guild_id] = dj_id
        self.db.write('Classes/dj_ids.json', self.dj_ids)
        
    def add_youtube_enable(self, user: Union[User, Member]) -> bool:
        if user in self.youtube_enable_users and self.youtube_data[user.id]:
            return True
        elif user not in self.youtube_enable_users:
            self.youtube_enable_users.append(user)
            
        self.youtube_data[user.id] = True
        self.db.write('Classes/youtube.json', self.youtube_data)
        
        return False
    
    def remove_youtube_enable(self, user: Union[User, Member]) -> bool:
        if user in self.youtube_enable_users and not self.youtube_data[user.id]:
            return True
        elif user not in self.youtube_enable_users:
            return True
            
        self.youtube_data[user.id] = False
        self.db.write('Classes/youtube.json', self.youtube_data)
        
        return False