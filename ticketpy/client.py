"""API client classes"""
import logging
import requests
from types import MappingProxyType
from typing import Literal, TypedDict, Optional, Any, Union, Generator, Tuple
from urllib.parse import urlparse, parse_qs, urlunparse
from pydantic import BaseModel
from ticketpy.query import (
    AttractionQuery,
    ClassificationQuery,
    EventQuery,
    VenueQuery,
    QueryParams,
)
from ticketpy.model import (
    Link,
    PageResponse,
    Event,
    Attraction,
    Classification,
    Venue,
)


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
        """

        :param api_key: Ticketmaster API key
        :param url: API URL
        """
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

    def search(
        self, method: SearchType, limit: Optional[int] = 10, **kwargs
    ) -> Generator[
        Union[Event, Attraction, Classification, Venue], None, None
    ]:
        """Generic API request

        :param method: Search type (*events*, *venues*...).
            Items of the given type are yielded from the page content.
        :param limit: Maximum number of pages to return
        :param kwargs: Search parameters
            (see: :class:`ticketpy.query.QueryParams`)
        """
        if method not in self.urls:
            raise KeyError(
                f"Unexpected method {method}- expected one of: "
                f"{list(self.urls.keys())}"
            )
        query_params = QueryParams(**kwargs)
        query_params = query_params.dict(by_alias=True, exclude_none=True)
        log.info("Query params: %s", query_params)
        query_params.update(dict(self.api_key))

        resp = requests.get(self.urls[method], params=query_params)
        data = self._handle_response(resp)
        page = PageResponse.parse_obj(data)
        for val in self.iter_pages(page=page, limit=limit):
            for v in getattr(val, method):
                yield v

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

    def next_page(self, page: PageResponse) -> Optional[PageResponse]:
        """
        Retrieves the next page of results, if a `next` link is present.
        """
        next_link = page.links.next_
        if not next_link:
            return
        log.info("Next link from page %s: %s", page.page.number, next_link)
        next_url = self._follow_link(link=next_link)
        log.info("Following next URL: %s", next_url)
        link, params = self._parse_link(next_url)
        resp = self._handle_response(requests.get(link, params=params))
        return PageResponse.parse_obj(resp)

    def iter_pages(
        self, page: PageResponse, limit: Optional[int] = 10,
    ) -> Generator[PageResponse, None, None]:
        """
        Yields the given page, and then iterates through the `next` links
        until either `limit` is reached, or the maximum search depth is
        reached, yielding each page.

        Delays between requests to avoid rate limiting should be handled
        client-side.
        """
        ct = 0
        while True:
            if limit is not None and ct >= limit:
                log.info("Reached page limit (%s)", limit)
                break

            if page.page.max_depth_reached:
                log.info(
                    "Maximum search depth reached "
                    "(size (%s) * number (%s) >= 1000",
                    page.page.size,
                    page.page.number,
                )
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

    def _parse_link(self, link: str) -> Tuple[str, dict]:
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
