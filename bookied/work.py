import time
import logging
import traceback
import grapheneapi
import bookied_sync
import bos_incidents
from bos_incidents.format import id_to_string
import random

from flask_rq import job
from datetime import datetime, timedelta

from bookied_sync.lookup import Lookup
from peerplays import PeerPlays
from peerplays.instance import set_shared_blockchain_instance
from peerplays.account import Account
from peerplays.proposal import Proposals

from bookiesports.normalize import NotNormalizableException

from .log import log
from .config import loadConfig
from . import exceptions, TRIGGERS


config = loadConfig()
peerplays = PeerPlays(
    node=config.get("node", None),
    nobroadcast=config.get("nobroadcast", False),
    num_retries=1  # Only try once then trow an exception
)
set_shared_blockchain_instance(peerplays)
lookup = Lookup(
    proposing_account=config.get("BOOKIE_PROPOSER"),
    approving_account=config.get("BOOKIE_APPROVER"),
    blockchain_instance=peerplays,
    network=config.get("network", "beatrice")
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
    peerplays.rpc.connect()
    try:
        t = time.time()
        log.info("processing " + message["unique_string"] + " for event " + id_to_string(message))
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

    log.debug("initializing {} call with args {}".format(
        call, str(args)
    ))
    try:

        if call in TRIGGERS:
            trigger = TRIGGERS[call](
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

    log.debug("processing {} call from event id {}".format(
        call, str(trigger.id)
    ))

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
        log.info("This incident has been postponed")
        """
        now = int(time.mktime(datetime.utcnow().timetuple()))
        expiration_time = trigger.event.can_open_by + timedelta(seconds=(now % 120))

        trigger.set_incident_status(
            status_name="postponed",
            status_expiration=expiration_time
        )

        """
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

    except bookied_sync.exceptions.ObjectNotFoundError as e:
        trigger.set_incident_status(status_name="related object not found")
        log.info(str(e))

    except exceptions.CreateIncidentTooOldException as e:
        trigger.set_incident_status(status_name="create too old")
        log.warning(str(e))

    except Exception as e:
        exception_details = "{}\n\n{}".format(str(e), traceback.format_exc())

        # retry uncaught exception once (to reduce ghost errors)
        if trigger.get_incident_status() is not None and\
                (
                    trigger.get_incident_status()["name"] == "unhandled exception, retrying soon" or
                    trigger.get_incident_status()["name"] == "unhandled exception"
        ):
            # already retried, finalize
            trigger.set_incident_status(
                status_name="unhandled exception",
                status_add={"details": exception_details}
            )
            log.critical("Uncaught exception: {}\n\n{}".format(
                str(e),
                traceback.format_exc())
            )
        else:
            # randomize it
            random_offset = random.randint(1, 3) * 60
            expiration_in_seconds = max(30, int(config["scheduler"]["expirations"]["UnhandledException"]) - random_offset)

            trigger.set_incident_status(
                status_name="unhandled exception, retrying soon",
                status_expiration=datetime.utcnow() + timedelta(
                    seconds=expiration_in_seconds
                ),
                status_add={"details": exception_details}
            )
            log.info("Uncaught exception, retrying soon: {}".format(str(e)))

    try:
        elapsed = time.time() - t
        log.debug("Done processing " + message["unique_string"] + ", call status now " + trigger.get_incident_status() + ", elapsed time is " + str(elapsed))
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
    peerplays.rpc.connect()
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

    proposals = Proposals("witness-account")
    approver = Account(myapprover)
    for proposal in proposals:
        proposer = Account(proposal.proposer)
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
