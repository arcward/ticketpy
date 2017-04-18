from collections import namedtuple
from unittest import TestCase
from configparser import ConfigParser
import os
import ticketpy
from ticketpy.client import ApiException
from math import radians, cos, sin, asin, sqrt

# Test objects
TestObject = namedtuple('TestObject', 'id name')
# Venues
v_tabernacle = TestObject('KovZpaFEZe', 'The Tabernacle')
v_smiths = TestObject('KovZpZAJledA', "Smith's Olde Bar")
# Segment / genre / subgenre
seg_music = TestObject('KZFzniwnSyZfZ7v7nJ', 'Music')
g_jazz = TestObject('KnvZfZ7vAvE', 'Jazz')
sg_bebop = TestObject('KZazBEonSMnZfZ7vkdl', 'Bebop')
# Attraction
a_yankees = TestObject('K8vZ9171okV', 'New York Yankees')


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


def get_client():
    """Returns ApiClient with api key from config.ini"""
    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    api_key = config.get('ticketmaster', 'api_key')
    return ticketpy.ApiClient(api_key)


class TestApiClient(TestCase):
    def setUp(self):
        self.api_client = get_client()

    def test_parse_link(self):
        base_str = "https://app.ticketmaster.com/discovery/v2/events"
        param_str = ("sort=date,asc"
                     "&marketId=10"
                     "&keyword=LCD%20Soundsystem")
        full_url = '{}?{}'.format(base_str, param_str)
        url, params = self.api_client._parse_link(full_url)
        self.assertEqual(base_str, url)
        self.assertEqual('date,asc', params['sort'])
        self.assertEqual('10', params['marketId'])
        self.assertEqual('LCD Soundsystem', params['keyword'])
        self.assertEqual(self.api_client.api_key['apikey'], params['apikey'])

    def test_apikey(self):
        tmp_client = ticketpy.ApiClient('random_key')
        self.assertIn('apikey', tmp_client.api_key)
        self.assertEqual('random_key', tmp_client.api_key['apikey'])

    def test_url(self):
        expected_url = "https://app.ticketmaster.com/discovery/v2"
        self.assertEqual(self.api_client.url, expected_url)

    def test_method_url(self):
        murl = self.api_client._ApiClient__method_url
        expected_url = "https://app.ticketmaster.com/discovery/v2/events.json"
        events_url = murl('events')
        self.assertEqual(expected_url, events_url)

    def test_bad_key(self):
        bk = "sadfasdfsadf"
        bad_client = ticketpy.ApiClient(bk)
        self.assertRaises(ApiException, bad_client.venues.find, keyword=bk)
        self.assertRaises(ApiException, bad_client.segments.by_id, bk)

    def test__bad_request(self):
        # Radius should be a whole number, so 1.5 should raise ApiException
        radius = '1.5'
        lat = '33.7838737'
        long = '-84.366088'

        self.assertRaises(ApiException, self.api_client.events.by_location,
                          latitude=lat, longitude=long, radius=radius)

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

        self.assertEqual(yno('asdf'), 'asdf')
        self.assertEqual(yno('Asdf'), 'asdf')


class TestVenueQuery(TestCase):
    def setUp(self):
        self.tm = get_client()
        self.kw = "TABERNACLE"

    def test_find(self):
        venue_list = self.tm.venues.find(keyword=self.kw).limit(2)
        for v in venue_list:
            self.assertIn(self.kw, v.name.upper())

    def test_by_name(self):
        # Make sure this returns only venues matching search terms...
        state = "GA"
        venue_list = self.tm.venues.by_name(self.kw, state).limit(2)
        for venue in venue_list:
            self.assertIn(self.kw, venue.name.upper())

    def test_get_venue(self):
        v = self.tm.venues.by_id(v_tabernacle.id)
        print(v)
        self.assertEqual(v_tabernacle.id, v.id)
        self.assertEqual(v_tabernacle.name, v.name)


class TestClassificationQuery(TestCase):
    def setUp(self):
        self.tm = get_client()

    def test_classification_search(self):
        child = "DRAMA"
        parent = "Film"

        classif = self.tm.classifications.find(keyword=child).limit()
        segment_names = [cl.segment.name for cl in classif]
        self.assertIn(parent, segment_names)

        genre_names = []
        for cl in classif:
            genre_names += [g.name.upper() for g in cl.segment.genres]
        self.assertIn(child, genre_names)

        for cl in classif:
            print(cl)

    def test_classification_by_id(self):
        classification = self.tm.classifications.by_id(sg_bebop.id)
        subgenre_ids = []
        for genre in classification.segment.genres:
            subgenre_ids += [sg.id for sg in genre.subgenres]
        self.assertIn(sg_bebop.id, subgenre_ids)

    def test_segment_by_id(self):
        seg = self.tm.segments.by_id(seg_music.id)
        self.assertEqual(seg_music.id, seg.id)
        self.assertEqual(seg_music.name, seg.name)

        seg_x = self.tm.segments.by_id(seg_music.id)
        self.assertEqual(seg_music.id, seg_x.id)
        self.assertEqual(seg_music.name, seg_x.name)

    def test_genre_by_id(self):
        g = self.tm.genres.by_id(g_jazz.id)
        print(g)
        self.assertEqual(g_jazz.id, g.id)
        self.assertEqual(g_jazz.name, g.name)

        g_x = self.tm.genres.by_id(g_jazz.id)
        self.assertEqual(g_jazz.id, g_x.id)
        self.assertEqual(g_jazz.name, g_x.name)

    def test_subgenre_by_id(self):
        sg = self.tm.subgenres.by_id(sg_bebop.id)
        print(sg)
        self.assertEqual(sg_bebop.id, sg.id)
        self.assertEqual(sg_bebop.name, sg.name)

        sg_x = self.tm.subgenres.by_id(sg_bebop.id)
        self.assertEqual(sg_bebop.id, sg_x.id)
        self.assertEqual(sg_bebop.name, sg_x.name)

    def test_raises_404(self):
        self.assertRaises(ApiException, self.tm.segments.by_id, 'asdfasdf')


class TestAttractionQuery(TestCase):
    def setUp(self):
        self.tm = get_client()

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
        attr = self.tm.attractions.by_id(a_yankees.id)
        print(attr)
        self.assertEqual(a_yankees.id, attr.id)
        self.assertEqual(a_yankees.name, attr.name)


class TestEventQuery(TestCase):
    def setUp(self):
        self.tm = get_client()

    def test_get_event_id(self):
        event_id = 'vvG1zZfbJQpVWp'
        e = self.tm.events.by_id(event_id)
        print(str(e))
        self.assertEqual(event_id, e.id)

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
                                {'latitude': v.location.latitude,
                                 'longitude': v.location.longitude}) <= 3]
            all_nearby += nearby
        # Ensure we aren't passing the test on an empty list
        self.assertGreater(len(all_nearby), 0)
        # Every city in the (populated) list should be Atlanta
        for v in all_nearby:
            self.assertEqual(city, v.city.name)

    def test_search_events(self):
        event_list = self.tm.events.find(venue_id=v_tabernacle.id, size=2,
                                         include_tba=True).limit(4)
        for e in event_list:
            for v in e.venues:
                self.assertEqual(v_tabernacle.id, v.id)
                self.assertEqual(v_tabernacle.name, v.name)

    def test_events_get(self):
        genre_name = 'Hip-Hop'

        elist = self.tm.events.find(
            classification_name=genre_name,
            venue_id=v_smiths.id
        ).limit(2)

        for e in elist:
            for v in e.venues:
                self.assertEqual(v_smiths.id, v.id)
                self.assertEqual(v_smiths.name, v.name)
            genres = [ec.genre.name for ec in e.classifications]

            matches = False
            for g in genres:
                if genre_name in g:
                    matches = True
            self.assertTrue(matches)


class TestPagedResponse(TestCase):
    def setUp(self):
        self.tm = get_client()

    def test_one(self):
        # Generic search returns numerous pages, ensure only 1 is returned
        event_list = self.tm.events.find(state_code='GA', size=7).one()
        self.assertEqual(7, len(event_list))
        resp = self.tm.venues.find(keyword='Tabernacle', size=5).one()
        self.assertEqual(5, len(resp))

    def test_limit(self):
        # API page size default=20, limit(max_pages) default=5
        with_defaults = self.tm.events.find().limit()
        self.assertEqual(100, len(with_defaults))

        # Switch up defaults
        multi = self.tm.events.find(state_code='GA', size=8).limit(3)
        self.assertEqual(24, len(multi))

    def test_all(self):
        # Manually iterate through response, then iterate automatically
        # via all(), so both lists of venue IDs should be equal.
        # page_counter should eventually equal the total_pages
        # from the first page as well
        page_iter = self.tm.venues.find(keyword="TABERNACLE", size=5)
        iter_all = [venue.id for venue in page_iter.all()]
        iter_manual = []
        for idx, pg in enumerate(page_iter):
            print(pg)
            self.assertEqual(idx, pg.number)
            iter_manual += [venue.id for venue in pg]
        self.assertListEqual(iter_all, iter_manual)









