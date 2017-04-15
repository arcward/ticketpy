"""API client classes"""
import requests
from urllib import parse
from urllib.parse import quote, unquote
from ticketpy.query import AttractionQuery, ClassificationQuery, \
    EventQuery, VenueQuery
from ticketpy.model import Page


class ApiClient:
    """ApiClient is the main wrapper for the Discovery API.
    
    **Example**:    
    Get the first page result for venues matching keyword '*Tabernacle*':
    
    .. code-block:: python
    
        import ticketpy
        
        client = ticketpy.ApiClient("your_api_key")
        resp = client.venues.find(keyword="Tabernacle").one()
        for venue in resp:
            print(venue.name)
    
    Output::
    
        Tabernacle
        The Tabernacle
        Tabernacle, Notting Hill
        Bethel Tabernacle
        Revivaltime Tabernacle
        ...       

    Request URLs end up looking like:
    http://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}
    """
    root_url = 'https://app.ticketmaster.com'
    url = 'https://app.ticketmaster.com/discovery/v2'

    def __init__(self, api_key):
        self.__api_key = None
        self.api_key = api_key
        self.events = EventQuery(api_client=self)
        self.venues = VenueQuery(api_client=self)
        self.attractions = AttractionQuery(api_client=self)
        self.classifications = ClassificationQuery(api_client=self)
        self.segment_by_id = self.classifications.by_id
        self.genre_by_id = self.classifications.by_id
        self.subgenre_by_id = self.classifications.by_id

    def search(self, method, **kwargs):
        """Generic API request
        
        :param method: Search type (*events*, *venues*...)
        :param kwargs: Search parameters (*venueId*, *eventId*, 
            *latlong*, etc...)
        :return: ``PagedResponse``
        """
        # Remove unfilled parameters, add apikey header.
        # Clean up values that might be passed in multiple ways.
        # Ex: 'includeTBA' might be passed as bool(True) instead of 'yes'
        # and 'radius' might be passed as int(2) instead of '2'
        kwargs = {k: v for (k, v) in kwargs.items() if v is not None}
        updates = self.api_key

        for k, v in kwargs.items():
            if k in ['includeTBA', 'includeTBD', 'includeTest']:
                updates[k] = self.__yes_no_only(v)
            elif k in ['size', 'radius', 'marketId']:
                updates[k] = str(v)
        kwargs.update(updates)

        urls = {
            'events': self.__method_url('events'),
            'venues': self.__method_url('venues'),
            'attractions': self.__method_url('attractions'),
            'classifications': self.__method_url('classifications')
        }
        response = requests.get(urls[method], params=kwargs).json()
        if 'errors' in response:
            raise ApiException(urls[method], kwargs, response)
        return PagedResponse(self, response)

    def get_url(self, link):
        """Gets a specific href from '_links' object in a response"""
        # API sometimes return incorrectly-formatted strings, need
        # to parse out parameters and pass them into a new request
        # rather than implicitly trusting the href in _links
        link_arr = link.split('?')
        params = self._link_params(link_arr[1])
        resp = requests.get(link_arr[0], params).json()
        if 'errors' in resp:
            raise ApiException(link, params, resp)
        return Page.from_json(resp)

    def _link_params(self, param_str):
        """Parse URL parameters from href split on '?' character"""
        search_params = {}
        params = parse.parse_qs(param_str)
        for k, v in params.items():
            search_params[k] = v[0]
            search_params.update(self.api_key)
        return search_params

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key):
        # Set this way by default to pass in request params
        self.__api_key = {'apikey': api_key}

    @staticmethod
    def __method_url(method):
        """Formats a search method URL"""
        return "{}/{}.json".format(ApiClient.url, method)

    @staticmethod
    def __yes_no_only(s):
        """Helper for parameters expecting ['yes', 'no', 'only']"""
        s = str(s).lower()
        if s in ['true', 'yes']:
            s = 'yes'
        elif s in ['false', 'no']:
            s = 'no'
        return s


class ApiException(Exception):
    """Exception thrown for API-related error messages"""
    def __init__(self, url, params, response):
        """
        :param url: Original (full) request url
        :param params: Request/search parameters
        :param response: Request response
        """
        self.url = url
        if not params:
            params = {}
        self.params = params
        self.errors = response['errors']
        super().__init__()

    def __msg(self, error):
        """Formats an exception message"""
        tmpl = ("Reason: {detail}\nRequest URL: {url}\n"
                "Query parameters: {sp}\nCode: {code} ({link})\n"
                "Status: {status}")
        search_params = ', '.join("({}={})".format(k, v)
                                  for (k, v) in self.params.items())
        return tmpl.format(url=self.url, code=error['code'],
                           status=error['status'], detail=error['detail'],
                           link=error['_links']['about']['href'],
                           sp=search_params)

    def __str__(self):
        msgs = [self.__msg(e) for e in self.errors]
        return '\n'.join(msgs)


class PagedResponse:
    """Iterates through API response pages"""

    def __init__(self, api_client, response):
        self.api_client = api_client
        self.page = None
        self.page = Page.from_json(response)

    def limit(self, max_pages=5):
        """Retrieve X number of pages, returning a ``list`` of all entities.
        
        Rather than iterating through ``PagedResponse`` to retrieve 
        each page (and its events/venues/etc), ``limit()``  will 
        automatically iterate up to ``max_pages`` and return 
        a flat/joined list of items in each ``Page``

        :param max_pages: Max page requests to make before returning list
        :return: Flat list of results from pages
        """
        all_items = []
        counter = 0
        for pg in self:
            if counter >= max_pages:
                break
            counter += 1
            all_items += pg
        return all_items

    def one(self):
        """Get items from first page result"""
        return [i for i in self.page]

    def all(self):
        """Retrieves **all** pages in a result, returning a flat list.

        Use ``limit()`` to restrict the number of page requests being made.
        **WARNING**: Generic searches may involve *a lot* of pages...
        
        :return: Flat list of results
        """
        return [i for item_list in self for i in item_list]

    def __iter__(self):
        yield self.page
        next_url = self.page.links.get('next')
        while next_url:
            pg = self.api_client.get_url(next_url)
            next_url = pg.links.get('next')
            yield pg




