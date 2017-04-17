ticketpy
========

**Python wrapper/SDK for Ticketmaster's Discovery API**

More info:
http://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

Requirements
------------

-  Python >= 3.5.2 (anything >= 3 is probably OK)
-  Requests >= 2.13.0

Installation
------------
To install via *pip*:

.. code-block:: bash

    $ pip install ticketpy

Or, locally from the same directory as ``setup.py``:

.. code-block:: bash

    $ python setup.py install

Example searches
-------------------

Events
^^^^^^
To pull all Hip-Hop events in Georgia between May 19th, 2017 and
May 21st, 2017:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient('your_api_key')

    pages = tm_client.events.find(
        classification_name='Hip-Hop',
        state_code='GA',
        start_date_time='2017-05-19T20:00:00Z',
        end_date_time='2017-05-21T20:00:00Z'
    )

    for page in pages:
        for event in page:
            print(event.name)

Output::

    Event:            Atlanta Funk Fest 2017 Fri/sun Combo Ticket
    Venues:           [Wolf Creek Amphitheater at 3025 Merk Road in Atlanta GA]
    Start date:       2017-05-19
    Start time:       19:00:00
    Price ranges:     [{'min': 88.0, 'max': 275.0}]
    Status:           onsale
    Classifications:  [Segment: Music / Genre: R&B / Subgenre: R&B / Type: Undefined / Subtype: Undefined]

    Event:            Atlanta Funk Fest 2017
    Venues:           [Wolf Creek Amphitheater at 3025 Merk Road in Atlanta GA]
    Start date:       2017-05-19
    Start time:       19:00:00
    Price ranges:     [{'min': 63.0, 'max': 158.0}]
    Status:           onsale
    Classifications:  [Segment: Music / Genre: R&B / Subgenre: R&B / Type: Undefined / Subtype: Undefined]

    Event:            Atlanta Funk Fest 2017 3 Day Ticket
    Venues:           [Wolf Creek Amphitheater at 3025 Merk Road in Atlanta GA]
    Start date:       2017-05-19
    Start time:       19:00:00
    Price ranges:     [{'min': 128.01, 'max': 424.0}]
    Status:           onsale
    Classifications:  [Segment: Music / Genre: R&B / Subgenre: R&B / Type: Undefined / Subtype: Undefined]

    Event:            Atlanta Funk Fest 2017
    Venues:           [Wolf Creek Amphitheater at 3025 Merk Road in Atlanta GA]
    Start date:       2017-05-20
    Start time:       17:00:00
    Price ranges:     [{'min': 63.0, 'max': 158.0}]
    Status:           onsale
    Classifications:  [Segment: Music / Genre: Hip-Hop/Rap / Subgenre: Urban / Type: Undefined / Subtype: Undefined]

    Event:            NF
    Venues:           [Center Stage Theater at 1374 W Peachtree St. NW in Atlanta GA]
    Start date:       2017-05-20
    Start time:       20:00:00
    Price ranges:     [{'min': 22.0, 'max': 83.0}]
    Status:           onsale
    Classifications:  [Segment: Music / Genre: Hip-Hop/Rap / Subgenre: Urban / Type: Undefined / Subtype: Undefined]

Calling ``ApiClient.find()`` returns a ``ticketpy.PagedResponse``
object, which iterates through API response pages (as ``ticketpy.Page``).

By default, pages have 20 elements. If there are >20 total elements,
calling ``PagedResponse.next()`` will request the next page from the API.

You can simplify that/do away with the nested loop by using
``PagedResponse.limit()``. By default, this requests a maximum of 5 pages,
and returns the elements of each in a flat list.

Use ``PagedResponse.one()`` to return just the list from the first page.

For example, the previous example could also be written as:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient('your_api_key')

    pages = tm_client.events.find(
        classification_name='Hip-Hop',
        state_code='GA',
        start_date_time='2017-05-19T20:00:00Z',
        end_date_time='2017-05-21T20:00:00Z'
    ).limit()

    for event in pages:
        print(event)

The output here would be the same as there was <1 page available, however,
this can save you some wasted API calls for large result sets. If you
really want *every page*, though, use ``all()`` to request every available
page.

Venues
^^^^^^
To search for all venues based on the string "*Tabernacle*":

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient("your_api_key")
    venues = tm_client.venues.find(keyword="Tabernacle").all()
    for v in venues:
        print("Name: {} / City: {}".format(v.name, v.city))

Output::

    Name: Tabernacle / City: London
    Name: The Tabernacle / City: Atlanta
    Name: Tabernacle, Notting Hill / City: London
    Name: Bethel Tabernacle / City: Penticton
    Name: Revivaltime Tabernacle / City: Toronto
    Name: Auckland Baptist Tabernacle / City: Auckland
    Name: Pentecostal Tabernacle / City: Nashville
    Name: The Tabernacle / City: Oak Bluffs
    Name: Tabernacle, Shoreditch / City: London
    Name: Revivaltime Tabernacle / City: Toronto
    Name: Tabernacle, Notting Hill / City: London
    Name: The Tabernacle / City: London
    Name: Tabernacle Junction / City: Yeovil
    Name: New Tabernacle 4th Baptist Church / City: Charleston

Attractions
^^^^^^^^^^^
Searching for attractions works similarly to the above:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient("your_api_key")
    attractions = tm_client.attractions.find(keyword="Yankees").one()
    for attr in attractions:
        print(attr.name)

Output::

    New York Yankees
    Scranton Wilkes-Barre RailRiders
    Staten Island Yankees
    Yankee Stadium Tours
    Tampa Yankees
    New York Yankees  Bomber Bucks
    Hands On History At Yankee Stadium
    Damn Yankees
    Damn Yankees
    Battle Creek Yankees
    New York Yankees Parking
    Offsite Parking at Yankee Stadium
    Quikpark at Yankee Stadium- NYCFC
    New York Yankees Fan Fest
    New York Yankees 3 (Do Not Use)
    New York Yankees 1 (Do Not Use)
    New York Yankees 2 (Do Not Use)
    Behind the Scenes At Yankee Stadium

Classifications
^^^^^^^^^^^^^^^
Classifications don't have IDs, so querying with ``classifications.by_id()``
will return a ``Classification`` object containing a segment, genre,
or subgenre with a matching ID. This can be helpful if you need to figure
out the parent genre/segment for a subgenre. For example:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient("your_api_key")
    classification = tm_client.classifications.by_id('KZazBEonSMnZfZ7vkdl')
    print(classification.segment)
    for genre in classification.segment.genres:
        print('-{}'.format(genre))
        for subgenre in genre.subgenres:
            print('--{}'.format(subgenre))

Output::

    Music
    -Jazz
    --Bebop

To query for a specific segment, genre or subgenre by ID, use
``segment_by_id()``, ``genre_by_id()`` or ``subgenre_by_id()``.
Each will return *only* their respective object upon finding a
match (or *None*). For example, this would just print '*Jazz*'
without having to look throughout a ``Classification`` object:

.. code-block:: python

    genre = tm_client.genre_by_id('KnvZfZ7vAvE')
    print(genre)


