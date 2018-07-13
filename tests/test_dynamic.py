import unittest
import bos_incidents
from copy import deepcopy
from datetime import datetime, timedelta

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

    def test_dynamic_testCondition(self):
        _message = {
            "timestamp": "2018-06-26T08:39:32Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Atlanta Hawks",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-23t221000z-baseball-mlb-regular-season-cleveland-indians-detroit-tigers-dynamic_bmgs-1x2_hc--2-cleveland-indians-ou-85",
            "arguments": {
                "types": [{
                    "value": "-2",
                    "participant": "Atlanta Hawks",
                    "type": "1x2_hc"
                }, {
                    "value": "8.5",
                    "type": "ou"
                }]},
            "provider_info": {
                "name": "enetpulse",
                "beb_id": "452",
                "source_file": "20180624-000114_c7a7901b-2eae-4343-b4f7-075f0c79a067.json",
                "tzfix": True,
                "pushed": "2018-06-23T22:01:13Z",
                "source": "event_id=2663863"}}

        _message["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        trigger = DynamicBmgTrigger(_message, lookup_instance=lookup, config=config, purge=True, mongodb="mongodbtest")
        with self.assertRaises(exceptions.PostPoneIncidentException):
            trigger.testConditions()

        _message["timestamp"] = (datetime.utcnow() - timedelta(hours=0.99)).strftime("%Y-%m-%dT%H:%M:%SZ")
        trigger = DynamicBmgTrigger(_message, lookup_instance=lookup, config=config, purge=True, mongodb="mongodbtest")
        with self.assertRaises(exceptions.PostPoneIncidentException):
            trigger.testConditions()

        # With this, we are allowed to continue and the test Conditions return True
        _message["timestamp"] = (datetime.utcnow() - timedelta(hours=1.00)).strftime("%Y-%m-%dT%H:%M:%SZ")
        trigger = DynamicBmgTrigger(_message, lookup_instance=lookup, config=config, purge=True, mongodb="mongodbtest")
        self.assertTrue(trigger.testConditions())

    def test_dynamic_ou(self):
        _message = {
            "timestamp": "2018-06-26T08:39:40Z",
            "call": "dynamic_bmgs",
            "arguments": {"types": [{"value": "8",
                                     "type": "ou"}]},
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Atlanta Hawks",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-24t170500z-foobar-any-string-",
            "provider_info": {"name": "Foobar",
                              "beb_id": "464",
                              "source_file": "20180624-030031_fcdf0eb2-d303-4c26-ba5e-d98519e4d097.json",
                              "tzfix": True,
                              "pushed": "2018-06-24T01:00:29Z",
                              "source": "event_id=2663884"}}
        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 3)
        self.assertIn(
            ["en", "Over/Under 8.5 pts"],
            ops[0][1]["proposed_ops"][0]['op'][1]["description"])
        self.assertIn(
            ['en', 'Under 8.5'],
            ops[0][1]["proposed_ops"][1]['op'][1]["description"])
        self.assertIn(
            ['en', 'Over 8.5'],
            ops[0][1]["proposed_ops"][2]['op'][1]["description"])

    def test_dynamic_hc(self):
        _message = {
            "timestamp": "2018-06-26T08:39:40Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Atlanta Hawks",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-24t170500z-baseball-mlb-regular-season-boston-red-sox-seattle-mariners-dynamic_bmgs-1x2_hc--1-boston-red-sox-1x2_hc--2-boston-red-sox",
            "arguments": {
                "types": [{
                    "value": "-1",
                    "participant": "Atlanta Hawks",
                    "type": "1x2_hc"
                }, {
                    "value": "-3",
                    "participant": "Atlanta Hawks",
                    "type": "1x2_hc"
                }]},
            "provider_info": {
                "name": "foobar",
                "beb_id": "478",
                "source_file": "20180624-071904_ce6d3a22-3a94-4d00-a5df-352d1e381892.json",
                "tzfix": True,
                "pushed": "2018-06-24T05:19:02Z",
                "source": "event_id=2663884"}}

        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 3)
        # We only create one handicap market and it
        # uses median() of both proposed markets
        self.assertIn(
            ["en", 'Handicap (2:0)'],
            ops[0][1]["proposed_ops"][0]['op'][1]["description"])
        self.assertIn(
            ['en', "Atlanta Hawks (-2)"],
            ops[0][1]["proposed_ops"][1]['op'][1]["description"])
        self.assertIn(
            ['en', "Boston Celtics (2)"],
            ops[0][1]["proposed_ops"][2]['op'][1]["description"])

    def test_dynamic_hc2(self):
        """ Need to make sure we can distinguish teams when handicap is provided
        """
        _message = {
            "timestamp": "2018-06-26T08:39:40Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Atlanta Hawks",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-24t170500z-baseball-mlb-regular-season-boston-red-sox-seattle-mariners-dynamic_bmgs-1x2_hc--1-boston-red-sox-1x2_hc--2-boston-red-sox",
            "arguments": {
                "types": [{
                    "value": "-1",
                    "participant": "Atlanta Hawks",
                    "type": "1x2_hc"
                }, {
                    "value": "-3",
                    "participant": "Boston Celtics",
                    "type": "1x2_hc"
                }]},
            "provider_info": {
                "name": "foobar",
                "beb_id": "478",
                "source_file": "20180624-071904_ce6d3a22-3a94-4d00-a5df-352d1e381892.json",
                "tzfix": True,
                "pushed": "2018-06-24T05:19:02Z",
                "source": "event_id=2663884"}}

        #   -1 : +1
        #   +3 : -3  # other team!
        # = +1 : -1

        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 3)
        # We only create one handicap market and it
        # uses median() of both proposed markets
        self.assertIn(
            ["en", 'Handicap (0:1)'],
            ops[0][1]["proposed_ops"][0]['op'][1]["description"])
        self.assertIn(
            ['en', "Atlanta Hawks (1)"],
            ops[0][1]["proposed_ops"][1]['op'][1]["description"])
        self.assertIn(
            ['en', "Boston Celtics (-1)"],
            ops[0][1]["proposed_ops"][2]['op'][1]["description"])

    def test_dynamic_hcou(self):
        _message = {
            "timestamp": "2018-06-26T08:39:32Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Atlanta Hawks",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-23t221000z-baseball-mlb-regular-season-cleveland-indians-detroit-tigers-dynamic_bmgs-1x2_hc--2-cleveland-indians-ou-85",
            "arguments": {
                "types": [{
                    "value": "-2",
                    "participant": "Atlanta Hawks",
                    "type": "1x2_hc"
                }, {
                    "value": "8.5",
                    "type": "ou"
                }]},
            "provider_info": {
                "name": "enetpulse",
                "beb_id": "452",
                "source_file": "20180624-000114_c7a7901b-2eae-4343-b4f7-075f0c79a067.json",
                "tzfix": True,
                "pushed": "2018-06-23T22:01:13Z",
                "source": "event_id=2663863"}}

        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 6)
        self.assertIn(
            ["en", 'Handicap (2:0)'],
            ops[0][1]["proposed_ops"][0]['op'][1]["description"])
        self.assertIn(
            ['en', "Atlanta Hawks (-2)"],
            ops[0][1]["proposed_ops"][1]['op'][1]["description"])
        self.assertIn(
            ['en', "Boston Celtics (2)"],
            ops[0][1]["proposed_ops"][2]['op'][1]["description"])
        self.assertIn(
            ["en", "Over/Under 8.5 pts"],
            ops[0][1]["proposed_ops"][3]['op'][1]["description"])
        self.assertIn(
            ['en', 'Under 8.5'],
            ops[0][1]["proposed_ops"][4]['op'][1]["description"])
        self.assertIn(
            ['en', 'Over 8.5'],
            ops[0][1]["proposed_ops"][5]['op'][1]["description"])

    # Test to ensure we don't publish two OUs
    def test_dynamic_ou_nohc(self):
        _message = {
            "timestamp": "2018-06-26T08:39:32Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Brooklyn Nets",
                   "away": "Boston Celtics",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "2018-06-23t221000z-baseball-mlb-regular-season-cleveland-indians-detroit-tigers-dynamic_bmgs-1x2_hc--2-cleveland-indians-ou-85",
            "arguments": {
                "types": [{
                    "value": "-2",
                    "participant": "Brooklyn Nets",
                    "type": "1x2_hc"
                }, {
                    "value": "9",
                    "type": "ou"
                }]},
            "provider_info": {
                "name": "enetpulse",
                "beb_id": "452",
                "source_file": "20180624-000114_c7a7901b-2eae-4343-b4f7-075f0c79a067.json",
                "tzfix": True,
                "pushed": "2018-06-23T22:01:13Z",
                "source": "event_id=2663863"}}

        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 3)
        self.assertIn(
            ["en", "Over/Under 9.5 pts"],
            ops[0][1]["proposed_ops"][0]['op'][1]["description"])
        self.assertIn(
            ['en', 'Under 9.5'],
            ops[0][1]["proposed_ops"][1]['op'][1]["description"])
        self.assertIn(
            ['en', 'Over 9.5'],
            ops[0][1]["proposed_ops"][2]['op'][1]["description"])

    def test_dynamic_ou_fuzzy(self):
        """ Let's test fuzzy matching logic for updating/creating a BMG

            There is a proposal for a BMG with overunder 3.5 on chain already!
        """
        _message = {
            "timestamp": "2018-06-26T08:39:32Z",
            "call": "dynamic_bmgs",
            "id": {"sport": "Basketball",
                   "start_time": "2022-10-16T00:00:00Z",
                   "home": "Cleveland Cavaliers",
                   "away": "Dallas Mavericks",
                   "event_group_name": "NBA Regular Season"},
            "unique_string": "not-so-unique",
            "arguments": {
                "types": [{
                    "value": "3.5",
                    "type": "ou"
                }]},
            "provider_info": {
                "name": "",
                "beb_id": "452",
                "source_file": "20180624-000114_c7a7901b-2eae-4343-b4f7-075f0c79a067.json",
                "tzfix": True,
                "pushed": "2018-06-23T22:01:13Z",
                "source": "event_id=2663863"}}

        trigger = DynamicBmgTrigger(
            _message,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        trigger.storage.insert_incident(_message)
        tx = trigger.trigger(_message.get("arguments"))
        self.assertEqual(len(tx), 1)
        self.assertTrue(tx[0].is_approval())
