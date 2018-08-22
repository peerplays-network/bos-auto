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

from .fixtures import fixture_data, lookup, config
# import logging
# logging.basicConfig(level=logging.DEBUG)


class Testcases(unittest.TestCase):

    def setUp(self):
        fixture_data()
        lookup.clear()

    def test_result(self):
        # Result incident
        _message_result_1 = {
            "timestamp": "2018-03-12T14:48:11.419285Z",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Utah Jazz",
                   "away": "Toronto Raptors",
                   "event_group_name": "NBA Regular Season"},
            "provider_info": {"match_id": "1487207",
                              "source_file": "20180310-031424_6a6448a1-36bf-47b3-9aca-e4f11a5ffea9.xml",
                              "source": "direct string input",
                              "name": "scorespro",
                              "bitArray": "00000000100",
                              "pushed": "2018-03-10T02:14:24.588Z"},
            "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-result-99-83",
            "arguments": {"home_score": "99",
                          "away_score": "83"},
            "call": "result"}
        _message_result_2 = deepcopy(_message_result_1)
        _message_result_2["provider_info"]["name"] += "foobar"
        _message_result_2["unique_string"] += "foobar"

        result = ResultTrigger(
            _message_result_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            result.trigger(_message_result_1.get("arguments"))

        result.storage.insert_incident(_message_result_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            result.trigger(_message_result_1.get("arguments"))

        result.storage.insert_incident(_message_result_2)

        # with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
        self.assertTrue(result.testConditions())

        tx = result.trigger(_message_result_1.get("arguments"))

        from pprint import pprint
        pprint(tx)

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        # 4 Ops
        # - status update to finished
        # - resolve moneyline
        # - resolve handicap
        # - resolve overunder
        self.assertEqual(len(ops[0][1]["proposed_ops"]), 4)
        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["status"],
            "finished")

        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["scores"],
            [
                int(_message_result_1["arguments"]["home_score"]),
                int(_message_result_1["arguments"]["away_score"])
            ])

        # Moneyline
        self.assertEqual(
            ops[0][1]["proposed_ops"][1]['op'][1]["resolutions"][0],
            ["1.21.2960", "win"],
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][1]['op'][1]["resolutions"][1],
            ["1.21.2961", "not_win"],
        )

        ## Dynamic BMGs!!
        self.assertEqual(
            ops[0][1]["proposed_ops"][2]['op'][1]["resolutions"][0],
            ["1.21.2974", "win"],
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][2]['op'][1]["resolutions"][1],
            ["1.21.2975", "not_win"],
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][3]['op'][1]["resolutions"][0],
            ["1.21.2972", "not_win"],
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][3]['op'][1]["resolutions"][1],
            ["1.21.2973", "win"],
        )

        d = result.storage.get_event_by_id(_message_result_2)
        self.assertEqual(d["result"]["status"]["actions"][0], "proposal")
        self.assertEqual(d["result"]["status"]["name"], "done")
