"""API client classes"""
import logging
import requests
from types import MappingProxyType
from typing import Literal, TypedDict, Optional, Any, Union, Generator
from urllib.parse import urlparse, parse_qs, urlunparse
from pydantic import BaseModel
from ticketpy.query import (
    AttractionQuery,
    ClassificationQuery,
    EventQuery,
    VenueQuery,
)
from ticketpy.model import Page, Link, PageResponse


log = logging.getLogger(__name__)


SearchType = Literal["events", "venues", "attractions", "classifications"]


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

    def __init__(
        self,
        api_key: str,
        url: str = "https://app.ticketmaster.com/discovery/v2",
    ):
        self.url = url
        _url_parts = urlparse(url)
        self.root_url = f"{_url_parts.scheme}://{_url_parts.netloc}"
        self.urls: dict[SearchType, str] = dict(
            events=f"{self.url}/events",
            venues=f"{self.url}/venues",
            attractions=f"{self.url}/attractions",
            classifications=f"{self.url}/classifications",
        )

        self._api_key = api_key
        self.api_key = MappingProxyType({"apikey": self._api_key})
        self.events = EventQuery(api_client=self)
        self.venues = VenueQuery(api_client=self)
        self.attractions = AttractionQuery(api_client=self)
        self.classifications = ClassificationQuery(api_client=self)
        self.segment_by_id = self.classifications.segment_by_id
        self.genre_by_id = self.classifications.genre_by_id
        self.subgenre_by_id = self.classifications.subgenre_by_id

        log.debug("URL: %s / API key: %s", self.url, self.api_key)

    def search(self, method: SearchType, **kwargs) -> PageResponse:
        """Generic API request

        :param method: Search type (*events*, *venues*...)
        :param kwargs: Search parameters (*venueId*, *eventId*,
            *latlong*, etc...)
        :return: ``PagedResponse``
        """
        if method not in self.urls:
            raise KeyError(
                f"Unexpected method {method}- expected one of: "
                f"{list(self.urls.keys())}"
            )
        # Remove unfilled parameters, add apikey header.
        # Clean up values that might be passed in multiple ways.
        # Ex: 'includeTBA' might be passed as bool(True) instead of 'yes'
        # and 'radius' might be passed as int(2) instead of '2'
        kwargs = {k: v for (k, v) in kwargs.items() if v is not None}
        updates = dict(self.api_key)

        for k, v in kwargs.items():
            if k in ["includeTBA", "includeTBD", "includeTest"]:
                updates[k] = self.__yes_no_only(v)
            elif k in ["size", "radius", "marketId"]:
                updates[k] = str(v)
        kwargs.update(updates)
        log.debug(kwargs)
        resp = requests.get(self.urls[method], params=kwargs)
        data = self._handle_response(resp)
        return PageResponse.parse_obj(data)

    def _follow_link(self, link: Link) -> str:
        if self.root_url in link.href:
            return link.href

        return f"{self.root_url}{link.href}"

    @staticmethod
    def _handle_response(response: requests.Response) -> Union[list, dict]:
        """Raises ``ApiException`` if needed, or returns response JSON obj

        Status codes
         * 401 = Invalid API key or rate limit quota violation
         * 400 = Invalid URL parameter
        """
        response.raise_for_status()
        return response.json()

    def get_url(self, link: str) -> "Page":
        """Gets a specific href from '_links' object in a response"""
        # API sometimes return incorrectly-formatted strings, need
        # to parse out parameters and pass them into a new request
        # rather than implicitly trusting the href in _links
        link, params = self._parse_link(link)
        resp = self._handle_response(requests.get(link, params=params))
        return PageResponse.parse_obj(resp)

    def next_page(self, page: PageResponse):
        next_link = page.links.next_
        if not next_link:
            return
        log.debug("Next link: %s", next_link)
        next_url = self._follow_link(link=next_link)
        log.debug("Following next URL: %s", next_url)
        return self.get_url(link=next_url)

    def iter_pages(
            self,
            page: PageResponse,
            limit: Optional[int] = None
    ) -> Generator[PageResponse, None, None]:
        ct = 0
        while True:
            if limit is not None and ct >= limit:
                break

            if ct == 0:
                yield page
                ct += 1
                continue

            page = self.next_page(page=page)
            if not page:
                break

            yield page
            ct += 1

    def _parse_link(self, link: str) -> tuple[str, dict]:
        """
        Parses the given link, and updates its query parameters
        to include the API key. Returns the base URL and the updated
        parameters
        """
        url = urlparse(link)
        query_params = parse_qs(url.query)
        query_params.update(dict(self.api_key))
        log.debug("Query params: %s", query_params)
        url = urlunparse(url._replace(query=None))
        return url, query_params

    @staticmethod
    def __yes_no_only(s: str) -> str:
        """Helper for parameters expecting ['yes', 'no', 'only']"""
        s = str(s).lower()
        if s in ["true", "yes"]:
            s = "yes"
        elif s in ["false", "no"]:
            s = "no"
        return s


class ApiException(Exception):
    """Exception thrown for API-related error messages"""

    def __init__(self, *args):
        super().__init__(*args)


class SearchURLs(TypedDict):
    events: str
    venues: str
    attractions: str
    classifications: str


class APIError(BaseModel):
    class Config:
        extra = "allow"

    code: Optional[Any]
    detail: Optional[Any]
    href: Optional[Any]


class APIErrors(BaseModel):
    class Config:
        extra = "allow"

    errors: list[APIError]
