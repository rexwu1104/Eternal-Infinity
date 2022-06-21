from __future__ import unicode_literals

from Functions import *
from Global import *

import asyncio
import youtube_dl

from typing_extensions import *
from typing import *
from discord import *
from urllib.request import *

__all__ = (
    'MusicCore',
    'MusicObject',
    'MusicSource',
)

class _Logger():
    
    def debug(self, msg: str) -> None:
        pass
        
    def warning(self, msg: str) -> None:
        pass
    
    def error(self, msg: str) -> None:
        print(msg)

ydl_opt = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredquality': '192'
    }],
    'logger': _Logger(),
    'cookiefile': 'cookies.txt'
}

class MusicObject():
    age_limit: int
    audio_url: str
    author: str
    channel: str
    counts: int
    id: str
    length: str
    likes: int
    living: bool
    tags: list[str]
    title: str
    thumbnail: str
    video_url: str
    
    def __init__(self, obj: dict) -> None:
        for k, v in obj.items():
            setattr(self, k, v)
            
def test_url(url: str):
    try:
        urlopen(url)
    except:
        return True
    return False

class MusicCore():
    
    @classmethod
    def info(cls, url: str, loop: asyncio.AbstractEventLoop) -> MusicObject:
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            times = 0
            info: dict = ydl.extract_info(url, download=False)
            
            while test_url(info['url']):
                if times == 2:
                    raise Exception('Audio download failed.')
                
                Logger.error('download failed')
                asyncio.run_coroutine_threadsafe(asyncio.sleep(0.2), loop=loop)
                info: dict = ydl.extract_info(url, download=False)
                times += 1
            
        return MusicObject({
            'id': info.get('id'),
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'author': info.get('uploader'),
            'channel': info.get('channel_url'),
            'length': duration_to_length(info.get('duration')),
            'counts': info.get('view_count'),
            'age_limit': info.get('age_limit'),
            'video_url': info.get('webpage_url'),
            'tags': info.get('tags'),
            'living': False if info.get('is_live') is None else True,
            'likes': info.get('like_count', 0),
            'audio_url': info.get('url')
        })
        
class MusicSource(PCMVolumeTransformer):
    elapsed: float = .0
    original_read: Callable[[Self], bytes]
    
    def __init__(self, original: FFmpegPCMAudio, volume: float = 1.0):
        super().__init__(original, volume)
        self.original_read = super().read
        
    def read(self) -> bytes:
        ret = self.original_read()
        if ret == b'':
            self.elapsed = .0
        else:
            self.elapsed += 0.02
            
        return ret