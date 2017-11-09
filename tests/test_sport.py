import os
import mock
import unittest
from pprint import pprint
from peerplays import PeerPlays
from bookie_lookup.lookup import Lookup
from bookie_lookup.sport import LookupSport

test_operation_dicts = [
        {
            "name": [["en", "American Football"], ["de", "Amerikanisches Football"]],
        }, {
            "name": [["de", "Amerikanisches Football"], ["en", "American Football"]],
        }
]
test_find_object_mock = dict(id="ZZZ", **test_operation_dicts[0])
test_issynced_object_mock = dict(id="ZZZ", **test_operation_dicts[0])
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
this_id = "1.16.0"
is_synced_mock = "peerplays.sport.Sport.refresh"
find_id_mock = "peerplays.sport.Sports.__init__"


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
        self.lookup = LookupSport("AmericanFootball")

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
            self.assertEqual(self.lookup.find_id(), "ZZZ")

    def test_is_synced(self):
        def mockedClass(m, *args, **kwargs):
            dict.__init__(m, test_issynced_object_mock)

        with mock.patch(
            is_synced_mock,
            new=mockedClass
        ):
            # Ensure our id is ZZZ
            tmp = self.lookup["id"]
            self.lookup["id"] = "ZZZ"
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
