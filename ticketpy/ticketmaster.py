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
        self.api_key = api_key
        self.response_type = response_type
        self.base_url = "http://app.ticketmaster.com/discovery/{version}/".format(version=version)
        
    def events(self, venue_id, size='20', sort='date,asc'):
        """Retrieves a list of events for the specified venue ID"""
        events_url = "events.{response_type}?size={size}&sort={sort}&venueId={venue_id}&apikey={api_key}" \
            .format(api_key=self.api_key, response_type=self.response_type,
                    size=str(size), sort=sort, venue_id=venue_id)
        request_url = ''.join([self.base_url, events_url])
        resp = requests.get(request_url).json()
        return [event['name'] for event in resp['_embedded']['events']]