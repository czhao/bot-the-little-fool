import logging
import os
import sqlite3

import apiai
import bill.memory
import bill.parser
import core.parser
import redis
import requests
import task.parser
from auth import requires_auth
from celery import Celery
from flask import Flask
from flask import json, g
from flask import request
from raven.contrib.flask import Sentry
from werkzeug.contrib.cache import MemcachedCache
from wit import Wit

app = Flask(__name__)

app.config.update(DEBUG=True, SECRET_KEY="123456")

app.config.update(dict(
    DATABASE=os.environ['SQLITE_DB_PATH'],
    USERNAME='admin',
    PASSWORD='default',
    CELERY_BROKER_URL='redis://localhost:12094',
    CELERY_RESULT_BACKEND='redis://localhost:12094',
    REDIS_HOST='127.0.0.1',
    REDIS_PORT='12094'
))

app.config.from_envvar('BOT_APPLICATION_SETTINGS')

sentry = Sentry(app, dsn=app.config['SENTRY_DSN'], logging=True, level=logging.ERROR)


def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    task_base = celery.Task

    class ContextTask(task_base):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return task_base.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


@app.route('/webhook', methods=['POST', 'GET'])
@requires_auth
def fb_webhook():
    # handle the validation
    if request.method == 'GET':
        mode = request.args.get('hub.mode', '')
        token = request.args.get('hub.verify_token')
        if mode == 'subscribe' and token == app.config['FB_VERIFY_TOKEN']:
            return request.args.get('hub.challenge')
    elif request.method == "POST":
        process_page_msg.delay(request.get_json())
    return ""


@app.route('/action', methods=['POST', 'GET'])
@requires_auth
def decision_webhook():
    # handle the validation
    if request.method == "POST":
        json_data = request.get_json()
        if 'result' in json_data:
            process_api_result.delay(json_data)
        return ''
    return "invalid request"


@app.route('/mock', methods=['POST'])
def mock_decision_webhook():
    # handle the validation
    json_data = request.get_json()
    if 'result' in json_data:
        process_query_result(json_data, '1288011787911930')
    return ''


@celery.task()
def process_page_msg(raw_msg):
    app.logger.error("res: %s", raw_msg)
    for msg in raw_msg['entry']:
        if msg['messaging'] is not None:
            for m in msg['messaging']:
                uid = m['sender']['id']
                if 'message' in m and 'text' in m['message']:
                    text_msg = m['message']['text']
                    response = ai_send_message(text_msg, "s_%s" % uid)
                    process_query_result(json.loads(response), uid)
                elif 'postback' in m:
                    # handle predefined payload
                    payload = m['postback']['payload']
                    if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_NEW_PAYMENT':
                        response = ai_send_message('Note a new payment', "s_%s" % uid)
                        process_query_result(json.loads(response), uid)


@celery.task()
def process_query_result(raw_msg, uid):
    app.logger.error("res: %s", raw_msg)
    if 'result' in raw_msg:
        fulfillment = raw_msg['result']['fulfillment']
        messages = fulfillment['messages']
        speech = fulfillment['speech']
        if speech is not None and len(speech) > 0:
            fb_send_text_msg(uid, speech)
        else:
            for m in messages:
                msg_type = m['type']
                if msg_type == 2:
                    # quick replay
                    title = m['title']
                    quick_replies = m['replies']
                    quick_reply_options = []
                    for option in quick_replies:
                        quick_reply_options.append({'content_type': 'text', 'title': option, 'payload': option})
                    data = {'recipient': {'id': uid}, 'message': {'text': title, 'quick_replies': quick_reply_options}}
                    fb_send_message(data)


@celery.task()
def process_api_result(raw_msg):
    app.logger.error("res: %s", raw_msg)

    if 'result' in raw_msg and 'sessionId' in raw_msg:
        session_id = raw_msg['sessionId']
        uid = session_id[2:]
        action = raw_msg['result']['action']
        if action == "payment_save":
            bill.parser.parse_decision(raw_msg, uid)
        elif action == "profile_update_currency":
            core.parser.parse_decision(raw_msg, uid)
        elif action == "estimate_bus_arrival":
            task.parser.parse_decision(raw_msg, uid)
        elif action == "estimate_bus_arrival_v2":
            task.parser.parse_decision_bus(raw_msg, uid)


@celery.task()
def process_task(task_info, recipient, is_follow_up_available):
    bill.parser.parse_task(task_info, recipient, is_follow_up_available)


def schedule_task(task_info, recipient, is_follow_up_available=False):
    process_task.delay(task_info, recipient, is_follow_up_available)
    if is_follow_up_available:
        data = {'recipient': {'id': recipient}, 'sender_action': 'typing_on'}
        fb_send_message(data)


def fb_start_typing(recipient):
    data = {'recipient': {'id': recipient}, 'sender_action': 'typing_on'}
    fb_send_message(data)


def fb_stop_typing(recipient):
    data = {'recipient': {'id': recipient}, 'sender_action': 'typing_off'}
    fb_send_message(data)


def fb_send_text_msg(uid, msg):
    data = {'recipient': {'id': uid}, 'message': {'text': msg}}
    fb_send_message(data)


def fb_send_message(message_data):
    url = 'https://graph.facebook.com/v2.6/me/messages'
    data = message_data
    headers = {'Content-Type': 'application/json'}
    payload = {'access_token': app.config['FB_ACCESS_TOKEN']}
    r = requests.post(url, data=json.dumps(data), headers=headers, params=payload)
    print payload
    print message_data
    # log the response
    if r.status_code != 200:
        app.logger.error('failed to send fb message %d', r.status_code)


def ai_send_message(text_msg, session_id):
    msg_request = get_ai_client().text_request()
    msg_request.lang = 'en'
    msg_request.session_id = session_id
    msg_request.query = text_msg
    response = msg_request.getresponse()
    return response.read()


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def connect_redis():
    """Connects to the specific redis."""
    rv = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'])
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def get_redis():
    if not hasattr(g, 'redis_db'):
        g.redis_db = connect_redis()
    return g.redis_db


def get_memcache():
    if not hasattr(g, 'mem_cache'):
        g.mem_cache = MemcachedCache([os.environ['MEMCACHED_HOST']])
    return g.mem_cache


def get_wit_client():
    if not hasattr(g, 'nlp_cient'):
        client = Wit(access_token=app.config['WIT_ACCESS_TOKEN'])
        g.nlp_client = client
    return g.nlp_client


def get_ai_client():
    if not hasattr(g, 'ai_cient'):
        client = apiai.ApiAI(app.config['APIAI_CLIENT_ACCESS_TOKEN'])
        g.ai_client = client
    return g.ai_client


def get_config():
    return app.config


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
