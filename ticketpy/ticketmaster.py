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