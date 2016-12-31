import bot
	
def parse_postback(payload_msg, recipient):
	if payload_msg == 'DEVELOPER_DEFINED_PAYLOAD_FOR_NEW_PAYMENT':
		# start a new conversation
		quick_reply_options = []
		quick_reply_options.append({'content_type':'text', 'title':'Grocery', 'payload':'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY_GROCERY'})
		quick_reply_options.append({'content_type':'text', 'title':'Transportation', 'payload':'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY_TRANSPORTATION'})
		quick_reply_options.append({'content_type':'text', 'title':'Social', 'payload':'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY_SOCIAL'})
		data = {'recipient':{'id': recipient},'message':{'text':'Great, let start! What did you pay for?', 'quick_replies':quick_reply_options}}		
		bot.fb_send_message(data)