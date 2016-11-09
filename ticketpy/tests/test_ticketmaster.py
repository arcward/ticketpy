from unittest import TestCase
from ticketpy.ticketmaster import Ticketmaster
from configparser import ConfigParser
import os

class TestTicketmaster(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
        api_key = config.get('ticketmaster', 'api_key')
        self.tm = Ticketmaster(api_key)
    
    def test_events(self):
        elist = self.tm.events('KovZpaFEZe', size=7)
        print(elist)