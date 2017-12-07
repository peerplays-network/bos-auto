import os
import mock
import unittest
from pprint import pprint
from peerplays import PeerPlays
from bookie_lookup.lookup import Lookup
from bookie_lookup.event import LookupEvent
from bookie_lookup.bettingmarketgroupresolve import (
    LookupBettingMarketGroupResolve
)
from bookie_lookup.rule import LookupRules
import datetime


miniumum_event_dict = {
    "id": "1.18.0",
    "teams": ["Demo", "Foobar"],
    "eventgroup_identifier": "NFL#PreSeas",
    "sport_identifier": "AmericanFootball",
    "season": {"en": "2017-00-00"},
    "start_time": datetime.datetime.utcnow()
}
test_result = [2, 3]
test_operation_dicts = [
    {
        "betting_market_group_id": "AFG",
        "resolutions": [
            ["1.21.257", "win"],
            ["1.21.258", "not_win"],
            ["1.21.259", "cancel"],
        ],
    }
]
list_test_bms = [
    {"id": "1.21.257", "description": [["en", "Demo wins"]], "group_id": "1.18.0"},
    {"id": "1.21.258", "description": [["en", "Foobar wins"]], "group_id": "1.18.0"},
    {"id": "1.21.259", "description": [["en", "Draw"]], "group_id": "1.18.0"},
]
test_find_object_mock = dict(id="YYY", **test_operation_dicts[0])
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
mock_resolutions = (
    "bookie_lookup.bettingmarketgroupresolve."
    "LookupBettingMarketGroupResolve.resolutions"
)


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
        self.event = LookupEvent(**miniumum_event_dict)
        self.bmg = next(self.event.bettingmarketgroups)
        # overwrite the BMG id since we cannot look on the chain
        self.bmg["id"] = "1.20.0"

        self.lookup = LookupBettingMarketGroupResolve(
            self.bmg, test_result
        )

    def test_init(self):
        self.assertIsInstance(self.lookup, LookupBettingMarketGroupResolve)

    def test_sport(self):
        self.assertEqual(
            self.lookup.sport["identifier"],
            self.event.sport["identifier"]
        )

    def test_rules(self):
        self.assertIsInstance(
            self.lookup.rules,
            LookupRules
        )

    def test_test_operation_equal(self):
        def mock_result(*args, **kwargs):
            return test_find_object_mock["resolutions"]

        with mock.patch(
            "bookie_lookup.bettingmarketgroupresolve." +
            "LookupBettingMarketGroupResolve.resolutions",
            new_callable=mock_result
        ):
            for x in test_operation_dicts:
                self.assertTrue(self.lookup.test_operation_equal(x))

    def test_find_id(self):
        pass

    def test_is_synced(self):
        """ FIXME: We always return False because the blockchain doesn't tell
            us yet if the bmgs have already been resolved.

        """
        return False

    def test_propose_new(self):
        from peerplaysbase.operationids import operations

        def mock_result(*args, **kwargs):
            return test_find_object_mock["resolutions"]

        def mockedClass(m, *args, **kwargs):
            dict.__init__(m, {"id": "asf"})

        with mock.patch(
            mock_resolutions,
            new_callable=mock_result
        ):
            with mock.patch(
                "peerplays.bettingmarketgroup.BettingMarketGroup.refresh",
                new=mockedClass
            ):
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
        pass

    def test_resolution(self):
        def mockedClass(m, *args, **kwargs):
            list.__init__(m, list_test_bms)
        with mock.patch(
            "peerplays.bettingmarket.BettingMarkets.__init__",
            new=mockedClass
        ):
            # Away Team wins
            lookup = LookupBettingMarketGroupResolve(
                self.bmg, [2, 3]
            )
            res = lookup.resolutions
            # should be:
            #[['1.21.257', 'not_win'],
            # ['1.21.258', 'win'],
            # ['1.21.259', 'not_win']]
            self.assertEqual(res[0][1], "not_win")
            self.assertEqual(res[1][1], "win")
            self.assertEqual(res[2][1], "not_win")

            # Draw
            lookup = LookupBettingMarketGroupResolve(
                self.bmg, [3, 3]
            )
            res = lookup.resolutions
            # should be:
            #[['1.21.257', 'not_win'],
            # ['1.21.258', 'not_win'],
            # ['1.21.259', 'win']]
            self.assertEqual(res[0][1], "not_win")
            self.assertEqual(res[1][1], "not_win")
            self.assertEqual(res[2][1], "win")

            # Home Team wins
            lookup = LookupBettingMarketGroupResolve(
                self.bmg, [4, 3]
            )
            res = lookup.resolutions
            # should be:
            #[['1.21.257', 'win'],
            # ['1.21.258', 'not_win'],
            # ['1.21.259', 'not_win']]
            self.assertEqual(res[0][1], "win")
            self.assertEqual(res[1][1], "not_win")
            self.assertEqual(res[2][1], "not_win")
