"""API client classes"""
import logging
import requests
from collections import namedtuple
from urllib import parse
from ticketpy.query import (
    AttractionQuery,
    ClassificationQuery,
    EventQuery,
    VenueQuery
)
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

    def __init__(self, api_key):
        self.__api_key = None
        self.api_key = api_key
        self.events = EventQuery(api_client=self)
        self.venues = VenueQuery(api_client=self)
        self.attractions = AttractionQuery(api_client=self)
        self.classifications = ClassificationQuery(api_client=self)
        self.segment_by_id = self.classifications.segment_by_id
        self.genre_by_id = self.classifications.genre_by_id
        self.subgenre_by_id = self.classifications.subgenre_by_id

        log.debug("Root URL: {}".format(self.url))

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
        if response.status_code == 200:
            return self.__success(response)
        elif response.status_code == 401:
            self.__fault(response)
        elif response.status_code == 400:
            self.__error(response)
        else:
            self.__unknown_error(response)

    @staticmethod
    def __success(response):
        """Successful response, just return JSON"""
        return response.json()

    @staticmethod
    def __error(response):
        """HTTP status code 400, or something with 'errors' object"""
        rj = response.json()
        error = namedtuple('error', ['code', 'detail', 'href'])
        errors = [
            error(err['code'], err['detail'], err['_links']['about']['href'])
            for err in rj['errors']
        ]
        log.error('URL: {}\nErrors: {}'.format(response.url, errors))
        raise ApiException(response.status_code, errors, response.url)

    @staticmethod
    def __fault(response):
        """HTTP status code 401, or something with 'faults' object"""
        rj = response.json()
        fault_str = rj['fault']['faultstring']
        detail = rj['fault']['detail']
        log.error('URL: {}, Faultstr: {}'.format(response.url, fault_str))
        raise ApiException(
            response.status_code,
            fault_str,
            detail,
            response.url
        )

    def __unknown_error(self, response):
        """Unexpected HTTP status code (not 200, 400, or 401)"""
        rj = response.json()
        if 'fault' in rj:
            self.__fault(response)
        elif 'errors' in rj:
            self.__error(response)
        else:
            raise ApiException(response.status_code, response.text)

    def get_url(self, link):
        """Gets a specific href from '_links' object in a response"""
        # API sometimes return incorrectly-formatted strings, need
        # to parse out parameters and pass them into a new request
        # rather than implicitly trusting the href in _links
        link = self._parse_link(link)
        resp = requests.get(link.url, link.params)
        return Page.from_json(self._handle_response(resp))

    def _parse_link(self, link):
        """Parses link into base URL and dict of parameters"""
        parsed_link = namedtuple('link', ['url', 'params'])
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
    def __init__(self, *args):
        super().__init__(*args)


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
            pg = self.api_client.get_url(next_url)
            next_url = pg.links.get('next')
            yield pg
        return
