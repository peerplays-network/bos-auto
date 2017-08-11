import sys
import os
import yaml
import json
from pprint import pprint
from glob import glob


class WitnessLookup(dict):

    def __init__(self, *args, **kwargs):
        """ Let's load all the data from the folder and its subfolders
        """
        self._cwd = os.path.dirname(os.path.realpath(__file__))

        # Read main index.yaml
        data = self.loadyaml(os.path.join(self._cwd, "index.yaml"))
        super(WitnessLookup, self).__init__(data)

        # Load sports
        self["sports"] = self.loadSports()

        # Tests
        self.tests()

    def loadyaml(self, f):
        try:
            t = yaml.load(open(f))
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
            eventgroups[eventgroup] = self.loadEventGroup(os.path.join(sportDir, eventgroup))
        sport["eventgroups"] = eventgroups

        # Rules
        rulesDir = os.path.join(sportDir, "rules")
        rules = dict()
        for ruleDir in glob(os.path.join(rulesDir, "*")):
            if not ".yaml" in ruleDir:
                continue
            rule = os.path.basename(ruleDir).replace(".yaml", "")
            rules[rule] = self.loadyaml(ruleDir)
        sport["rules"] = rules

        # participants
        participantsDir = os.path.join(sportDir, "participants")
        participants = dict()
        for participantDir in glob(os.path.join(participantsDir, "*")):
            if not ".yaml" in participantDir:
                continue
            participant = os.path.basename(participantDir).replace(".yaml", "")
            participants[participant] = self.loadyaml(participantDir)
        sport["participants"] = participants

        # def_bmgs
        def_bmgsDir = os.path.join(sportDir, "bettingmarketgroups")
        def_bmgs = dict()
        for def_bmgDir in glob(os.path.join(def_bmgsDir, "*")):
            if not ".yaml" in def_bmgDir:
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
        for bettingmarketgroup in event["bettingmarketgroups"]:
            bettingmarketgroups[bettingmarketgroup] = self.loadBettingMarketGroup(os.path.join(eventDir, bettingmarketgroup))
        event["bettingmarketgroups"] = bettingmarketgroups
        return event

    def loadBettingMarketGroup(self, bmgDir):
        bmg = self.loadyaml(os.path.join(bmgDir, "index.yaml"))
        return bmg

    def tests(self):
        """ Tests and requirements
        """
        for sportname, sport in self["sports"].items():
            self.test_required_attributes(sport, sportname, ["name", "id"])

            for evengroupname, eventgroup in sport["eventgroups"].items():
                self.test_required_attributes(eventgroup, evengroupname, ["name", "id"])

                for bmg in eventgroup["bettingmarketgroups"]:
                    # Test that each used BMG is deinfed
                    assert bmg in sport["bettingmarketgroups"], \
                        "Betting market group {} is used in {}:{} but wasn't defined!".format(
                            bmg, sportname, evengroupname
                        )
            for rule in sport["rules"]:
                pass
            for bettingmarketgroupname, bettingmarketgroup in sport["bettingmarketgroups"].items():
                self.test_required_attributes(bettingmarketgroup, bettingmarketgroupname, ["name"])

                # Test that each used rule is defined
                assert bettingmarketgroup["grading"]["rules"] in sport["rules"], \
                    "Rule {} is used in {}:{} but wasn't defined!".format(
                        bettingmarketgroup["grading"]["rules"],
                        sportname, 
                        bettingmarketgroupname
                    )

                for bettingmarkets in bettingmarketgroup["bettingmarkets"]:
                    self.test_required_attributes(bettingmarkets, bettingmarketgroupname, ["name"])

    def test_required_attributes(self, data, name, checks):
        for check in checks:
            assert check in data, "{} is missing a {}".format(name, check)


if __name__ == "__main__":
    w = WitnessLookup()
    print(json.dumps(w, indent=4))
