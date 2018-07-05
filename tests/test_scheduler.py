import os
import unittest
import bos_incidents

from copy import deepcopy
from mock import MagicMock, PropertyMock
from rq import use_connection, Queue
from datetime import datetime, timedelta

from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance

from bookied_sync.lookup import Lookup
from bookied_sync.event import LookupEvent

from bookied import exceptions
from bookied.triggers.create import CreateTrigger

from .fixtures import fixture_data, lookup, config


class Testcases(unittest.TestCase):

    def mockEvent(self, x=False):
        # Do not update the event
        LookupEvent.can_open = PropertyMock(return_value=x)
        LookupEvent.can_open_by = PropertyMock(
            return_value=(datetime.utcnow() - timedelta(minutes=1)))

    def setUp(self):
        fixture_data()
        lookup.clear()

    def test_create(self):

        # Create incidents
        _message_create_1 = {
            "timestamp": "2018-03-12T14:48:11.418371Z",
            "id": {
                "sport": "Basketball",
                "start_time": "2022-10-16T00:00:00Z",
                "away": "Chicago Bulls",
                "home": "Detroit Pistons",
                "event_group_name": "NBA Regular Season"
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
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["provider_info"]["name"] = "foobar"
        _message_create_2["unique_string"] += "foobar"

        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )
        from bookied import schedule

        self.mockEvent()

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        create.storage.insert_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        create.storage.insert_incident(_message_create_2)
        self.assertTrue(
            create.testConditions(_message_create_1.get("arguments")))

        with self.assertRaises(exceptions.EventCannotOpenException):
            create.trigger(_message_create_1.get("arguments"))

        # From here on, we should have a 'postponed' incident in database

        events = create.storage.get_events_by_call_status(
            call="create",
            status_name="postponed",
            status_expired_before=datetime.utcnow())
        events = list(events)

        self.assertEqual(len(events), 1)

        class MockReturn:
            id = "foobar"

        Queue.enqueue = MagicMock(return_value=MockReturn)

        ret = schedule.check_scheduled(create.storage, func_callback=print)

        self.assertIn("foobar", ret)
        self.assertTrue(Queue.enqueue.called)

        self.mockEvent(True)

        tx = create.trigger(_message_create_1.get("arguments"))

        ops = tx[0].get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) > 1)
        self.assertTrue(ops[0][1]["proposed_ops"][0]['op'][0], 56)
