from unittest import TestCase
from configparser import ConfigParser
import os
import ticketmaster


class TestTicketmaster(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')
        self.tm = ticketmaster.ApiClient(api_key)
        
    def test_search_events(self):
        search_params = {
            'size': '10',
            'sort': 'date,asc',
            'venueId': 'KovZpaFEZe',
        }
        self.tm.search_events(**search_params)
    
    def test_events(self):
        elist = self.tm.events_by_venue_id('KovZpZAJledA', size=7)
        print(elist)
        
    def test_search_events_by_location(self):
        atl_centerish = "33.7838737,-84.366088"
        radius = '1'
        event_list = self.tm.events.by_location(
            atl_centerish,
            radius=radius
        )
        
    def test_search_venues(self):
        search_params = {
            'keyword': 'tabernacle',
            'stateCode': 'GA',
            'size': '10',
        }
        vlist = self.tm.venues.find(**search_params)
        print(vlist)
    
    def test_venues_by_name(self):
        params = {
            'venue_name': 'tabernacle',
            'state_code': 'GA'
        }
        vlist = self.tm.venues_by_name(**params)
        print(vlist)