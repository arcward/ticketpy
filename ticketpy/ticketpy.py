"""Client/library for Ticketmaster's Discovery API"""
import requests
from datetime import datetime


class ApiClient:
    """ApiClient for the Ticketmaster Discovery API

    Request URLs end up looking like:
    http://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}
    """
    base_url = "https://app.ticketmaster.com"
    _method_tmpl = "{url}/{method}.{response_type}"

    def __init__(self, api_key, version='v2', response_type='json'):
        """Initialize the API client.

        :param api_key: Ticketmaster discovery API key
        :param version: API version (default: v2)
        :param response_type: Data format (JSON, XML...) (default: json)
        """
        self.__api_key = api_key  #: Ticketmaster API key
        self.response_type = response_type  #: Response type (json, xml...)
        self.version = version
        self.events = _EventSearch(api_client=self)
        self.venues = _VenueSearch(api_client=self)

    @property
    def url(self):
        """Root URL"""
        return "{}/discovery/{}".format(self.base_url, self.version)

    @property
    def events_url(self):
        """URL for */events/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='events',
                                        response_type=self.response_type)

    @property
    def venues_url(self):
        """URL for */venues/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='venues',
                                        response_type=self.response_type)

    @property
    def api_key(self):
        """API key"""
        return {'apikey': self.__api_key}

    @api_key.setter
    def api_key(self, api_key):
        self.__api_key = api_key

    def _search(self, method, **kwargs):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param kwargs: Search parameters, ex. venueId, eventId, 
            latlong, radius..
        :return: ``PageIterator``
        """
        # Get basic request URL
        if method == 'events':
            search_url = self.events_url
        elif method == 'venues':
            search_url = self.venues_url
        else:
            raise ValueError("Received: '{}' but was expecting "
                             "one of: {}".format(method, ['events', 'venues']))

        # Make updates to parameters. Add apikey, make sure params that
        # may be passed as integers are cast, and cast bools to 'yes' 'no'
        kwargs = {k: v for (k, v) in kwargs.items() if v is not None}
        updates = self.api_key

        for k, v in kwargs.items():
            if k in ['includeTBA', 'includeTBD', 'includeTest']:
                updates[k] = self.__yes_no_only(v)
            elif k in ['size', 'radius', 'marketId']:
                updates[k] = str(v)

        kwargs.update(updates)
        response = requests.get(search_url, params=kwargs).json()

        if 'errors' in response:
            raise ApiException(search_url, kwargs, response)

        return PageIterator(self, **response)

    @staticmethod
    def __yes_no_only(s):
        if s in ['yes', 'no', 'only']:
            pass
        elif s == True:
            s = 'yes'
        elif s == False:
            s = 'no'
        else:
            s = s.lower()
        return s


class ApiException(Exception):
    """Exception thrown for API-related error messages"""
    def __init__(self, url, params, response):
        self.url = url
        del params['apikey']
        self.params = params
        self.errors = response['errors']
        super().__init__()

    def __str__(self):
        tmpl = ("Reason: {detail}\n"
                "Request URL: {url}\n"
                "Query parameters: {sp}\n"
                "Code: {code} ({link})\n"
                "Status: {status}")
        msgs = []
        for e in self.errors:
            msgs.append(tmpl.format(
                url=self.url,
                sp=', '.join('({}={})'.format(k, v) for
                             (k, v) in self.params.items()),
                code=e['code'],
                status=e['status'],
                detail=e['detail'],
                link=e['_links']['about']['href']
            ))
        return '\n'.join(msgs)


class _VenueSearch:
    """Queries for venues"""

    def __init__(self, api_client):
        """Init VenueSearch
        
        :param api_client: Instance of `ticketpy.ApiClient`
        """
        self.api_client = api_client
        self.method = "venues"

    def get(self, venue_id):
        """Get details for a specific venue

        :param venue_id: Venue ID
        :return: Venue
        """
        get_url = "{}/venues/{}".format(self.api_client.url, venue_id)
        r = requests.get(get_url, params=self.api_client.api_key).json()
        return Venue.from_json(r)

    def find(self, keyword=None, venue_id=None, sort=None, state_code=None,
             country_code=None, source=None, include_test=None,
             page=None, size=None, locale=None):
        """Search for venues matching provided parameters
        
        :param keyword: Keyword to search on (such as part of the venue name)
        :param venue_id: Venue ID 
        :param sort: Sort method for response (API default: 'name,asc')
        :param state_code: Filter by state code (ex: 'GA' not 'Georgia')
        :param country_code: Filter by country code
        :param source: Filter entities by source (['ticketmaster', 'universe', 
            'frontgate', 'tmr'])
        :param include_test: ['yes', 'no', 'only'], whether to include 
            entities flagged as test in the response (default: 'no')
        :param page: Page number (default: 0)
        :param size: Page size of the response (default: 20)
        :param locale: Locale (default: 'en')
        :return: Venues found matching criteria 
        :rtype: `ticketpy.PageIterator`fff
        """
        kw_map = {
            'sort': sort,
            'stateCode': state_code,
            'countryCode': country_code,
            'keyword': keyword,
            'id': venue_id,
            'source': source,
            'includeTest': include_test,
            'page': page,
            'size': size,
            'locale': locale
        }
        kwargs = {k: v for (k, v) in kw_map.items() if v is not None}
        return self.__get(**kwargs)

    def __get(self, **kwargs):
        """Calls `ApiClient.get()` with final parameters"""
        response = self.api_client._search('venues', **kwargs)
        return response

    def by_name(self, venue_name, state_code=None, **kwargs):
        """Search for a venue by name.

        :param venue_name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
            (default: None)
        :return: List of venues found matching search criteria
        """
        return self.find(keyword=venue_name, state_code=state_code, **kwargs)


class _EventSearch:
    """Abstraction to search API for events"""
    attr_map = {
        'start_date_time': 'startDateTime',
        'end_date_time': 'endDateTime',
        'onsale_start_date_time': 'onsaleStartDateTime',
        'onsale_end_date_time': 'onsaleEndDateTime',
        'country_code': 'countryCode',
        'state_code': 'stateCode',
        'venue_id': 'venueId',
        'attraction_id': 'attractionId',
        'segment_id': 'segmentId',
        'segment_name': 'segmentName',
        'classification_name': 'classificationName',
        'classification_id': 'classificationId',
        'market_id': 'marketId',
        'promoter_id': 'promoterId',
        'dma_id': 'dmaId',
        'include_tba': 'includeTBA',
        'include_tbd': 'includeTBD',
        'client_visibility': 'clientVisibility',
        'include_test': 'includeTest'
    }

    def __init__(self, api_client):
        """Init EventSearch
        
        :param api_client: Instance of `ticketpy.ApiClient`
        """
        self.api_client = api_client
        self.method = "events"

    def get(self, event_id):
        """Get details for a specific event
        
        :param event_id: Event ID
        :return: Event
        """
        get_url = "{}/events/{}".format(self.api_client.url, event_id)
        r = requests.get(get_url, params=self.api_client.api_key).json()
        return Event.from_json(r)

    def find(self, sort='date,asc', latlong=None, radius=None, unit=None,
             start_date_time=None, end_date_time=None,
             onsale_start_date_time=None, onsale_end_date_time=None,
             country_code=None, state_code=None, venue_id=None,
             attraction_id=None, segment_id=None, segment_name=None,
             classification_name=None, classification_id=None,
             market_id=None, promoter_id=None, dma_id=None,
             include_tba=None, include_tbd=None, client_visibility=None,
             keyword=None, event_id=None, source=None, include_test=None,
             page=None, size=None, locale=None, **kwargs):
        """Search for events matching given criteria.

        :param sort: Sorting order of search result 
            (default: *'relevance, desc'*)
        :param latlong: Latitude/longitude filter
        :param radius: Radius of area to search
        :param unit: Unit of radius, 'miles' or 'km' (default: miles)
        :param start_date_time: Filter by start date/time.
            Timestamp format: *YYYY-MM-DDTHH:MM:SSZ*
        :param end_date_time: Filter by end date/time.
            Timestamp format: *YYYY-MM-DDTHH:MM:SSZ*
        :param onsale_start_date_time: 
        :param onsale_end_date_time: 
        :param country_code: 
        :param state_code: State code (ex: 'GA' not 'Georgia')
        :param venue_id: Find events for provided venue ID
        :param attraction_id: 
        :param segment_id: 
        :param segment_name: 
        :param classification_name: Filter events by a list of 
            classification name(s) (genre/subgenre/type/subtype/segment)
        :param classification_id: 
        :param market_id: 
        :param promoter_id: 
        :param dma_id: 
        :param include_tba: True to include events with a to-be-announced 
            date (['yes', 'no', 'only'])
        :param include_tbd: True to include an event with a date to be 
            defined (['yes', 'no', 'only'])
        :param client_visibility: 
        :param keyword: 
        :param event_id: Event ID to search 
        :param source: Filter entities by source name: ['ticketmaster', 
            'universe', 'frontgate', 'tmr']
        :param include_test: 'yes' to include test entities in the 
            response. False or 'no' to exclude. 'only' to return ONLY test 
            entities. (['yes', 'no', 'only'])
        :param page: Page number to get (default: 0)
        :param size: Size of page (default: 20)
        :param locale: Locale (default: 'en')
        :return: 
        """

        # Translate parameters to API-friendly parameters
        kw_map = {
            'sort': sort,
            'latlong': latlong,
            'radius': radius,
            'unit': unit,
            'startDateTime': start_date_time,
            'endDateTime': end_date_time,
            'onsaleStartDateTime': onsale_start_date_time,
            'onsaleEndDateTime': onsale_end_date_time,
            'countryCode': country_code,
            'stateCode': state_code,
            'venueId': venue_id,
            'attractionId': attraction_id,
            'segmentId': segment_id,
            'segmentName': segment_name,
            'classificationName': classification_name,
            'classificationId': classification_id,
            'marketId': market_id,
            'promoterId': promoter_id,
            'dmaId': dma_id,
            'includeTBA': include_tba,
            'includeTBD': include_tbd,
            'clientVisibility': client_visibility,
            'keyword': keyword,
            'id': event_id,
            'source': source,
            'includeTest': include_test,
            'page': page,
            'size': size,
            'locale': locale
        }

        # Update search parameters with kwargs
        for k, v in kwargs.items():
            # If arg is API-friendly (ex: stateCode='GA')
            if k in kw_map:
                kw_map[k] = v
            # If arg matches a param name (ex: state_code='GA')
            if k in self.attr_map:
                kw_map[self.attr_map[k]] = v

        # Only use ones that have been set
        search_params = {k: v for (k, v) in kw_map.items() if v is not None}
        return self.__get(**search_params)

    def __get(self, **kwargs):
        """Find events matching parameters

        Common search parameters:
        classificationName
        venueId
        latlong


        :param kwargs: Search parameters
        :return: 
        """
        response = self.api_client._search(self.method, **kwargs)
        return response

    def by_location(self, latitude, longitude, radius='10', unit='miles',
                    **kwargs):
        """
        Searches events within a radius of a latitude/longitude coordinate.

        :param latitude: Latitude of radius center
        :param longitude: Longitude of radius center
        :param radius: Radius to search outside given latitude/longitude
        :param unit: Unit of radius ('miles' or 'km')
        :return: List of events within that area
        """
        latitude = str(latitude)
        longitude = str(longitude)
        radius = str(radius)
        latlong = "{lat},{long}".format(lat=latitude, long=longitude)
        return self.find(latlong=latlong, radius=radius, unit=unit, **kwargs)


class Venue:
    """A Ticketmaster venue
    
    The JSON returned from the Discovery API looks something like this 
    (*edited for brevity*):
    
    .. code-block:: json
    
        {
            "id": "KovZpaFEZe",
            "name": "The Tabernacle",
            "url": "http://www.ticketmaster.com/venue/115031",
            "timezone": "America/New_York",
            "address": {
                "line1": "152 Luckie Street"
            },
            "city": {
                "name": "Atlanta"
            },
            "postalCode": "30303",
            "state": {
                "stateCode": "GA",
                "name": "Georgia"
            },
            "country": {
                "name": "United States Of America",
                "countryCode": "US"
            },
            "location": {
                "latitude": "33.758688",
                "longitude": "-84.391449"
            },
            "social": {
                "twitter": {
                    "handle": "@TabernacleATL"
                }
            },
            "markets": [
                {
                    "id": "10"
                }
            ]
        }

    
    """
    def __init__(self, name=None, address=None, city=None, state_code=None,
                 postal_code=None, latitude=None, longitude=None,
                 markets=None, url=None, box_office_info=None,
                 dmas=None, general_info=None, venue_id=None,
                 social=None, timezone=None, images=None,
                 parking_detail=None, accessible_seating_detail=None):
        self.name = name  #: Venue's name
        self.venue_id = venue_id  #: Venue ID (use to look up events)
        self.address = address  #: Street address (first line)
        self.postal_code = postal_code  #: Zip/postal code
        self.city = city  #: City name
        self.state_code = state_code  #: State code (ex: 'GA' not 'Georgia')
        self.latitude = latitude  #: Latitude
        self.longitude = longitude  #: Longitude
        self.timezone = timezone  #: Timezone venue's located in
        self.url = url  #: Ticketmaster internal venue URL
        self.box_office_info = box_office_info
        self.dmas = dmas  # TODO what is this
        self.markets = markets  #: List of market IDs
        self.general_info = general_info  #: General info on the venue
        self.social = social  #: Social media links (Twitter, etc)
        self.images = images  #: Ticketmaster venue image links
        self.parking_detail = parking_detail  #: Parking details
        self.accessible_seating_detail = accessible_seating_detail

    @property
    def location(self):
        """All location-based data (full address, lat/lon, timezone"""
        return {
            'address': self.address,
            'postal_code': self.postal_code,
            'city': self.city,
            'state_code': self.state_code,
            'timezone': self.timezone,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

    def __str__(self):
        return "'{}' at {} in {} {}".format(self.name, self.address,
                                            self.city, self.state_code)

    @staticmethod
    def from_json(json_venue):
        """Create a `Venue` object from the API response's JSON data
        
        :param json_venue: Deserialized JSON from API response
        :return: `ticketpy.Venue`
        """
        v = Venue()
        v.venue_id = json_venue['id']
        v.name = json_venue['name']
        v.url = json_venue.get('url')

        if 'markets' in json_venue:
            v.markets = [m['id'] for m in json_venue['markets']]

        # Location data
        v.postal_code = json_venue.get('postalCode')
        if 'city' in json_venue:
            v.city = json_venue['city']['name']
        if 'address' in json_venue:
            v.address = json_venue['address']['line1']
        if 'location' in json_venue:
            v.latitude = json_venue['location']['latitude']
            v.longitude = json_venue['location']['longitude']
        if 'state' in json_venue:
            v.state_code = json_venue['state']['stateCode']

        # Other general data
        v.general_info = json_venue.get('generalInfo')
        v.box_office_info = json_venue.get('boxOfficeInfo')
        v.dmas = json_venue.get('dmas')
        v.social = json_venue.get('social')
        v.timezone = json_venue.get('timezone')
        v.images = json_venue.get('images')
        v.parking_detail = json_venue.get('parkingDetail')
        v.accessible_seating_detail = json_venue.get('accessibleSeatingDetail')

        return v


class Event:
    """Ticketmaster event.
    
    The JSON returned from the Discovery API (at least, as far as 
    what's being used here) looks like:
    
    .. code-block:: json
    
        {
            "name": "Event name",
            "dates": {
                "start": {
                    "localDate": "2019-04-01",
                    "localTime": "2019-04-01T23:00:00Z"
                },
                "status": {
                    "code": "onsale"
                }
            },
            "classifications": [
                {
                    "genre": {
                        "name": "Rock"
                    }
                },
                {
                    "genre": {
                        "name": "Funk"
                    }
                }
            ],
            "priceRanges": [
                {
                    "min": 10,
                    "max": 25
                }
            ],
            "_embedded": {
                "venues": [
                    {
                        "name": "The Tabernacle"
                    }
                ]
            }
        }
    """
    def __init__(self, event_id=None, name=None, start_date=None,
                 start_time=None, status=None, genres=None, price_ranges=None,
                 venues=None, utc_datetime=None):
        self.event_id = event_id
        self.name = name
        #: **Local** start date (*YYYY-MM-DD*)
        self.local_start_date = start_date
        #: **Local** start time (*HH:MM:SS*)
        self.local_start_time = start_time
        #: Sale status (such as *Cancelled, Offsale...*)
        self.status = status
        #: List of genre classifications
        self.genres = genres
        #: Price ranges found for tickets
        self.price_ranges = price_ranges
        #: List of ``ticketpy.Venue`` objects associated with this event
        self.venues = venues

        self.__utc_datetime = None
        if utc_datetime is not None:
            self.utc_datetime = utc_datetime

    @property
    def utc_datetime(self):
        """Start date/time in UTC (Format: *YYYY-MM-DDTHH:MM:SSZ*)
        
        :return: Start date/time in UTC
        :rtype: ``datetime``
        """
        return self.__utc_datetime

    @utc_datetime.setter
    def utc_datetime(self, utc_datetime):
        if not utc_datetime:
            self.__utc_datetime = None
        else:
            ts_format = "%Y-%m-%dT%H:%M:%SZ"
            self.__utc_datetime = datetime.strptime(utc_datetime, ts_format)

    def __str__(self):
        tmpl = ("Event:        {event_name}\n"
                "Venue(s):     {venues}\n"
                "Start date:   {start_date}\n"
                "Start time:   {start_time}\n"
                "Price ranges: {ranges}\n"
                "Status:       {status}\n"
                "Genres:       {genres}\n")

        ranges = ['-'.join([str(pr['min']), str(pr['max'])])
                  for pr in self.price_ranges]
        return tmpl.format(
            event_name=self.name,
            venues=' / '.join([str(v) for v in self.venues]),
            start_date=self.local_start_date,
            start_time=self.local_start_time,
            ranges=', '.join(ranges),
            status=self.status,
            genres=', '.join(self.genres)
        )

    @staticmethod
    def from_json(json_event):
        """Creates an ``Event`` from API's JSON response
        
        :param json_event: Deserialized JSON object from API response
        :return: `ticketpy.Event`
        """
        e = Event()
        e.event_id = json_event['id']
        e.name = json_event.get('name')

        # Dates/times
        dates = json_event.get('dates')
        start_dates = dates.get('start', {})
        e.local_start_date = start_dates.get('localDate')
        e.local_start_time = start_dates.get('localTime')
        e.utc_datetime = start_dates.get('dateTime')

        # Event status (ex: 'onsale')
        status = dates.get('status', {})
        e.status = status.get('code')

        # Pull genre names from classifications
        genres = []
        if 'classifications' in json_event:
            for cl in json_event['classifications']:
                if 'genre' in cl:
                    genres.append(cl['genre']['name'])
        e.genres = genres

        # min/max price ranges
        price_ranges = []
        if 'priceRanges' in json_event:
            for pr in json_event['priceRanges']:
                price_ranges.append({
                    'min': pr['min'],
                    'max': pr['max']
                })
        e.price_ranges = price_ranges

        # venue list (occasionally >1 venue)
        venues = []
        if 'venues' in json_event.get('_embedded', {}):
            for v in json_event['_embedded']['venues']:
                venues.append(Venue.from_json(v))
        e.venues = venues
        return e


class PageIterator:
    """Iterates through API response pages"""
    def __init__(self, api_client, **kwargs):
        self.api_client = api_client  #: Parent API client
        self.page = None  #: Current page
        self.page = self.__page(**kwargs)

        self.start_page = self.page.number  #: Initial page number
        self.current_page = self.start_page  #: Current page number
        self.end_page = self.page.total_pages  #: Final page number

    def __iter__(self):
        return self

    def limit(self, max_pages=10):
        """Limit the number of page requests. Default: 5
        
        With a default page size of 20, ``limit(max_pages=5`` would 
        return a maximum of 200 items (fewer, if there are fewer results).
        
        Use this to contain the number of API calls being made, as the 
        API restricts users to a maximum of 5,000 per day. Very 
        broad searches can return a large number of pages.
        
        To contrast, ``all()`` will automatically request every 
        page available.
        
        :param max_pages: Maximum number of pages to request. 
            Default: *10*. Set to *None* (or use ``all()``) to return 
            all pages.
        :return: Flat list of results from pages
        """
        if max_pages is None:
            return self.all()

        all_items = []
        for i in range(0, max_pages):
            all_items += self.next()
        return all_items

    def all(self):
        """Returns a flat list of all results. Queries all possible pages.
        
        Use ``limit()`` to restrict the number of calls being made.
        
        :return: Flat list of results
        """
        return [i for item_list in self for i in item_list]

    @staticmethod
    def __page(**kwargs):
        """Instantiate and return a Page(list)"""
        page = kwargs['page']

        links = kwargs['_links']

        if 'next' not in links:
            links_next = None
        else:
            links_next = links['next']['href']

        return Page(
            page['number'],
            page['size'],
            page['totalElements'],
            page['totalPages'],
            links['self']['href'],
            links_next,
            kwargs.get('_embedded', {})
        )

    def next(self):
        # Return initial Page result if we haven't yet
        if self.page.number == self.current_page:
            self.current_page += 1
            return [i for i in self.page]

        # StopIteration if we know we've run out of pages.
        # Check for current>end as empty results still return
        # a page and increment the counter.
        if self.current_page >= self.end_page:
            raise StopIteration

        # Otherwise, +1 our count and pull the next page
        self.current_page += 1
        r = requests.get(self.page.link_next,
                         params=self.api_client.api_key).json()

        self.page = self.__page(**r)

        # If 'next' link goes missing, there were fewer pages than
        # expected for some reason, so bump current_page to end_page to
        # throw StopIteration next time next() is called
        if self.page.link_next is None:
            self.current_page = self.end_page

        return [i for i in self.page]

    __next__ = next


class Page(list):
    """API response page"""
    def __init__(self, number, size, total_elements, total_pages,
                 link_self, link_next, embedded):
        super().__init__([])
        self.number = number  #: Page number
        self.size = size  #: Page size
        self.total_elements = total_elements  #: Total elements (all pages)
        self.total_pages = total_pages  #: Total pages

        self._link_self = link_self  #: Link to this page
        self._link_next = link_next  #: Link to the next page

        # Parse embedded objects and add them to ourself
        items = []
        if 'events' in embedded:
            items = [Event.from_json(e) for e in embedded['events']]
        elif 'venues' in embedded:
            items = [Venue.from_json(v) for v in embedded['venues']]

        for i in items:
            self.append(i)

    @property
    def link_next(self):
        """Link to the next page"""
        return "{}{}".format(ApiClient.base_url, self._link_next)

    @property
    def link_self(self):
        """Link to this page"""
        return "{}{}".format(ApiClient.base_url, self._link_self)
