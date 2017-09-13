import sys
import os
import yaml
import json
from pprint import pprint
from glob import glob
import logging
log = logging.getLogger(__name__)


UPDATE_PROPOSING_NEW = 1
UPDATE_PENDING_NEW = 2


class WitnessLookup(dict):

    # Singelton to store data and prevent rereading if WitnessLookup is
    # instantiated multiple times
    data = dict()

    def __init__(self, *args, **kwargs):
        """ Let's load all the data from the folder and its subfolders
        """
        self._cwd = os.path.dirname(os.path.realpath(__file__))

        if not self.data:
            # Read main index.yaml
            data = self.loadyaml(os.path.join(self._cwd, "index.yaml"))
            super(WitnessLookup, self).__init__(data)

            # Load sports
            self.data["sports"] = self.loadSports()

            # Tests
            self.tests()

    def loadyaml(self, f):
        try:
            t = yaml.load(open(f))
            pprint(t)
            return t
        except yaml.YAMLError as exc:
            print("Error in configuration file {}: {}".format(f, exc))
            sys.exit(1)
        except:
            print("The file {} is required but doesn't exist!".format(f))
            sys.exit(1)

    def loadSports(self):
        ret = dict()
        for sportDir in glob(os.path.join(self._cwd, "sports/*")):
            if not os.path.isdir(sportDir):
                continue
            sport = os.path.basename(sportDir)
            ret[sport] = self.loadSport(sportDir)
        return ret

    def loadSport(self, sportDir):
        sport = self.loadyaml(os.path.join(sportDir, "index.yaml"))
        eventgroups = dict()
        for eventgroup in sport["eventgroups"]:
            eventgroups[eventgroup] = self.loadEventGroup(
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
            rules[rule] = self.loadyaml(ruleDir)
        sport["rules"] = rules

        # participants
        participantsDir = os.path.join(sportDir, "participants")
        participants = dict()
        for participantDir in glob(os.path.join(participantsDir, "*")):
            if ".yaml" not in participantDir:
                continue
            participant = os.path.basename(participantDir).replace(".yaml", "")
            participants[participant] = self.loadyaml(participantDir)
        sport["participants"] = participants

        # def_bmgs
        def_bmgsDir = os.path.join(sportDir, "bettingmarketgroups")
        def_bmgs = dict()
        for def_bmgDir in glob(os.path.join(def_bmgsDir, "*")):
            if ".yaml" not in def_bmgDir:
                continue
            def_bmg = os.path.basename(def_bmgDir).replace(".yaml", "")
            def_bmgs[def_bmg] = self.loadyaml(def_bmgDir)
        sport["bettingmarketgroups"] = def_bmgs

        return sport

    def loadEventGroup(self, eventgroupDir):
        eventgroup = self.loadyaml(os.path.join(eventgroupDir, "index.yaml"))

        """
        # Events
        events = dict()
        for event in eventgroup["events"]:
            events[event] = self.loadEvent(os.path.join(eventgroupDir, event))
        eventgroup["events"] = events
        """

        return eventgroup

    def loadEvent(self, eventDir):
        event = self.loadyaml(os.path.join(eventDir, "index.yaml"))
        bettingmarketgroups = dict()
        for bmg in event["bettingmarketgroups"]:
            bettingmarketgroups[bmg] = self.loadBettingMarketGroup(
                os.path.join(eventDir, bmg)
            )
        event["bettingmarketgroups"] = bettingmarketgroups
        return event

    def loadBettingMarketGroup(self, bmgDir):
        bmg = self.loadyaml(os.path.join(bmgDir, "index.yaml"))
        return bmg

    def tests(self):
        """ Tests and requirements
        """
        for sportname, sport in self.data["sports"].items():
            self.test_required_attributes(sport, sportname, ["name", "id"])

            for evengroupname, eventgroup in sport["eventgroups"].items():
                self.test_required_attributes(
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
                self.test_required_attributes(bmg, bmgname, ["name"])

                # Test that each used rule is defined
                assert bmg["grading"]["rules"] in sport["rules"], \
                    "Rule {} is used in {}:{} but wasn't defined!".format(
                        bmg["grading"]["rules"],
                        sportname,
                        bmgname)

                for bettingmarkets in bmg["bettingmarkets"]:
                    self.test_required_attributes(
                        bettingmarkets,
                        bmgname,
                        ["name"]
                    )

    def test_required_attributes(self, data, name, checks):
        for check in checks:
            assert check in data, "{} is missing a {}".format(name, check)

    # List calls
    def list_sports(self):
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
        if "id" not in self.data or not self.data["id"]:

            # Test if an object with the characteristics (i.e. name) exist
            id = self.find_id()
            if id:
                log.warn((
                    "Object {} carries id {} on the blockchain. "
                    "Please update your witness lookup"
                ).format(self.identifier, id))
                self.data["id"] = id
            elif self.has_pending_new():
                self.approve_new()
                return UPDATE_PENDING_NEW
            else:
                # Propose the creation of this object
                self.propose_new()
                return UPDATE_PROPOSING_NEW

        if not self.is_synced():
            if self.has_pending_update():
                self.approve_update()
            else:
                self.propose_update()


class WitnessLookupSport(WitnessLookup, dict):
    def __init__(self, sport):
        self.identifier = sport
        super(WitnessLookupSport, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        dict.__init__(self, self.data["sports"][sport])

    def find_id():
        """ Try to find an id for the object of the witness lookup on the
            blockchain
        """
        pass

    def is_synced(self):
        """ Test if data on chain matches witness lookup
        """
        # Compare blockchain content with witness lookup

    def has_pending_new(self):
        """ This call tests if a pending proposal would create this object

            It only returns true if the exact content is proposed
        """
        pass

    def has_pending_update(self):
        """ Test if there is an update to properly match blockchain content
            with witness lookup content
        """
        pass

    def propose_new(self):
        """ Propose operation to create this object
        """
        pass

    def propose_update(self):
        """ Propose to update this object to match witness lookup
        """
        pass

    def approve_new(self):
        """ Approve a proposal for creation

            This call approves a proposal that would create a new object.

            The call has to identify the correct operation of a proposal on its
            own.
        """
        pass

    def approve_update(self):
        """ Approve a proposal

            This call basically flags a single update operation of a proposal
            as "approved". Only if all operations in the proposal are approved,
            will this tool approve the whole proposal and otherwise ignore the
            proposal.

            The call has to identify the correct operation of a proposal on its
            own.
        """
        pass


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
    w = WitnessLookup()
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
