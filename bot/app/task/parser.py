from math import sin, cos, sqrt, atan2, radians

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


def update_bus_stop_info():
    external_apis.load_all_bus_stops()


R = 6371.0


def real_distance(x1, y1, x2, y2):
    lat1 = radians(x1)
    lon1 = radians(y1)
    lat2 = radians(x2)
    lon2 = radians(y2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def parse_decision_bus_stops_nearby(data, uid):
    result = data['result']
    contexts = result['contexts']

    min_distance = 0.300
    stop_names = []

    for context in contexts:
        name = context['name']
        params = context['parameters']
        if name == 'location_based_query':
            gps = params['location_gps']
            lat_x = gps['latitude']
            lng_x = gps['longitude']

            # use latitude/longitude to find the bus stop nearby
            db = app.get_db()

            c = db.cursor()
            c.execute('SELECT `code`,`road_name`,`description`,`lat`, `lng` FROM bus_stop')
            rows = c.fetchall()
            if len(rows) > 0:
                for row in rows:
                    lat = row[3]
                    lng = row[4]
                    distance = real_distance(lat_x, lng_x, lat, lng)
                    if min_distance > distance:
                        stop_names.append('%s %s,%s' % (row[0], row[1], row[2]))

    if len(stop_names) > 0:
        reply = "You are close to \n"
        for stop in stop_names:
            reply = reply + stop + '\n'
        app.fb_send_text_msg(uid, reply)
    else:
        app.fb_send_text_msg(uid, "No bus stop nearby!")
