"""Classes to handle API queries/searches"""
import logging
from typing import (
    TYPE_CHECKING,
    Optional,
    Literal,
    Union,
    Generator,
    Any,
    Type,
)
import requests
from pydantic import BaseModel, Field
from ticketpy.model import Venue, Event, Attraction, Classification


log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ticketpy.client import ApiClient, SearchType
    from ticketpy.model import (
        APIModelBase,
        Attraction,
        Event,
        Venue,
        Classification,
        Genre,
        Segment,
        SubGenre,
    )


class QueryParams(BaseModel):
    """Generic query parameters"""

    class Config:
        extra = "allow"
        allow_population_by_field_name = True

    #: Response sort type (API default: *name,asc*)
    id_: Optional[str] = Field(alias="id")
    #: Sorting order (`name,asc`, `relevance,desc`, etc)
    sort: Optional[str]
    #: Page number to get
    page: Optional[str] = "0"
    #: Page size of the response
    size: Optional[str] = "20"
    #: API default: *en*
    locale: Optional[str]
    keyword: Optional[str]
    #: Include test entities (events, attractions, ...)
    include_test: Optional[Literal["yes", "no", "only"]] = Field(
        alias="includeTest"
    )
    include_tba: Optional[Literal["yes", "no", "only"]] = Field(
        alias="includeTBA"
    )
    include_tbd: Optional[Literal["yes", "no", "only"]] = Field(
        alias="includeTBD"
    )

    venue_id: Optional[Any] = Field(alias="venueId")

    start_date_time: Optional[Any] = Field(alias="startDateTime")
    end_date_time: Optional[Any] = Field(alias="endDateTime")

    onsale_start_date_time: Optional[Any] = Field(alias="onsaleStartDateTime")
    onsale_end_date_time: Optional[Any] = Field(alias="onsaleEndDateTime")

    country_code: Optional[Any] = Field(alias="countryCode")
    state_code: Optional[Any] = Field(alias="stateCode")

    attraction_id: Optional[Any] = Field(alias="attractionId")

    segment_id: Optional[Any] = Field(alias="segmentId")
    segment_name: Optional[Any] = Field(alias="segmentName")

    classification_name: Optional[Any] = Field(alias="classificationName")
    classification_id: Optional[Any] = Field(alias="classificationId")

    market_id: Optional[str] = Field(alias="marketId")
    promoter_id: Optional[Any] = Field(alias="promoterId")
    dma_id: Optional[Any] = Field(alias="dmaId")

    client_visibility: Optional[Any] = Field(alias="clientVisibility")

    latlong: Optional[str]
    radius: Optional[str]
    unit: Optional[Literal["miles", "km"]] = Field(alias="unit")


class BaseQuery:
    """Base query/parent class for specific search types."""

    #: API method (events, venues, ...)
    method: "SearchType"
    #: Model from ``ticketpy.model``
    model: Union[
        Type["Venue"],
        Type["Event"],
        Type["Attraction"],
        Type["Classification"],
    ]

    def __init__(self, api_client: "ApiClient"):
        self.api_client = api_client

    def by_id(
        self, entity_id: str
    ) -> Union[
        "APIModelBase",
        "Event",
        "Attraction",
        "Classification",
        "Venue",
    ]:
        """Get a specific object by its ID"""
        get_url = f"{self.api_client.url}/{self.method}/{entity_id}"
        r = requests.get(get_url, params=self.api_client.api_key)
        r_json = self.api_client._handle_response(r)
        return self.model.parse_obj(r_json)

    def find(
        self, limit: Optional[int] = 10, **kwargs
    ) -> Generator[
        Union[Event, Attraction, Classification, Venue], None, None
    ]:
        """
        Basic API search request. Specify search parameters via keyword
        parameters (see: ``QueryParams`` - which also accepts additional
        parameters).

        Returns a generator that yields ``PageResponse`` objects.

        :param limit: Limit the number of pages retrieved. **Note**: Be
            aware of the `size` parameter and rate limiting - if you set
            `limit` to 10 and `size` to 1, then *ten* requests may be made.
            If you set `size` to `10` and `limit` to 1, then *one* request will
            be made.
        """
        search_params = QueryParams(**kwargs)
        search_params = search_params.dict(by_alias=True, exclude_none=True)
        log.info("Query parameters: %s", search_params)
        return self.api_client.search(
            method=self.method, limit=limit, **search_params
        )


class AttractionQuery(BaseQuery):
    """Query class for Attractions"""
    method = "attractions"
    model = Attraction


class ClassificationQuery(BaseQuery):
    """Classification search/query class"""
    method = "classifications"
    model = Classification

    def segment_by_id(self, segment_id: str) -> "Segment":
        """Return a ``Segment`` matching this ID"""
        return self.by_id(segment_id).segment

    def genre_by_id(self, genre_id: str) -> Optional["Genre"]:
        """Return a ``Genre`` matching this ID"""
        resp = self.by_id(genre_id)
        if resp.segment:
            for genre in resp.segment.genres:
                if genre.id == genre_id:
                    return genre

    def subgenre_by_id(self, subgenre_id: str) -> Optional["SubGenre"]:
        """Return a ``SubGenre`` matching this ID"""
        segment = self.by_id(subgenre_id).segment
        if segment:
            subgenres = [
                subg for genre in segment.genres for subg in genre.subgenres
            ]
            for subg in subgenres:
                if subg.id == subgenre_id:
                    return subg


class EventQuery(BaseQuery):
    """Abstraction to search API for events"""

    method = "events"
    model = Event

    def by_location(
        self,
        latitude: str,
        longitude: str,
        radius: str = "10",
        unit: Literal["miles", "km"] = "miles",
        sort: str = "relevance,desc",
        **kwargs,
    ) -> Generator[Event, None, None]:
        """Search events within a radius of a latitude/longitude coordinate.

        :param latitude: Latitude of radius center
        :param longitude: Longitude of radius center
        :param radius: Radius to search outside given latitude/longitude
        :param unit: Unit of radius ('miles' or 'km'),
        :param sort: Sort method. (Default: *relevance, desc*). If changed,
            you may get wonky results (*date, asc* returns far-away events)
        :return: List of events within that area
        """
        latitude = str(latitude)
        longitude = str(longitude)
        radius = str(radius)
        return self.find(
            latlong=f"{latitude},{longitude}",
            radius=radius,
            unit=unit,
            sort=sort,
            **kwargs,
        )


class VenueQuery(BaseQuery):
    """Queries for venues"""
    method = "venues"
    model = Venue

    def by_name(
        self, venue_name: str, state_code: Optional[str] = None, **kwargs
    ) -> Generator[Venue, None, None]:
        """Search for a venue by name.

        :param venue_name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
            (default: None)
        """
        return self.find(keyword=venue_name, state_code=state_code, **kwargs)
