import unittest
import bos_incidents
from copy import deepcopy

from bookied import exceptions
from bookied.triggers.create import CreateTrigger
from bookied.triggers.result import ResultTrigger
from bookied.triggers.in_progress import InProgressTrigger
from bookied.triggers.finish import FinishTrigger
from bookied.triggers.cancel import CancelTrigger
from bookied.triggers.dynamic_bmg import DynamicBmgTrigger

from .fixtures import fixture_data, lookup, config, receive_incident, reset_storage

# import logging
# logging.basicConfig(level=logging.DEBUG)


class Testcases(unittest.TestCase):
    def setUp(self):
        fixture_data()
        lookup.clear()
        self.storage = reset_storage()

    def test_correct_proposal(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "San Antonio Spurs",
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
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["provider_info"]["name"] += "foobar"
        _message_create_2["unique_string"] += "foobar"

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        receive_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        receive_incident(_message_create_2)
        self.assertTrue(create.testConditions(_message_create_1.get("arguments")))

        tx = create.trigger(_message_create_1.get("arguments"))
        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 23)
        self.assertEqual(ops[0][1]["proposal"], "1.10.11245")
        self.assertEqual(ops[0][1]["active_approvals_to_add"][0], "1.2.7")

    def test_incomplete_proposal(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Toronto Raptors",
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
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["provider_info"]["name"] += "foobar"
        _message_create_2["unique_string"] += "foobar"

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        receive_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        receive_incident(_message_create_2)
        self.assertTrue(create.testConditions(_message_create_1.get("arguments")))

        tx = create.trigger(_message_create_1.get("arguments"))
        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 23)
        self.assertEqual(ops[0][1]["proposal"], "1.10.11246")
        self.assertEqual(ops[0][1]["active_approvals_to_add"][0], "1.2.7")

    def test_too_long_proposal(self):
        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Sacramento Kings",
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
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["provider_info"]["name"] += "foobar"
        _message_create_2["unique_string"] += "foobar"

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        receive_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        receive_incident(_message_create_2)
        self.assertTrue(create.testConditions(_message_create_1.get("arguments")))

        tx = create.trigger(_message_create_1.get("arguments"))
        self.assertFalse(bool(tx))
