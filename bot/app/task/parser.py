import app
import external_apis


def parse_decision(data, uid=None):
    result = data['result']
    parameters = result['parameters']
    bus_no = parameters['bus_no']
    station_no = parameters['station_no']

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


def parse_decision_bus(data, uid=None):
    result = data['result']
    contexts = result['contexts']

    station_no = None
    bus_no = None

    for context in contexts:
        name = context['name']
        params = context['parameters']
        if name == 'task_bus_timing':
            station_no = params['station_no']
            bus_no = params['bus_no']

    if uid is not None and bus_no is not None and station_no is not None:
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
            app.fb_send_text_msg(uid, 'No response from LTA, any alternatives?')
    return False
