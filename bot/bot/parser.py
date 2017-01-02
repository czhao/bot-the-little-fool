import bot
import bill
import uuid
from utils import retrieve_text_from_message


def send_plain_text_message(recipient, text_message):
	data = {'recipient':{'id': recipient},
				'message':{'text':text_message}}		
	bot.fb_send_message(data)


def process_context_text_message(recipient, m):
	if 'postback' in m:
		#handle post back message
		postback =  m['postback']
		return parse_postback(postback['payload'], m, recipient)
	elif 'message' in m:
		plain_message = m['message']
		text_message = None
		quick_reply_payload = None
		print plain_message
		if 'text' in plain_message:
			text_message = plain_message['text']
		if 'quick_reply' in plain_message:
			quick_reply_payload = plain_message['quick_reply']['payload']

		# check if any pending bill session
		if bill.is_session_active(recipient):
			# wait for description/price
			if quick_reply_payload is not None:
				parse_quick_reply(quick_reply_payload, m, recipient)
			else:
				(accepted, message) = bill.update_session_info_within_context(recipient, text_message)
				send_plain_text_message(recipient, message)
			return True
		else:
			return False

	# cannot handle this message
	return False

def parse_quick_reply(payload, message, recipient):
	if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY':
		# locate the session
		# read the message
		msg = retrieve_text_from_message(message)
		bill.update_session_info(recipient, 'pending_for_currency', 'category', msg.lower())

		quick_reply_options = []
		customize_payload = 'DEVELOPER_DEFINED_PAYLOAD_FOR_CURRENCY'
		quick_reply_options.append({'content_type':'text', 'title':'SGD', 'payload': customize_payload})
		quick_reply_options.append({'content_type':'text', 'title':'USD', 'payload':customize_payload})
		quick_reply_options.append({'content_type':'text', 'title':'RMB', 'payload':customize_payload})
		quick_reply_options.append({'content_type':'text', 'title':'JPY', 'payload':customize_payload})
		data = {'recipient':{'id': recipient},
				'message':{'text':'Currency in use?', 'quick_replies':quick_reply_options}
				}		
		bot.fb_send_message(data)

	if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_CURRENCY':
		msg = retrieve_text_from_message(message)
		bill.update_session_info(recipient, 'pending_for_description', 'currency', msg.upper())
		send_plain_text_message(recipient, 'Describe this purchase')


def parse_postback(payload, message, recipient):

	if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_SAY_HI':
		data = {'recipient':{'id': recipient},
				'message':{'text':'Hi!'}}		
		bot.fb_send_message(data)
		return True

	if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_NEW_PAYMENT':
		# start a new conversation
		quick_reply_options = []
		customize_payload = 'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY'
		quick_reply_options.append({'content_type':'text', 'title':'Grocery', 'payload': customize_payload})
		quick_reply_options.append({'content_type':'text', 'title':'Transportation', 'payload':customize_payload})
		quick_reply_options.append({'content_type':'text', 'title':'Social', 'payload':customize_payload})

		# generate the new conversation
		bill.open_new_session(recipient)
		data = {'recipient':{'id': recipient},
				'message':{'text':'Great, let start! What did you pay for?', 
				'quick_replies':quick_reply_options
				}}		
		bot.fb_send_message(data)
		return True





		
