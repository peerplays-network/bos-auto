import os
import unittest

from copy import deepcopy

from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance

from bookied_sync.lookup import Lookup

from bookiesports.normalize import NotNormalizableException

from bos_incidents import factory

from bookied.triggers import (
    CreateTrigger,
)


# Create incidents
_message_create_1 = {
    "timestamp": "2018-03-12T14:48:11.418371Z",
    "id": {
        "sport": "Basketball",
        "start_time": "2022-10-16T00:00:00Z",
        "away": "Chicago Bulls",
        "home": "Detroit Pistons",
        "event_group_name": "NBAREGULARSEASON",
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

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

config = dict(
    nobroadcast=True
)
ppy = PeerPlays(
    keys=[wif],
    nobroadcast=config["nobroadcast"],
    num_retries=1,
)
set_shared_peerplays_instance(ppy)
lookup = Lookup(
    proposer="init0",
    blockchain_instance=ppy,
    network="unittests",
    sports_folder=os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "bookiesports"
    ),
)
storage = factory.get_incident_storage(
    "mongodbtest", purge=True)


assert lookup.blockchain.nobroadcast


class Testcases(unittest.TestCase):

    def test_normalize_incident(self):
        create = CreateTrigger(
            _message_create_1,
            lookup_instance=lookup,
            config=config,
            storage=storage,
        )
        self.assertEqual(create.message["id"]["event_group_name"], "NBA Regular Season")

    def test_unnormalize_incident(self):
        _message_create_2 = deepcopy(_message_create_1)
        _message_create_2["id"]["event_group_name"] = "Foobar"
        storage.insert_incident(_message_create_2)

        with self.assertRaises(NotNormalizableException):
            create = CreateTrigger(
                _message_create_2,
                lookup_instance=lookup,
                config=config,
                storage=storage,
            )

        event = storage.get_event_by_id(_message_create_2)
        self.assertEqual(event["create"]["status"]["name"], "not normalizable")
