from pprint import pprint
from flask_rq import job
from bookied_sync.lookup import Lookup
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.eventstatus import LookupEventStatus
from bookied_sync.event import LookupEvent
from bookied_sync.bettingmarketgroupresolve import (
    LookupBettingMarketGroupResolve
)
from peerplays.account import Account
from dateutil.parser import parse
from . import log
from .config import loadConfig


config = loadConfig()
lookup = Lookup(
    proposing_account=config.get("BOOKIE_PROPOSER"),
    approving_account=config.get("BOOKIE_APPROVER")
)

if "passphrase" not in config:
    raise ValueError("No 'passphrase' found in configuration!")

if not lookup.wallet.created():
    raise Exception("Please create a wallet and import the keys first!")

lookup.wallet.unlock(config.get("passphrase"))


class Process():
    """ This class is used to deal with Messages that have been received by any
        means and need processing thru bookied-sync
    """
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
        """ Get an event from the lookup
        """
        existing = LookupEvent.find_event(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )
        if existing:
            return existing, True
        elif allowNew:
            log.info("Event not found, but allowed to create. Creating...")
            return LookupEvent(
                teams=self.teams,
                start_time=self.start_time,
                eventgroup_identifier=self.eventgroup.identifier,
                sport_identifier=self.sport.identifier
            ), False
        else:
            log.error("Event could not be found: {}".format(
                str(dict(
                    teams=self.teams,
                    start_time=self.start_time,
                    eventgroup_identifier=self.eventgroup.identifier,
                    sport_identifier=self.sport.identifier
                ))))
            return None, False

    def create(self, args):
        """ Process the 'create' message
        """
        season = args.get("season")
        if isinstance(season, str):
            season = {"en": season}

        # Obtain event
        event, event_exists = self.getEvent(allowNew=True)

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
        """ Set a BMG to ``in_progress``
        """
        event, event_exists = self.getEvent(allowNew=True)
        if not event_exists and event:
            event.update()
        event.status_update("in_progress")

    def finish(self, args):
        """ Set a BMG to ``finish``.
        """
        event, event_exists = self.getEvent()
        if not event:
            return
        event.status_update("frozen")

    def result(self, args):
        """ Publish results to a BMG
        """
        home_score = args.get("home_score")
        away_score = args.get("away_score")

        event, event_exists = self.getEvent()
        if not event:
            return

        event.status_update(
            "finished",
            scores=[str(home_score), str(away_score)]
        )

    def settle(self, args):
        """ Trigger settle of BMGs
        """
        event, event_exists = self.getEvent()
        if not event:
            return

        home_score = event["scores"][0]
        away_score = event["scores"][1]

        for bmg in event.bettingmarketgroups:

            # Skip those bmgs that coudn't be found
            if not bmg.find_id():
                log.error("BMG could not be found: {}".format(
                    str(bmg.identifier)))
                continue

            settle = LookupBettingMarketGroupResolve(
                bmg,
                [home_score, away_score]
            )
            settle.update()

        event.status_update("settled")


#
# Processing Job
#
@job
def process(
    message,
    **kwargs
):
    """ This process is called by the queue to process an actual message
        received. It instantiates from ``Process`` and let's the object deal
        with the message types.
    """
    assert isinstance(message, dict)
    assert "id" in message

    approver = kwargs.get("approver", None)
    if not approver:
        approver = message.get("approver", None)
    if approver:
        lookup.set_approving_account(approver)

    proposer = kwargs.get("proposer", None)
    if not proposer:
        proposer = message.get("proposer", None)
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

    elif call == "settle":
        processing.settle(args)

    else:
        pass

    if not config.get("nobroadcast", False):
        lookup.broadcast()
    else:
        pprint(Lookup.direct_buffer.json())
        pprint(Lookup.proposal_buffer.json())
        lookup.clear_proposal_buffer()
        lookup.clear_direct_buffer()

#
# Approve my own Proposals
#
@job
def selfapprove(*args, **kwargs):
    """ This process is meant to approve proposals that I have created.

        The reason for this is that proposals created by accountA are not
        automatically also approved by accountA and need an explicit approval.
    """
    from peerplays.proposal import Proposals
    from .config import loadConfig
    from time import sleep

    # We sleep 3 seconds to allow the proposal we created to end up in the
    # blockchain
    sleep(3)

    config = loadConfig()

    myapprover = kwargs.get("approver", None)
    if not myapprover:
        myapprover = config.get("BOOKIE_APPROVER")

    myproposer = kwargs.get("proposer", None)
    if not myproposer:
        myproposer = config.get("BOOKIE_PROPOSER")

    log.info(
        "Testing for pending proposals created by {} that we could approve by {}".format(
        myproposer, myapprover))

    peerplays = lookup.peerplays
    proposals = Proposals("witness-account", peerplays_instance=peerplays)
    for proposal in proposals:
        proposer = Account(
            proposal.proposer,
            peerplays_instance=peerplays)
        if (
            proposer["name"] == myproposer and
            proposer["id"] not in proposal["available_active_approvals"]
        ):
            log.info("Proposal {} has been proposed by us. Let's approve it!".format(
                proposal["id"]
            ))
            pprint(peerplays.approveproposal(proposal["id"], account=myproposer))
