import os
import flask
from flask import request
from flask import Flask
from flask import json
from auth import requires_auth
from parser import parse_postback
import requests
import logging
from raven.contrib.flask import Sentry


app = Flask(__name__)

app.config.update(DEBUG = True, SECRET_KEY = "123456")
app.config.from_envvar('BOT_APPLICATION_SETTINGS')

sentry = Sentry(app, dsn=app.config['SENTRY_DSN'],logging=True,level=logging.ERROR)


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
			return process_page_msg(json_data)
	else:
		return "invalid request"


def process_page_msg(raw_msg):
	app.logger.error("res: %s",raw_msg)
	for msg in raw_msg['entry']:
		if msg['messaging'] is not None:
				for m in msg['messaging']:
					sender = m['sender']['id']
					if 'message' in m:
						plain_message = m['message']
						if 'text' in plain_message:
							# this is a text message
							text_message = plain_message['text']
							# make http calls to link the message
							data = {'recipient':{'id': sender},'message':{'text':text_message}}
							fb_send_message(data)
						if 'quick_reply' in plain_message:
							pass

					if 'postback' in m:
						#handle post back message
						postback =  m['postback']
						parse_postback(postback['payload'], sender)

	return ''


def fb_send_message(message_data):
	url = 'https://graph.facebook.com/v2.6/me/messages'
	data = message_data
	headers = {'Content-Type': 'application/json'}
	payload = {'access_token': app.config['FB_ACCESS_TOKEN']}
	r = requests.post(url, data = json.dumps(data), headers = headers, params = payload)
	# log the response
	if r.status_code != 200:
		app.logger.error('failed to send fb message %d', r.status_code)

