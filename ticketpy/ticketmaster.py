import requests
import os
from configparser import ConfigParser

# smithe's old bar: KovZpZAJledA
# tabernacle: KovZpaFEZe


class Ticketmaster:
    def __init__(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        self.api_key = config.get('ticketmaster', 'api_key')
        self.events_url = config.get('ticketmaster', 'events_url')
        
    def events(self, venue_id, size):
        """Returns a list of events for the specified venue ID"""
        request_url = self.events_url.format(sort='date,asc', size=size, api_key=self.api_key, venue_id=venue_id)
        resp = requests.get(request_url).json()
        event_list = [event['name'] for event in resp['_embedded']['events']]
        print(event_list)
        return event_list