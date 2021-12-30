from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root_get():
	return {'hello': 'web!'}

def start_server():
	import uvicorn, asyncio
	config = uvicorn.Config(
		app,
		host = '0.0.0.0',
		port = 8080
	)
	server = uvicorn.Server(config=config)

	asyncio.run(server.serve())