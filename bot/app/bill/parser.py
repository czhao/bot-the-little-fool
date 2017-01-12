import app
import memory
from app.core import profile
from app.utils import retrieve_text_from_message


def send_plain_text_message(recipient, text_message):
    data = {'recipient': {'id': recipient},
            'message': {'text': text_message}}
    app.fb_send_message(data)


def process_context_text_message(recipient, m):
    if 'postback' in m:
        # handle post back message
        postback = m['postback']
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
        if memory.is_session_active(recipient):
            # wait for description/price
            if quick_reply_payload is not None:
                parse_quick_reply(quick_reply_payload, m, recipient)
            else:
                (accepted, message) = memory.update_session_info_within_context(recipient, text_message)
                if accepted == -1:
                    return False
                send_plain_text_message(recipient, message)
                if accepted == 1:
                    # engage run a summary
                    app.schedule_task('bill_summary', recipient, True)
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
        memory.update_session_info(recipient, 'pending_for_currency', 'category', msg.lower())

        # check if we have a preference
        preference = profile.get_currency_preference(recipient)
        if preference is None:
            quick_reply_options = []
            customize_payload = 'DEVELOPER_DEFINED_PAYLOAD_FOR_CURRENCY'
            options = ['SGD', 'USD', 'RMB', 'JPY']
            for option in options:
                quick_reply_options.append({'content_type': 'text', 'title': option, 'payload': customize_payload})
            data = {'recipient': {'id': recipient},
                    'message': {'text': 'Currency in use?', 'quick_replies': quick_reply_options}
                    }
            app.fb_send_message(data)
        else:
            memory.update_session_info(recipient, 'pending_for_description', 'currency', preference)
            send_plain_text_message(recipient, 'Describe this purchase')

    if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_CURRENCY':
        msg = retrieve_text_from_message(message)
        memory.update_session_info(recipient, 'pending_for_description', 'currency', msg.upper())
        send_plain_text_message(recipient, 'Describe this purchase')


def parse_postback(payload, message, recipient):
    if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_SAY_HI':
        data = {'recipient': {'id': recipient},
                'message': {'text': 'Hi!'}}
        app.fb_send_message(data)
        return True

    if payload == 'DEVELOPER_DEFINED_PAYLOAD_FOR_NEW_PAYMENT':
        # start a new conversation
        quick_reply_options = []
        customize_payload = 'DEVELOPER_DEFINED_PAYLOAD_FOR_CATEGORY'

        options = ['Food', 'Grocery', 'Transportation', 'Social',
                   'Entertainment', 'Gift', 'Vacation', 'Education', 'Others']

        for option in options:
            quick_reply_options.append({'content_type': 'text', 'title': option, 'payload': customize_payload})

        # generate the new conversation
        memory.open_new_session(recipient)
        data = {'recipient': {'id': recipient},
                'message': {'text': 'Great, let start! What did you pay for?',
                            'quick_replies': quick_reply_options
                            }}
        app.fb_send_message(data)
        return True


def parse_task(task_info, recipient, is_interactive):
    if task_info == "bill_summary":
        all_sections = memory.get_today_spending()
        app.fb_stop_typing(recipient)
        for section in all_sections:
            print len(section)
            data = {'recipient': {'id': recipient},
                    'message': {'text': section}
                    }
            app.fb_send_message(data)


def parse_decision(data):
    result = data['result']
    contexts = result['contexts']
    ai_session_id = data['sessionId']

    uid = None
    price = None
    description = None
    category = None

    for context in contexts:
        name = context['name']
        if name == 'payment_daily_flow':
            params = context['parameters']
            price = params['cash_amount']
            description = params['description']
            category = params['payment-category']
        elif name == 'generic':
            params = context['parameters']
            uid = params['facebook_sender_id']

    if uid is not None:
        session_id = memory.get_session_key(uid)
        currency = profile.get_currency_preference(uid)
        if currency is None:
            currency = "SGD"
        memory.save_bill(session_id, category, description, price, currency)
        app.fb_send_text_msg(uid, 'Got it.')
