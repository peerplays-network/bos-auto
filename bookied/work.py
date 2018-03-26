from flask_rq import job
from bookied_sync.lookup import Lookup
from .log import log
from .config import loadConfig
from .processing import Process
import traceback


config = loadConfig()
lookup = Lookup(
    proposing_account=config.get("BOOKIE_PROPOSER"),
    approving_account=config.get("BOOKIE_APPROVER")
)

if "passphrase" not in config:
    err = "No 'passphrase' found in configuration!"
    log.critical(err)
    raise ValueError(err)

if not lookup.wallet.created():
    err = "Please create a wallet and import the keys first!"
    log.critical(err)
    raise Exception(err)

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
        processing = Process(
            message,
            lookup_instance=lookup,
        )
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

    log.info("Sending {} to processing!".format(call))
    try:
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
    except Exception as e:
        log.critical("Uncaught exception: {}".format(str(e)))
        log.critical(traceback.format_exc())

    if not config.get("nobroadcast", False):
        try:
            lookup.broadcast()
        except Exception as e:
            log.critical("Broadcast Error: {}".format(str(e)))
            log.critical(traceback.format_exc())
    else:
        log.debug(Lookup.direct_buffer.json())
        log.debug(Lookup.proposal_buffer.json())
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
    from peerplays.account import Account
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
            log.warn(peerplays.approveproposal(proposal["id"], account=myproposer))
