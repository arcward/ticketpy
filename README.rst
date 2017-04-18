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
If you wanted to query for information on *Shaky Beats Music Festival*:

.. code-block:: python

    import ticketpy

    tm_client = ticketpy.ApiClient('your_api_key')
    events = tm_client.events.find(keyword="Shaky Beats").all()
    tmpl = "{date}: {event_name} at {venues}: {attractions}\n"
        for event in events:
            print(tmpl.format(date=event.dates.start.local_date,
                              event_name=event.name,
                              venues=event.venues,
                              attractions=event.attractions))

Output::

    2017-05-05: Shaky Beats Music Festival at [Centennial Park-Atlanta]:
    [Unknown]

    2017-05-05: Shaky Beats Music Festival at [Centennial Olympic Park]:
    [Shaky Beats Music Festival, The Chainsmokers, Kaskade, Griz,
    Flosstradamus, Zeds Dead, Galantis, RL Grime, Girl Talk, Gramatik,
    Bonobo, Alison Wonderland, Flatbush Zombies, Getter, Little Dragon,
    Claude VonStroke, Snails, Slander, Slushii, Lost Kings, Ephwurd,
    Party Favor, Mija, Pouya, Rezz, Haywyre, Boombox Cartel, Joyryde, VANIC,
    Mutemath, Ganja White Night, Loudpvck, Crywolf, Grandtheft, Ekali,
    Bad Royale, Said the Sky, Mayhem, Echos, Young Bombs, Kaido, Cid,
    Armnhmr, Wingtip, Modern Measure, Mantis, Illenium]


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
            print("{}: {}\n".format(event.name, event.attractions))

Output::

    Atlanta Funk Fest 2017 Fri/sun Combo Ticket: [Erykah Badu, Ro James,
    Digable Planets, Kenny 'Babyface' Edmonds, Brandy, Joe]

    Atlanta Funk Fest 2017: [Erykah Badu, Ro James, Digable Planets]

    Atlanta Funk Fest 2017 3 Day Ticket: [Erykah Badu, Ro James,
    Digable Planets, Bell Biv Devoe, Guy, Teddy Riley, SWV, Mystikal,
    En Vogue, Kenny 'Babyface' Edmonds, Brandy, Joe]

    Atlanta Funk Fest 2017: [Bell Biv Devoe, Guy, Teddy Riley, SWV, Mystikal,
    En Vogue]


Calling ``ApiClient.find()`` returns a ``ticketpy.PagedResponse``
object. Iterating through a ``PagedResponse`` will make an API request for
each subsequent page until there are no pages left, or you break the loop.

To return a flat list of results from each page, use ``ApiClient.one()``,
``ApiClient.limit()`` or ``ApiClient.all()``.

* ``ApiClient.one()`` returns objects from the first page result.
* ``ApiClient.limit(max_pages)`` returns objects from the first *X* pages.
* ``ApiClient.all()`` returns objects from every available page
    (**Careful**: Generic searches return *a lot* of pages...)

The previous example could also be written with ``limit()``:

.. code-block:: python

    events = tm_client.events.find(
            classification_name='Hip-Hop',
            state_code='GA',
            start_date_time='2017-05-19T20:00:00Z',
            end_date_time='2017-05-21T20:00:00Z'
        ).limit()
        for e in events:
            print("{}: {}\n".format(e.name, e.attractions))

The output here would be the same as there was <1 page available, however,
this can save you some wasted API calls for large result sets.

Venues
^^^^^^
To _search for all venues based on the string "*Tabernacle*":

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
Classifications don't have IDs, so querying with
``ApiClient.classifications.by_id()`` will return an entire
``Classification`` object (containing whatever segment/genre/subgenre
matches that ID), rather than a ``Segment``, ``Genre`` or ``Subgenre``.

This can be helpful if you have an object ID and want to find out
what it belongs to/any children it has. For example, to query a
``Segment`` ID and print its genre/subgenre:

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

To query for a specific segment, genre or subgenre, use
``segment_by_id()``, ``genre_by_id()`` or ``subgenre_by_id()``.
Each will return *only* their respective object upon finding a
match. For example, this would just print '*Jazz*'
without having to look throughout a ``Classification`` object:

.. code-block:: python

    genre = tm_client.genre_by_id('KnvZfZ7vAvE')
    print(genre)

An ``ApiException`` is raised if the ID doesn't belong to anything (404).