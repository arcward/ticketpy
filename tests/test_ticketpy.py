import json
from pathlib import Path
import pytest
from ticketpy.model import Event, Venue, PageResponse


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent.absolute() / "fixtures"


@pytest.fixture
def event_response(fixture_dir):
    return json.loads((fixture_dir / "event.json").read_text())


@pytest.fixture
def event_search(fixture_dir):
    return json.loads((fixture_dir / "event_search.json").read_text())


def test_event_parsing(event_response):
    ev = Event.parse_obj(event_response)
    print(ev)
    assert ev.embedded is None
    assert ev.venues
    assert isinstance(ev.venues[0], Venue)


def test_event_search_parsing(event_search):
    pg = PageResponse.parse_obj(event_search)
    print(pg)
