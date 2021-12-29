from nextcord import (
	Embed, Colour
)
from .functions import (
	_second_to_duration,
	_duration_to_second
)

def info_embed(controller):
	description = f'**length:** `{controller.now_info["length"]}`\n'
	description += f'**suffle:** `{controller.loop_range == "random"}`\n'
	description += f'**loop:** `'
	
	if controller.loop_range is None or type(controller.loop_range) == str:
		description += 'Nothing`\n'
	elif type(controller.loop_range) == int:
		description += f'{controller.loop_range + 1}`\n'
	elif type(controller.loop_range) == list:
		description += f'{controller.loop_range[0] + 1}~{controller.loop_range[1] + 1}`\n'

	description += f'**volume:** `{int(controller.volume*100)}%`\n'
	description += f'**position:** `{controller.now_pos + 1}`/`{len(controller.tmps)}`\n'
	description += f'**player:** `{controller.queue[controller.now_pos][1]}`\n\n'

	embed = Embed(
		title=controller.now_info['title'],
		colour=Colour.random(),
		description=description,
		url='https://youtu.be/' + controller.now_info['id']
	)

	embed.set_image(url=controller.now_info['thumbnail'][-1]['url'])

	return embed

def queue_embed(controller, user):
	description = '__Now playing:__\n[%s](%s)\n\n' % (
		controller.now_info['title']
			.replace('(', '\(')
			.replace(')', '\)'),
		'https://youtu.be/' + controller.now_info['id']
	)
	description += '__Up next:__\n'

	for idx in range(1, 13):
		try:
			description += '%d. [%s](%s)\n\n' % (
				controller.now_pos + idx + 1,
				controller.information[controller.now_pos + idx]['title']
					.replace('(', '\(')
					.replace(')', '\)'),
				'https://youtu.be/' + controller.information[controller.now_pos + idx]['id']
			)
		except:
			if idx == 1:
				description += '__here is nothing...__\n\n'

			break

	description += '`Request by: %s`' % (
		user.name + user.discriminator
	)

	embed = Embed(
		title='Queue',
		colour=Colour.random(),
		description=description
	)
	
	return embed

def now_embed(controller, user):
	progress = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
	d = _second_to_duration(int(controller.time))
	description = '[%s](%s)\n\n' % (
		controller.now_info['title'],
		'https://youtu.be/' + controller.now_info['id']
	)

	t = _duration_to_second(controller.now_info['length'])
	description += '`' + progress[:int(controller.time/t*29)] + \
		'🔘' + \
		progress[int(controller.time/t*29):] + '`\n\n'

	description += '`' + \
		d + \
		'/' + \
		_second_to_duration(t) + \
		'`\n\n'

	description += '`Request by: %s`' % (
		user.name + user.discriminator
	)

	embed = Embed(
		colour=Colour.random(),
		description=description,
		title='Now playing'
	)
	embed.set_thumbnail(url=controller.now_info['thumbnail'][-1]['url'])

	return embed