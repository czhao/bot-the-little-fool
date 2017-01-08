import datetime
import json
from urlparse import urlparse

import app
import httplib2 as http
from dateutil import parser


def find_bus_arrival_time(bus_no, stop_no):
    headers = {'AccountKey': app.get_config()['LTA_TOKEN'], 'accept': 'application/json'}
    uri = 'http://datamall2.mytransport.sg/'
    path = '/ltaodataservice/BusArrival?BusStopID=%s&ServiceNo=%s&SST=True'
    target = urlparse((uri + path) % (stop_no, bus_no))
    method = 'GET'
    body = ''
    h = http.Http()
    # Obtain results
    response, content = h.request(target.geturl(), method, body, headers)
    # Parse JSON to print
    json_data = json.loads(content)
    services = json_data.get('Services', None)
    next_bus_arrival_min = None
    next_next_bus_arrival_min = None
    if services is not None:
        service = services[0]
        next_bus_info = service['NextBus']
        next_bus_arrival = next_bus_info['EstimatedArrival']
        if next_bus_arrival:
            d = parser.parse(next_bus_arrival)
            diff = d.replace(tzinfo=None) - datetime.datetime.now()
            next_bus_arrival_min = diff.seconds / 60
        next_next_bus_info = service['SubsequentBus']
        next_bus_arrival = next_next_bus_info['EstimatedArrival']
        if next_bus_arrival:
            d = parser.parse(next_bus_arrival)
            diff = d.replace(tzinfo=None) - datetime.datetime.now()
            next_next_bus_arrival_min = diff.seconds / 60
    return next_bus_arrival_min, next_next_bus_arrival_min


