"""API client classes"""
import logging
import requests
from ticketpy.model import Attraction, Classification, Event, Venue, \
    _assign_links
from ticketpy.query import AttractionQuery, ClassificationQuery, \
    EventQuery, VenueQuery

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sf = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(sf)
log.addHandler(sh)


class ApiClient:
    """ApiClient is the main wrapper for the Discovery API.
    
    Example
    -------
    
    .. code-block:: python
    
        import ticketpy
        
        client = ticketpy.ApiClient("your_api_key")
        r = client.venues.find(keyword="Tabernacle")
        

    Request URLs end up looking like:
    http://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}
    """
    base_url = "https://app.ticketmaster.com"

    def __init__(self, api_key, version='v2', response_type='json'):
        """

        :param api_key: Ticketmaster discovery API key
        :param version: API version (default: v2)
        :param response_type: Data format (JSON, XML...) (default: json)
        """
        self.__api_key = api_key  #: Ticketmaster API key
        self.response_type = response_type  #: Response type (json, xml...)
        self.version = version
        self.events = EventQuery(api_client=self)
        self.venues = VenueQuery(api_client=self)
        self.attractions = AttractionQuery(api_client=self)
        self.classifications = ClassificationQuery(api_client=self)
        self.segment_by_id = self.classifications.by_id
        self.genre_by_id = self.classifications.by_id
        self.subgenre_by_id = self.classifications.by_id

        log.debug("Root URL: {}".format(self.url))

    def search(self, method, **kwargs):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param kwargs: Search parameters, ex. venueId, eventId, 
            latlong, radius..
        :return: ``PagedResponse``
        """
        # Remove unneeded parameters and add apikey header
        kwargs = {k: v for (k, v) in kwargs.items() if v is not None}
        updates = self.api_key

        # Cast bools to 'yes' 'no' and integers to str
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
        response = requests.get(urls[method], params=kwargs).json()
        if 'errors' in response:
            raise ApiException(urls[method], kwargs, response)
        return PagedResponse(self, response)

    @property
    def api_key(self):
        """API key header to pass with API requests"""
        return {'apikey': self.__api_key}

    @api_key.setter
    def api_key(self, api_key):
        self.__api_key = api_key

    @property
    def url(self):
        """Root URL"""
        return "{}/discovery/{}".format(self.base_url, self.version)

    def __method_url(self, method):
        """Formats search method URL

        :param method: Method (ex: 'events' 'venues' ...)
        :return: Search method URL
        """
        return "{}/{}.{}".format(self.url, method, self.response_type)

    @staticmethod
    def __yes_no_only(s):
        """Helper function for parameters expecting yes/no/only
        
        :param s: str/bool to change
        :return: 'yes' 'no' or 'only' (or the original str in lowercase)
        """
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
        
        :param url: Original request url
        :param params: Request parameters
        :param response: Request response
        """
        self.url = url
        del params['apikey']
        self.params = params
        self.errors = response['errors']
        super().__init__()

    def __msg(self, error):
        """Format an error message"""
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

    def __init__(self, api_client, response, **kwargs):
        """
        
        :param api_client: Instance of ``ticketpy.client.ApiClient``
        :param kwargs: 
        """
        self.api_client = api_client  #: Parent API client
        self.page = None  #: Current page
        self.page = Page.from_json(response)

    def limit(self, max_pages=5):
        """Limit the number of page requests. Default: 5

        With a default page size of 20, ``limit(max_pages=5`` would 
        return a maximum of 200 items (fewer, if there are fewer results).

        Use this to contain the number of API calls being made, as the 
        API restricts users to a maximum of 5,000 per day. Very 
        broad searches can return a large number of pages.

        To contrast, ``all()`` will automatically request every 
        page available.

        :param max_pages: Maximum number of pages to request. 
            Default: *10*. Set to *None* (or use ``all()``) to return 
            all pages.
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

    def all(self):
        """Returns a flat list of all results. Queries all possible pages.

        Use ``limit()`` to restrict the number of calls being made.

        :return: Flat list of results
        """
        return [i for item_list in self for i in item_list]

    def __iter__(self):
        yield self.page
        api_key = self.api_client.api_key
        next_url = self.page.links.get('next')
        while next_url:
            log.debug("Requesting page: {}".format(next_url))
            next_pg = requests.get(next_url, params=api_key).json()
            pg = Page.from_json(next_pg)
            next_url = pg.links.get('next')
            yield pg


class Page(list):
    """API response page"""

    def __init__(self, number=None, size=None, total_elements=None,
                 total_pages=None):
        super().__init__([])
        self.number = number
        self.size = size
        self.total_elements = total_elements
        self.total_pages = total_pages

    @staticmethod
    def from_json(json_obj):
        """Instantiate and return a Page(list)"""
        p = Page()
        _assign_links(p, json_obj, ApiClient.base_url)
        p.number = json_obj['page']['number']
        p.size = json_obj['page']['size']
        p.total_pages = json_obj['page']['totalPages']
        p.total_elements = json_obj['page']['totalElements']

        embedded = json_obj.get('_embedded')
        if not embedded:
            return p

        object_models = {
            'events': Event,
            'venues': Venue,
            'attractions': Attraction,
            'classifications': Classification
        }
        for k, v in embedded.items():
            if k in object_models:
                obj_type = object_models[k]
                p += [obj_type.from_json(obj) for obj in v]

        return p
