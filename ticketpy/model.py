"""Models for API objects"""
from collections import namedtuple
from datetime import datetime
import re
import ticketpy

#: Maps API parameters to keyword arguments
attr_map = {
    "accepted_payment_detail": "acceptedPaymentDetail",
    "accessible_seating_detail": "accessibleSeatingDetail",
    "additional_info": "additionalInfo",
    "attraction_id": "attractionId",
    "box_office_info": "boxOfficeInfo",
    "child_rule": "childRule",
    "classification_id": "classificationId",
    "classification_name": "classificationName",
    "client_visibility": "clientVisibility",
    "country_code": "countryCode",
    "date_tba": "dateTBA",
    "date_tbd": "dateTBD",
    "date_time": "dateTime",
    "dma_id": "dmaId",
    "end_approximate": "endApproximate",
    "end_date_time": "endDateTime",
    "general_info": "generalInfo",
    "general_rule": "generalRule",
    "id": "id",
    "include_tba": "includeTBA",
    "include_tbd": "includeTBD",
    "include_test": "includeTest",
    "keyword": "keyword",
    "latlong": "latlong",
    "line_1": "line1",
    "line_2": "line2",
    "line_3": "line3",
    "local_date": "localDate",
    "local_time": "localTime",
    "locale": "locale",
    "market_id": "marketId",
    "no_specific_time": "noSpecificTime",
    "onsale_end_date_time": "onsaleEndDateTime",
    "onsale_start_date_time": "onsaleStartDateTime",
    "open_hours_detail": "openHoursDetail",
    "page": "page",
    "parking_detail": "parkingDetail",
    "phone_number_detail": "phoneNumberDetail",
    "please_note": "pleaseNote",
    "postal_code": "postalCode",
    "price_ranges": "priceRanges",
    "promoter_id": "promoterId",
    "radius": "radius",
    "segment_id": "segmentId",
    "segment_name": "segmentName",
    "size": "size",
    "sort": "sort",
    "span_multiple_days": "spanMultipleDays",
    "start_approximate": "startApproximate",
    "start_date_time": "startDateTime",
    "start_tbd": "startTBD",
    "state_code": "stateCode",
    "subtype": "subType",
    "time_tba": "timeTBA",
    "venue_id": "venueId",
    "will_call_detail": "willCallDetail",
}

# API response objects found in >1 object model
Address = namedtuple('Address', 'line_1 line_2 line_3')
City = namedtuple('City', 'name')
State = namedtuple('State', 'state_code name')
Country = namedtuple('Country', 'country_code name')
Location = namedtuple('Location', 'latitude longitude')
Area = namedtuple('Area', 'name')
Image = namedtuple('Image', 'url ratio width height fallback attribution')


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
        """Instantiate and return a ``Page(list)`` object"""
        pg = Page()
        _Util.assign_links(pg, json_obj, ticketpy.ApiClient.root_url)
        pg.number = json_obj['page']['number']
        pg.size = json_obj['page']['size']
        pg.total_pages = json_obj['page']['totalPages']
        pg.total_elements = json_obj['page']['totalElements']

        embedded = json_obj.get('_embedded')
        # No objects in response for some reason
        if not embedded:
            return pg

        object_models = {
            'events': Event,
            'venues': Venue,
            'attractions': Attraction,
            'classifications': Classification
        }
        for k, v in embedded.items():
            if k in object_models:
                obj_type = object_models[k]
                pg += [obj_type.from_json(obj) for obj in v]
        return pg

    def __str__(self):
        return ("Page {number}/{total_pages}, Size: {size}, "
                "Total elements: {total_elements}").format(**self.__dict__)

    def __repr__(self):
        return str(self)


class Event:
    """Ticketmaster event"""
    __Price = namedtuple('Price', 'type currency min max')
    __Promoter = namedtuple('Promoter', 'id name description')

    def __init__(self, additional_info=None, attractions=None,
                 classifications=None, dates=None, description=None,
                 distance=None, event_id=None, images=None, info=None,
                 links=None, locale=None, name=None, test=None, place=None,
                 please_note=None, price_ranges=None, promoter=None,
                 sales=None, units=None, url=None, venues=None):
        self.additional_info = additional_info
        self.attractions = attractions
        self.classifications = classifications
        self.dates = dates
        self.description = description
        self.distance = distance
        self.id = event_id
        self.images = images
        self.info = info
        self.links = links
        self.locale = locale
        self.name = name
        self.place = place
        self.please_note = please_note
        self.price_ranges = price_ranges
        self.promoter = promoter
        self.sales = sales
        self.test = test
        self.units = units
        self.url = url
        self.venues = venues

    @staticmethod
    def from_json(json_event):
        """Creates an ``Event`` from API's JSON response"""
        args = ['name', 'distance', 'units', 'locale', 'description',
                'url', 'test', 'info']
        kwargs = {k: json_event.get(k) for k in args}
        kwargs.update({
            'event_id': json_event.get('id'),
            'promoter': _Util.namedtuple(Event.__Promoter,
                                         json_event.get('promoter')),
            'dates': Dates.from_json(json_event.get('dates'))
        })
        kwargs['event_id'] = json_event.get('id')
        ev = Event(**kwargs)

        sales = json_event.get('sales')
        if sales:
            ev.sales = Sales.from_json(sales)

        images = json_event.get('images')
        if images:
            ev.images = [_Util.namedtuple(Image, i) for i in images]

        place = json_event.get('place')
        if place:
            ev.place = Place.from_json(place)

        price_ranges = json_event.get('priceRanges')
        if price_ranges:
            ev.price_ranges = [_Util.namedtuple(Event.__Price, p)
                               for p in price_ranges]

        classifications = json_event.get('classifications')
        if classifications:
            ev.classifications = [EventClassification.from_json(cl)
                                  for cl in classifications]

        embedded = json_event.get('_embedded', {})
        venues = embedded.get('venues')
        if venues:
            ev.venues = [Venue.from_json(v) for v in venues]

        attractions = embedded.get('attractions')
        if attractions:
            ev.attractions = [Attraction.from_json(a) for a in attractions]

        _Util.assign_links(ev, json_event)
        return ev

    def __str__(self):
        tmpl = ("Event:            {name}\n"
                "Venues:           {venues}\n"
                "Price ranges:     {price_ranges}\n"
                "Classifications:  {classifications!s}\n")
        return tmpl.format(**self.__dict__)

    def __repr__(self):
        return str(self)


class Attraction:
    """Attraction"""

    def __init__(self, attraction_id=None, attraction_name=None,
                 classifications=None, images=None, links=None, test=None,
                 url=None):
        self.id = attraction_id
        self.name = attraction_name
        self.classifications = classifications
        self.images = images
        self.links = links
        self.test = test
        self.url = url

    @staticmethod
    def from_json(json_obj):
        """Convert JSON object to ``Attraction`` object"""
        att = Attraction()
        att.id = json_obj.get('id')
        att.name = json_obj.get('name')
        att.url = json_obj.get('url')
        att.test = json_obj.get('test')

        images = json_obj.get('images')
        if images:
            att.images = [_Util.namedtuple(Image, i) for i in images]

        classifications = json_obj.get('classifications')
        if classifications:
            att.classifications = [Classification.from_json(cl) for
                                   cl in classifications]

        _Util.assign_links(att, json_obj)
        return att

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class Classification:
    """Classification object (segment/genre/sub-genre)

    For the structure returned by ``EventSearch``, see ``EventClassification``
    """

    def __init__(self, classification_type=None, links=None, primary=None,
                 subtype=None, segment=None):
        self.type = classification_type
        self.links = links
        self.primary = primary
        self.segment = segment
        self.subtype = subtype

    @staticmethod
    def from_json(json_obj):
        """Create/return ``Classification`` object from JSON"""
        cl = Classification()
        cl.primary = json_obj.get('primary')

        segment = json_obj.get('segment')
        if segment:
            cl.segment = Segment.from_json(segment)

        cl_t = json_obj.get('type')
        if cl_t:
            cl.type = ClassificationType(cl_t['id'], cl_t['name'])

        subtype = json_obj.get('subType')
        if subtype:
            cl.subtype = ClassificationSubType(subtype['id'], subtype['name'])

        _Util.assign_links(cl, json_obj)
        return cl


class Venue:
    """A Ticketmaster venue"""
    __DMA = namedtuple('DMA', 'id')
    __BoxOfficeInfo = namedtuple('BoxOfficeInfo', 'phone_number_detail '
                                                  'open_hours_detail '
                                                  'accepted_payment_detail '
                                                  'will_call_detail')
    __Market = namedtuple('Market', 'id')
    __GeneralInfo = namedtuple('GeneralInfo', 'general_rule child_rule')

    def __init__(self, accessible_seating_detail=None, additional_info=None,
                 address=None, box_office_info=None, city=None, country=None,
                 currency=None, description=None, distance=None, dmas=None,
                 general_info=None, images=None, links=None, locale=None,
                 location=None, markets=None, name=None, parking_detail=None,
                 postal_code=None, social=None, state=None, test=None,
                 timezone=None, type=None, units=None, url=None,
                 venue_id=None):

        self.accessible_seating_detail = accessible_seating_detail
        self.additional_info = additional_info
        self.address = address
        self.box_office_info = box_office_info
        self.city = city
        self.country = country
        self.currency = currency
        self.description = description
        self.distance = distance
        self.dmas = dmas
        self.general_info = general_info
        self.id = venue_id
        self.images = images
        self.links = links
        self.locale = locale
        self.location = location
        self.markets = markets
        self.name = name
        self.parking_detail = parking_detail
        self.postal_code = postal_code
        self.social = social
        self.state = state
        self.test = test
        self.type = type
        self.timezone = timezone
        self.units = units
        self.url = url

    @staticmethod
    def from_json(json_venue):
        """Returns a ``Venue`` object from JSON"""
        args = ['name', 'url', 'type', 'distance', 'units', 'locale',
                'description', 'additionalInfo', 'postalCode', 'timezone',
                'currency', 'parkingDetail', 'test', 'social']
        kwargs = {k: json_venue.get(k) for k in args}
        kwargs.update({
            'venue_id': json_venue.get('id'),
            'city': _Util.namedtuple(City, json_venue.get('city')),
            'state': _Util.namedtuple(State, json_venue.get('state')),
            'country': _Util.namedtuple(Country, json_venue.get('country')),
            'address': _Util.namedtuple(Address, json_venue.get('address')),
            'location': _Util.namedtuple(Location, json_venue.get('location')),
            'generalInfo': _Util.namedtuple(Venue.__GeneralInfo,
                                            json_venue.get('generalInfo')),
            'boxOfficeInfo': _Util.namedtuple(Venue.__BoxOfficeInfo,
                                              json_venue.get('boxOfficeInfo')),
            'accessibleSeatingDetail':
                json_venue.get('accessibleSeatingDetail')
        })
        _Util.update_kwargs(kwargs)
        v = Venue(**kwargs)

        images = json_venue.get('images')
        if images:
            v.images = [_Util.namedtuple(Image, i) for i in images]

        markets = json_venue.get('markets')
        if markets:
            v.markets = [_Util.namedtuple(Venue.__Market, m) for m in markets]

        dmas = json_venue.get('dmas')
        if dmas:
            v.dmas = [_Util.namedtuple(Venue.__DMA, d) for d in dmas]

        _Util.assign_links(v, json_venue)
        return v

    def __str__(self):
        return self.name if self.name is not None else 'Missing venue name'

    def __repr__(self):
        return str(self)


class Place:
    def __init__(self, address=None, area=None, city=None, country=None,
                 location=None, name=None, postal_code=None, state=None):
        self.address = address
        self.area = area
        self.city = city
        self.country = country
        self.location = location
        self.name = name
        self.postal_code = postal_code
        self.state = state

    @staticmethod
    def from_json(json_obj):
        kwargs = {
            'name': json_obj.get('name'),
            'postalCode': json_obj.get('postalCode'),
            'area': _Util.namedtuple(Area, json_obj.get('area')),
            'address': _Util.namedtuple(Address, json_obj.get('address')),
            'city': _Util.namedtuple(City, json_obj.get('city')),
            'state': _Util.namedtuple(State, json_obj.get('state')),
            'country': _Util.namedtuple(Country, json_obj.get('country')),
            'location': _Util.namedtuple(Location, json_obj.get('location'))
        }
        _Util.update_kwargs(kwargs)
        return Place(**kwargs)


class Dates:
    __Start = namedtuple('Start', 'local_date local_time date_time date_tbd '
                                  'date_tba time_tba no_specific_time')
    __End = namedtuple('End', 'local_time local_date date_time '
                              'approximate no_specific_time')
    __Access = namedtuple('Access', 'start_date_time start_approximate '
                                    'end_date_time end_approximate')
    __Status = namedtuple('Status', 'code')

    def __init__(self, access=None, start=None, end=None, timezone=None,
                 status=None, span_multiple_days=None):
        self.start = start
        self.end = end
        self.access = access
        self.timezone = timezone
        self.status = status
        # TODO span_multiple_days not shown in API docs
        self.span_multiple_days = span_multiple_days

    @staticmethod
    def from_json(json_obj):
        dates = Dates()
        dates.timezone = json_obj.get('timezone')
        dates.span_multiple_days = json_obj.get('spanMultipleDays')
        dates.start = _Util.namedtuple(Dates.__Start, json_obj.get('start'))
        dates.end = _Util.namedtuple(Dates.__End, json_obj.get('end'))
        dates.access = _Util.namedtuple(Dates.__Access, json_obj.get('access'))
        dates.status = _Util.namedtuple(Dates.__Status, json_obj.get('status'))
        return dates


class Sales:
    __PublicSale = namedtuple('PublicSales', 'start_date_time end_date_time '
                                             'start_tbd')
    __Presale = namedtuple('Presale', 'name description url start_date_time '
                                      'end_date_time')

    def __init__(self, public=None, presales=None):
        self.public = public
        self.presales = presales

    @staticmethod
    def from_json(json_obj):
        sales = Sales()

        public = json_obj.get('public')
        if public:
            sales.public = _Util.namedtuple(Sales.__PublicSale, public)

        presales = json_obj.get('presales')
        if presales:
            sales.presales = [_Util.namedtuple(Sales.__Presale, ps)
                              for ps in presales]
        return sales


class EventClassification:
    """Classification as it's represented in event search results
    See ``Classification()`` for results from classification searches"""
    def __init__(self, classification_subtype=None, classification_type=None,
                 genre=None, links=None, segment=None, subgenre=None,
                 primary=None):
        self.subtype = classification_subtype
        self.type = classification_type
        self.genre = genre
        self.links = links
        self.primary = primary
        self.segment = segment
        self.subgenre = subgenre

    @staticmethod
    def from_json(json_obj):
        """Create/return ``EventClassification`` object from JSON"""
        ec = EventClassification()
        ec.primary = json_obj.get('primary')

        segment = json_obj.get('segment')
        if segment:
            ec.segment = Segment.from_json(segment)

        genre = json_obj.get('genre')
        if genre:
            ec.genre = Genre.from_json(genre)

        subgenre = json_obj.get('subGenre')
        if subgenre:
            ec.subgenre = Subgenre.from_json(subgenre)

        cl_t = json_obj.get('type')
        if cl_t:
            ec.type = ClassificationType(cl_t['id'], cl_t['name'])

        cl_st = json_obj.get('subType')
        if cl_st:
            ec.subtype = ClassificationSubType(cl_st['id'], cl_st['name'])

        _Util.assign_links(ec, json_obj)
        return ec

    def __str__(self):
        return ("Segment: {segment} / Genre: {genre} / Subgenre: {subgenre} / "
                "Type: {type} / Subtype: {subtype}").format(**self.__dict__)

    def __repr__(self):
        return str(self)


class ClassificationType:
    def __init__(self, type_id=None, type_name=None, subtypes=None):
        self.id = type_id
        self.name = type_name
        self.subtypes = subtypes

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class ClassificationSubType:
    def __init__(self, type_id=None, type_name=None):
        self.id = type_id
        self.name = type_name

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class Segment:
    def __init__(self, segment_id=None, segment_name=None, genres=None,
                 links=None):
        self.id = segment_id
        self.name = segment_name
        self.genres = genres
        self.links = links

    @staticmethod
    def from_json(json_obj):
        """Create and return a ``Segment`` from JSON"""
        seg = Segment()
        seg.id = json_obj['id']
        seg.name = json_obj['name']

        if '_embedded' in json_obj:
            genres = json_obj['_embedded']['genres']
            seg.genres = [Genre.from_json(g) for g in genres]

        _Util.assign_links(seg, json_obj)
        return seg

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class Genre:
    def __init__(self, genre_id=None, genre_name=None, subgenres=None,
                 links=None):
        self.id = genre_id
        self.name = genre_name
        self.subgenres = subgenres
        self.links = links

    @staticmethod
    def from_json(json_obj):
        g = Genre()
        g.id = json_obj.get('id')
        g.name = json_obj.get('name')
        if '_embedded' in json_obj:
            embedded = json_obj['_embedded']
            subgenres = embedded['subgenres']
            g.subgenres = [Subgenre.from_json(sg) for sg in subgenres]

        _Util.assign_links(g, json_obj)
        return g

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class Subgenre:
    def __init__(self, subgenre_id=None, subgenre_name=None, links=None):
        self.id = subgenre_id
        self.name = subgenre_name
        self.links = links

    @staticmethod
    def from_json(json_obj):
        sg = Subgenre()
        sg.id = json_obj['id']
        sg.name = json_obj['name']
        _Util.assign_links(sg, json_obj)
        return sg

    def __str__(self):
        return self.name if self.name is not None else 'Unknown'

    def __repr__(self):
        return str(self)


class _Util:
    """Utility class for generating namedtuples/modifying data"""
    @staticmethod
    def assign_links(obj, json_obj, base_url=None):
        """Assigns ``links`` attribute to an object from JSON"""
        # Normal link strucutre is {link_name: {'href': url}},
        # but some responses also have lists of other models.
        # API occasionally returns bad URLs (with {&sort} and similar)
        json_links = json_obj.get('_links', {})
        obj_links = {}
        for k, v in json_links.items():
            if 'href' in v:
                href = re.sub("({.+})", "", v['href'])
                if base_url:
                    href = "{}{}".format(base_url, href)
                obj_links[k] = href
            else:
                obj_links[k] = v
        obj.links = obj_links

    @staticmethod
    def namedtuple(namedtuple_model, json_obj=None):
        """Initializes the provided ``namedtuple`` using ``json_obj``
        
        Creates dict with necessary keys (``NoneType`` values), then 
        updates it with those found in ``json_obj`` after updating 
        ``json_obj`` keys with those found in ``attr_map``
        """
        if not json_obj:
            return None
        kwargs = {k: None for k in namedtuple_model._fields}
        _Util.update_kwargs(json_obj)
        kwargs.update(json_obj)
        return namedtuple_model(**kwargs)

    @staticmethod
    def update_kwargs(kwargs):
        """Updates parameter names in kwargs based on ``attr_map``"""
        for k, v in attr_map.items():
            if v in kwargs and v != k:
                kwargs[k] = kwargs[v]
                del kwargs[v]

        if 'dateTime' in kwargs:
            kwargs['dateTime'] = _Util.format_utc_timestamp(kwargs['dateTime'])

    @staticmethod
    def format_utc_timestamp(timestamp):
        """Cast timestamp str to ``datetime``"""
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
