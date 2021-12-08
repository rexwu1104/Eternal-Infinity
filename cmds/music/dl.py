from NPytdl import Pytdl
from typing import (
	List,
	Dict,
	Union
)

ysdl = Pytdl()

async def get_youtube(q : str) -> str:
	s_l = await ysdl.resultList(q)
	return 'https://youtu.be/' + s_l[0]['id'], s_l[0]

async def get_youtube_list(q : str) -> List[Dict]:
	s_l = await ysdl.resultList(q)
	return s_l

async def get_spotify(q : str) -> str:
	s_l = await ysdl.spotifyResultList(q)
	n_l = filter(lambda i: q.lower() in i['title'].lower().split(' '), s_l)
	s_l = await ysdl.resultList(
		n_l[0]['title'] + '-' + \
		n_l[0]['author'][0]['name']
	)
	return 'https://youtu.be/' + s_l[0]['id'], s_l[0]