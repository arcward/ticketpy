"""Models for API objects"""
import re
from decimal import Decimal
from typing import Optional, List, Union, TypedDict, Any
from pydantic import root_validator, validator
from pydantic import BaseModel, Field


def move_embedded(values: dict):
    embedded = values.get("_embedded")
    if embedded:
        values.update(embedded)
        del values["_embedded"]
    return values


class Embedded(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True
        validate_always = True

    venues: Optional[List["Venue"]]
    attractions: Optional[List["Attraction"]]


class Image(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True

    url: Optional[str]
    ratio: Optional[str] = Field(examples=["16_9", "3_2", "4_3"])
    width: Optional[int]
    height: Optional[int]
    fallback: Optional[bool]
    attribution: Optional[str]


class Link(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True

    href: Optional[str]
    templated: Optional[bool]

    @validator("href", pre=True)
    def _remove_braces(cls, v):
        if not v:
            return v
        return re.sub("({.+})", "", v)


class Links(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True

    self_: Optional[Link] = Field(alias="self")
    next_: Optional[Link] = Field(alias="next")
    prev: Optional[Link]
    venues: Optional[List[Link]]
    attractions: Optional[List[Link]]


class APIModelBase(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True
        validate_always = True
        validate_all = True

    id: Optional[Union[int, str]]
    name: Optional[str]
    url: Optional[str]
    links: Optional[Links] = Field(alias="_links")
    embedded: Optional[dict] = Field(alias="_embedded")

    @root_validator(pre=True)
    def _move_embedded(cls, values):
        return move_embedded(values)


class Promoter(APIModelBase):
    description: Optional[str]


class Page(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True

    size: Optional[int]
    total_elements: Optional[int] = Field(alias="totalElements")
    total_pages: Optional[int] = Field(alias="totalPages")
    number: Optional[int]

    @property
    def max_depth_reached(self) -> bool:
        """
        Returns *True* if the max page depth has been
        reached, *False* otherwise.

        As of this time, the API only supports retrieving
        the 1000th item (size * page < 1000)
        """
        if self.size * self.number < 1000:
            return False
        return True


class PageResponse(BaseModel):
    class Config:
        extra = "allow"
        validate_assignment = True

    page: Optional[Page]
    links: Optional["Links"] = Field(alias="_links")
    events: Optional[List["Event"]]
    venues: Optional[List["Venue"]]
    attractions: Optional[List["Attraction"]]
    classifications: Optional[List["Classification"]]

    embedded: Optional[dict] = Field(alias="_embedded")

    @root_validator(pre=True)
    def _move_embedded(cls, values):
        return move_embedded(values)


class ClassificationSubType(APIModelBase):
    ...


class ClassificationType(APIModelBase):
    subtypes: Optional[List[ClassificationSubType]]


class SubGenre(APIModelBase):
    ...


class Genre(APIModelBase):
    subgenres: Optional[list[SubGenre]]


class Segment(APIModelBase):
    genres: Optional[list[Genre]]


class EventClassification(APIModelBase):
    """Classification as it's represented in event search results

    See ``Classification()`` for results from classification searches
    """

    primary: Optional[Any]
    segment: Optional[Segment]
    genre: Optional[Genre]
    subgenre: Optional[SubGenre] = Field(alias="subGenre")
    type: Optional[ClassificationType]
    subtype: Optional[ClassificationSubType] = Field(alias="subType")


class Classification(APIModelBase):
    """Classification object (segment/genre/sub-genre)

    For the structure returned by ``EventSearch``, see ``EventClassification``
    """

    primary: Optional[bool]
    segment: Optional[Segment]
    genre: Optional[Genre]
    subgenre: Optional[SubGenre] = Field(alias="subGenre")
    type: Optional[ClassificationType]
    subtype: Optional[ClassificationSubType] = Field(alias="subType")


class Attraction(APIModelBase):
    """Attraction"""

    url: Optional[Any]
    test: Optional[Any]
    images: Optional[List[Image]]
    classifications: Optional[List[Classification]]


class Market(BaseModel):
    class Config:
        extra = "allow"

    id: Optional[str]


class City(BaseModel):
    class Config:
        extra = "allow"

    name: Optional[str]


class Address(BaseModel):
    class Config:
        extra = "allow"

    line1: Optional[str]
    line2: Optional[str]
    line3: Optional[str]


class Location(BaseModel):
    class Config:
        extra = "allow"

    latitude: Optional[str]
    longitude: Optional[str]


class State(BaseModel):
    class Config:
        extra = "allow"

    name: Optional[str]
    state_code: Optional[str] = Field(alias="stateCode")


class Venue(APIModelBase):
    """A Ticketmaster venue

    The JSON returned from the Discovery API looks something like this
    (*edited for brevity*):

    .. code-block:: json

        {
            "id": "KovZpaFEZe",
            "name": "The Tabernacle",
            "url": "http://www.ticketmaster.com/venue/115031",
            "timezone": "America/New_York",
            "address": {
                "line1": "152 Luckie Street"
            },
            "city": {
                "name": "Atlanta"
            },
            "postalCode": "30303",
            "state": {
                "stateCode": "GA",
                "name": "Georgia"
            },
            "country": {
                "name": "United States Of America",
                "countryCode": "US"
            },
            "location": {
                "latitude": "33.758688",
                "longitude": "-84.391449"
            },
            "social": {
                "twitter": {
                    "handle": "@TabernacleATL"
                }
            },
            "markets": [
                {
                    "id": "10"
                }
            ]
        }


    """

    url: Optional[str]
    postal_code: Optional[str] = Field(alias="postalCode")
    general_info: Optional[Any] = Field(alias="generalInfo")
    box_office_info: Optional[Any] = Field(alias="boxOfficeInfo")
    dmas: Optional[Any]
    social: Optional[Any]
    timezone: Optional[Any]
    images: Optional[List[Image]]
    parking_detail: Optional[Any] = Field(alias="parkingDetail")
    accessible_seating_detail: Optional[Any] = Field(
        alias="accessibleSeatingDetail"
    )
    markets: Optional[list[Market]]
    city: Optional[City]
    address: Optional[Address]
    location: Optional[Location]
    state: Optional[State]


class DateModel(BaseModel):
    class Config:
        extra = "allow"

    local_date: Optional[str] = Field(alias="localDate")
    date_time: Optional[str] = Field(alias="dateTime")
    date_tbd: Optional[bool] = Field(alias="dateTBD")
    date_tba: Optional[bool] = Field(alias="dateTBA")
    time_tba: Optional[bool] = Field(alias="timeTBA")
    no_specific_time: Optional[bool] = Field(alias="noSpecificTime")
    approximate: Optional[bool]


class EventDates(BaseModel):
    class Config:
        extra = "allow"

    start: Optional[DateModel]
    end: Optional[DateModel]


class PriceRange(BaseModel):
    class Config:
        extra = "allow"

    min: Optional[Decimal]
    max: Optional[Decimal]
    currency: Optional[str]
    type: Optional[str]


class Event(APIModelBase):
    """Ticketmaster event

    The JSON returned from the Discovery API (at least, as far as
    what's being used here) looks like:

    .. code-block:: json

        {
            "name": "Event name",
            "dates": {
                "start": {
                    "localDate": "2019-04-01",
                    "localTime": "2019-04-01T23:00:00Z"
                },
                "status": {
                    "code": "onsale"
                }
            },
            "classifications": [
                {
                    "genre": {
                        "name": "Rock"
                    }
                },
                {
                    "genre": {
                        "name": "Funk"
                    }
                }
            ],
            "priceRanges": [
                {
                    "min": 10,
                    "max": 25
                }
            ],
            "_embedded": {
                "venues": [
                    {
                        "name": "The Tabernacle"
                    }
                ]
            }
        }
    """

    dates: Optional[EventDates]
    classifications: Optional[List[Classification]]
    price_ranges: Optional[list[PriceRange]] = Field(alias="priceRanges")
    venues: Optional[List[Venue]]
    attractions: Optional[List[Attraction]]
    images: Optional[List[Image]]
    promoter: Optional[Promoter]
    promoters: Optional[List[Promoter]]


Embedded.update_forward_refs()
PageResponse.update_forward_refs()
