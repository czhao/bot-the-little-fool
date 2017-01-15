import app
import external_apis


def parse_decision(data):
    result = data['result']
    contexts = result['contexts']

    uid = None

    parameters = result['parameters']
    bus_no = parameters['bus_no']
    station_no = parameters['station_no']

    for context in contexts:
        name = context['name']
        params = context['parameters']
        if name == 'generic':
            uid = params['facebook_sender_id']

    if uid is not None:
        next_bus, sub_next_bus = external_apis.find_bus_arrival_time(bus_no, stop_no=station_no)
        if next_bus is not None:
            message = "The next bus comes in %d minutes" % next_bus
            if sub_next_bus is not None:
                message += " and the subsequent bus will arrive in %d minutes." % sub_next_bus
            else:
                message += "."
            app.fb_send_text_msg(uid, message)
            return True
        else:
            app.fb_send_text_msg(uid, 'No response from LTA')
    return False

