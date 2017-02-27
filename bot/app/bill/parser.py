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
                memory.save_bill(session_id, category, description, price, currency)
                app.fb_send_text_msg(uid, 'Got it.')
                app.schedule_task("bill_summary", uid, True)

        elif name == 'bill_monthly_summary':
            params = context['parameters']
            month = params['month-period']
            month_original = params['month-period.original']
            dates = month.split('/')
            start_date = dates[0]
            end_date = dates[1]
            answer = memory.get_monthly_spending(start_date + " 00:00:00", end_date + " 23:59:59")
            output = "You spent %.1f SGD in %s" % (answer, month_original)
            app.fb_send_text_msg(uid, output)

        elif name == 'new_income':
            params = context['parameters']
            source = params['income_source']
            description = params['description']
            price = params['cash_amount']

            if uid is not None:
                # save the income
                currency = profile.get_currency_preference(uid)
                session_id = memory.get_session_key(uid)
                memory.save_income(session_id, source, description, price, currency)
                app.fb_send_text_msg(uid, 'Got it')


