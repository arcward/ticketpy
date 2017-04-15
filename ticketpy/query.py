"""Classes to handle API queries/searches"""
import requests
from ticketpy.model import Venue, Event, Attraction, Classification


class BaseQuery:
    """Base query/parent class for specific serach types."""
    #: Maps parameter names to parameters expected by the API
    #: (ex: *market_id* maps to *marketId*)
    attr_map = {
        'start_date_time': 'startDateTime',
        'end_date_time': 'endDateTime',
        'onsale_start_date_time': 'onsaleStartDateTime',
        'onsale_end_date_time': 'onsaleEndDateTime',
        'country_code': 'countryCode',
        'state_code': 'stateCode',
        'venue_id': 'venueId',
        'attraction_id': 'attractionId',
        'segment_id': 'segmentId',
        'segment_name': 'segmentName',
        'classification_name': 'classificationName',
        'classification_id': 'classificationId',
        'market_id': 'marketId',
        'promoter_id': 'promoterId',
        'dma_id': 'dmaId',
        'include_tba': 'includeTBA',
        'include_tbd': 'includeTBD',
        'client_visibility': 'clientVisibility',
        'include_test': 'includeTest',
        'keyword': 'keyword',
        'id': 'id',
        'sort': 'sort',
        'page': 'page',
        'size': 'size',
        'locale': 'locale',
        'latlong': 'latlong',
        'radius': 'radius'
    }

    def __init__(self, api_client, method, model):
        """
        :param api_client: Instance of ``ticketpy.client.ApiClient``
        :param method: API method (ex: *events*, *venues*...)
        :param model: Model from ``ticketpy.model``. Either 
            ``Event``, ``Venue``, ``Attraction`` or ``Classification``
        """
        self.api_client = api_client
        self.method = method
        self.model = model

    def __get(self, **kwargs):
        """Sends final request to ``ApiClient``"""
        response = self.api_client.search(self.method, **kwargs)
        return response

    def _get(self, keyword=None, entity_id=None, sort=None, include_test=None,
             page=None, size=None, locale=None, **kwargs):
        """Basic API search request, with only the parameters common to all 
        search functions. Specific searches pass theirs through **kwargs.
        
        :param keyword: Keyword to search on
        :param entity_id: ID of the object type (such as an event ID...)
        :param sort: Sort method
        :param include_test: ['yes', 'no', 'only'] to include test objects in 
            results. Default: *no*
        :param page: Page to return (default: 0)
        :param size: Page size (default: 20)
        :param locale: Locale (default: *en*)
        :param kwargs: Additional search parameters
        :return: 
        """
        # Combine universal parameters and supplied kwargs into single dict,
        # then map our parameter names to the ones expected by the API and
        # make the final request
        search_args = dict(kwargs)
        search_args.update({
            'keyword': keyword,
            'id': entity_id,
            'sort': sort,
            'include_test': include_test,
            'page': page,
            'size': size,
            'locale': locale
        })
        params = self._search_params(**search_args)
        return self.__get(**params)

    def by_id(self, entity_id):
        """Get a specific object by its ID"""
        get_tmpl = "{}/{}/{}"
        get_url = get_tmpl.format(self.api_client.url, self.method, entity_id)
        r = requests.get(get_url, params=self.api_client.api_key).json()
        return self.model.from_json(r)

    def _search_params(self, **kwargs):
        """Returns API-friendly search parameters from kwargs
        
        Maps parameter names to ``self.attr_map`` and removes 
        paramters == ``None``
        
        :param kwargs: Keyword arguments
        :return: API-friendly parameters
        """
        # Update search parameters with kwargs
        kw_map = {}
        for k, v in kwargs.items():
            # If arg is API-friendly (ex: stateCode='GA')
            if k in self.attr_map.keys():
                kw_map[self.attr_map[k]] = v
            elif k in self.attr_map.values():
                kw_map[k] = v
            else:
                kw_map[k] = v

        return {k: v for (k, v) in kw_map.items() if v is not None}


class VenueQuery(BaseQuery):
    """Queries for venues"""
    def __init__(self, api_client):
        super().__init__(api_client, 'venues', Venue)

    def find(self, keyword=None, venue_id=None, sort=None, state_code=None,
             country_code=None, source=None, include_test=None,
             page=None, size=None, locale=None, **kwargs):
        """Search for venues matching provided parameters
        
        :param keyword: Keyword to search on (such as part of the venue name)
        :param venue_id: Venue ID 
        :param sort: Sort method for response (API default: 'name,asc')
        :param state_code: Filter by state code (ex: 'GA' not 'Georgia')
        :param country_code: Filter by country code
        :param source: Filter entities by source (['ticketmaster', 'universe', 
            'frontgate', 'tmr'])
        :param include_test: ['yes', 'no', 'only'], whether to include 
            entities flagged as test in the response (default: 'no')
        :param page: Page number (default: 0)
        :param size: Page size of the response (default: 20)
        :param locale: Locale (default: 'en')
        :return: Venues found matching criteria 
        :rtype: ``ticketpy.PagedResponse``
        """
        return self._get(keyword, venue_id, sort, include_test, page,
                         size, locale, state_code=state_code,
                         country_code=country_code, source=source, **kwargs)

    def by_name(self, venue_name, state_code=None, **kwargs):
        """Search for a venue by name.

        :param venue_name: Venue name to search
        :param state_code: Two-letter state code to narrow results (ex 'GA')
            (default: None)
        :return: List of venues found matching search criteria
        """
        return self.find(keyword=venue_name, state_code=state_code, **kwargs)


class EventQuery(BaseQuery):
    """Abstraction to search API for events"""
    def __init__(self, api_client):
        super().__init__(api_client, 'events', Event)

    def find(self, sort='date,asc', latlong=None, radius=None, unit=None,
             start_date_time=None, end_date_time=None,
             onsale_start_date_time=None, onsale_end_date_time=None,
             country_code=None, state_code=None, venue_id=None,
             attraction_id=None, segment_id=None, segment_name=None,
             classification_name=None, classification_id=None,
             market_id=None, promoter_id=None, dma_id=None,
             include_tba=None, include_tbd=None, client_visibility=None,
             keyword=None, event_id=None, source=None, include_test=None,
             page=None, size=None, locale=None, **kwargs):
        """Search for events matching given criteria.

        :param sort: Sorting order of search result 
            (default: *'relevance,desc'*)
        :param latlong: Latitude/longitude filter
        :param radius: Radius of area to search
        :param unit: Unit of radius, 'miles' or 'km' (default: miles)
        :param start_date_time: Filter by start date/time.
            Timestamp format: *YYYY-MM-DDTHH:MM:SSZ*
        :param end_date_time: Filter by end date/time.
            Timestamp format: *YYYY-MM-DDTHH:MM:SSZ*
        :param onsale_start_date_time: 
        :param onsale_end_date_time: 
        :param country_code: 
        :param state_code: State code (ex: 'GA' not 'Georgia')
        :param venue_id: Find events for provided venue ID
        :param attraction_id: 
        :param segment_id: 
        :param segment_name: 
        :param classification_name: Filter events by a list of 
            classification name(s) (genre/subgenre/type/subtype/segment)
        :param classification_id: 
        :param market_id: 
        :param promoter_id: 
        :param dma_id: 
        :param include_tba: True to include events with a to-be-announced 
            date (['yes', 'no', 'only'])
        :param include_tbd: True to include an event with a date to be 
            defined (['yes', 'no', 'only'])
        :param client_visibility: 
        :param keyword: 
        :param event_id: Event ID to search 
        :param source: Filter entities by source name: ['ticketmaster', 
            'universe', 'frontgate', 'tmr']
        :param include_test: 'yes' to include test entities in the 
            response. False or 'no' to exclude. 'only' to return ONLY test 
            entities. (['yes', 'no', 'only'])
        :param page: Page number to get (default: 0)
        :param size: Size of page (default: 20)
        :param locale: Locale (default: 'en')
        :return: 
        """
        return self._get(keyword, event_id, sort, include_test, page,
                         size, locale, latlong=latlong, radius=radius,
                         unit=unit, start_date_time=start_date_time,
                         end_date_time=end_date_time,
                         onsale_start_date_time=onsale_start_date_time,
                         onsale_end_date_time=onsale_end_date_time,
                         country_code=country_code, state_code=state_code,
                         venue_id=venue_id, attraction_id=attraction_id,
                         segment_id=segment_id, segment_name=segment_name,
                         classification_name=classification_name,
                         classification_id=classification_id,
                         market_id=market_id, promoter_id=promoter_id,
                         dma_id=dma_id, include_tba=include_tba,
                         include_tbd=include_tbd, source=source,
                         client_visibility=client_visibility, **kwargs)

    def by_location(self, latitude, longitude, radius='10', unit='miles',
                    sort='relevance,desc', **kwargs):
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
        latlong = "{lat},{long}".format(lat=latitude, long=longitude)
        return self.find(latlong=latlong, radius=radius, unit=unit,
                         sort=sort, **kwargs)


class AttractionQuery(BaseQuery):
    """Query class for Attractions"""
    def __init__(self, api_client):
        self.api_client = api_client
        super().__init__(api_client, 'attractions', Attraction)

    def find(self, sort=None, keyword=None, attraction_id=None,
             source=None, include_test=None, page=None, size=None,
             locale=None, **kwargs):
        """
        :param sort: Response sort type (API default: *name,asc*)
        :param keyword: 
        :param attraction_id: 
        :param source: 
        :param include_test: Include test attractions (['yes', 'no', 'only'])
        :param page: 
        :param size: 
        :param locale: API default: *en*
        :param kwargs: 
        :return: 
        """
        return self._get(keyword, attraction_id, sort, include_test,
                         page, size, locale, source=source, **kwargs)


class ClassificationQuery(BaseQuery):
    """Classification search/query class"""
    #: Inherited method reassigned as classifications don't have IDs
    query_subclass_id = BaseQuery.by_id

    def __init__(self, api_client):
        super().__init__(api_client, 'classifications', Classification)

    def find(self, sort=None, keyword=None, classification_id=None,
             source=None, include_test=None, page=None, size=None,
             locale=None, **kwargs):
        """Search classifications

        :param sort: Response sort type (API default: *name,asc*)
        :param keyword: 
        :param classification_id: 
        :param source: 
        :param include_test: Include test classifications 
            (['yes', 'no', 'only'])
        :param page: 
        :param size: 
        :param locale: API default: *en*
        :param kwargs: 
        :return: 
        """
        return self._get(keyword, classification_id, sort, include_test,
                         page, size, locale, source=source, **kwargs)

    def by_id(self, entity_id):
        """Returns a ``Segment``, ``Genre`` or ``SubGenre`` matching the 
        given entity ID. (or ``None``)
        
        Aliased in ``ticketpy.client.ApiClient`` as 
        methods ``segment_by_id()``, ``genre_by_id()`` and 
        ``subgenre_by_id()`` although they're technically all 
        the same method.
        
        :param entity_id: Segment, genre or subgenre ID
        :return: ``Segment``, ``Genre`` or ``SubGenre``, depending which 
            matches the ID.
        """
        cl = self.query_subclass_id(entity_id)
        # No segment = no matches anywhere
        if not cl.segment:
            return None
        elif cl.segment.id == entity_id:
            return cl.segment

        # Check deeper, return whatever object matches ``entity_id``
        for genre in cl.segment.genres:
            if genre.id == entity_id:
                return genre
            for subgenre in genre.subgenres:
                if subgenre.id == entity_id:
                    return subgenre

        # Return ``None`` if one still wasn't found for some reason
        return None
