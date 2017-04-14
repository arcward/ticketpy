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
    _method_tmpl = "{url}/{method}.{response_type}"

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

    @property
    def url(self):
        """Root URL"""
        return "{}/discovery/{}".format(self.base_url, self.version)

    @property
    def events_url(self):
        """URL for */events/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='events',
                                        response_type=self.response_type)

    @property
    def venues_url(self):
        """URL for */venues/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='venues',
                                        response_type=self.response_type)

    @property
    def attractions_url(self):
        """URL for */attractions/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='attractions',
                                        response_type=self.response_type)

    @property
    def classifications_url(self):
        """URL for */attractions/*"""
        return self._method_tmpl.format(url=self.url,
                                        method='classifications',
                                        response_type=self.response_type)

    @property
    def api_key(self):
        """API key"""
        return {'apikey': self.__api_key}

    @api_key.setter
    def api_key(self, api_key):
        self.__api_key = api_key

    def _search(self, method, **kwargs):
        """Generic method for API requests.
        :param method: Search type (events, venues...)
        :param kwargs: Search parameters, ex. venueId, eventId, 
            latlong, radius..
        :return: ``PageIterator``
        """
        # Get basic request URL
        if method == 'events':
            search_url = self.events_url
        elif method == 'venues':
            search_url = self.venues_url
        elif method == 'attractions':
            search_url = self.attractions_url
        elif method == 'classifications':
            search_url = self.classifications_url
        else:
            raise ValueError("Received: '{}' but was expecting "
                             "one of: {}".format(method, ['events', 'venues']))

        # Make updates to parameters. Add apikey, make sure params that
        # may be passed as integers are cast, and cast bools to 'yes' 'no'
        kwargs = {k: v for (k, v) in kwargs.items() if v is not None}
        updates = self.api_key

        for k, v in kwargs.items():
            if k in ['includeTBA', 'includeTBD', 'includeTest']:
                updates[k] = self.__yes_no_only(v)
            elif k in ['size', 'radius', 'marketId']:
                updates[k] = str(v)

        kwargs.update(updates)
        response = requests.get(search_url, params=kwargs).json()

        if 'errors' in response:
            raise ApiException(search_url, kwargs, response)

        return PageIterator(self, **response)

    @staticmethod
    def __yes_no_only(s):
        if s in ['yes', 'no', 'only']:
            pass
        elif s == True:
            s = 'yes'
        elif s == False:
            s = 'no'
        else:
            s = s.lower()
        return s


class ApiException(Exception):
    """Exception thrown for API-related error messages"""
    def __init__(self, url, params, response):
        self.url = url
        del params['apikey']
        self.params = params
        self.errors = response['errors']
        super().__init__()

    def __str__(self):
        tmpl = ("Reason: {detail}\n"
                "Request URL: {url}\n"
                "Query parameters: {sp}\n"
                "Code: {code} ({link})\n"
                "Status: {status}")
        msgs = []
        for e in self.errors:
            msgs.append(tmpl.format(
                url=self.url,
                sp=', '.join('({}={})'.format(k, v) for
                             (k, v) in self.params.items()),
                code=e['code'],
                status=e['status'],
                detail=e['detail'],
                link=e['_links']['about']['href']
            ))
        return '\n'.join(msgs)


class PageIterator:
    """Iterates through API response pages"""

    def __init__(self, api_client, **kwargs):
        self.api_client = api_client  #: Parent API client
        self.page = None  #: Current page
        self.page = self.__page(**kwargs)

        self.start_page = self.page.number  #: Initial page number
        self.current_page = self.start_page  #: Current page number
        self.end_page = self.page.total_pages  #: Final page number

    def __iter__(self):
        return self

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

        return Page(
            page['number'],
            page['size'],
            page['totalElements'],
            page['totalPages'],
            links['self']['href'],
            links_next,
            kwargs.get('_embedded', {})
        )

    def next(self):
        # Return initial Page result if we haven't yet
        if self.page.number == self.current_page:
            self.current_page += 1
            return [i for i in self.page]

        # StopIteration if we know we've run out of pages.
        # Check for current>end as empty results still return
        # a page and increment the counter.
        if self.current_page >= self.end_page:
            raise StopIteration

        # Otherwise, +1 our count and pull the next page
        self.current_page += 1
        r = requests.get(self.page.link_next,
                         params=self.api_client.api_key).json()

        self.page = self.__page(**r)

        # If 'next' link goes missing, there were fewer pages than
        # expected for some reason, so bump current_page to end_page to
        # throw StopIteration next time next() is called
        if self.page.link_next is None:
            self.current_page = self.end_page

        return [i for i in self.page]

    __next__ = next


class Page(list):
    """API response page"""

    def __init__(self, number, size, total_elements, total_pages,
                 link_self, link_next, embedded):
        super().__init__([])
        self.number = number  #: Page number
        self.size = size  #: Page size
        self.total_elements = total_elements  #: Total elements (all pages)
        self.total_pages = total_pages  #: Total pages

        self._link_self = link_self  #: Link to this page
        self._link_next = link_next  #: Link to the next page

        # Parse embedded objects and add them to ourself
        items = []
        if 'events' in embedded:
            items = [Event.from_json(e) for e in embedded['events']]
        elif 'venues' in embedded:
            items = [Venue.from_json(v) for v in embedded['venues']]
        elif 'attractions' in embedded:
            items = [Attraction.from_json(a) for a in embedded['attractions']]
        elif 'classifications' in embedded:
            items = [Classification.from_json(cl)
                     for cl in embedded['classifications']]

        for i in items:
            self.append(i)

    @property
    def link_next(self):
        """Link to the next page"""
        link = "{}{}".format(ApiClient.base_url, self._link_next)
        return link.replace('{&sort}', '')

    @property
    def link_self(self):
        """Link to this page"""
        return "{}{}".format(ApiClient.base_url, self._link_self)


# Query/search classes


# API object models







