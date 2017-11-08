import os
import mock
import unittest
from pprint import pprint
from peerplays import PeerPlays
from peerplays.event import Event
from peerplays.eventgroup import EventGroups
from bookie_lookup.lookup import Lookup
from bookie_lookup.eventgroup import LookupEventGroup
from bookie_lookup.event import LookupEvent, MissingMandatoryValue
from peerplays.utils import parse_time
import datetime

miniumum_init_dict = {
    "name": {"en": "Demo vs. Foobar"},
    "teams": "Demo: Foobar",
    "eventgroup_identifier": "NFL#PreSeas",
    "sport_identifier": "AmericanFootball",
    "season": {"en": "2017-00-00"},
    "start_time": datetime.datetime.utcnow()
}
test_operation_dicts = [
    {
        "name": [["en", "Demo vs. Foobar"]],
        "event_group_id": "1.17.16",
        "season": [["en", "2017-00-00"]],
        "start_time": parse_time("2017-09-04T08:00:00")
    }
]
test_find_object_mock = dict(id="XXX", **test_operation_dicts[0])
test_issynced_object_mock = dict(id="XXX", **test_operation_dicts[0])
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
this_id = "1.18.0"
is_synced_mock = "peerplays.event.Event.refresh"
find_id_mock = "peerplays.event.Events.__init__"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Lookup._clear()
        Lookup(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "testsports"
            ),
            peerplays_instance=PeerPlays(
                nobroadcast=True,
                wif=[wif]   # ensure we can sign
            )
        )
        self.lookup = LookupEvent(miniumum_init_dict)

    def test_eventgroup(self):

        self.assertIsInstance(self.lookup, dict)
        self.assertIsInstance(self.lookup.peerplays, PeerPlays)
        self.assertEqual(self.lookup["name"]["en"], miniumum_init_dict["name"]["en"])

        def mockedClass(m, *args, **kwargs):
            dict.__init__(m, {
            "name": [["en", "NFL - Pre-Season"], ["de", "NFL - Vorseason"]],
            "sport_id": "1.16.0"
        })

        with mock.patch(
            "peerplays.eventgroup.EventGroup.refresh",
            new=mockedClass
        ):
            self.assertTrue(self.lookup.parent)
            self.assertTrue(self.lookup.parent_id)
            self.assertEqual(self.lookup.parent["id"], self.lookup.parent_id)

    def test_test_operation_equal(self):
        for x in test_operation_dicts:
            self.assertTrue(self.lookup.test_operation_equal(x))

        with self.assertRaises(ValueError):
            self.assertTrue(self.lookup.test_operation_equal({}))

    def test_find_id(self):
        def mockedClass(m, *args, **kwargs):
            list.__init__(m, [test_find_object_mock])

        with mock.patch(
            find_id_mock,
            new=mockedClass
        ):
            self.assertEqual(self.lookup.find_id(), "XXX")

    def test_is_synced(self):
        def mockedClass(m, *args, **kwargs):
            dict.__init__(m, test_issynced_object_mock)

        with mock.patch(
            is_synced_mock,
            new=mockedClass
        ):
            # Ensure our id is XXX
            tmp = self.lookup.get("id", None)
            self.lookup["id"] = "XXX"
            self.assertTrue(self.lookup.is_synced())
            self.lookup["id"] = tmp

    def test_propose_new(self):
        from peerplaysbase.operationids import operations
        self.lookup.clear_proposal_buffer()
        tx = self.lookup.propose_new()
        tx = tx.json()
        self.assertIsInstance(tx, dict)
        self.assertIn("operations", tx)
        self.assertIn("ref_block_num", tx)
        self.assertEqual(tx["operations"][0][0], 22)
        self.assertEqual(
            tx["operations"][0][1]["proposed_ops"][0]["op"][0],
            operations[self.lookup.operation_create]
        )

    def test_propose_update(self):
        from peerplaysbase.operationids import operations
        self.lookup["id"] = this_id
        self.lookup.clear_proposal_buffer()
        tx = self.lookup.propose_update()
        tx = tx.json()
        self.assertIsInstance(tx, dict)
        self.assertIn("operations", tx)
        self.assertIn("ref_block_num", tx)
        self.assertEqual(tx["operations"][0][0], 22)
        self.assertEqual(
            tx["operations"][0][1]["proposed_ops"][0]["op"][0],
            operations[self.lookup.operation_update]
        )

    def test_init(self):
        self.assertIsInstance(self.lookup, LookupEvent)
        self.assertIsInstance(LookupEvent({
            "name": {"en": "Demo Event"},
            "teams": "Demo : Foobar",
            "eventgroup_identifier": "NFL#PreSeas",
            "sport_identifier": "AmericanFootball",
            "season": "2017-00-00",
            "start_time": datetime.datetime.utcnow()
        }), LookupEvent)

        with self.assertRaises(MissingMandatoryValue):
            self.assertIsInstance(LookupEvent({
                "teams": "Demo : Foobar",
                "eventgroup_identifier": "NFL#PreSeas",
                "sport_identifier": "AmericanFootball",
                "season": "2017-00-00",
                "start_time": datetime.datetime.utcnow()
            }), LookupEvent)

        with self.assertRaises(MissingMandatoryValue):
            self.assertIsInstance(LookupEvent({
                "name": {"en": "Demo Event"},
                "eventgroup_identifier": "NFL#PreSeas",
                "sport_identifier": "AmericanFootball",
                "season": "2017-00-00",
                "start_time": datetime.datetime.utcnow()
            }), LookupEvent)

        with self.assertRaises(MissingMandatoryValue):
            self.assertIsInstance(LookupEvent({
                "name": {"en": "Demo Event"},
                "teams": "Demo : Foobar",
                "sport_identifier": "AmericanFootball",
                "season": "2017-00-00",
                "start_time": datetime.datetime.utcnow()
            }), LookupEvent)

        with self.assertRaises(MissingMandatoryValue):
            self.assertIsInstance(LookupEvent({
                "name": {"en": "Demo Event"},
                "teams": "Demo : Foobar",
                "eventgroup_identifier": "NFL#PreSeas",
                "season": "2017-00-00",
                "start_time": datetime.datetime.utcnow()
            }), LookupEvent)

        with self.assertRaises(MissingMandatoryValue):
            self.assertIsInstance(LookupEvent({
                "name": {"en": "Demo Event"},
                "teams": "Demo : Foobar",
                "eventgroup_identifier": "NFL#PreSeas",
                "sport_identifier": "AmericanFootball",
                "start_time": datetime.datetime.utcnow()
            }), LookupEvent)

        with self.assertRaises(ValueError):
            self.assertIsInstance(LookupEvent({
                "name": {"en": "Demo Event"},
                "teams": "Demo : Foobar",
                "eventgroup_identifier": "NFL#PreSeas",
                "sport_identifier": "AmericanFootball",
                "season": "2017-00-00",
                "start_time": "Foobar"
            }), LookupEvent)

        self.assertIsInstance(self.lookup["teams"], list)
        self.assertEqual(self.lookup["teams"][0], "Demo")
        self.assertEqual(self.lookup["teams"][1], "Foobar")
