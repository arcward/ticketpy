ticketpy
========

**Client/library for Ticketmaster's Discovery API**

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

Quickstart/examples
-------------------

Events
^^^^^^
To pull all Hip-Hop events in Georgia between May 19th, 2017 and
May 21st, 2017:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient('your_api_key')

    pages = self.tm.events.find(
        classification_name='Hip-Hop',
        state_code='GA',
        start_date_time='2017-05-19T20:00:00Z',
        end_date_time='2017-05-21T20:00:00Z'
    )

    for page in pages:
        for event in page:
            print(event)

Output::

    Event:        Atlanta Funk Fest 2017 3 Day Ticket
    Venue(s):     'Wolf Creek Amphitheater' at 3025 Merk Road in Atlanta GA
    Start date:   2017-05-19
    Start time:   19:00:00
    Price ranges: 128.01-424.0
    Status:       onsale
    Genres:       R&B

    Event:        Atlanta Funk Fest 2017
    Venue(s):     'Wolf Creek Amphitheater' at 3025 Merk Road in Atlanta GA
    Start date:   2017-05-19
    Start time:   19:00:00
    Price ranges: 63.0-158.0
    Status:       onsale
    Genres:       R&B

    Event:        Atlanta Funk Fest 2017
    Venue(s):     'Wolf Creek Amphitheater' at 3025 Merk Road in Atlanta GA
    Start date:   2017-05-20
    Start time:   17:00:00
    Price ranges: 63.0-158.0
    Status:       onsale
    Genres:       Hip-Hop/Rap

    Event:        NF
    Venue(s):     'Center Stage Theater' at 1374 W Peachtree St. NW in Atlanta GA
    Start date:   2017-05-20
    Start time:   20:00:00
    Price ranges: 22.0-83.0
    Status:       onsale
    Genres:       Hip-Hop/Rap

Calling ``ApiClient.find()`` returns a ``ticketpy.PageIterator``
object, which iterates through API response pages (as ``ticketpy.Page``).

By default, pages have 20 elements. If there are >20 total elements,
calling ``PageIterator.next()`` will request the next page from the API.

You can simplify that/do away with the nested loop by using
``PageIterator.limit()``. By default, this requests a maximum of 10 pages,
and returns the elements of each in a flat list.

For example, the previous example could also be written as:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient('your_api_key')

    pages = self.tm.events.find(
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
