import time
import logging
import traceback
import grapheneapi
import bookied_sync
import bos_incidents

from flask_rq import job
from datetime import datetime, timedelta

from bookied_sync.lookup import Lookup
from peerplays import PeerPlays
from peerplays.instance import set_shared_blockchain_instance

from bookied.triggers.create import CreateTrigger
from bookied.triggers.result import ResultTrigger
from bookied.triggers.in_progress import InProgressTrigger
from bookied.triggers.finish import FinishTrigger
from bookied.triggers.cancel import CancelTrigger
from bookied.triggers.dynamic_bmg import DynamicBmgTrigger

from bookiesports.normalize import NotNormalizableException

from .log import log
from .config import loadConfig
from . import exceptions


config = loadConfig()
peerplays = PeerPlays(
    node=config.get("node", None),
    num_retries=1  # Only try once then trow an exception
)
set_shared_blockchain_instance(peerplays)
lookup = Lookup(
    proposing_account=config.get("BOOKIE_PROPOSER"),
    approving_account=config.get("BOOKIE_APPROVER"),
    blockchain_instance=peerplays,
    network=config.get("network", "baxter")
)

_triggers = {
    "create": CreateTrigger,
    "in_progress": InProgressTrigger,
    "finish": FinishTrigger,
    "result": ResultTrigger,
    "canceled": CancelTrigger,
    "dynamic_bmgs": DynamicBmgTrigger
}


def unlock():
    """ Unlock the python-peerplays wallet so we can sign the things we are
        proposing/approving.
    """
    # We need to know the passphrase to unlock the wallet
    if "passphrase" not in config:
        err = "No 'passphrase' found in configuration!"
        log.critical(err)
        raise ValueError(err)

    if not lookup.wallet.created():
        err = "Please create a wallet and import the keys first!"
        log.critical(err)
        raise Exception(err)

    print("unlocking wallet ...")
    lookup.wallet.unlock(config.get("passphrase"))


#
# Processing Job
#
@job
def process(
    message,
    **kwargs
):
    """ This process is called by the queue to process an actual message
        received.

        Hence, this method has the look and feel of a dispatcher!
    """
    try:
        t = time.time()
        log.debug("Processing " + message["unique_string"])
    except Exception as e:
        pass

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

    log.debug("Proposer account: {}".format(lookup.proposing_account))
    log.debug("Approver account: {}".format(lookup.approving_account))

    # Call
    call = message.get("call").lower()

    # Obtain arguments
    args = message.get("arguments")

    log.info("processing {} call with args {}".format(
        call, str(args)
    ))
    try:

        if call in _triggers:
            trigger = _triggers[call](
                message,
                lookup_instance=lookup,
                config=config,
            )

        elif call == "unknown":
            return

        else:
            log.error(
                "Received an unknown trigger {} with content: {}"
                .format(call, message)
            )
            return

    except bookied_sync.exceptions.ObjectNotFoundInLookup as e:
        log.info(str(e))
        return

    except NotNormalizableException as e:
        log.warning("Incident not normalizable: {}".format(message))
        return

    except Exception as e:
        log.critical("Uncaught exception: {}\n\n{}".format(
            str(e),
            traceback.format_exc()))
        # No trigger can be executed!
        return

    try:
        # Execute the trigger
        trigger.trigger(args)

    except exceptions.EventDoesNotExistException:
        log.warning("Event does not exist on chain!")
        trigger.set_incident_status(status_name="event missing")

    except exceptions.EventGroupClosedException:
        log.warning("The event group is closed!")
        trigger.set_incident_status(status_name="event group closed")

    except exceptions.EventCannotOpenException:
        trigger.set_incident_status(
            status_name="postponed",
            status_expiration=datetime.utcnow() + timedelta(
                seconds=int(config["scheduler"]["expirations"]["EventCannotOpenException"])
            )
        )

    except exceptions.PostPoneIncidentException:
        log.info("This incident has been postponed")
        trigger.set_incident_status(
            status_name="postponed",
            status_expiration=datetime.utcnow() + timedelta(
                seconds=int(config["scheduler"]["expirations"]["PostPoneIncidentException"])
            )
        )

    except exceptions.InsufficientIncidents:
        trigger.set_incident_status(status_name="insufficient incidents")

    except exceptions.InsufficientEqualResults:
        log.info("This incident couldn't lead to a decision")
        trigger.set_incident_status(status_name="undecided")

    except grapheneapi.exceptions.NumRetriesReached:
        log.critical("Connection to backend node has been lost!")
        trigger.set_incident_status(status_name="connection lost")

    except bos_incidents.exceptions.EventNotFoundException as e:
        traceback.format_exc()
        log.warning("Invalid bos_incident event!")
        trigger.set_incident_status(
            status_name="event missing in bos_incidents")

    except bookied_sync.exceptions.ObjectNotFoundInLookup as e:
        trigger.set_incident_status(status_name="related object not found")
        log.info(str(e))

    except exceptions.CreateIncidentTooOldException as e:
        trigger.set_incident_status(status_name="create too old")
        log.warning(str(e))

    except Exception as e:
        trigger.set_incident_status(status_name="unhandled exception")
        log.critical("Uncaught exception: {}\n\n{}".format(
            str(e),
            traceback.format_exc()))

    try:
        elapsed = time.time() - t
        log.debug("Done processing " + message["unique_string"] + ", elapsed time is " + str(elapsed))
    except Exception as e:
        pass


#
# Approve my own Proposals
#
@job
def approve(*args, **kwargs):
    """ This process is meant to approve proposals that I have created.

        The reason for this is that proposals created by accountA are not
        automatically also approved by accountA and need an explicit approval.
    """
    from peerplays.account import Account
    from peerplays.proposal import Proposals
    from .config import loadConfig

    config = loadConfig()

    myapprover = kwargs.get("approver", None)
    if not myapprover:
        myapprover = config.get("BOOKIE_APPROVER")

    myproposer = kwargs.get("proposer", None)
    if not myproposer:
        myproposer = config.get("BOOKIE_PROPOSER")

    log.info(
        "Testing for pending proposals "
        "created by {} that we could approve by {}"
        .format(myproposer, myapprover))

    peerplays = lookup.peerplays
    proposals = Proposals("witness-account", peerplays_instance=peerplays)
    approver = Account(myapprover, peerplays_instance=peerplays)
    for proposal in proposals:
        proposer = Account(
            proposal.proposer,
            peerplays_instance=peerplays)
        if (
            proposer["name"] == myproposer and
            approver["id"] not in proposal["available_active_approvals"]
        ):
            log.info(
                "Proposal {} has been proposed by {}. Approving it!".format(
                    proposal["id"],
                    myproposer))
            log.info(peerplays.approveproposal(
                proposal["id"],
                account=myapprover
            ))
