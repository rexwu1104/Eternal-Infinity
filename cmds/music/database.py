from sqlite3 import connect

conn = connect('./cmds/music/music.db')
cur = conn.cursor()