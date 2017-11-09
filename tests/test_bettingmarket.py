import os
import mock
import unittest
from peerplays import PeerPlays
from peerplays.event import Event
from peerplays.eventgroup import EventGroups
from bookie_lookup.lookup import Lookup
from bookie_lookup.eventgroup import LookupEventGroup
from bookie_lookup.event import LookupEvent, MissingMandatoryValue
from bookie_lookup.bettingmarket import LookupBettingMarket
from peerplays.utils import parse_time
import datetime


miniumum_event_dict = {
    "id": "1.0.0",
    "name": {"en": "Demo vs. Foobar"},
    "teams": "Demo: Foobar",
    "eventgroup_identifier": "NFL#PreSeas",
    "sport_identifier": "AmericanFootball",
    "season": {"en": "2017-00-00"},
    "start_time": datetime.datetime.utcnow()
}
test_operation_dicts = [
    {
        "description": [["en", "Demo"]],
        "group_id": "1.18.0",
    }
]
test_find_object_mock = dict(id="XXX", **test_operation_dicts[0])
test_issynced_object_mock = dict(id="XXX", **test_operation_dicts[0])
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
this_id = "1.21.0"
is_synced_mock = "peerplays.bettingmarket.BettingMarket.refresh"
find_id_mock = "peerplays.bettingmarket.BettingMarkets.__init__"


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
        event = LookupEvent(miniumum_event_dict)
        bmg = next(event.bettingmarketgroups)
        # overwrite the BMG id since we cannot look on the chain
        bmg["id"] = "1.20.0"
        self.lookup = next(bmg.bettingmarkets)

    def test_init(self):
        self.assertIsInstance(self.lookup, LookupBettingMarket)

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

        def mockedClass(m, *args, **kwargs):
            # Make sure we can find the object that we want to replace
            dict.__init__(m, {"id": "1.21.0"})

        with mock.patch(
            is_synced_mock,
            new=mockedClass
        ):
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
