import os
import yaml
import datetime

from dateutil.parser import parse

from peerplays import PeerPlays
from peerplays.instance import set_shared_peerplays_instance
from peerplays.blockchainobject import BlockchainObject, ObjectCache
from peerplays.sport import Sports
from peerplays.event import Events
from peerplays.rule import Rules
from peerplays.proposal import Proposals
from peerplays.eventgroup import EventGroups
from peerplays.bettingmarketgroup import BettingMarketGroups
from peerplays.bettingmarket import BettingMarkets
from peerplays.witness import Witnesses
from peerplaysbase.operationids import operations

from bookied_sync.lookup import Lookup
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent

from bos_incidents import factory


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
lookup.set_approving_account("init0")
assert lookup.blockchain.nobroadcast

# Storage
storage = factory.get_incident_storage(
    "mongodbtest", purge=True)

# Setup custom Cache
BlockchainObject._cache = ObjectCache(
    default_expiration=60 * 60 * 1,
    no_overwrite=True
)


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


def add_to_object_cache(objects, key="id"):
    if objects:
        for i in objects:
            if key in i and i[key]:
                BlockchainObject._cache[i[key]] = i


def add_event(data):
    add_to_object_cache([data])
    if "event_group_id" in data:
        Events.cache[data["event_group_id"]].append(data)


def fixture_data():
    BettingMarkets.cache = dict()
    Rules.cache = dict()
    Proposals.cache = dict()
    BettingMarketGroups.cache = dict()
    Events.cache = dict()
    EventGroups.cache = dict()
    Sports.cache = dict()

    with open(os.path.join(
        os.path.dirname(__file__),
        "fixtures.yaml"
    )) as fid:
        data = yaml.safe_load(fid)
    for ob in data.keys():
        add_to_object_cache(data[ob])

    add_to_object_cache(data.get("accounts", []), key="name")

    for witness in data.get("witnesses", []):
        id = witness["id"]
        if id not in Witnesses.cache or not Witnesses.cache[id]:
            Witnesses.cache[id] = []
        Witnesses.cache[id].append(witness)
    Witnesses.cache["2.12.0"] = data.get("witness_schedule", [])

    for sport in data.get("sports", []):
        id = "sports"
        if id not in Sports.cache or not Sports.cache[id]:
            Sports.cache[id] = []
        Sports.cache[id].append(sport)

    for event_group in data.get("eventgroups", []):
        id = event_group["sport_id"]
        if id not in EventGroups.cache or not EventGroups.cache[id]:
            EventGroups.cache[id] = []
        EventGroups.cache[id].append(event_group)

    for event in data.get("events", []):
        id = event["event_group_id"]
        if id not in Events.cache or not Events.cache[id]:
            Events.cache[id] = []
        Events.cache[id].append(event)

    for bettingmarketgroup in data.get("bettingmarketgroups", []):
        id = bettingmarketgroup["event_id"]
        if id not in BettingMarketGroups.cache or not BettingMarketGroups.cache[id]:
            BettingMarketGroups.cache[id] = []
        BettingMarketGroups.cache[id].append(bettingmarketgroup)

    for bettingmarket in data.get("bettingmarkets", []):
        id = bettingmarket["group_id"]
        if id not in BettingMarkets.cache or not BettingMarkets.cache[id]:
            BettingMarkets.cache[id] = []
        BettingMarkets.cache[id].append(bettingmarket)

    for rule in data.get("rules", []):
        id = "rules"
        if id not in Rules.cache or not Rules.cache[id]:
            Rules.cache[id] = []
        Rules.cache[id].append(rule)

    for proposal in data.get("proposals", []):
        # id = proposal["required_active_approvals"][0]
        id = "1.2.1"
        ops = list()
        for _op in proposal["operations"]:
            for opName, op in _op.items():
                ops.append(
                    [operations[opName], op]
                )
        # Proposal!
        proposal_id = proposal["proposal_id"]
        proposal_data = {'available_active_approvals': [],
                         'available_key_approvals': [],
                         'available_owner_approvals': [],
                         'expiration_time': '2018-05-29T10:23:13',
                         'id': proposal_id,
                         'proposed_transaction': {'expiration': '2018-05-29T10:23:13',
                                                  'extensions': [],
                                                  'operations': ops,
                                                  'ref_block_num': 0,
                                                  'ref_block_prefix': 0},
                         'proposer': '1.2.7',
                         'required_active_approvals': ['1.2.1'],
                         'required_owner_approvals': []}

        if id not in Proposals.cache or not Proposals.cache[id]:
            Proposals.cache[id] = []
        Proposals.cache[id].append(proposal_data)
        # Also define the actual object in the Object Cache
        BlockchainObject._cache[proposal_id] = proposal_data
