import orjson

class DB:
	file_name = './cmds/music/music.json'

	def __init__(self):
		with open(self.file_name, 'r', encoding='utf8') as rjson:
			self.tmp = {} or orjson.loads(rjson.read())

	def get(self, key):
		with open(self.file_name, 'r', encoding='utf8') as rjson:
			self.tmp = orjson.loads(rjson.read())

		return self.tmp.get(key)

	def set(self, key, val):
		with open(self.file_name, 'w', encoding='utf8') as wjson:
			self.tmp[key] = val
			wjson.write(orjson.dumps(self.tmp).decode())

	def keys(self):
		return self.tmp.keys()

	def delete(self, key):
		with open(self.file_name, 'w', encoding='utf8') as wjson:
			del self.tmp[key]
			wjson.write(orjson.dumps(self.tmp).decode())