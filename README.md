# ticketpy
**Client/library for Ticketmaster's Discovery API**
http://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

#### Requirements
* Python >= 3.5.2 (anything >= 3 is probably OK)
* Requests >= 2.13.0

#### Installation
Just run `python setup.py install`

## Usage examples
### Events
To pull ~20 events for marketId 10 (Atlanta):
```python
import ticketpy

tm_client = ticketpy.ApiClient("your_api_key")
events = tm_client.events.find(market_id=10).limit(20)

    for e in events:
        print("[What/When] {} / {}".format(e.name, e.start_date))

```

Output
```
[What/When] Viva La Hop / 2017-04-07
[What/When] Gwinnett Braves vs. Durham Bulls / 2017-04-07
[What/When] Old Dominion / 2017-04-07
[What/When] Macon Mayhem vs. Roanoke Rail Yard Dawgs / 2017-04-07
[What/When] Rachmaninov / 2017-04-07
[What/When] The Young Dubliners / 2017-04-07
[What/When] The Whiskey Gentry / 2017-04-07
[What/When] Festival Of Laughs: Mike Epps, Bruce Bruce, Sommore, Arnez J / 2017-04-07
[What/When] Three Dog Night / 2017-04-07
[What/When] Permagroove and Friends / 2017-04-07
[What/When] Georgia Bulldogs v. Missouri Tigers Men's Baseball / 2017-04-08
[What/When] Gwinnett Braves vs. Durham Bulls / 2017-04-08
[What/When] Blurry / 2017-04-08
[What/When] Georgia Firebirds Vs Corpus Christi Rage / 2017-04-08
[What/When] Ron White / 2017-04-08
[What/When] Macon Mayhem vs. Roanoke Rail Yard Dawgs / 2017-04-08
[What/When] MAJIC 107.5/97.5 Presents Leela James & Daley / 2017-04-08
[What/When] JoJo - Mad Love Tour / 2017-04-08
[What/When] Duran Duran / 2017-04-08
[What/When] Glass Animals / 2017-04-08
```

### Venues
To search for all venues based on the string '*Tabernacle*':
```python
import ticketpy

tm_client = ticketpy.ApiClient("your_api_key")
venues = tm_client.venues.find(keyword="Tabernacle").all()
for v in venues:
    print("Name: {} / City: {}".format(v.name, v.city))
```

Output:
```
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
```
