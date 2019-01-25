import os
import unittest
from copy import deepcopy
from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance
from bookied_sync.lookup import Lookup
from bookiesports.normalize import NotNormalizableException
from bookied.triggers.create import CreateTrigger
from .fixtures import fixture_data, lookup, config, storage, factory


class Testcases(unittest.TestCase):
    def setUp(self):
        fixture_data()
        self.storage = factory.get_incident_storage("mongodbtest", purge=True)

    def test_normalize_incident(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBAREGULARSEASON",
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
            purge=True,
            mongodb="mongodbtest",
        )
        self.assertEqual(create.message["id"]["event_group_name"], "NBA Regular Season")

    def test_unnormalize_incident(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBAREGULARSEASON",
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

        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["id"]["event_group_name"] = "Foobar"
        storage.insert_incident(_message_create_2)

        with self.assertRaises(NotNormalizableException):
            create = CreateTrigger(
                _message_create_2,
                lookup_instance=lookup,
                config=config,
                storage=self.storage,
                purge=True,
                mongodb="mongodbtest",
            )

        event = storage.get_event_by_id(_message_create_2)
        self.assertEqual(event["create"]["status"]["name"], "not normalizable")
