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
    def __init__(self, name=None, city=None, markets=None, address=None):
        self.name = name  #: Venue's name
        self.city = city  #: City name
        self.markets = markets  #: Market IDs
        self.address = address  #: Street address (first line)

    @staticmethod
    def from_json(json_venue):
        v = _Venue()
        v.name = json_venue['name']
        if 'city' in json_venue:
            v.city = json_venue['city']['name']
        if 'markets' in json_venue:
            v.markets = [m['id'] for m in json_venue['markets']]
        if 'address' in json_venue:
            v.address = json_venue['address']['line1']
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
            venues=', '.join(self.venues),
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
                venues.append(v['name'])
        e.venues = venues
        return e

        
class _Venues:
    """Abstraction for venue searches. Returns lists of venues."""
    def __init__(self, api_client):
        self.api_client = api_client
        self.method = "venues"
        
    def find(self, **search_parameters):
        response = self.api_client.search('venues', **search_parameters)

        # pull out the important stuff for readability
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
        return self.find(**search_params)


class _Events:
    """Abstraction to search API for events"""
    def __init__(self, api_client):
        self.api_client = api_client
        self.method = "events"
        
    def find(self, **kwargs):
        """Find events matching parameters
        
        :param search_parameters: 
        :return: 
        """
        response = self.api_client.search(self.method, **kwargs)

        if '_embedded' not in response:
            raise KeyError("Expected '_embedded' key in events response")
        if 'events' not in response['_embedded']:
            raise KeyError("Expected 'events' key in this response...")

        return [_Event.from_json(e) for e in response['_embedded']['events']]

    def by_location(self, latlong, radius='10'):
        """
        Searches events within a radius of a latitude/longitude coordinate.
        
        :param latlong: Latitude/longitude of the radius center
        :param radius: Radius to search around provided latitude/longitude
        :return: List of events
        """
        return self.find(**{'latlong': latlong, 'radius': radius})
    
    def by_venue_id(self, venue_id, size='20', sort='date,asc'):
        return self.find(**{
            'venueId': venue_id,
            'size': size,
            'sort': sort
        })


class Client:
    """Client for the Ticketmaster Discovery API
    
    Request URLs end up looking like:
    http://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}
    """
    _base_url = "http://app.ticketmaster.com/discovery"  #: Base URL
    _method_tmpl = "{url}/{method}.{response_type}"  #: URL method template

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
        return "{}/{}".format(self._base_url, self.version)

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
    
    def search(self, method, **kwargs):
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
        return requests.get(search_url, params=kwargs).json()