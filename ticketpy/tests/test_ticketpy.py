from unittest import TestCase
from configparser import ConfigParser
import os
import ticketpy
from ticketpy.client import ApiException
from math import radians, cos, sin, asin, sqrt


def haversine(latlon1, latlon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    Sourced from Stack Overflow:
    https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians
    lat1 = float(latlon1['latitude'])
    lon1 = float(latlon1['longitude'])

    lat2 = float(latlon2['latitude'])
    lon2 = float(latlon2['longitude'])

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 3956  # Radius of earth in kilometers. Use 6371 for kilometers
    return c * r


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


class TestVenueQuery(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')
        self.api_client = ticketpy.ApiClient(api_key)

    def test_find(self):
        venue_list = self.api_client.venues.find(keyword="TABERNACLE").limit(2)
        for v in venue_list:
            self.assertIn("TABERNACLE", v.name.upper())

    def test_by_name(self):
        # Make sure this returns only venues matching search terms...
        venue_name = "TABERNACLE"
        state = "GA"
        venue_list = self.api_client.venues.by_name(venue_name, state).limit(2)
        for venue in venue_list:
            self.assertIn(venue_name, venue.name.upper())


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

    def test_attraction_search(self):
        attr_name = "YANKEES"
        attractions = self.tm.attractions.find(keyword=attr_name).limit(1)
        attraction_names = [a.name for a in attractions]

        matched = False
        for a in attraction_names:
            if attr_name in a.upper():
                matched = True
        self.assertTrue(matched)

    def test_attraction_by_id(self):
        attraction_id = 'K8vZ9171okV'
        attraction_name = 'New York Yankees'

        attr = self.tm.attractions.by_id(attraction_id)
        print(attr)
        self.assertEqual(attraction_id, attr.id)
        self.assertEqual(attraction_name, attr.name)

    def test_classification_search(self):
        classif = self.tm.classifications.find(keyword="DRAMA").limit()
        segment_names = [cl.segment.name for cl in classif]
        self.assertIn('Film', segment_names)
        genre_names = []
        for cl in classif:
            genre_names += [g.name.upper() for g in cl.segment.genres]
        self.assertIn("DRAMA", genre_names)

        for cl in classif:
            print(cl)

    def test_classification_segment(self):
        seg_id = 'KZFzniwnSyZfZ7v7nJ'
        seg_name = 'Music'
        seg = self.tm.classifications.by_id(seg_id)
        print(seg)
        self.assertEqual(seg_id, seg.id)
        self.assertEqual(seg_name, seg.name)

        genre_id = 'KnvZfZ7vAvE'
        genre_name = 'Jazz'
        g = self.tm.classifications.by_id(genre_id)
        print(g)
        self.assertEqual(genre_id, g.id)
        self.assertEqual(genre_name, g.name)

        subgenre_id = 'KZazBEonSMnZfZ7vkdl'
        subgenre_name = 'Bebop'
        sg = self.tm.classifications.by_id(subgenre_id)
        print(sg)
        self.assertEqual(subgenre_id, sg.id)
        self.assertEqual(subgenre_name, sg.name)

    def test_get_event_id(self):
        event_id = 'vvG1zZfbJQpVWp'
        e = self.tm.events.by_id(event_id)
        print(e)
        self.assertEqual(event_id, e.id)

    def test_get_venue(self):
        venue_id = 'KovZpaFEZe'
        venue_name = 'The Tabernacle'
        v = self.tm.venues.by_id(venue_id)
        print(v)
        self.assertEqual(venue_id, v.id)
        self.assertEqual(venue_name, v.name)

    def test_search_events(self):
        venue_id = 'KovZpaFEZe'
        venue_name = 'The Tabernacle'
        event_list = self.tm.events.find(venue_id=venue_id).limit(2)
        for e in event_list:
            for v in e.venues:
                self.assertEqual(venue_id, v.id)
                self.assertEqual(venue_name, v.name)

    def test_events_get(self):
        genre_name = 'Hip-Hop'
        venue_id = 'KovZpZAJledA'
        venue_name = "Smith's Olde Bar"

        elist = self.tm.events.find(
            classification_name=genre_name,
            venue_id=venue_id
        ).limit(2)

        for e in elist:
            for v in e.venues:
                self.assertEqual(venue_id, v.id)
                self.assertEqual(venue_name, v.name)
            genres = [ec.genre.name for ec in e.classifications]

            matches = False
            for g in genres:
                if genre_name in g:
                    matches = True
            self.assertTrue(matches)

    def test_search_events_by_location(self):
        # Search for events within 1 mile of lat/lon
        # Coordinates here are vaguely within Virginia Highlands
        # It might be sort of overkill, but the distance between the
        # original latitude/longitude is measured against what's
        # returned for the venue and we only evaluate events/venues
        # within 3 miles of the original coordinates. This is because
        # the API will return crazy far results if you let it
        # (ex: sorting by date,asc returns events in Austin...)
        city = 'Atlanta'
        latlon1 = {'latitude': '33.7838737', 'longitude': '-84.366088'}

        event_list = self.tm.events.by_location(
            latitude=latlon1['latitude'],
            longitude=latlon1['longitude'],
            radius=3,
            unit='miles'
        ).limit(3)

        all_nearby = []
        for e in event_list:
            nearby = [v for v in e.venues if
                      haversine(latlon1,
                                {'latitude': v.location['latitude'],
                                 'longitude': v.location['longitude']}) <= 3]
            all_nearby += nearby
        # Ensure we aren't passing the test on an empty list
        self.assertGreater(len(all_nearby), 0)
        # Every city in the (populated) list should be Atlanta
        for v in all_nearby:
            self.assertEqual(city, v.city)
            self.assertEqual(city, v.location['city'])




