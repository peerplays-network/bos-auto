import os
import mock
import unittest
from peerplays import PeerPlays
from bookie_lookup.lookup import Lookup
from bookie_lookup.sport import LookupSport
from peerplaysbase.operationids import operations


wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"


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

    def setUp(self):
        self.lookup.clear_proposal_buffer()
        self.lookup.clear_direct_buffer()

    def test_search_pending_props(self):
        # Proposal creation
        self.lookup.propose_new()

        props = Lookup.proposal_buffer.json()
        self.assertIsInstance(props, list)
        self.assertIsInstance(props[1], dict)
        self.assertEqual(props[0], 22)
        proposed_op = props[1]["proposed_ops"][0]["op"]
        self.assertEqual(proposed_op[0], operations[self.lookup.operation_create])

        # The id as defined in the yaml file has priority
        self.assertEqual(self.lookup.id, "1.16.0")

        # Let's remove the id from the yaml file to load from chain
        self.lookup.pop("id", None)
        self.assertEqual(self.lookup.id, "1.16.0")

        # Let's also remove the id from chain to look into proposal buffer
        def mockedClass(m, *args, **kwargs):
            return False

        with mock.patch(
            "bookie_lookup.sport.LookupSport.find_id",
            new=mockedClass
        ):
            self.lookup.pop("id", None)
            self.assertEqual(self.lookup.id, "0.0.0")
