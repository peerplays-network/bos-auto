import os
import time
from pprint import pprint
from flask_rq import job
from bookied_sync.lookup import Lookup
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent
from bookied_sync.bettingmarketgroup import LookupBettingMarketGroup
from bookied_sync.bettingmarketgroupresolve import LookupBettingMarketGroupResolve
from bookied_sync.bettingmarket import LookupBettingMarket
from bookied_sync.rule import LookupRules
from bookied_sync.exceptions import ObjectNotFoundError
from dateutil.parser import parse
from . import log
from .config import loadConfig

if __name__ == "__main__":
    config = loadConfig()
    lookup = Lookup("bookiesports")

    if "passphrase" not in config:
        raise ValueError("No 'passphrase' found in configuration!")

    if not lookup.wallet.created():
        raise Exception("Please create a wallet and import the keys first!")

    lookup.wallet.unlock(config.get("passphrase"))


class Process():
    def __init__(self, message):
        self.message = message

        # Obtain data for unique key
        self.id = message.get("id")
        try:
            self.sport = LookupSport(self.id.get("sport"))
        except Exception:
            raise Exception(
                "Sport {} not found".format(self.id.get("sport"))
            )
        try:
            self.eventgroup = LookupEventGroup(
                self.sport,
                self.id.get("event_group_name"))
        except Exception:
            raise Exception(
                "Event group {} not found".format(
                    self.id.get("event_group_name"))
            )
        self.teams = [
            self.id.get("home"),
            self.id.get("away")]
        self.start_time = parse(
            self.id.get("start_time", ""))

    def getEvent(self, allowNew=False):
        existing = LookupEvent.find_event(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )
        if existing:
            return existing
        elif allowNew:
            return LookupEvent(
                teams=self.teams,
                start_time=self.start_time,
                eventgroup_identifier=self.eventgroup.identifier,
                sport_identifier=self.sport.identifier
            )
        else:
            log.error("Event could not be found: {}".format(
                str(dict(
                    teams=self.teams,
                    start_time=self.start_time,
                    eventgroup_identifier=self.eventgroup.identifier,
                    sport_identifier=self.sport.identifier
                ))))
            return

    def create(self, args):
        """ Process the 'create' message
        """
        season = args.get("season")
        if isinstance(season, str):
            season = {"en": season}

        # Obtain event
        event = self.getEvent(allowNew=True)

        # Set parameters
        if (
            event["season"] and
            event["season"].get("en") != season.get("en")
        ):
            raise Exception(
                "Seasons don't match: {} != {}".format(
                    season.get("en"),
                    event["season"].get("en")))
        event["season"] = season

        # Update event
        event.update()
        # Go through all Betting Market groups
        for bmg in event.bettingmarketgroups:
            # Skip dynamic bmgs
            if bmg["dynamic"]:
                log.warning("Skipping dynamic BMG: {}".format(
                    str(bmg.identifier)))
                continue
            bmg.update()
            # Go through all betting markets
            for bm in bmg.bettingmarkets:
                bm.update()

        log.debug(event.proposal_buffer.json())

    def in_progress(self, args):
        # whistle_start_time = args.get("whistle_start_time")
        pass

    def finish(self, args):
        # whistle_end_time = args.get("whistle_end_time")
        pass

    def result(self, args):
        away_score = args.get("away_score")
        home_score = args.get("home_score")

        event = self.getEvent()
        if not event:
            return

        for bmg in event.bettingmarketgroups:

            # Skip those bmgs that coudn't be found
            if not bmg.find_id():
                log.error("BMG could not be found: {}".format(
                    str(bmg.identifier)))
                continue

            resolve = LookupBettingMarketGroupResolve(
                bmg,
                [home_score, away_score]
            )
            resolve.update()


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

    approver = kwargs.get("approver")
    if approver:
        lookup.set_approving_account(approver)

    proposer = kwargs.get("proposer")
    if proposer:
        lookup.set_proposing_account(proposer)

    log.info("Proposer account: {}".format(lookup.proposing_account))
    log.info("Approver account: {}".format(lookup.approving_account))

    try:
        processing = Process(message)
    except Exception as e:
        log.error(str(e))
        return str(e), 503

    # Call
    call = message.get("call").lower()

    # Obtain arguments
    args = message.get("arguments")

    log.info("processing {} call with args {}".format(
        call, str(args)
    ))

    if call == "create":
        processing.create(args)

    elif call == "in_progress":
        processing.in_progress(args)

    elif call == "finish":
        processing.finish(args)

    elif call == "result":
        processing.result(args)

    else:
        pass

    if not config.get("nobroadcast", False):
        lookup.broadcast()
    else:
        pprint(Lookup.direct_buffer.json())
        pprint(Lookup.proposal_buffer.json())
        lookup.clear_proposal_buffer()
        lookup.clear_direct_buffer()
