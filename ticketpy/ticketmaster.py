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


class Ticketmaster:
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
        self.base_url = "http://app.ticketmaster.com/discovery/{version}/".format(version=version)
        self.method_url = "{base_url}{method}.{response_type}"
        
    def _build_uri(self, method):
        """Build a request URL.
        :param method: Search type (events, venues..)
        :return: Appropriate request URL
        """
        return self.method_url.format(base_url=self.base_url,
                                      method=method,
                                      response_type=self.response_type)
    
    def _search(self, method, **search_parameters):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param search_parameters: Search parameters, ex. venueId, eventId, latlong, radius..
        :return: List of results
        """
        search_url = self._build_uri(method)
        search_parameters.update({'apikey': self.api_key})
        return requests.get(search_url, params=search_parameters).json()
        
    def search_venues(self, **search_parameters):
        response = self._search('venues', **search_parameters)
        # pull out the important stuff for readability
        venue_list = []
        for venue in response['_embedded']['venues']:
            venue_dict = {
                'name': venue.get('name'),
                'city': venue.get('city').get('name'),
                'markets': [market.get('id') for market in venue.get('markets', [])],  # account for missing markets
                'address': venue.get('address').get('line1')
            }
            venue_list.append(venue_dict)
        return venue_list
    
    def venues_by_name(self, venue_name, state_code=None, size='10'):
        """Search for a venue by name.
        
        :param venue_name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
        :param size: Size of returned list
        :return: List of venues found matching search criteria
        """
        search_params = {'keyword': venue_name, 'size': size}
        if state_code is not None:
            search_params.update({'stateCode': state_code})
        return self.search_venues(**search_params)
        
    def search_events(self, **search_parameters):
        """Search events with provided search parameters. Generic class for ones like search_by_venue_id()"""
        response = self._search('events', **search_parameters)
        # Pick apart the serialized JSON response and just return the good stuff
        event_list = []
        for event in response.get('_embedded').get('events'):
            event_dict = {
                'name': event.get('name'),
                'start_date': event.get('dates').get('start').get('localDate'),
                'start_time': event.get('dates').get('start').get('localTime'),
                'status': event.get('dates').get('status').get('code'),
                'genres': [classification.get('genre').get('name')
                           for classification in event.get('classifications')]
            }
            
            # Add venue - some events have >1 venue (or possibly none??), join them into one string
            venues = event.get('_embedded').get('venues')
            if venues is not None:
                event_dict['venue'] = ','.join([venue.get('name') for venue in venues])
                
            # Not all events have a price range attached, or have multiple pricing tiers
            # TODO account for >1 pricing tier
            price_ranges = event.get('priceRanges')
            if price_ranges is not None:
                event_dict['price_range'] = "{}-{}".format(price_ranges[0].get('min', ''),
                                                           price_ranges[0].get('max', ''))
            event_list.append(event_dict)
        return event_list
    
    def events_by_location(self, latlong, radius='10'):
        """ Searches events within a radius of a latitude/longitude coordinate.
        :param latlong: Latitude/longitude of the radius center
        :param radius: Radius to search around provided latitude/longitude
        :return: List of events
        """
        search_params = {
            'latlong': latlong,
            'radius': radius
        }
        return self.search_events(**search_params)
    
    def events_by_venue_id(self, venue_id, size='20', sort='date,asc'):
        """Retrieve a list of events for the provided venue ID.
        
        :param venue_id: Venue ID
        :param size: Number of results (default: 20)
        :param sort: Sort method (default: date,asc)
        :return: List of events
        """
        search_params = {
            'size': size,
            'sort': sort,
            'venueId': venue_id
        }
        return self.search_events(**search_params)