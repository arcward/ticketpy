import json
from unittest import TestCase
from configparser import ConfigParser
import os
from ticketpy import ticketpy
from ticketpy.ticketpy import ApiException


class TestApiClient(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')
        self.api_client = ticketpy.ApiClient(api_key)

    def test_url(self):
        expected_url = "https://app.ticketmaster.com/discovery/v2"
        self.assertEqual(self.api_client.url, expected_url)

    def test_events_url(self):
        expected_url = "https://app.ticketmaster.com/discovery/v2/events.json"
        self.assertEqual(self.api_client.events_url, expected_url)

    def test_venues_url(self):
        expected_url = "https://app.ticketmaster.com/discovery/v2/venues.json"
        self.assertEqual(self.api_client.venues_url, expected_url)

    def test__search(self):
        # Should be 'events' or 'venues' and anything else: ValueError!
        self.assertRaises(ValueError, self.api_client._search, 'asdf')

        # Radius should be a whole number, so 1.5 should raise ApiException
        self.assertRaises(ApiException, self.api_client._search, 'events',
                          latlon='33.7838737, -84.366088', radius='1.5')

    def test___yes_no_only(self):
        yno = self.api_client._ApiClient__yes_no_only
        self.assertEqual(yno('yes'), 'yes')
        self.assertEqual(yno('YES'), 'yes')
        self.assertEqual(yno('Yes'), 'yes')
        self.assertEqual(yno(True), 'yes')

        self.assertEqual(yno('no'), 'no')
        self.assertEqual(yno('NO'), 'no')
        self.assertEqual(yno('No'), 'no')
        self.assertEqual(yno(False), 'no')

        self.assertEqual(yno('only'), 'only')
        self.assertEqual(yno('ONLY'), 'only')
        self.assertEqual(yno('Only'), 'only')


class Test_VenueSearch(TestCase):
    # TODO write tests for get() and find()
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')
        self.api_client = ticketpy.ApiClient(api_key)

    def test_get(self):
        pass

    def test_find(self):
        pass

    def test_by_name(self):
        # Make sure this returns only venues matching search terms...
        venue_list = self.api_client.venues.by_name('TABERNACLE', 'GA').limit()
        for venue in venue_list:
            self.assertIn('TABERNACLE', venue.name.upper())


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

    def test_search_events(self):
        event_list = self.tm.events.find(
            venue_id=self.venues['tabernacle'],
            size=1,
            include_tba=True
        ).all()
        for e in event_list:
            print(str(e))

    def test_events_get(self):
        elist = self.tm.events.find(
            classification_name='Hip-Hop',
            venue_id='KovZpZAJledA',
            size=7
        )
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
