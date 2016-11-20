"""
MIT License

Copyright (c) 2016 - Edward Wells

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import requests


def _event_params_from_json_obj(json_object):
    """
    'Cleans up' the JSON object received from the API, returns a dictionary
    to pass to Event class to initialize
    :param json_object: object deserialized from JSON, from API
    :return:
    """
    j_obj = json_object
    print(j_obj)
    # localTime in format: YYYY-MM-DDTHH:MM:SSZ
    # status usually something like.. Cancelled, Offsale..
    return {
        'name': j_obj.get('name'),
        'start_date': j_obj.get('dates', {}).get('start', {})
            .get('localDate'),
        'start_time': j_obj.get('dates', {}).get('start', {})
            .get('localTime'),
        'status': j_obj.get('dates', {}).get('status', {})
            .get('code'),
        'genres': [
            classification.get('genre', {}).get('name')
            for classification in j_obj.get('classifications', [{}])
            ],
        'price_ranges': [
            {'min': p_range.get('min'), 'max': p_range.get('max')}
            for p_range in j_obj.get('priceRanges', [{}])
            ],
        'venues': [
            venue.get('name')
            for venue in j_obj.get('_embedded', {}).get('venues', [{}])
            ]
    }


def _venue_params_from_json_obj(json_object):
    j_obj = json_object
    return {
        'name': j_obj.get('name'),
        'city': j_obj.get('city', {}).get('name'),
        'markets': [market.get('id') for market in j_obj.get('markets', {})],
        'address': j_obj.get('address', {}).get('line1')
    }


class Venue:
    def __init__(self, name=None, city=None, markets=None, address=None):
        self.name = name
        self.city = city
        self.markets = markets
        self.address = address
        

class Event:
    def __init__(self, name=None, start_date=None, start_time=None,
                 status=None, genres=None, price_ranges=None, venues=None):
        self.name = name
        self.start_date = start_date
        self.start_time = start_time
        self.status = status
        self.price_ranges = price_ranges
        self.venues = venues
        self.genres = genres
        
        
class Venues:
    def __init__(self, api_client):
        self.api_client = api_client
        self.method = "venues"
        
    def find(self, **search_parameters):
        response = self.api_client.search('venues', **search_parameters)
        # pull out the important stuff for readability
        venue_list = response.get('_embedded', {}).get('venues')
        return [
            Venue(**_venue_params_from_json_obj(venue)) for venue in venue_list
        ]
    
    def by_name(self, name, state_code=None, size='10'):
        """Search for a venue by name.

        :param name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
        :param size: Size of returned list
        :return: List of venues found matching search criteria
        """
        search_params = {'keyword': name, 'size': size}
        if state_code is not None:
            search_params.update({'stateCode': state_code})
        self.api_client.search(self.method, **search_params)


class Events:
    """Abstraction to search API for events"""
    def __init__(self, api_client):
        self.api_client = api_client
        self.method = "events"
        
    def find(self, **search_parameters):
        event_list = self.api_client.search(**search_parameters)\
            .get('_embedded', {}).get('events')
        return [
            Event(**_event_params_from_json_obj(event))
            for event in event_list
            ]
    
    def by_location(self, latlong, radius='10'):
        """
        Searches events within a radius of a latitude/longitude coordinate.
        
        :param latlong: Latitude/longitude of the radius center
        :param radius: Radius to search around provided latitude/longitude
        :return: List of events
        """
        return self.find(**{'latlong': latlong, 'radius': radius})
    
    def by_venue_id(self, venue_id, size='20', sort='date,asc'):
        return self.find(**{'venueId': venue_id,
                            'size': size,
                            'sort': sort})


class ApiClient:
    """Client for the Ticketmaster discovery API"""
    def __init__(self, api_key, version='v2', response_type='json'):
        """Initialize the API client.
        
        :param api_key: Ticketmaster discovery API key
        :param version: API version (default: v2)
        :param response_type: Data format (JSON, XML...)
        """
        # URL ends up looking something lke:
        # http://app.ticketmaster.com/discovery/v2/events.json?apikey=[api key]
        self.api_key = api_key
        self.response_type = response_type  # JSON, XML...
        self.base_url = "http://app.ticketmaster.com/discovery/{version}/" \
            .format(version=version)
        self.method_url = "{base_url}{method}.{response_type}"
        
        self.events = Events(api_client=self)
        self.venues = Venues(api_client=self)
    
    def _build_uri(self, method):
        """Build a request URL.
        :param method: Search type (events, venues..)
        :return: Appropriate request URL
        """
        return self.method_url.format(
            base_url=self.base_url,
            method=method,
            response_type=self.response_type
        )
    
    def search(self, method, **search_parameters):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param search_parameters: Search parameters, ex. venueId, eventId, latlong, radius..
        :return: List of results
        """
        search_url = self._build_uri(method)
        search_parameters.update({'apikey': self.api_key})
        return requests.get(search_url, params=search_parameters).json()