from mock import MagicMock
import unittest
from datetime import datetime
from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance
from bookied_sync.lookup import Lookup
from bookied_sync.event import LookupEvent
from bookied_sync.eventstatus import LookupEventStatus
from bookied_sync.bettingmarketgroup import LookupBettingMarketGroup
from bookied_sync.bettingmarket import LookupBettingMarket
from peerplays.bettingmarketgroup import BettingMarketGroup
from peerplays.blockchainobject import BlockchainObject, ObjectCache
from peerplays.event import Event
from bookied import exceptions
from bookied.triggers import (
    CreateTrigger,
    ResultTrigger,
    InProgressTrigger,
    FinishTrigger,
)
import bos_incidents


# Create incidents
_message_create_1 = {
    "timestamp": "2018-03-12T14:48:11.418371Z",
    "id": {
        "sport": "Basketball",
        "start_time": "2018-03-10T00:00:00Z",
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
_message_create_2 = _message_create_1.copy()
_message_create_2["provider_info"]["name"] = "foobar"
_message_create_2["unique_string"] += "foobar"

# In play incident
_message_in_play = {
    "timestamp": "2018-03-12T14:48:11.418371Z",
    "id": {"sport": "Basketball",
           "start_time": "2018-03-10T00:00:00Z",
           "away": "Chicago Bulls",
           "home": "Detroit Pistons",
           "event_group_name": "NBA Regular Season"},
    "provider_info": {"match_id": "1487207",
                      "source_file": "20180310-011131_06d6bc2c-9280-4989-b86c-9f3c9cc716ad.xml",
                      "source": "direct string input",
                      "name": "scorespro",
                      "bitArray": "00000001100",
                      "pushed": "2018-03-10T00:11:31.79Z"},
    "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-in_progress-2018-03-10t00112083z",
    "arguments": {"whistle_start_time": "2018-03-10T00:11:20.83Z"},
    "call": "in_progress"}

# Finish incident
_message_finish_1 = {
    "timestamp": "2018-03-12T14:48:11.417374Z",
    "id": {"sport": "Basketball",
           "start_time": "2018-03-10T00:00:00Z",
           "away": "Chicago Bulls",
           "home": "Detroit Pistons",
           "event_group_name": "NBA Regular Season"},
    "provider_info": {"match_id": "1487207",
                      "source_file": "20180310-031424_6a6448a1-36bf-47b3-9aca-e4f11a5ffea9.xml",
                      "source": "direct string input",
                      "name": "scorespro",
                      "bitArray": "00000000100",
                      "pushed": "2018-03-10T02:14:24.588Z"},
    "unique_string": "2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-finish-2018-03-10t021409751z",
    "arguments": {"whistle_end_time": "2018-03-10T02:14:09.751Z"},
    "call": "finish"}

_message_finish_2 = _message_finish_1.copy()
_message_finish_2["provider_info"]["name"] = "foobar"
_message_finish_2["unique_string"] += "foobar"

# Result incident
_message_result_1 = {
    "timestamp": "2018-03-12T14:48:11.419285Z",
    "id": {"sport": "Basketball",
           "start_time": "2018-03-10T00:00:00Z",
           "away": "Chicago Bulls",
           "home": "Detroit Pistons",
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
_message_result_2 = _message_result_1.copy()
_message_result_2["provider_info"]["name"] = "foobar"
_message_result_2["unique_string"] += "foobar"

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

config = dict(
    nobroadcast=True
)
lookup = Lookup(
    proposer="init0",
    keys=[wif],
    nobroadcast=config["nobroadcast"],
    num_retries=1,
)
set_shared_peerplays_instance(lookup.blockchain)


class Testcases(unittest.TestCase):

    def mockEvent(self, x, m):
        event_id = "1.18.2241"
        bm_id = "1.20.212"
        _objects = [{
            "id": event_id,
            "status": "upcoming",
            "event_group_id": "1.17.12125",
            "name": [],
            "season": [],
            "start_time": "2018-04-18T12:00:29"
        }, {
            "id": bm_id,
            'asset_id': '1.3.0',
            'delay_before_settling': 300,
            'description': [['en', 'MSeaward BMG1']],
            'event_id': '1.18.1',
            'never_in_play': False,
            'rules_id': '1.19.22',
            'settling_time': None,
            'status': 'upcoming',
            'total_matched_bets_amount': 709101
        }]

        # Inject test data into cache
        _cache = ObjectCache(default_expiration=60 * 60 * 1, no_overwrite=True)
        for i in _objects:
            _cache[i["id"]] = i
        BlockchainObject._cache = _cache

        # Do not update the event
        LookupEvent.test_operation_equal = MagicMock(return_value=True)

        LookupEventStatus.is_synced = MagicMock(return_value=False)
        x.getEvent = MagicMock(return_value=LookupEvent(
            teams=[m["id"]["home"], m["id"]["away"]],
            start_time=datetime.utcnow(),
            eventgroup_identifier=m["id"]["event_group_name"],
            sport_identifier=m["id"]["sport"],
            id=event_id,
            extra_data=dict(status="upcoming", event_id="1.214.124")
        ))

        LookupBettingMarketGroup.find_id = MagicMock(return_value=bm_id)
        BettingMarketGroup.is_synced = MagicMock(return_value=False)
        LookupBettingMarket.find_id = MagicMock(return_value="1.21.2214")

    def setUp(self):
        lookup.clear()

    """
    def test_num_retries(self):
        previous_url = lookup.blockchain.rpc.url
        print(lookup.blockchain.rpc.num_retries)
        print("=" * 80)
        lookup.blockchain.rpc.url = "wss://rpc.example.com"
        lookup.blockchain.rpc.get_objects(["2.0.0"])
        lookup.blockchain.rpc.url = previous_url
    """

    def test_dublicate_incident(self):
        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )
        create.store_incident()
        with self.assertRaises(bos_incidents.exceptions.DuplicateIncidentException):
            create.store_incident()

    def test_create(self):
        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            create.testConditions(_message_create_1.get("arguments"))

        create.storage.insert_incident(_message_create_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            create.trigger(_message_create_1.get("arguments"))

        create.storage.insert_incident(_message_create_2)
        self.assertTrue(
            create.testConditions(_message_create_1.get("arguments")))

        tx = create.trigger(_message_create_1.get("arguments"))

        ops = tx.get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) > 1)
        self.assertTrue(ops[0][1]["proposed_ops"][0]['op'][0], 56)

    def test_in_play(self):
        play = InProgressTrigger(
            _message_in_play,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        with self.assertRaises(exceptions.EventDoesNotExistException):
            play.trigger(_message_in_play.get("arguments"))

        self.assertTrue(play.testConditions())

        self.mockEvent(play, _message_in_play)

        tx = play.trigger(_message_in_play.get("arguments"))
        play.getEvent.assert_called_with()

        ops = tx.get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 1)
        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["status"],
            "in_progress")

    def test_finish(self):
        finish = FinishTrigger(
            _message_finish_1,
            lookup_instance=lookup,
            config=config,
            purge=True, mongodb="mongodbtest",
        )

        with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
            finish.trigger(_message_finish_1.get("arguments"))

        finish.storage.insert_incident(_message_finish_1)

        with self.assertRaises(exceptions.InsufficientIncidents):
            finish.trigger(_message_finish_1.get("arguments"))

        finish.storage.insert_incident(_message_finish_2)

        # with self.assertRaises(bos_incidents.exceptions.EventNotFoundException):
        self.assertTrue(finish.testConditions())

        self.mockEvent(finish, _message_finish_1)

        tx = finish.trigger(_message_finish_1.get("arguments"))
        finish.getEvent.assert_called_with()

        ops = tx.get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 1)
        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["status"],
            "finished")

    def test_result(self):
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

        self.mockEvent(result, _message_result_1)

        tx = result.trigger(_message_result_1.get("arguments"))
        result.getEvent.assert_called_with()

        ops = tx.get("operations")
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0][0], 22)
        self.assertTrue(len(ops[0][1]["proposed_ops"]) == 2)
        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["status"],
            "finished")

        self.assertEqual(
            ops[0][1]["proposed_ops"][0]['op'][1]["scores"],
            [
                int(_message_result_1["arguments"]["home_score"]),
                int(_message_result_1["arguments"]["away_score"])
            ])

        self.assertEqual(
            ops[0][1]["proposed_ops"][1]['op'][1]["resolutions"][0][1],
            "not_win",
        )
        self.assertEqual(
            ops[0][1]["proposed_ops"][1]['op'][1]["resolutions"][1][1],
            "win",
        )
