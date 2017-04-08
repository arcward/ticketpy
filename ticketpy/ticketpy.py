import requests


class _Venue:
    """A venue
    
    JSON response from the Ticketmaster API looks similar to below 
    (at least as far as what's being used here):
    
    ```json
    {
        "name": "Venue name",
        "city": {"name": "Atlanta"},
        "markets": [{"id": "12345"}, {"id": "67890"}],
        "address": {"line1": "123 Fake St"}
    }
    ```
    
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
        v = _Venue()
        v.venue_id = json_venue['id']
        v.name = json_venue['name']
        v.url = json_venue['url']

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


class _Event:
    """An event
    
    JSON from API response, as far as what's being used here, looks like: 
    
    ```json
    {
        "name": "Event name",
        "dates": {
            "start": {
                "localDate": "2019-04-01", 
                "localTime": "2019-04-01T23:00:00Z"
            },
            "status": {"code": "onsale"}
        },
        "classifications": [
            {"genre": {"name": "Rock"}},
            {"genre": {"name": "Funk"}
        ],
        "priceRanges": [{"min": 10, "max": 25}],
        "_embedded": {
            "venues": [{"name": "The Tabernacle"}]
        }
    }
    
    ```
    
    """
    def __init__(self, name=None, start_date=None, start_time=None,
                 status=None, genres=None, price_ranges=None, venues=None):
        self.name = name  #: Event name/title
        self.start_date = start_date  #: Local start date
        self.start_time = start_time  #: Start time (YYYY-MM-DDTHH:MM:SSZ)
        self.status = status  #: Sale status (such as *Cancelled, Offsale...*)
        self.genres = genres  #: List of genre classifications
        self.price_ranges = price_ranges  #: Price ranges found for tickets
        self.venues = venues  #: List of venue names

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
            start_date=self.start_date,
            start_time=self.start_time,
            ranges=', '.join(ranges),
            status=self.status,
            genres=', '.join(self.genres)
        )

    @staticmethod
    def from_json(json_event):
        """Creates an ``_Event`` from API's JSON response
        
        :param json_event: Deserialized JSON dict
        :return: 
        """
        e = _Event()
        e.name = json_event.get('name')

        # Dates/times
        dates = json_event.get('dates')
        start_dates = dates.get('start', {})
        e.start_date = start_dates.get('localDate')
        e.start_time = start_dates.get('localTime')

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
                venues.append(_Venue.from_json(v))
        e.venues = venues
        return e

        
class _Venues:
    """Abstraction for venue searches. Returns lists of venues."""
    def __init__(self, api_client):
        self.api_client = api_client
        self.method = "venues"

    def find(self, keyword=None, venue_id=None, sort=None, state_code=None,
             country_code=None, source=None, include_test=None,
             page=None, size=None, locale=None):

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
        response = self.api_client._search('venues', **kwargs)

        # No matches
        if response['page']['totalPages'] == 0:
            return []

        if '_embedded' not in response:
            raise KeyError("Expected '_embedded' key in venues response")

        if 'venues' not in response['_embedded']:
            raise KeyError("Expected 'venues' key in this response...")

        return [_Venue.from_json(e) for e in
                response['_embedded']['venues']]
    
    def by_name(self, name, state_code=None, size='10'):
        """Search for a venue by name.

        :param name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
            (default: None)
        :param size: Size of returned list (default: 10)
        :return: List of venues found matching search criteria
        """
        search_params = {'keyword': name, 'size': size}
        if state_code is not None:
            search_params.update({'stateCode': state_code})
        return self.__get(**search_params)


class ApiException(Exception):
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
            msgs.append(tmpl.format(url=self.url,
                                    sp=', '.join('({}={})'.format(k, v) for
                                                (k, v) in self.params.items()),
                                    code=e['code'],
                                    status=e['status'],
                                    detail=e['detail'],
                                    link=e['_links']['about']['href']))
        return '\n'.join(msgs)


class _Events:
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
        self.api_client = api_client
        self.method = "events"

    def find(self, sort='date,asc', latlong=None, radius=None, unit=None,
             start_date_time=None, end_date_time=None,
             onsale_start_date_time=None, onsale_end_date_time=None,
             country_code=None, state_code=None, venue_id=None,
             attraction_id=None, segment_id=None, segment_name=None,
             classification_name=None, classification_id=None,
             market_id=None, promoter_id=None, dma_id=None,
             include_tba=None, include_tbd=None, client_visibility=None,
             keyword=None, id=None, source=None, include_test=None,
             page=None, size='20', locale=None, **kwargs):
        """
        
        :param sort: Sorting order of search result (default: date,asc)
        :param latlong: Latitude/longitude filter
        :param radius: Radius of area to search
        :param unit: Unit of radius ('miles' or 'km')
        :param start_date_time: 
        :param end_date_time: 
        :param onsale_start_date_time: 
        :param onsale_end_date_time: 
        :param country_code: 
        :param state_code: 
        :param venue_id: 
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
        :param id: 
        :param source: Filter entities by source name: ['ticketmaster', 
            'universe', 'frontgate', 'tmr']
        :param include_test: 'yes' to include test entities in the 
            response. False or 'no' to exclude. 'only' to return ONLY test 
            entities. (['yes', 'no', 'only'])
        :param page: Page number to get
        :param size: Size of page (default: 20)
        :param locale: 
        :return: 
        """

        try:
            int(size)
        except ValueError:
            raise ValueError("'size' parameter requires an "
                             "integer. Received: {}".format(size))

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
            'id': id,
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

        # No matches
        if response['page']['totalPages'] == 0:
            return []

        if '_embedded' not in response:
            raise KeyError("Expected '_embedded' key in events response")

        if 'events' not in response['_embedded']:
            raise KeyError("Expected 'events' key in this response...")

        return [_Event.from_json(e) for e in response['_embedded']['events']]

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
        return self.find(latlong=latlong, radius=radius, unit=unit)


class Client:
    """Client for the Ticketmaster Discovery API
    
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
        self.api_key = api_key  #: Ticketmaster API key
        self.response_type = response_type  #: Response type (json, xml...)
        self.version = version
        self.events = _Events(api_client=self)
        self.venues = _Venues(api_client=self)

    @property
    def url(self):
        """Root URL"""
        return "{}/discovery/{}".format(self.base_url, self.version)

    @property
    def events_url(self):
        return self._method_tmpl.format(url=self.url,
                                        method='events',
                                        response_type=self.response_type)

    @property
    def venues_url(self):
        return self._method_tmpl.format(url=self.url,
                                        method='venues',
                                        response_type=self.response_type)
    
    def _search(self, method, **kwargs):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param kwargs: Search parameters, ex. venueId, eventId, 
            latlong, radius..
        :return: List of results
        """
        # Get basic request URL
        if method == 'events':
            search_url = self.events_url
        elif method == 'venues':
            search_url = self.venues_url
        else:
            raise ValueError("Received: '{}' but was expecting "
                             "one of: {}".format(method, ['events', 'venues']))

        # Add ?api_key={api_key} and then search parameters
        kwargs.update({'apikey': self.api_key})
        response = requests.get(search_url, params=kwargs).json()
        if 'errors' in response:
            raise ApiException(search_url, kwargs, response)
