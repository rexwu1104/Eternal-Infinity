import lavapy
from lavapy import (
	YoutubeTrack,
	YoutubeMusicTrack,
	SoundcloudTrack,
	LocalTrack,
	YoutubePlaylist
)
from lavapy.ext.spotify import (
	SpotifyTrack,
	SpotifyPlaylist,
	SpotifyAlbum
)
from nextcord.ext import commands
from nextcord import (
	VoiceChannel
)
from .embeds import (
	info_embed
)
from .functions import (
	_second_to_duration,
	_duration_to_second
)

class Player(lavapy.Player):
	def __init__(self, bot: commands.Bot, channel: VoiceChannel):
		super().__init__(bot, channel)
		self.ctx: commands.Context = None

class VoiceController(object):
	def __init__(self, bot, **funcs):
		self.player = None
		self.message = None
		self.tracks = []
		self.information = []
		self.now_info = {}
		self.DJs = []
		self.bot = bot
		self.funcs = funcs
		self.queue = []
		self.volume = 100
		self.loop_range = None
		self.in_sequence = False
		self.use_ui = False
		self.now_pos = None

	def parse(self, track, user):
		if isinstance(track, YoutubeTrack):
			data = {
				'base64_id': track.id,
				'id': track.identifier,
				'seekable': track.isSeekable,
				'author': track.author,
				'length': _second_to_duration(track.length//1000),
				'is_stream': track.isStream,
				'type': track.type,
				'title': track.title,
				'url': track.uri,
				'thumbnail': track.thumbnail
			}
			self.tracks.append(track)
		elif isinstance(track, YoutubePlaylist) or\
			isinstance(track, SpotifyPlaylist) or\
			isinstance(track, SpotifyAlbum):
			data = {
				'list_title': track.name,
				'tracks': []
			}
			self.tracks += track.tracks

			for child in track.tracks:
				data['tracks'].append({
					'base64_id': child.id,
					'id': child.identifier,
					'seekable': child.isSeekable,
					'author': child.author,
					'length': _second_to_duration(child.length//1000),
					'is_stream': child.isStream,
					'type': child.type,
					'title': child.title,
					'url': child.uri,
					'thumbnail': child.thumbnail,
					'player': user
				})
		else:
			data = {
				'base64_id': track.id,
				'id': track.identifier,
				'seekable': track.isSeekable,
				'author': track.author,
				'length': _second_to_duration(track.length//1000),
				'is_stream': track.isStream,
				'type': track.type,
				'title': track.title,
				'url': track.uri
			}
			self.tracks.append(track)

		data['player'] = user
		if data.get('tracks', None) is None:
			self.information.append(data)
		else:
			self.information += data['tracks']
		
		if not self.in_sequence:
			if data.get('tracks'):
				self.now_info = data['tracks'][0]
			else:
				self.now_info = data

			self.now_pos = self.information.index(self.now_info)
		else:
			self.bot.bot.loop.create_task(self.message.edit(
				embed=info_embed(self)
			))

	async def play(self):
		if self.now_pos >= len(self.tracks):
			await self.message.delete()

			node = self.player.node
			await self.player.destroy()
			await node.disconnect()
			
			self.reset()
			return

		await self.player.play(self.tracks[self.now_pos], volume=self.volume)
		self.now_info = self.information[self.now_pos]

	async def skip(self, pos):
		loop_range = self.loop_range
		if isinstance(loop_range, int):
			pass
		elif isinstance(loop_range, list):
			if self.now_pos + pos > loop_range[1]:
				self.now_pos = loop_range[1]
			else:
				self.now_pos += pos
		elif isinstance(loop_range, str):
			pass
		else:
			self.now_pos += pos

		await self.play()

	async def prev(self, pos):
		loop_range = self.loop_range
		if isinstance(loop_range, int):
			pass
		elif isinstance(loop_range, list):
			if self.now_pos - pos < loop_range[0]:
				self.now_pos = loop_range[0]
			else:
				self.now_pos -= pos
		elif isinstance(loop_range, str):
			pass
		else:
			self.now_pos -= pos
			
		await self.play()

	def vol(self, volume):
		if volume >= 100:
			self.volume = min(1000, volume)
		else:
			self.volume = max(0, volume)

		self.bot.bot.loop.create_task(self.player.setVolume(self.volume))

	def reset(self):
		self.player = None
		self.message = None
		self.tracks = []
		self.information = []
		self.now_info = {}
		self.queue = []
		self.volume = 100
		self.loop_range = None
		self.in_sequence = False
		self.now_pos = None