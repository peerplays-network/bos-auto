import os
import unittest
import bos_incidents

from copy import deepcopy
from mock import MagicMock, PropertyMock
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

from .fixtures import fixture_data, lookup, config


class Testcases(unittest.TestCase):
    def test_create(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2014-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBA OLD"
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-011131_06d6bc2c-9280-4989-b86c-9f3c9cc716ad.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000001100",
                "pushed": "2018-03-10T00:11:31.79Z"
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018",
            "arguments": {
                "season": "2017/2018"
            },
            "call": "create"
        }

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        with self.assertRaises(exceptions.CreateIncidentTooOldException):
            create.testConditions(_message_create_1.get("arguments"))
