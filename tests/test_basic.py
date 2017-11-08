import os
import unittest
from pprint import pprint
from peerplays import PeerPlays
from bookie_lookup.lookup import Lookup, SportsNotFoundError


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Lookup._clear()
        self.lookup = Lookup(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "testsports"
            ),
            peerplays_instance=PeerPlays(nobroadcast=True)
        )

    def test_lookup(self):
        self.assertIsInstance(self.lookup, dict)
        self.assertIsInstance(self.lookup.peerplays, PeerPlays)
        self.assertTrue(self.lookup.peerplays.nobroadcast)

        self.assertIn("sports", self.lookup.data)
        self.assertTrue(self.lookup.data["sports"])

    def test_proper_accounts(self):
        lookup = Lookup(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "testsports"
            ),
            proposing_account="init0",
            approving_account="init1",
        )
        self.assertEqual(lookup.approving_account, "init1")
        self.assertEqual(lookup.proposing_account, "init0")

        with self.assertRaises(SportsNotFoundError):
            Lookup._clear()
            Lookup("/tmp/random-non-exiting-sport")
            Lookup._clear()
