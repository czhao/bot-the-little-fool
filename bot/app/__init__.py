import os
import flask
from flask import request
from flask import Flask
from flask import json,g
from auth import requires_auth
import requests
import logging
import sqlite3
import bill.parser
from celery import Celery

from raven.contrib.flask import Sentry
from werkzeug.contrib.cache import MemcachedCache

app = Flask(__name__)

app.config.update(DEBUG = True, SECRET_KEY = "123456")

app.config.update(dict(
    DATABASE= os.environ['SQLITE_DB_PATH'],
    USERNAME='admin',
    PASSWORD='default',
    CELERY_BROKER_URL='redis://localhost:12094',
    CELERY_RESULT_BACKEND='redis://localhost:12094'
))

app.config.from_envvar('BOT_APPLICATION_SETTINGS')

sentry = Sentry(app, dsn=app.config['SENTRY_DSN'],logging=True,level=logging.ERROR)

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@app.route('/webhook', methods=['POST','GET'])
@requires_auth
def fb_webhook():
	# handle the validation
	if request.method == 'GET':
		mode = request.args.get('hub.mode','')
		token = request.args.get('hub.verify_token')
		if mode == 'subscribe' and token == app.config['FB_VERIFY_TOKEN']:
			return request.args.get('hub.challenge')
		else:
			return "invalid request"
	elif request.method == "POST":
		json_data = request.get_json()
		if json_data['object'] == 'page':	
			process_page_msg.delay(json_data)	    
		return ''
	else:
		return "invalid request"

@celery.task()
def process_page_msg(raw_msg):
	app.logger.error("res: %s",raw_msg)
	for msg in raw_msg['entry']:
		if msg['messaging'] is not None:
				for m in msg['messaging']:
					sender = m['sender']['id']
					if bill.parser.process_context_text_message(sender, m):
						pass
					else:
						data = {'recipient':{'id': sender},'message':{'text':'oops, I cannot understand'}}
						fb_send_message(data)

	return ''

@celery.task()
def process_task(task_info, recipient, is_follow_up_available):
	bill.parser.parse_task(task_info, recipient, is_follow_up_available)


def schedule_task(task_info, recipient, is_follow_up_available = False):		
	process_task.delay(task_info, recipient, is_follow_up_available)
	if is_follow_up_available:
		data = {'recipient':{'id': recipient},'sender_action':'typing_on'}
		fb_send_message(data)


def fb_stop_typing(recipient):
	data = {'recipient':{'id': recipient},'sender_action':'typing_off'}
	fb_send_message(data)

def fb_send_message(message_data):
	url = 'https://graph.facebook.com/v2.6/me/messages'
	data = message_data
	headers = {'Content-Type': 'application/json'}
	payload = {'access_token': app.config['FB_ACCESS_TOKEN']}
	r = requests.post(url, data = json.dumps(data), headers = headers, params = payload)
	# log the response
	if r.status_code != 200:
		app.logger.error('failed to send fb message %d', r.status_code)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
	
def get_memcache():
	if not hasattr(g, 'mem_cache'):
		g.mem_cache = MemcachedCache([os.environ['MEMCACHED_HOST']])
	return g.mem_cache

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()