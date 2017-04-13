from unittest import TestCase
from configparser import ConfigParser
import os
from ticketpy import ticketpy
from ticketpy.ticketpy import ApiException


class TestTicketpy(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')

        self.tm = ticketpy.ApiClient(api_key)
        self.venues = {
            'smithes': 'KovZpZAJledA',
            'tabernacle': 'KovZpaFEZe'
        }

    def test_get_event_id(self):
        e = self.tm.events.get('vvG1zZfbJQpVWp')
        print(e)

    def test_get_venue(self):
        v = self.tm.venues.get('KovZpaFEZe')
        print(v)

    def test_iterator(self):
        event_list = self.tm.events.find(venue_id=self.venues['tabernacle'],
                                         size='1').limit(5)
        for e in event_list:
            print(e.event_id)
        
    def test_search_events(self):
        event_list = self.tm.events.find(venue_id=self.venues['tabernacle'],
                                         size=5, include_tba=True).all()
        for e in event_list:
            print(str(e))

    def test_event_search_genre(self):
        pages = self.tm.events.find(
            classification_name='Hip-Hop',
            state_code='GA',
            start_date_time="2017-05-19T20:00:00Z",
            end_date_time="2017-05-21T20:00:00Z"
        )
        for page in pages:
            for event in page:
                print(event)


    def test_events_get(self):
        elist = self.tm.events.find(classification_name='Hip-Hop',
                                    venue_id='KovZpZAJledA', size=7).all()
        for e in elist:
            print(e)
        
    def test_search_events_by_location(self):
        event_list = self.tm.events.by_location(
            latitude='33.7838737',
            longitude='-84.366088',
            radius=1,
            unit='miles'
        ).all()
        for e in event_list:
            print(e)

    def test_venue_search(self):
        venue_list = self.tm.venues.find(keyword="The Tabernacle",
                                         state_code="GA",
                                         size=1).all()
        self.assertEqual(1, len(venue_list))
        tabernacle = venue_list[0]
        self.assertEqual("The Tabernacle", tabernacle.name)
