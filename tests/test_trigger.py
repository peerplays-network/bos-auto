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

    def test_duplicate_incident(self):
        _message_duplicate = {
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

        receive_incident(_message_duplicate)
        CreateTrigger(
            _message_duplicate,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )
        with self.assertRaises(bos_incidents.exceptions.DuplicateIncidentException):
            receive_incident(_message_duplicate)

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
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["provider_info"]["name"] += "foobar"
        _message_create_2["unique_string"] += "foobar"

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        receive_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        receive_incident(_message_create_2)
        self.assertTrue(create.testConditions(_message_create_1.get("arguments")))

        tx = create.trigger(_message_create_1.get("arguments"))
        self.assertTrue(create.lookup.peerplays.blocking)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) > 1)
        self.assertTrue(ops[0][1]["proposed_ops"][0]["op"][0], 56)

        d = create.storage.get_event_by_id(_message_create_1)
        self.assertEqual(d["create"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["create"]["status"]["name"], "done")

    def test_in_play(self):
        # In play incident
        _message_in_play = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "home": "Atlanta Hawks",
                "away": "Boston Celtics",
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
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-in_progress-2018-03-10t00112083z",
            "arguments": {"whistle_start_time": "2018-03-10T00:11:20.83Z"},
            "call": "in_progress",
        }

        play = InProgressTrigger(
            _message_in_play,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )
        receive_incident(_message_in_play)

        self.assertTrue(play.testConditions())

        tx = play.trigger(_message_in_play.get("arguments"))

        self.assertTrue(play.lookup.peerplays.blocking)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 1)
        self.assertEqual(ops[0][1]["proposed_ops"][0]["op"][1]["status"], "in_progress")

        d = play.storage.get_event_by_id(_message_in_play)
        self.assertEqual(d["in_progress"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["in_progress"]["status"]["name"], "done")

    def test_finish(self):

        # Finish incident
        _message_finish_1 = {
            "timestamp": "2018-03-12T14:48:11.417374Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "home": "Atlanta Hawks",
                "away": "Boston Celtics",
                "event_group_name": "NBA Regular Season",
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-031424_6a6448a1-36bf-47b3-9aca-e4f11a5ffea9.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000000100",
                "pushed": "2018-03-10T02:14:24.588Z",
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-finish-2018-03-10t021409751z",
            "arguments": {"whistle_end_time": "2018-03-10T02:14:09.751Z"},
            "call": "finish",
        }

        _message_finish_2 = deepcopy(_message_finish_1)
        _message_finish_2["provider_info"]["name"] += "foobar"
        _message_finish_2["unique_string"] += "foobar"

        finish = FinishTrigger(
            _message_finish_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        receive_incident(_message_finish_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            finish.trigger(_message_finish_1.get("arguments"))

        receive_incident(_message_finish_2)

        self.assertTrue(finish.testConditions())

        tx = finish.trigger(_message_finish_1.get("arguments"))

        self.assertTrue(finish.lookup.peerplays.blocking)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 1)
        self.assertEqual(ops[0][1]["proposed_ops"][0]["op"][1]["status"], "finished")

        d = finish.storage.get_event_by_id(_message_finish_1)
        self.assertEqual(d["finish"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["finish"]["status"]["name"], "done")

    def test_result(self):
        # Result incident
        _message_result_1 = {
            "timestamp": "2018-03-12T14:48:11.419285Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "home": "Atlanta Hawks",
                "away": "Boston Celtics",
                "event_group_name": "NBA Regular Season",
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-031424_6a6448a1-36bf-47b3-9aca-e4f11a5ffea9.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000000100",
                "pushed": "2018-03-10T02:14:24.588Z",
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-result-99-83",
            "arguments": {"home_score": "99", "away_score": "83"},
            "call": "result",
        }
        _message_result_2 = deepcopy(_message_result_1)
        _message_result_2["provider_info"]["name"] += "foobar"
        _message_result_2["unique_string"] += "foobar"

        result = ResultTrigger(
            _message_result_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            result.trigger(_message_result_1.get("arguments"))

        receive_incident(_message_result_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            result.trigger(_message_result_1.get("arguments"))

        receive_incident(_message_result_2)

        # with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
        self.assertTrue(result.testConditions())

        tx = result.trigger(_message_result_1.get("arguments"))

        self.assertTrue(result.lookup.peerplays.blocking)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 2)
        self.assertEqual(ops[0][1]["proposed_ops"][0]["op"][1]["status"], "finished")

        self.assertEqual(
            ops[0][1]["proposed_ops"][0]["op"][1]["scores"],
            [
                int(_message_result_1["arguments"]["home_score"]),
                int(_message_result_1["arguments"]["away_score"]),
            ],
        )

        self.assertEqual(
            ops[0][1]["proposed_ops"][1]["op"][1]["resolutions"][0][1], "not_win"
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][1]["op"][1]["resolutions"][1][1], "win"
        )

        d = result.storage.get_event_by_id(_message_result_2)
        self.assertEqual(d["result"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["result"]["status"]["name"], "done")

    def test_cancel(self):
        _message_cancel_1 = {
            "timestamp": "2018-03-12T14:48:11.417374Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "home": "Atlanta Hawks",
                "away": "Boston Celtics",
                "event_group_name": "NBA Regular Season",
            },
            "provider_info": {
                "match_id": "1487207",
                "source_file": "20180310-031424_6a6448a1-36bf-47b3-9aca-e4f11a5ffea9.xml",
                "source": "direct string input",
                "name": "scorespro",
                "bitArray": "00000000100",
                "pushed": "2018-03-10T02:14:24.588Z",
            },
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-cancel-2018-03-10t021409751z",
            "arguments": {},
            "call": "canceled",
        }
        _message_cancel_2 = deepcopy(_message_cancel_1)
        _message_cancel_2["provider_info"]["name"] += "foobar"
        _message_cancel_2["unique_string"] += "foobar"

        cancel = CancelTrigger(
            _message_cancel_1,
            lookup_instance=lookup,
            config=config,
            storage=self.storage,
            clear_caches=False,
        )

        receive_incident(_message_cancel_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            cancel.trigger(_message_cancel_1.get("arguments"))

        receive_incident(_message_cancel_2)

        self.assertTrue(cancel.testConditions())

        tx = cancel.trigger(_message_cancel_1.get("arguments"))

        self.assertTrue(cancel.lookup.peerplays.blocking)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 1)
        self.assertEqual(ops[0][1]["proposed_ops"][0]["op"][1]["status"], "canceled")

        d = cancel.storage.get_event_by_id(_message_cancel_1)
        self.assertEqual(d["canceled"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["canceled"]["status"]["name"], "done")
