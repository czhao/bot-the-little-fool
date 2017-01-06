"""
Utility class
"""

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def retrieve_text_from_message(m):
	if 'message' in m:
		plain_message = m['message']
		if 'text' in plain_message:
			# this is a text message
			return plain_message['text']
	return ''