from NPytdl import Pytdl
from typing import (
	List,
	Dict
)

ysdl = Pytdl()

async def get_youtube(q: str) -> str:
	s_l = await ysdl.resultList(q)
	return 'https://youtu.be/' + s_l[0]['id'], s_l[0]

async def get_youtube_list(q: str) -> List[Dict]:
	s_l = await ysdl.resultList(q)
	return s_l