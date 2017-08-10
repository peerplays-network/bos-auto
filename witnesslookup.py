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
            sport = os.path.basename(sportDir)
            ret[sport] = self.loadSport(sportDir)
        return ret

    def loadSport(self, sportDir):
        sport = self.loadyaml(os.path.join(sportDir, "index.yaml"))
        eventgroups = dict()
        for eventgroup in sport["eventgroups"]:
            eventgroups[eventgroup] = self.loadEventGroup(os.path.join(sportDir, eventgroup))
        sport["eventgroups"] = eventgroups
        return sport

    def loadEventGroup(self, eventgroupDir):
        eventgroup = self.loadyaml(os.path.join(eventgroupDir, "index.yaml"))
        events = dict()
        for event in eventgroup["events"]:
            events[event] = self.loadEvent(os.path.join(eventgroupDir, event))

        # Rules
        rulesDir = os.path.join(eventgroupDir, "rules")
        rules = dict()
        for ruleDir in glob(os.path.join(rulesDir, "*")):
            rule = os.path.basename(ruleDir).replace(".yaml", "")
            rules[rule] = self.loadyaml(ruleDir)

        # participants
        participantsDir = os.path.join(eventgroupDir, "participants")
        participants = dict()
        for participantDir in glob(os.path.join(participantsDir, "*")):
            participant = os.path.basename(participantDir).replace(".yaml", "")
            participants[participant] = self.loadyaml(participantDir)

        # def_bmgs
        def_bmgsDir = os.path.join(eventgroupDir, "def_bmg")
        def_bmgs = dict()
        for def_bmgDir in glob(os.path.join(def_bmgsDir, "*")):
            def_bmg = os.path.basename(def_bmgDir).replace(".yaml", "")
            def_bmgs[def_bmg] = self.loadyaml(def_bmgDir)

        eventgroup["rules"] = rules
        eventgroup["participants"] = participants
        eventgroup["def_bmgs"] = def_bmgs
        eventgroup["events"] = events

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


if __name__ == "__main__":
    w = WitnessLookup()
    print(json.dumps(w, indent=4))
