"""API client classes"""
import requests

from ticketpy.model import Attraction, Classification, Event, Venue
from ticketpy.query import AttractionQuery, ClassificationQuery, \
    EventQuery, VenueQuery


class ApiClient:
    """ApiClient for the Ticketmaster Discovery API

    Request URLs end up looking like:
    http://app.ticketmaster.com/discovery/v2/events.json?apikey={api_key}
    """
    base_url = "https://app.ticketmaster.com"

    def __init__(self, api_key, version='v2', response_type='json'):
        """Initialize the API client.

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

    def search(self, method, **kwargs):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param kwargs: Search parameters, ex. venueId, eventId, 
            latlong, radius..
        :return: ``PageIterator``
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

        urls = {
            'events': self.__method_url('events'),
            'venues': self.__method_url('venues'),
            'attractions': self.__method_url('attractions'),
            'classifications': self.__method_url('classifications')
        }
        response = requests.get(urls[method], params=kwargs).json()
        if 'errors' in response:
            raise ApiException(urls[method], kwargs, response)
        return PageIterator(self, **response)

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


class PageIterator:
    """Iterates through API response pages"""

    def __init__(self, api_client, **kwargs):
        """
        
        :param api_client: Instance of ``ticketpy.client.ApiClient``
        :param kwargs: 
        """
        self.api_client = api_client  #: Parent API client
        self.page = None  #: Current page
        self.page = self.__page(**kwargs)

        self.start_page = self.page.number  #: Initial page number
        self.current_page = self.start_page  #: Current page number
        self.end_page = self.page.total_pages  #: Final page number

    def limit(self, max_pages=10):
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
        if max_pages is None:
            return self.all()

        all_items = []
        for i in range(0, max_pages):
            try:
                all_items += self.next()
            except StopIteration:
                break
        return all_items

    def all(self):
        """Returns a flat list of all results. Queries all possible pages.

        Use ``limit()`` to restrict the number of calls being made.

        :return: Flat list of results
        """
        return [i for item_list in self for i in item_list]

    @staticmethod
    def __page(**kwargs):
        """Instantiate and return a Page(list)"""
        page = kwargs['page']
        links = kwargs['_links']

        if 'next' not in links:
            links_next = None
        else:
            links_next = links['next']['href']

        return Page(page['number'], page['size'], page['totalElements'],
                    page['totalPages'], links['self']['href'], links_next,
                    kwargs.get('_embedded', {}))

    def next(self):
        # First call to next(), return initial page
        if self.page.number == self.current_page:
            self.current_page += 1
            return [i for i in self.page]

        if self.current_page >= self.end_page:
            raise StopIteration

        self.current_page += 1
        r = requests.get(self.page.link_next,
                         params=self.api_client.api_key).json()
        self.page = self.__page(**r)

        if self.page.link_next is None:
            self.current_page = self.end_page

        return [i for i in self.page]

    def __iter__(self):
        return self


class Page(list):
    """API response page"""

    def __init__(self, number, size, total_elements, total_pages,
                 link_self, link_next, embedded):
        super().__init__([])
        self.number = number
        self.size = size
        self.total_elements = total_elements
        self.total_pages = total_pages
        self._link_self = link_self
        self._link_next = link_next

        object_models = {
            'events': Event,
            'venues': Venue,
            'attractions': Attraction,
            'classifications': Classification
        }
        for k, v in embedded.items():
            if k in object_models:
                obj_type = object_models[k]
                self += [obj_type.from_json(obj) for obj in v]

    @property
    def link_next(self):
        """Link to the next page"""
        link = "{}{}".format(ApiClient.base_url, self._link_next)
        return link.replace('{&sort}', '')

    @property
    def link_self(self):
        """Link to this page"""
        return "{}{}".format(ApiClient.base_url, self._link_self)
