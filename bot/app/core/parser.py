import app
from app.core import profile


def parse_task(task_info, recipient, is_interactive):
    if task_info == "bill_summary":
        all_sections = memory.get_today_spending()
        if is_interactive:
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

    uid = None
    currency = None

    for context in contexts:
        name = context['name']
        params = context['parameters']
        if name == 'profile_update_currency':
            currency = params['currency-name']
        elif name == 'generic':
            uid = params['facebook_sender_id']

    if uid is not None:
        profile.save_currency_preference(uid, currency)
        app.fb_send_text_msg(uid, 'Got it.')

