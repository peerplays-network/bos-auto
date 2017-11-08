import os
import unittest
from peerplays import PeerPlays
from bookie_lookup.lookup import Lookup
from bookie_lookup.sport import LookupSport


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Lookup._clear()
        self.lookup = Lookup(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "testsports"
            ),
            peerplays_instance=PeerPlays(
                nobroadcast=True,
            )
        )

    def test_sport(self):
        self.assertIsInstance(self.lookup, dict)
        self.assertIsInstance(self.lookup.peerplays, PeerPlays)

    def test_list_sports(self):
        sports = self.lookup.list_sports()
        self.assertIsInstance(sports, list)
        for sport in sports:
            self.assertIsInstance(sport, LookupSport)
        self.assertEqual(len(sports), 1)
        self.assertEqual(sports[0]["identifier"], "AmericanFootball")

    def test_get_sport(self):
        sport = self.lookup.get_sport("AmericanFootball")
        self.assertEqual(sport["identifier"], "AmericanFootball")
        self.assertEqual(sport["id"], sport.id)
