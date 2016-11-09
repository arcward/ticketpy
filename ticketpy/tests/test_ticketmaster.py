from unittest import TestCase
from ticketpy.ticketmaster import Ticketmaster


class TestTicketmaster(TestCase):
    def test_events(self):
        tm = Ticketmaster()
        tm.events('KovZpaFEZe', 7)