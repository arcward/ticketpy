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
    
    def events(self, venue_id, size='20', sort='date,asc'):
        """Retrieve a list of events for the provided venue ID.
        
        :param venue_id: Venue ID
        :param size: Number of results (default: 20)
        :param sort: Sort method (default: date,asc)
        :return: List of events
        """
        events_url = "events.{response_type}?size={size}&sort={sort}&venueId={venue_id}&apikey={api_key}" \
            .format(api_key=self.api_key, response_type=self.response_type,
                    size=str(size), sort=sort, venue_id=venue_id)
        request_url = ''.join([self.base_url, events_url])
        resp = requests.get(request_url).json()
        print(resp)
        return [
            {
                'name': event['name'],
                'start_date': event['dates']['start']['localDate'],
                'start_time': event['dates']['start']['localTime'],
                'genres': [classification['genre']['name'] for classification in event['classifications']],
                'status': event['dates']['status']['code'],  # watch for 'cancelled'
                'price_range': ("{} - {}".format(event['priceRanges'][0]['min'],
                                                event['priceRanges'][0]['max'])
                                if 'priceRanges' in event else 'N/A')
            }
            for event in resp['_embedded']['events']
        ]
