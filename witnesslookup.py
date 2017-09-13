import sys
import os
import yaml
import logging
from glob import glob
from peerplays.instance import shared_peerplays_instance
from peerplays.sport import Sports, Sport
from peerplays.account import Account
from peerplays.proposal import Proposal, Proposals
from peerplays.storage import configStorage as config
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

UPDATE_PROPOSING_NEW = 1
UPDATE_PENDING_NEW = 2


class WitnessLookup(dict):

    #: Singelton to store data and prevent rereading if WitnessLookup is
    #: instantiated multiple times
    data = dict()
    approval_map = {}

    def __init__(
        self,
        peerplays_instance=None,
        proposing_account=None,
        approving_account=None,
        *args,
        **kwargs
    ):
        """ Let's load all the data from the folder and its subfolders
        """
        self.peerplays = peerplays_instance or shared_peerplays_instance()
        self._cwd = os.path.dirname(os.path.realpath(__file__))

        if not proposing_account:
            if "default_account" in config:
                proposing_account = config["default_account"]
            else:
                proposing_account = proposing_account
        self.peerplays.proposer = proposing_account

        if not approving_account:
            if "default_account" in config:
                approving_account = config["default_account"]
            else:
                approving_account = approving_account
        self.approving_account = approving_account

        if not self.data:
            # Read main index.yaml
            data = self._loadyaml(os.path.join(self._cwd, "index.yaml"))
            super(WitnessLookup, self).__init__(data)

            # Load sports
            self.data["sports"] = self._loadSports()

            # _tests
            self._tests()

    def _loadyaml(self, f):
        """ Load a YAML file

            :param str f: YAML File location
        """
        try:
            t = yaml.load(open(f))
            return t
        except yaml.YAMLError as exc:
            log.error("Error in configuration file {}: {}".format(f, exc))
            sys.exit(1)
        except:
            log.error("The file {} is required but doesn't exist!".format(f))
            sys.exit(1)

    def _loadSports(self):
        """ This loads all sports recursively from the ``sports/`` folder
        """
        ret = dict()
        for sportDir in glob(os.path.join(self._cwd, "sports/*")):
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
                assert bmg["grading"]["rules"] in sport["rules"], \
                    "Rule {} is used in {}:{} but wasn't defined!".format(
                        bmg["grading"]["rules"],
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
        """ List all sports in the witness lookup
        """
        return [WitnessLookupSport(x) for x in self.data["sports"]]

    # Update call
    def update(self):
        """ This call makes sure that the data in the witness lookup matches
            the data on the blockchain for the object we are currenty looking
            at.

            It works like this:

            1. Test if the witness lookup knows the "id" of the object on chain
            1.1. If it does not, try to identify the object from the blockchain
                  * if available, warn about existing id
                  * if pending creation proposal, approve it
                  * if none of the above, create proposal
            1.2. Test if witness lookup and blockchain data match, if not
                * if exists proposal for update, approve
                * if not, create proposal to update
        """
        # See if witness lookup already has an id
        if "id" not in self or not self["id"]:

            # Test if an object with the characteristics (i.e. name) exist
            id = self.find_id()
            has_pending_new = self.has_pending_new()
            if id:
                log.warn((
                    "Object {} carries id {} on the blockchain. "
                    "Please update your witness lookup"
                ).format(self.identifier, id))
                self["id"] = id
            elif has_pending_new:
                self.approve(*has_pending_new)
                return UPDATE_PENDING_NEW
            else:
                # Propose the creation of this object
                self.propose_new()
                return UPDATE_PROPOSING_NEW

        if not self.is_synced():
            log.info("Object not fully synced: {}: {}".format(
                self.__class__.__name__,
                str(self.get("name", ""))
            ))
            has_pending_update = self.has_pending_update()
            if has_pending_update:
                log.info("Object has pending update: {}: {}".format(
                    self.__class__.__name__,
                    str(self.get("name", ""))
                ))
                self.approve(*has_pending_update)
            else:
                log.info("Object has no pending update, yet: {}: {}".format(
                    self.__class__.__name__,
                    str(self.get("name", ""))
                ))
                self.propose_update()

    def get_pending_operations(self, account="witness-account"):
        pending_proposals = Proposals("witness-account")
        for proposal in pending_proposals:
            if not proposal["id"] in WitnessLookup.approval_map:
                WitnessLookup.approval_map[proposal["id"]] = {}
            for oid, operations in enumerate(proposal.proposed_operations):
                if oid not in WitnessLookup.approval_map[proposal["id"]]:
                    WitnessLookup.approval_map[proposal["id"]][oid] = False
                yield operations, proposal["id"], oid

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
        WitnessLookup.approval_map[pid][oid] = True
        for p in WitnessLookup.approval_map:
            if all(WitnessLookup.approval_map[p].values()):
                self.peerplays.use_direct_buffer()
                proposal = Proposal(p)
                account = Account(self.approving_account)
                if account["id"] not in proposal["available_active_approvals"]:
                    log.info("Approving proposal {}".format(p))
                    self.peerplays.approveproposal(p)

    def has_pending_new(self):
        """ This call tests if a pending proposal would create this object

            It only returns true if the exact content is proposed
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_create:
                if self.test_operation_equal(op[1]):
                    return pid, oid

    def has_pending_update(self):
        """ Test if there is an update to properly match blockchain content
            with witness lookup content
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_update:
                if self.test_operation_equal(op[1]):
                    return pid, oid

    # Prototypes #############################################################
    def find_id(self):
        """ Try to find an id for the object of the witness lookup on the
            blockchain
        """
        pass

    def is_synced(self):
        """ Test if data on chain matches witness lookup
        """
        # Compare blockchain content with witness lookup

    def propose_new(self):
        """ Propose operation to create this object
        """
        pass

    def propose_update(self):
        """ Propose to update this object to match witness lookup
        """
        pass

    def test_operation_equal(self, sport):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the witness lookup
        """
        pass


class WitnessLookupSport(WitnessLookup, dict):

    operation_update = "sport_update"
    operation_create = "sport_create"

    def __init__(self, sport):
        self.identifier = sport
        super(WitnessLookupSport, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        dict.__init__(self, self.data["sports"][sport])

    def test_operation_equal(self, sport):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the witness lookup
        """
        lookupnames = [[k, v] for k, v in self["name"].items()]
        chainsnames = [[]]
        if "name" in sport:
            chainsnames = sport["name"]
        elif "new_name" in sport:
            chainsnames = sport["new_name"]
        else:
            raise ValueError
        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames])):
            return True

    def find_id(self):
        """ Try to find an id for the object of the witness lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
        """
        sports = Sports(peerplays_instance=self.peerplays)
        for sport in sports:
            for i in sport["name"]:
                if i[0] == "en" and i[1] == self["name"]["en"]:
                    return sport["id"]

    def is_synced(self):
        """ Test if data on chain matches witness lookup
        """
        if "id" in self:
            sport = Sport(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        """ Propose operation to create this object
        """
        names = [[k, v] for k, v in self["name"].items()]
        self.peerplays.use_proposal_buffer()
        self.peerplays.sport_create(names)

    def propose_update(self):
        """ Propose to update this object to match witness lookup
        """
        names = [[k, v] for k, v in self["name"].items()]
        self.peerplays.use_proposal_buffer()
        self.peerplays.sport_update(self["id"], names)


class WitnessLookupEventGroup(WitnessLookup, dict):
    def __init__(self, sport, eventgroup):
        self.identifier = "{}/{}".format(sport, eventgroup)
        super(WitnessLookupEventGroup, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert eventgroup in self.data["sports"][sport]["eventgroups"], \
            "Eventgroup {} not avaialble in sport {}".format(
                eventgroup, sport)
        dict.__init__(
            self,
            self.data["sports"][sport]["eventgroups"][eventgroup]
        )


class WitnessLookupBettingMarketGroup(WitnessLookup, dict):
    def __init__(self, sport, bmg):
        self.identifier = "{}/{}".format(sport, bmg)
        super(WitnessLookupBettingMarketGroup, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert bmg in self.data["sports"][sport]["bettingmarketgroups"], \
            "Bettingmarketgroup {} not avaialble in sport {}".format(
                bmg, sport)
        dict.__init__(
            self,
            self.data["sports"][sport]["bettingmarketgroups"][bmg]
        )


class WitnessLookupParticipants(WitnessLookup, dict):
    def __init__(self, sport, participants):
        self.identifier = "{}/{}".format(sport, participants)
        super(WitnessLookupParticipants, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert participants in self.data["sports"][sport]["participants"], \
            "Participants {} not avaialble in sport {}".format(
                participants, sport)
        # This is a list and not a dictionary!
        dict.__init__(
            self,
            self.data["sports"][sport]["participants"][participants]
        )


class WitnessLookupRules(WitnessLookup, dict):
    def __init__(self, sport, rules):
        self.identifier = "{}/{}".format(sport, rules)
        super(WitnessLookupRules, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert rules in self.data["sports"][sport]["rules"], \
            "rules {} not avaialble in sport {}".format(
                rules, sport)
        # This is a list and not a dictionary!
        dict.__init__(
            self,
            self.data["sports"][sport]["rules"][rules]
        )


if __name__ == "__main__":
    from getpass import getpass
    w = WitnessLookup()
    w.peerplays.wallet.unlock(getpass())
    w.peerplays.nobroadcast = True
    sport = WitnessLookupSport("AmericanFootball")
    # sport = WitnessLookupSport("Soccer")
    sport.update()
    """
    print(json.dumps(w, indent=4))
    print(json.dumps(w.data, indent=4))
    print(w.list_sports())
    print(WitnessLookupSport("AmericanFootball"))
    print(WitnessLookupEventGroup("AmericanFootball", "NFL#PreSeas"))
    print(WitnessLookupBettingMarketGroup(
        "AmericanFootball", "NFL_HCP_2017-18_1")
    )
    print(WitnessLookupParticipants("AmericanFootball", "NFL_Teams_2017-18"))
    print(WitnessLookupRules("AmericanFootball", "R_NFL_MO_1"))
    """
