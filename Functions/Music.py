from Global import *

import asyncio
import orjson as json
import re

from pytube import YouTube, Playlist, Search

__all__ = (
    'duration_to_length',
    'length_to_duration',
    'get_translation_data',
    'process_url',
    'process_url_list',
    'process_url_struct',
    'process_url_structs',
    'await_run',
)

YoutubeUrlRe = re.compile(r'(?:https://)?(?:www\.)?youtu(?:\.)?be(?:\.com).*')
await_run = asyncio.run_coroutine_threadsafe

def get_translation_data() -> dict[str, dict[str, str]]:
    with open('Classes/keyword.json', 'r', encoding='utf-8') as tfile:
        return json.loads(tfile.read())
    
async def process_url_structs(yet_url: str) -> tuple[list[dict], str]:    
    if YoutubeUrlRe.match(yet_url) is None:
        data: list[YouTube] = list(Search(yet_url).results)
        result_type = 'normal'
    elif yet_url.find('list') != -1:
        yet_url = 'https://www.youtube.com/playlist?list=' + re.search(r'list=([0-9a-zA-Z_-]*)', yet_url).group(1)
        Logger.debug('list url is \'{0}\''.format(yet_url))
        data: list[YouTube] = list(Playlist(yet_url).videos)
        result_type = 'list'
    else:
        data: list[YouTube] = [YouTube(yet_url)]
        result_type = 'normal'
        
    return ([{
        'id': datum.video_id,
        'url': datum.watch_url,
        'title': datum.title,
        'thumbnail': datum.thumbnail_url
    } for datum in data], result_type)

async def process_url_struct(yet_url: str) -> dict:
    return await process_url_structs(yet_url)[0][0]

async def process_url_list(yet_url: str) -> list[str]:
    return [struct['url'] for struct, _ in await process_url_structs(yet_url)]
    
async def process_url(yet_url: str) -> str:
    return await process_url_list(yet_url)[0]

def duration_to_length(duration: int) -> str:
    duration = int(duration)
    result = ''
    
    hours = duration // 3600
    minutes = (duration - hours * 3600) // 60
    seconds = (duration - hours * 3600) - minutes * 60

    if hours < 10:
        result += '0' + str(hours)
    else:
        result += str(hours)
        
    result += ':'
    if minutes < 10:
        result += '0' + str(minutes)
    else:
        result += str(minutes)
        
    result += ':'
    if seconds < 10:
        result += '0' + str(seconds)
    else:
        result += str(seconds)

    return result

def length_to_duration(length: str) -> int:
    result = 0
    for num in map(lambda v: int(v), length.split(':')):
        result *= 60; result += num
        
    return result