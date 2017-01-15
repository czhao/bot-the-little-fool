import app
import memory
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


def parse_decision(data, uid=None):
    result = data['result']
    contexts = result['contexts']

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

    if uid is not None:
        session_id = memory.get_session_key(uid)
        currency = profile.get_currency_preference(uid)
        if currency is None:
            currency = "SGD"
        memory.save_bill(session_id, category, description, price, currency)
        app.fb_send_text_msg(uid, 'Got it.')
        app.schedule_task("bill_summary", uid, True)
