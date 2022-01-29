def _second_to_duration(time: int):
	h: int = time // 3600
	m: int = (time - h * 3600) // 60
	s: int = (time - h * 3600) - m * 60
	result: str = ''

	if h < 10:
		result += '0' + str(h)
	else:
		result += str(h)
	result += ':'
	if m < 10:
		result += '0' + str(m)
	else:
		result += str(m)
	result += ':'
	if s < 10:
		result += '0' + str(s)
	else:
		result += str(s)

	return result

def _duration_to_second(d: str):
	dl = d.split(':')
	s: int = 0
	for idx in range(0, len(dl)):
		s += s * 60 + int(dl[idx])

	return s