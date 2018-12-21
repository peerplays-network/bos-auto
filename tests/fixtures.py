import os
import yaml
import datetime

from pprint import pprint
from dateutil.parser import parse

from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance
from peerplays.account import Account
from peerplays.sport import Sports, Sport
from peerplays.event import Events, Event
from peerplays.rule import Rules, Rule
from peerplays.proposal import Proposals, Proposal
from peerplays.eventgroup import EventGroups, EventGroup
from peerplays.bettingmarketgroup import BettingMarketGroups, BettingMarketGroup
from peerplays.bettingmarket import BettingMarkets, BettingMarket
from peerplays.witness import Witnesses, Witness
from peerplaysbase.operationids import operations

from bookied_sync.lookup import Lookup
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent

from bos_incidents import factory

# default wifs key for testing
wifs = [
    "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3",
    "5KCBDTcyDqzsqehcb52tW5nU6pXife6V2rX9Yf7c3saYSzbDZ5W",
]
wif = wifs[0]
core_unit = "TEST"

# peerplays instance
peerplays = PeerPlays(
    "wss://api.ppy-beatrice.blckchnd.com", keys=wifs, nobroadcast=True, num_retries=1
)
config = peerplays.config

# Set defaults
peerplays.set_default_account("init0")
set_shared_peerplays_instance(peerplays)

# Ensure we are not going to transaction anythin on chain!
assert peerplays.nobroadcast

# Setup base lookup
lookup = Lookup(
    proposer="init0",
    blockchain_instance=peerplays,
    network="unittests",
    sports_folder=os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "bookiesports"
    ),
)
lookup.set_approving_account("init0")
lookup.set_proposing_account("init0")

# ensure lookup isn't broadcasting either
assert lookup.blockchain.nobroadcast

# Storage
storage = factory.get_incident_storage("mongodbtest", purge=True)


def lookup_test_event(id):
    event = {
        "id": "1.22.2242",
        "teams": ["Atlanta Hawks", "Boston Celtics"],
        "eventgroup_identifier": "NBA",
        "sport_identifier": "Basketball",
        "season": {"en": "2017-00-00"},
        "start_time": parse("2022-10-16T00:00:00"),
        "status": "upcoming",
    }
    return LookupEvent(**event)


def lookup_test_eventgroup(id):
    return LookupEventGroup("Basketball", "NBA")


def fixture_data():
    peerplays.clear()
    BettingMarkets.clear_cache()
    Rules.clear_cache()
    BettingMarketGroups.clear_cache()
    Proposals.clear_cache()
    Witnesses.clear_cache()
    Events.clear_cache()
    EventGroups.clear_cache()
    Sports.clear_cache()

    with open(os.path.join(os.path.dirname(__file__), "fixtures.yaml")) as fid:
        data = yaml.safe_load(fid)

    Witnesses.cache_objects([Witness(x) for x in data.get("witnesses", [])])
    Sports.cache_objects([Sport(x) for x in data.get("sports", [])])

    for evg in data.get("eventgroups", []):
        EventGroups.cache_objects([EventGroup(evg)], key=evg["sport_id"])

    for event in data.get("events", []):
        Events.cache_objects([Event(event)], key=event["event_group_id"])

    for bmg in data.get("bettingmarketgroups", []):
        BettingMarketGroups.cache_objects(
            [BettingMarketGroup(bmg)], key=bmg["event_id"]
        )

    for bm in data.get("bettingmarkets", []):
        BettingMarkets.cache_objects([BettingMarketGroup(bm)], bm["group_id"])

    Rules.cache_objects([Rule(x) for x in data.get("rules", [])])
    for x in data.get("accounts"):
        Account.cache_object(x, x["name"])
        Account.cache_object(x, x["id"])

    proposals = []
    for proposal in data.get("proposals", []):
        ops = list()
        for _op in proposal["operations"]:
            for opName, op in _op.items():
                ops.append([operations[opName], op])
        # Proposal!
        proposal_id = proposal["proposal_id"]
        proposal_data = {
            "available_active_approvals": [],
            "available_key_approvals": [],
            "available_owner_approvals": [],
            "expiration_time": "2018-05-29T10:23:13",
            "id": proposal_id,
            "proposed_transaction": {
                "expiration": "2018-05-29T10:23:13",
                "extensions": [],
                "operations": ops,
                "ref_block_num": 0,
                "ref_block_prefix": 0,
            },
            "proposer": "1.2.7",
            "required_active_approvals": ["1.2.1"],
            "required_owner_approvals": [],
        }
        proposals.append(Proposal(proposal_data))

    Proposals.cache_objects(proposals, "1.2.1")
    Proposals.cache_objects(proposals, "witness-account")
