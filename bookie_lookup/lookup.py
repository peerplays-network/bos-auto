import sys
import os
import yaml
from glob import glob
from peerplays.instance import shared_peerplays_instance
from peerplays.account import Account
from peerplays.proposal import Proposal, Proposals
from peerplays.storage import configStorage as config
from . import log, UPDATE_PENDING_NEW, UPDATE_PROPOSING_NEW


class ObjectNotFoundError(Exception):
    pass


class SportsNotFoundError(Exception):
    pass


class LookupDatabaseConfig:
    name = "db_peerplays"
    user = "peerplays"
    password = "I<3storage"


class Lookup(dict):

    #: Singelton to store data and prevent rereading if Lookup is
    #: instantiated multiple times
    data = dict()
    approval_map = {}

    direct_buffer = None
    proposal_buffer = None
    sports_folder = None

    def __init__(
        self,
        sports_folder=None,
        peerplays_instance=None,
        proposing_account=None,
        approving_account=None,
        *args,
        **kwargs
    ):
        """ Let's load all the data from the folder and its subfolders
        """
        self.peerplays = peerplays_instance or shared_peerplays_instance()
        # self._cwd = os.path.dirname(os.path.realpath(__file__))
        self._cwd = os.getcwd()

        if Lookup.sports_folder is None:
            Lookup.sports_folder = sports_folder or "bookiesports"
        elif sports_folder and sports_folder != Lookup.sports_folder:
            # clear .data
            Lookup._clear()
            Lookup.sports_folder = sports_folder

        if not proposing_account:
            if "default_account" in config:
                proposing_account = config["default_account"]
            else:
                proposing_account = proposing_account
        self.proposing_account = proposing_account

        if not approving_account:
            if "default_account" in config:
                approving_account = config["default_account"]
            else:
                approving_account = approving_account
        self.approving_account = approving_account

        # We define two transaction buffers
        if not Lookup.direct_buffer:
            self.clear_direct_buffer()
        if not Lookup.proposal_buffer:
            self.clear_proposal_buffer()

        # Do not reload sports if already stored in data
        if not Lookup.data:
            if not os.path.isdir(
                os.path.join(
                    self._cwd,
                    Lookup.sports_folder)):
                # Reset the sports_folder (since it is a singelton)
                Lookup.sports_folder = None
                raise SportsNotFoundError(
                    "You need to clone the bookiesports repository into your "
                    "working directory first! ({})".format(Lookup.sports_folder)
                )

            # Load sports
            self.data["sports"] = self._loadSports(Lookup.sports_folder)

            # _tests
            self._tests()

    @staticmethod
    def _clear():
        Lookup.data = dict()
        Lookup.approval_map = {}
        Lookup.direct_buffer = None
        Lookup.proposal_buffer = None
        Lookup.sports_folder = None

    def clear_proposal_buffer(self):
        Lookup.proposal_buffer_tx = self.peerplays.new_tx()
        Lookup.proposal_buffer = self.peerplays.new_proposal(
            Lookup.proposal_buffer_tx,
            proposer=self.proposing_account)

    def clear_direct_buffer(self):
        Lookup.direct_buffer = self.peerplays.new_tx()

    def broadcast(self):
        """ Since we are using multiple txbuffers, we need to do multiple
            broadcasts
        """
        from pprint import pprint
        pprint(Lookup.direct_buffer.broadcast())
        pprint(Lookup.proposal_buffer.broadcast())

    def _loadyaml(self, f):
        """ Load a YAML file

            :param str f: YAML File location
        """
        try:
            with open(f) as fid:
                t = yaml.load(fid)
            return t
        except yaml.YAMLError as exc:
            log.error("Error in configuration file {}: {}".format(f, exc))
            sys.exit(1)
        except Exception as e:
            log.error("The file {} is required but doesn't exist!".format(f))
            sys.exit(1)

    def _loadSports(self, sports_folder):
        """ This loads all sports recursively from the ``sports/`` folder
        """
        ret = dict()
        for sportDir in glob(
            os.path.join(
                self._cwd,
                sports_folder,
                "*")):
            if not os.path.isdir(sportDir):
                continue
            sport = os.path.basename(sportDir)
            ret[sport] = self._loadSport(sportDir)
        return ret

    def _loadSport(self, sportDir):
        """ Load an individual sport, recursively
        """
        sport = self._loadyaml(os.path.join(sportDir, "index.yaml"))
        eventgroups = dict()
        for eventgroup in sport["eventgroups"]:
            eventgroups[eventgroup] = self._loadEventGroup(
                os.path.join(sportDir, eventgroup)
            )
            eventgroups[eventgroup]["sport_id"] = sport.get("id")
        sport["eventgroups"] = eventgroups

        # Rules
        rulesDir = os.path.join(sportDir, "rules")
        rules = dict()
        for ruleDir in glob(os.path.join(rulesDir, "*")):
            if ".yaml" not in ruleDir:
                continue
            rule = os.path.basename(ruleDir).replace(".yaml", "")
            rules[rule] = self._loadyaml(ruleDir)
        sport["rules"] = rules

        # participants
        participantsDir = os.path.join(sportDir, "participants")
        participants = dict()
        for participantDir in glob(os.path.join(participantsDir, "*")):
            if ".yaml" not in participantDir:
                continue
            participant = os.path.basename(participantDir).replace(".yaml", "")
            participants[participant] = self._loadyaml(participantDir)
        sport["participants"] = participants

        # def_bmgs
        def_bmgsDir = os.path.join(sportDir, "bettingmarketgroups")
        def_bmgs = dict()
        for def_bmgDir in glob(os.path.join(def_bmgsDir, "*")):
            if ".yaml" not in def_bmgDir:
                continue
            def_bmg = os.path.basename(def_bmgDir).replace(".yaml", "")
            def_bmgs[def_bmg] = self._loadyaml(def_bmgDir)
        sport["bettingmarketgroups"] = def_bmgs

        return sport

    def _loadEventGroup(self, eventgroupDir):
        """ Load an event group (recursively)
        """
        eventgroup = self._loadyaml(os.path.join(eventgroupDir, "index.yaml"))

        """
        # Events
        events = dict()
        for event in eventgroup["events"]:
            events[event] = self._loadEvent(os.path.join(eventgroupDir, event))
        eventgroup["events"] = events
        """

        return eventgroup

    def _tests(self):
        """ Tests for consistencies and requirements
        """
        for sportname, sport in self.data["sports"].items():
            self._test_required_attributes(sport, sportname, ["name", "id"])

            for evengroupname, eventgroup in sport["eventgroups"].items():
                self._test_required_attributes(
                    eventgroup,
                    evengroupname,
                    ["name", "id"]
                )

                for bmg in eventgroup["bettingmarketgroups"]:
                    # Test that each used BMG is deinfed
                    assert bmg in sport["bettingmarketgroups"], (
                        "Betting market group {} is used"
                        "in {}:{} but wasn't defined!"
                    ).format(
                        bmg, sportname, evengroupname
                    )
            for rule in sport["rules"]:
                pass
            for bmgname, bmg in sport["bettingmarketgroups"].items():
                self._test_required_attributes(bmg, bmgname, ["name"])

                # Test that each used rule is defined
                assert bmg["rules"] in sport["rules"], \
                    "Rule {} is used in {}:{} but wasn't defined!".format(
                        bmg["rules"],
                        sportname,
                        bmgname)

                for bettingmarkets in bmg["bettingmarkets"]:
                    self._test_required_attributes(
                        bettingmarkets,
                        bmgname,
                        ["name"]
                    )

    def _test_required_attributes(self, data, name, checks):
        for check in checks:
            assert check in data, "{} is missing a {}".format(name, check)

    # List calls
    def list_sports(self):
        """ List all sports in the  lookup
        """
        from .sport import LookupSport
        return [LookupSport(x) for x in self.data["sports"]]

    def get_sport(self, sportname):
        from .sport import LookupSport
        return LookupSport(sportname)

    # Update call
    def update(self):
        """ This call makes sure that the data in the  lookup matches
            the data on the blockchain for the object we are currenty looking
            at.

            It works like this:

            1. Test if the  lookup knows the "id" of the object on chain
            1.1. If it does not, try to identify the object from the blockchain
                  * if available, warn about existing id
                  * if pending creation proposal, approve it
                  * if none of the above, create proposal
            1.2. Test if  lookup and blockchain data match, if not
                * if exists proposal for update, approve
                * if not, create proposal to update
        """
        # See if  lookup already has an id
        if "id" not in self or not self["id"]:

            # Test if an object with the characteristics (i.e. name) exist
            id = self.find_id()
            has_pending_new = self.has_pending_new()
            if id:
                log.error((
                    "Object {} carries id {} on the blockchain. "
                    "Please update your lookup"
                ).format(self.identifier, id))
                self["id"] = id
            elif has_pending_new:
                log.warn((
                    "Object {} has pending update proposal. Approving ..."
                ).format(self.identifier))
                self.approve(*has_pending_new)
                return UPDATE_PENDING_NEW
            else:
                log.warn((
                    "Object {} does not exist on chain. Proposing ..."
                ).format(self.identifier))
                self.propose_new()
                return UPDATE_PROPOSING_NEW

        if not self.is_synced():
            log.warn("Object not fully synced: {}: {}".format(
                self.__class__.__name__,
                str(self.get("name", ""))
            ))
            has_pending_update = self.has_pending_update()
            if has_pending_update:
                log.info("Object has pending update: {}: {} in {}".format(
                    self.__class__.__name__,
                    str(self.get("name", "")),
                    str(has_pending_update)
                ))
                self.approve(*has_pending_update)
            else:
                log.info("Object has no pending update, yet: {}: {}".format(
                    self.__class__.__name__,
                    str(self.get("name", ""))
                ))
                self.propose_update()

    def get_pending_operations(self, account="witness-account"):
        pending_proposals = Proposals(account)
        for proposal in pending_proposals:
            if not proposal["id"] in Lookup.approval_map:
                Lookup.approval_map[proposal["id"]] = {}
            for oid, operations in enumerate(proposal.proposed_operations):
                if oid not in Lookup.approval_map[proposal["id"]]:
                    Lookup.approval_map[proposal["id"]][oid] = False
                yield operations, proposal["id"], oid

    def get_buffered_operations(self):
        # Obtain the proposals that we have in our buffer
        # from peerplaysbase.operationids import getOperationNameForId
        for oid, op in enumerate(
            Lookup.proposal_buffer.list_operations()
        ):
            yield op.json(), "0.0.0", "0.0.%d" % oid

    def approve(self, pid, oid):
        """ Approve a proposal

            This call basically flags a single update operation of a proposal
            as "approved". Only if all operations in the proposal are approved,
            will this tool approve the whole proposal and otherwise ignore the
            proposal.

            The call has to identify the correct operation of a proposal on its
            own.

            Internally, a proposal is approved partially using a map that
            contains the approval of each operation in a proposal. Once all
            operations of a proposal are approved, the whole proopsal is
            approved.

            :param str pid: Proposal id
            :param int oid: Operation number within the proposal
        """
        if pid == "0.0.0":
            log.info("Cannot approve pending-for-broadcast proposals")
            return
        Lookup.approval_map[pid][oid] = True
        approved_read_for_delete = []
        for p in Lookup.approval_map:
            if all(Lookup.approval_map[p].values()):
                proposal = Proposal(p)
                account = Account(self.approving_account)
                if account["id"] not in proposal["available_active_approvals"]:
                    log.info("Approving proposal {}".format(p))
                    approved_read_for_delete.append(p)
                    self.peerplays.approveproposal(
                        p,
                        account=self.approving_account,
                        append_to=Lookup.direct_buffer
                    )
                else:
                    log.info(
                        "Proposal {} has already been approved by us".format(p)
                    )
        # In order not to approve the same proposal again and again, we remove
        # it from the map
        for p in approved_read_for_delete:
            del Lookup.approval_map[p]

    def has_pending_new(self):
        """ This call tests if a pending proposal would create this object

            It only returns true if the exact content is proposed
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_create:
                if self.test_operation_equal(op[1]):
                    return pid, oid

        for op, pid, oid in self.get_buffered_operations():
            if getOperationNameForId(op[0]) == self.operation_create:
                if self.test_operation_equal(op[1]):
                    return pid, oid

    def has_pending_update(self):
        """ Test if there is an update to properly match blockchain content
            with  lookup content

            It only returns true if the exact content is proposed
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_update:
                if self.test_operation_equal(op[1]):
                    return pid, oid

        for op, pid, oid in self.get_buffered_operations():
            if getOperationNameForId(op[0]) == self.operation_update:
                if self.test_operation_equal(op[1]):
                    return pid, oid

    @property
    def id(self):
        """ Returns the id of the object on chain

            :raises IdNotFoundError: if the object couldn't be matched to an
                object on chain
        """
        # Do we already know the id?
        if "id" in self and self["id"]:
            return self["id"]

        # Try find the id on the blockchain
        found = self.find_id()
        if found:
            return found

        # Try find the id in the pending proposals
        found = self.has_pending_new()
        if found:
            return found[1]

        raise ObjectNotFoundError(
            "Object not found on chain: {}: {}".format(
                self.__class__.__name__,
                str(self.items())))
        return found

    @property
    def parent_id(self):
        if hasattr(self, "parent"):
            return self.parent.id

    # Prototypes #############################################################
    def test_operation_equal(self, sport):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """
        pass

    def find_id(self):
        """ Try to find an id for the object of the  lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
        """
        pass

    def is_synced(self):
        """ Test if data on chain matches  lookup
        """
        # Compare blockchain content with  lookup

    def propose_new(self):
        """ Propose operation to create this object
        """
        pass

    def propose_update(self):
        """ Propose to update this object to match  lookup
        """
        pass
