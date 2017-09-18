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
from peerplays.eventgroup import EventGroups, EventGroup
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)
from peerplays.rule import Rules, Rule
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

# logging.basicConfig(level=logging.DEBUG)

UPDATE_PROPOSING_NEW = 1
UPDATE_PENDING_NEW = 2


class WitnessLookup(dict):

    #: Singelton to store data and prevent rereading if WitnessLookup is
    #: instantiated multiple times
    data = dict()
    approval_map = {}

    direct_buffer = None
    proposal_buffer = None

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
        self.proposing_account = proposing_account

        if not approving_account:
            if "default_account" in config:
                approving_account = config["default_account"]
            else:
                approving_account = approving_account
        self.approving_account = approving_account

        # We define two transaction buffers
        if not WitnessLookup.direct_buffer:
            WitnessLookup.direct_buffer = self.peerplays.new_txbuffer()
        if not WitnessLookup.proposal_buffer:
            WitnessLookup.proposal_buffer = self.peerplays.new_txbuffer(proposer=self.proposing_account)

        if not self.data:
            # Read main index.yaml
            data = self._loadyaml(os.path.join(self._cwd, "index.yaml"))
            super(WitnessLookup, self).__init__(data)

            # Load sports
            self.data["sports"] = self._loadSports()

            # _tests
            self._tests()

    def _use_direct_buffer(self):
        self.peerplays.set_txbuffer(self.direct_buffer)

    def _use_proposal_buffer(self):
        self.peerplays.set_txbuffer(self.proposal_buffer)

    def broadcast(self):
        """ Since we are using multiple txbuffers, we need to do multiple
            broadcasts
        """
        self._use_direct_buffer()
        self.peerplays.txbuffer.broadcast()
        self._use_proposal_buffer()
        self.peerplays.txbuffer.broadcast()

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
                log.error((
                    "Object {} carries id {} on the blockchain. "
                    "Please update your witness lookup"
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
        pending_proposals = Proposals(account)
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
        approved_read_for_delete = []
        for p in WitnessLookup.approval_map:
            if all(WitnessLookup.approval_map[p].values()):
                self._use_direct_buffer()
                proposal = Proposal(p)
                account = Account(self.approving_account)
                if account["id"] not in proposal["available_active_approvals"]:
                    log.info("Approving proposal {}".format(p))
                    approved_read_for_delete.append(p)
                    self._use_direct_buffer()
                    self.peerplays.approveproposal(
                        p,
                        account=self.approving_account
                    )
                else:
                    log.info(
                        "Proposal {} has already been approved by us".format(p)
                    )
        # In order not to approve the same proposal again and again, we remove
        # it from the map
        for p in approved_read_for_delete:
            del WitnessLookup.approval_map[p]

    def has_pending_new(self):
        """ This call tests if a pending proposal would create this object

            It only returns true if the exact content is proposed
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_create:
                if self.test_operation_equal(op[1]):
                    return pid, oid

        # FIXME: Test for our own proposals pending in txbuffer

    def has_pending_update(self):
        """ Test if there is an update to properly match blockchain content
            with witness lookup content
        """
        from peerplaysbase.operationids import getOperationNameForId
        for op, pid, oid in self.get_pending_operations():
            if getOperationNameForId(op[0]) == self.operation_update:
                if self.test_operation_equal(op[1]):
                    return pid, oid

        # FIXME: Test for our own proposals pending in txbuffer

    # Prototypes #############################################################
    def test_operation_equal(self, sport):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the witness lookup
        """
        pass

    def find_id(self):
        """ Try to find an id for the object of the witness lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
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

    @property
    def eventgroups(self):
        for e in self["eventgroups"]:
            yield WitnessLookupEventGroup(
                self.identifier, e)

    @property
    def rules(self):
        for e in self["rules"]:
            yield WitnessLookupRules(
                self.identifier, e)

    @property
    def participants(self):
        for e in self["participants"]:
            yield WitnessLookupParticipants(
                self.identifier, e)

    @property
    def bettingmarketgroups(self):
        for e in self["bettingmarketgroups"]:
            yield WitnessLookupBettingMarketGroup(
                self.identifier, e)

    def test_operation_equal(self, sport):
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
        sports = Sports(peerplays_instance=self.peerplays)
        for sport in sports:
            if (
                ["en", self["name"]["en"]] in sport["name"]
            ):
                return sport["id"]

    def is_synced(self):
        if "id" in self:
            sport = Sport(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        names = [[k, v] for k, v in self["name"].items()]
        self._use_proposal_buffer()
        self.peerplays.sport_create(
            names,
            account=self.proposing_account)

    def propose_update(self):
        names = [[k, v] for k, v in self["name"].items()]
        self._use_proposal_buffer()
        self.peerplays.sport_update(
            self["id"],
            names=names,
            account=self.proposing_account)


class WitnessLookupEventGroup(WitnessLookup, dict):

    operation_update = "event_group_update"
    operation_create = "event_group_create"

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

    def test_operation_equal(self, eventgroup):
        lookupnames = [[k, v] for k, v in self["name"].items()]
        chainsnames = [[]]
        if "name" in eventgroup:
            chainsnames = eventgroup["name"]
            sport_id = eventgroup["sport_id"]
        elif "new_name" in eventgroup:
            chainsnames = eventgroup["new_name"]
            sport_id = eventgroup["new_sport_id"]
        else:
            raise ValueError

        parts = sport_id.split(".")
        assert len(parts) == 3,\
            "{} is a strange sport object id".format(sport_id)
        if int(parts[0]) == 0:
            sport_id = ""

        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames]) and
                (sport_id and self["sport_id"] == sport_id)):
            return True

    def find_id(self):
        assert "sport_id" in self, "The {} ({}) has no sport_id".format(
            self.__class__.__name__, self["name"]["en"])
        if self["sport_id"]:
            egs = EventGroups(self["sport_id"], peerplays_instance=self.peerplays)
            for eg in egs:
                if (
                    ["en", self["name"]["en"]] in eg["name"] and
                    self.get("sport_id") == eg["sport_id"]
                ):
                    return eg["id"]

    def is_synced(self):
        if "id" in self:
            eventgroup = EventGroup(self["id"])
            if self.test_operation_equal(eventgroup):
                return True
        return False

    def propose_new(self):
        assert "sport_id" in self, "The {} ({}) has no sport_id".format(
            self.__class__.__name__, self["name"]["en"])
        if self["sport_id"]:
            names = [[k, v] for k, v in self["name"].items()]
            self._use_proposal_buffer()
            self.peerplays.event_group_create(
                names,
                sport_id=self["sport_id"],
                account=self.proposing_account
            )

    def propose_update(self):
        assert "sport_id" in self, "The {} ({}) has no sport_id".format(
            self.__class__.__name__, self["name"]["en"])
        if self["sport_id"]:
            names = [[k, v] for k, v in self["name"].items()]
            self._use_proposal_buffer()
            self.peerplays.event_group_update(
                self["id"],
                names=names,
                sport_id=self["sport_id"],
                account=self.proposing_account
            )


class WitnessLookupBettingMarketGroup(WitnessLookup, dict):

    operation_update = "betting_market_group_update"
    operation_create = "betting_market_group_create"

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

    def test_operation_equal(self, bmg):
        lookupdescr = [[k, v] for k, v in self["name"].items()]
        chainsdescr = [[]]
        if "description" in bmg:
            chainsdescr = bmg["description"]
            rulesid = bmg["rules_id"]
            freeze = ""
            delay_bets = ""
        elif "new_description" in bmg:
            chainsdescr = bmg["new_description"]
            rulesid = bmg["new_rules_id"]
            freeze = bmg["freeze"]
            delay_bets = bmg["delay_bets"]
        else:
            raise ValueError
        parts = rulesid.split(".")
        assert len(parts) == 3, \
            "{} is a strange rule object id".format(rulesid)
        if int(parts[0]) == 0:
            rules = False
        else:
            rules = Rules(rulesid)
        if (all([a in chainsdescr for a in lookupdescr]) and
                all([b in lookupdescr for b in chainsdescr]) and
                (rules and self["grading"]["rules"] in rules["name"])):
            # FIXME: How to deal with 'freeze' and 'delay_bets'?!?
            return True

    def find_id(self):
        return False

        bmgs = BettingMarketGroups(
            event_id="0.0.0",         # FIXME: This requires an event
            peerplays_instance=self.peerplays)
        for bmg in bmgs:
            if (
                ["en", self["name"]["en"]] in bmg["description"]
            ):
                return bmg["id"]

    def is_synced(self):
        if "id" in self:
            sport = BettingMarketGroup(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        descriptions = [[k, v] for k, v in self["description"].items()]
        self._use_proposal_buffer()
        self.peerplays.betting_market_rules_create(
            descriptions,
            event_id=self["event_id"],
            rules_id=0,
            account=self.proposing_account
        )
        # FIXME --- get rules ID by looking through the rules associated with
        # this sport and see if an id is provided .. if not, complain!

    def propose_update(self):
        names = [[k, v] for k, v in self["name"].items()]
        descriptions = [[k, v] for k, v in self["description"].items()]
        self._use_proposal_buffer()
        # FIXME here!
        # self.peerplays.sport_update(
        #    self["id"],
        #    names=names,
        #    descriptions=descriptions,
        #    account=self.proposing_account)


class WitnessLookupRules(WitnessLookup, dict):

    operation_update = "betting_market_rules_update"
    operation_create = "betting_market_rules_create"

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

    def find_id(self):
        rules = Rules(peerplays_instance=self.peerplays)
        for rule in rules:
            if (
                ["en", self["name"]["en"]] in rule["name"]
            ):
                return rule["id"]

    def is_synced(self):
        if "id" in self:
            sport = Rule(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        names = [[k, v] for k, v in self["name"].items()]
        descriptions = [[k, v] for k, v in self["description"].items()]
        self._use_proposal_buffer()
        self.peerplays.betting_market_rules_create(
            names,
            descriptions,
            account=self.proposing_account
        )

    def propose_update(self):
        names = [[k, v] for k, v in self["name"].items()]
        descriptions = [[k, v] for k, v in self["description"].items()]
        self._use_proposal_buffer()
        self.peerplays.sport_update(
            self["id"],
            names=names,
            descriptions=descriptions,
            account=self.proposing_account
        )


class WitnessLookupParticipants(WitnessLookup, dict):

    operation_update = ""
    operation_create = ""

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


if __name__ == "__main__":
    from getpass import getpass
    w = WitnessLookup()
    w.peerplays.wallet.unlock(getpass())
    w.peerplays.nobroadcast = True
    w.peerplays.bundle = True
    #for sport in w.list_sports():
    sport = WitnessLookupSport("Soccer")
    sport.update()
    for e in sport.eventgroups:
        e.update()
    for r in sport.rules:
        r.update()

    w.broadcast()

    """
    for p in sport.participants:
        p.update()
    for b in sport.bettingmarketgroups:
        b.update()
    """
    # sport.update()
    # eventgroup = WitnessLookupEventGroup("AmericanFootball", "NFL#PreSeas")
    # eventgroup.update()

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
