import os
import time
import unittest
import bos_incidents

from copy import deepcopy
from mock import MagicMock, PropertyMock, patch
from datetime import datetime, timedelta

from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance
from peerplays.bettingmarketgroup import BettingMarketGroup
from peerplays.blockchainobject import BlockchainObject, ObjectCache
from peerplays.event import Event

from bookied_sync.lookup import Lookup
from bookied_sync.event import LookupEvent
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.eventstatus import LookupEventStatus
from bookied_sync.bettingmarketgroup import LookupBettingMarketGroup
from bookied_sync.bettingmarket import LookupBettingMarket

from bookied import exceptions
from bookied.triggers.create import CreateTrigger
from .fixtures import fixture_data, lookup, config, receive_incident, reset_storage


class Testcases(unittest.TestCase):
    def setUp(self):
        fixture_data()
        lookup.clear()
        self.storage = reset_storage()

    def test_create(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBA Regular Season",
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-011131_06d6bc2c-9280-4989-b86c-9f3c9cc716ad.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000001100",
                "pushed": "2018-03-10T00:11:31.79Z",
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018",
            "arguments": {"season": "2017/2018"},
            "call": "create",
        }

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        event = create.getIncidentEvent()
        self.assertEqual(str(event.can_open_by), "2018-02-19 00:00:00")
        self.assertTrue(event.can_open)

    @patch(
        "bookied_sync.eventgroup.LookupEventGroup.leadtime_Max",
        PropertyMock(return_value=2),
    )
    def test_old(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBA Regular Season",
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-011131_06d6bc2c-9280-4989-b86c-9f3c9cc716ad.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000001100",
                "pushed": "2018-03-10T00:11:31.79Z",
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018",
            "arguments": {"season": "2017/2018"},
            "call": "create",
        }

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        receive_incident(_message_create_1)
        with self.assertRaises(exceptions.EventDoesNotExistException):
            create.getEvent()
        with self.assertRaises(exceptions.EventCannotOpenException):
            create.createEvent()
        with self.assertRaises(exceptions.EventCannotOpenException):
            create.getIncidentEvent()

        self.assertEqual(str(create.event.can_open_by), "2022-10-14 00:00:00")
        self.assertFalse(create.event.can_open)

        now = int(time.mktime(datetime.utcnow().timetuple()))
        expiration_time = create.event.can_open_by + timedelta(seconds=(now % 120))

        self.assertLessEqual(
            expiration_time, create.event.can_open_by + timedelta(seconds=120)
        )
        self.assertGreaterEqual(expiration_time, create.event.can_open_by)
