import yaml
import os
import time
from pprint import pprint
from flask_rq import job
from bookie_lookup.lookup import Lookup
from bookie_lookup.sport import LookupSport
from bookie_lookup.eventgroup import LookupEventGroup
from bookie_lookup.event import LookupEvent
from bookie_lookup.bettingmarketgroup import LookupBettingMarketGroup
from bookie_lookup.bettingmarketgroupresolve import LookupBettingMarketGroupResolve
from bookie_lookup.bettingmarket import LookupBettingMarket
from bookie_lookup.rule import LookupRules
from dateutil.parser import parse
from . import log

lookup = Lookup("bookiesports")

# Load wallet passphrase from config
if not os.path.isfile("worker-config.yaml"):
    raise Exception("No 'worker-config.yaml' file found")

with open("worker-config.yaml", "r") as fid:
    config = yaml.load(fid)

if "passphrase" not in config:
    raise ValueError("No 'passphrase' found in configuration!")

if not lookup.wallet.created():
    raise Exception("Please create a wallet and import the keys first!")

lookup.wallet.unlock(config.get("passphrase"))

if (
    not lookup.wallet.getActiveKeyForAccount(lookup.approving_account) or
    not lookup.wallet.getActiveKeyForAccount(lookup.proposing_account)
):
    raise Exception(
        "We couldn't find the key for %s or %s in the wallet!" % (
            lookup.approving_account,
            lookup.proposing_account)
    )


class Process():
    def __init__(self, message):
        self.message = message

        # Obtain data for unique key
        self.id = message.get("id")
        self.sport = LookupSport(self.id.get("sport"))
        self.eventgroup = LookupEventGroup(
            self.sport,
            self.id.get("event_group_name"))
        self.teams = [
            self.id.get("home"),
            self.id.get("away")]
        self.start_time = parse(
            self.id.get("start_time", ""))

    def getEvent(self):
        return LookupEvent.find_event(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )
        return
        event.update()

    def create(self, args):
        """ Process the 'create' message
        """
        season = args.get("season")
        if isinstance(season, str):
            season = {"en": season}

        event = self.getEvent()


        # Go through all Betting Market groups
        for bmg in event.bettingmarketgroups:
            # Skip dynamic bmgs
            if bmg["dynamic"]:
                continue
            bmg.update()
            # Go through all betting markets
            for bm in bmg.bettingmarkets:
                bm.update()

        log.debug(event.proposal_buffer.json())

        return event

    def in_progress(self, args):
        whistle_start_time = args.get("whistle_start_time")

    def finish(self, args):
        whistle_end_time = args.get("whistle_end_time")

    def result(self, args):
        away_score = args.get("away_score")
        home_score = args.get("home_score")


#
# Processing Job
#
@job
def process(
    message,
    **kwargs
):
    assert isinstance(message, dict)
    assert "id" in message

    processing = Process(message)

    # Call
    call = message.get("call").lower()

    # Obtain arguments
    args = message.get("arguments")

    if call == "create":
        obj = processing.create(args)

    elif call == "in_progress":
        obj = processing.in_progress(args)

    elif call == "finish":
        obj = processing.finish(args)

    elif call == "result":
        obj = processing.result(args)

    else:
        pass

    if not config.get("nobroadcast", False):
        obj.broadcast()
    else:
        obj.clear_proposal_buffer()
