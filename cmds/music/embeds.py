from nextcord import (
	Embed, Colour
)

def info_embed(controller):
	description = f'**length:** `{controller.now_info["length"]}`\n'
	description += f'**suffle:** `{controller.loop_range == "random"}`\n'
	description += f'**loop:** `'
	
	if controller.loop_range is None or type(controller.loop_range) == str:
		description += 'Nothing`\n'
	elif type(controller.loop_range) == int:
		description += 'Single`\n'
	elif type(controller.loop_range) == list:
		description += 'Queue`\n'

	description += f'**volume:** `{int(controller.volume*100)}%`\n'
	description += f'**position:** `{controller.now_pos + 1}`/`{len(controller.tmps)}`\n\n'

	embed = Embed(
		title=controller.now_info['title'],
		colour=Colour.random(),
		description=description,
		url='https://youtu.be/' + controller.now_info['id']
	)

	embed.set_image(url=controller.now_info['thumbnail'][-1]['url'])

	return embed