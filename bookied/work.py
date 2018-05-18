import traceback
import grapheneapi
import bookied_sync
import bos_incidents
from flask_rq import job
from bookied_sync.lookup import Lookup
from peerplays import PeerPlays
from peerplays.instance import set_shared_blockchain_instance
from .log import log
from .config import loadConfig
from .triggers import (
    CreateTrigger,
    ResultTrigger,
    InProgressTrigger,
    FinishTrigger
)
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
        # Instanciate trigger
        if call == "create":
            trigger = CreateTrigger(
                message,
                lookup_instance=lookup,
                config=config,
            )

        elif call == "in_progress":
            trigger = InProgressTrigger(
                message,
                lookup_instance=lookup,
                config=config,
            )

        elif call == "finish":
            trigger = FinishTrigger(
                message,
                lookup_instance=lookup,
                config=config,
            )

        elif call == "result":
            trigger = ResultTrigger(
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

    except bookied_sync.exceptions.ObjectNotFoundInLookup as e:
        log.info(str(e))
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
        trigger.set_incident_status(status_name="event missing")

    except exceptions.EventGroupClosedException:
        trigger.set_incident_status(status_name="event group closed")

    except exceptions.EventCannotOpenException:
        # is set in the trigger itself
        # self.set_incident_status(status_name="postponed")
        pass

    except exceptions.InsufficientIncidents:
        trigger.set_incident_status(status_name="insufficient incidents")

    except exceptions.InsufficientEqualResults:
        trigger.set_incident_status(status_name="undecided")

    except grapheneapi.exceptions.NumRetriesReached:
        trigger.set_incident_status(status_name="connection lost")

    except bos_incidents.exceptions.EventNotFoundException:
        trigger.set_incident_status(
            status_name="event missing in bos_incidents")

    except bookied_sync.exceptions.ObjectNotFoundInLookup as e:
        log.info(str(e))

    except exceptions.CreateIncidentTooOldException as e:
        log.warning(str(e))

    except Exception as e:
        log.critical("Uncaught exception: {}\n\n{}".format(
            str(e),
            traceback.format_exc()))


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
