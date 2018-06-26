import os
import yaml
from datetime import datetime

from peerplays.blockchainobject import BlockchainObject, ObjectCache
from peerplays.event import Event, Events
from peerplays.rule import Rules
from peerplays.proposal import Proposals
from peerplays.eventgroup import EventGroups
from peerplays.bettingmarketgroup import BettingMarketGroups
from peerplays.bettingmarket import BettingMarkets

from bookied_sync.event import LookupEvent

# Setup custom Cache
BlockchainObject._cache = ObjectCache(
    default_expiration=60 * 60 * 1,
    no_overwrite=True
)


def add_to_object_cache(objects):
    if objects:
        for i in objects:
            BlockchainObject._cache[i["id"]] = i


def add_event(data):
    add_to_object_cache([data])
    if "event_group_id" in data:
        Events.cache[data["event_group_id"]].append(data)


def fixture_data():
    with open(os.path.join(
        os.path.dirname(__file__),
        "fixtures.yaml"
    )) as fid:
        data = yaml.safe_load(fid)
    for ob in data.keys():
        add_to_object_cache(data[ob])

    for event_group in data.get("eventgroups", []):
        id = event_group["sport_id"]
        if id not in EventGroups.cache and not EventGroups.cache[id]:
            EventGroups.cache[id] = []
        EventGroups.cache[id].append(event_group)

    for event in data.get("events", []):
        id = event["event_group_id"]
        if id not in Events.cache and not Events.cache[id]:
            Events.cache[id] = []
        Events.cache[id].append(event)

    for bettingmarketgroup in data.get("bettingmarketgroups", []):
        id = bettingmarketgroup["event_id"]
        if id not in BettingMarketGroups.cache and not BettingMarketGroups.cache[id]:
            BettingMarketGroups.cache[id] = []
        BettingMarketGroups.cache[id].append(bettingmarketgroup)

    for bettingmarket in data.get("bettingmarkets", []):
        id = bettingmarket["group_id"]
        if id not in BettingMarkets.cache and not BettingMarkets.cache[id]:
            BettingMarkets.cache[id] = []
        BettingMarkets.cache[id].append(bettingmarket)

    for rule in data.get("rules", []):
        id = "rules"
        if id not in Rules.cache and not Rules.cache[id]:
            Rules.cache[id] = []
        Rules.cache[id].append(rule)

    for proposal in data.get("proposals", []):
        id = proposal["required_active_approvals"][0]
        if id not in Proposals.cache and not Proposals.cache[id]:
            Proposals.cache[id] = []
        Proposals.cache[id].append(proposal)
