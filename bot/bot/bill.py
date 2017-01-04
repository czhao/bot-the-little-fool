import bot
import utils
"""
Bill Management
"""

def is_session_active(session_id):
	cache_key = 'bill_%s' % session_id
	cache = bot.get_memcache();
	return cache.get(cache_key) != None


def open_new_session(session_id):
	cache_key = 'bill_%s' % session_id
	cache = bot.get_memcache();
	data = {}
	cache.set(cache_key, data)

"""
update the session info

status: pending_for_price, pending_for_category,  pending_for_description

"""
def update_session_info(session_id, status, key, value):
	cache_key = 'bill_%s' % session_id
	cache = bot.get_memcache();
	data = cache.get(cache_key)
	if data == None:
		return False
	data[key] = value;
	data['status'] = status
	cache.set(cache_key, data)
	return True


"""
return 0: accepted  1: context completed -1: irrelevant
"""
def update_session_info_within_context(session_id, text_message):
	cache_key = 'bill_%s' % session_id
	cache = bot.get_memcache();
	data = cache.get(cache_key)
	status = data.get('status', '')
	if status == 'pending_for_description':
		data['description'] = text_message;
		data['status'] = 'pending_for_price'
		cache.set(cache_key, data)
		return (0, 'How much is it?')
	elif status == 'pending_for_price' and utils.is_number(text_message):
		cache.delete(cache_key)
		save_bill(cache_key, data['category'], data['description'], text_message, data['currency'])
		return (1, 'Got it.')
	else:
		return (-1, 'I do not get it')

def save_bill(session_id, category, description, amount, currency):
	db = bot.get_db()
	db.execute('INSERT INTO task_bill (session, category, description, payment, currency) VALUES (?, ?, ?, ?, ?)', 
		[session_id, category, description, amount, currency])
	db.commit()


def get_today_spending():
	db = bot.get_db()
	statement = 'Today you have spent:\n'
	result = []
	c = db.cursor()
	c.execute('SELECT `description`,`currency`,`payment`'+
		'FROM task_bill WHERE `timestamp` >= date("now", "start of day", "localtime") ' + 
		'ORDER BY `timestamp` DESC')
	rows = c.fetchall()
	if len(rows) > 0:
		for row in rows:
			statement = statement + '%s %s %s' % (row[0], row[1], row[2]) + '\n'
			if len(statement) > 200:
				result.append(statement)
				statement = ''
		if len(statement) > 0:
			result.append(statement)		
	else:
		result.append("You have no spending today.")
	return result


