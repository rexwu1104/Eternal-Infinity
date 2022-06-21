from ..Imports import *

from discord.ext import commands
from discord import Member, User

__all__ = (
    'MSong',
)

class MSong(AsyncObject):
    url: str = None
    audio_url: str = None
    dict_info: dict = None
    info: MusicObject = None
    author: Union[Member, User] = None
    
    async def __init__(self, search_data: Union[str, dict], author: Union[Member, User], *, search: bool = True) -> None:
        if search:
            data, data_type = await process_url_structs(search_data)
            Logger.debug('get data')
        else:
            data, data_type = [search_data], 'normal'
            
        if data_type == 'list':
            self.songs = data
        else:
            self.dict_info = data[0]
            self.url = data[0]['url']
            self.author = author
        
    def load(self, bot: commands.AutoShardedBot) -> None:
        if self.audio_url is not None:
            return
        
        self.info = MusicCore.info(self.url, bot.loop)
        self.audio_url = self.info.audio_url