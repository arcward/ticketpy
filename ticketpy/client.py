"""API client classes"""
import logging
import requests
from collections import namedtuple
from urllib import parse
from ticketpy.query import AttractionQuery, ClassificationQuery, \
    EventQuery, VenueQuery, SegmentQuery, GenreQuery, SubGenreQuery
from ticketpy.model import Page

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sf = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(sf)
log.addHandler(sh)


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
    __RateLimit = namedtuple('RateLimit', 'limit available over reset')
    # Alias query classes here so they show in Sphinx docs
    events = EventQuery
    venues = VenueQuery
    attractions = AttractionQuery
    classifications = ClassificationQuery
    segments = SegmentQuery
    genres = GenreQuery
    subgenres = SubGenreQuery

    def __init__(self, api_key):
        self.__api_key = None
        self.api_key = api_key
        self.rate_limit = None
        self.events = self.events(api_client=self)
        self.venues = self.venues(api_client=self)
        self.attractions = self.attractions(api_client=self)
        self.classifications = self.classifications(api_client=self)
        self.segments = self.segments(api_client=self)
        self.genres = self.genres(api_client=self)
        self.subgenres = self.subgenres(api_client=self)

    def _search(self, method, **kwargs):
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
        log.debug(kwargs)
        urls = {
            'events': self.__method_url('events'),
            'venues': self.__method_url('venues'),
            'attractions': self.__method_url('attractions'),
            'classifications': self.__method_url('classifications')
        }
        resp = requests.get(urls[method], params=kwargs)
        return PagedResponse(self, self._handle_response(resp))

    def _handle_response(self, response):
        """Raises ``ApiException`` if needed, or returns response JSON obj
        
        Status codes
         * 401 = Invalid API key or rate limit quota violation
         * 400 = Invalid URL parameter
        """
        if response.status_code != 200:
            raise ApiException(response)

        self.__rate_limit(response)
        return response.json()

    def __rate_limit(self, response):
        self.rate_limit = ApiClient.__RateLimit(
            response.headers.get('Rate-Limit'),
            response.headers.get('Rate-Limit-Available'),
            response.headers.get('Rate-Limit-Over'),
            response.headers.get('Rate-Limit-Reset')
        )

    def _get_url(self, link):
        """Gets a specific href from '_links' object in a response"""
        # API sometimes return incorrectly-formatted strings, need
        # to parse out parameters and pass them into a new request
        # rather than implicitly trusting the href in _links
        link = self._parse_link(link)
        resp = requests.get(link.url, link.params)
        return Page.from_json(self._handle_response(resp))

    def _get_id(self, resource, entity_id):
        id_url = "{}/{}/{}".format(self.url, resource, entity_id)
        r = requests.get(id_url, params=self.api_key)
        return self._handle_response(r)

    def _parse_link(self, link):
        """Parses link into base URL and dict of parameters"""
        parsed_link = namedtuple('link', 'url params')
        link_url, link_params = link.split('?')
        params = self._link_params(link_params)
        return parsed_link(link_url, params)

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
    _ApiFault = namedtuple('ApiFault', 'faultstring detail')
    _ApiError = namedtuple('ApiError', 'code detail href')
    _error_codes = [400, 404]  #: 400=Bad API call
    _fault_codes = [401]  #: 401=Unauthorized (bad API key)

    def __init__(self, response):
        self.url = response.url
        self.status_code = response.status_code
        self.detail = None

        if response.status_code in self._error_codes:
            self.detail = ApiException.__error(response)
        elif response.status_code in self._fault_codes:
            self.detail = ApiException.__fault(response)
        else:
            self.detail = ApiException.__unknown(response)

        super().__init__(self.status_code, self.detail, self.url)

    @staticmethod
    def __fault(response):
        """Handle API faults (such as unauthorized/bad API key)"""
        rj = response.json()
        r_fault = rj['fault']
        return ApiException._ApiFault(r_fault['faultstring'], r_fault['detail'])

    @staticmethod
    def __error(response):
        """Handle API errors (such as bad query parameters/obj not found)"""
        rj = response.json()
        return [
            ApiException._ApiError(err['code'], err['detail'],
                                   err['_links']['about']['href'])
            for err in rj['errors']
        ]

    @staticmethod
    def __unknown(response):
        """Handle unexpected status codes, inspect JSON structure"""
        rj = response.json()
        if 'fault' in rj:
            return ApiException.__fault(response)
        elif 'errors' in rj:
            return ApiException.__error(response)
        else:
            return None


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
        # TODO Rename this since all() is a built-in function...
        return [i for item_list in self for i in item_list]

    def __iter__(self):
        yield self.page
        next_url = self.page.links.get('next')
        while next_url:
            log.debug("Requesting page: {}".format(next_url))
            pg = self.api_client._get_url(next_url)
            next_url = pg.links.get('next')
            yield pg
        return
