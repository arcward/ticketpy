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
        self.api_key = api_key
        self.response_type = response_type  # JSON, XML...
        self.base_url = "http://app.ticketmaster.com/discovery/{version}/".format(version=version)
        
    def search_events(self, **search_parameters):
        """Search events with provided search parameters. Generic class for ones like search_by_venue_id()"""
        events_url = "{base_url}events.{response_type}".format(base_url=self.base_url,
                                                               response_type=self.response_type)
        search_parameters.update({'apikey': self.api_key})  # Inject API key into URL
        response = requests.get(events_url, params=search_parameters).json()  # TODO update to consider xml?
        # Severely hacky way of ignoring missing stuff from the API response. Create dicts with blank values
        # for things we expect to be there, but sometimes aren't for some events, so we can set them as
        # the default for {}.get(key, default)
        # TODO do something smarter
        missing_date = {'dates': {'start': {'localDate': '', 'localTime': ''},'status': {'code': ''}}}
        missing_genre = {'classifications': [{'genre': {'name': ''}}]}
        missing_venue = [{'name': ''}]
        missing = {'date': missing_date, 'genre': missing_genre, 'venue': missing_venue}
        return [
            {
                'name': event['name'],
                'start_date': event.get('dates', missing['date']['dates']).get('start').get('localDate'),
                'start_time': event.get('dates', missing['date']['dates']).get('start').get('localTime'),
                'genres': ([classification.get('genre')['name']
                            for classification in event.get('classifications',
                                                            missing['genre']['classifications'])]),
                'status': event.get('dates', missing['date']['dates'])['status']['code'],  # watch for 'cancelled'
                'price_range': ("{} - {}".format(event['priceRanges'][0]['min'],
                                                 event['priceRanges'][0]['max'])
                                if 'priceRanges' in event else 'N/A'),
                'venue': event['_embedded'].get('venues', missing['venue']).pop()['name'] # TODO cases w/ >1 venue?
            }
            for event in response['_embedded']['events']
            ]
    
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
