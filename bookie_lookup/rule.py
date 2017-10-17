from .lookup import Lookup
from peerplays.rule import Rules, Rule


class LookupRules(Lookup, dict):

    operation_update = "betting_market_rules_update"
    operation_create = "betting_market_rules_create"

    def __init__(self, sport, rules):
        self.identifier = "{}/{}".format(sport, rules)
        super(LookupRules, self).__init__()
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

    def test_operation_equal(self, operation):
        lookupnames = [[k, v] for k, v in self["description"].items()]
        chainsnames = [[]]
        if "name" in operation:
            chainsnames = operation["description"]
        elif "new_name" in operation:
            chainsnames = operation["new_description"]
        else:
            raise ValueError

        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames])):
            return True

    def propose_new(self):
        names = [[k, v] for k, v in self["name"].items()]
        descriptions = [[k, v] for k, v in self["description"].items()]
        self.peerplays.betting_market_rules_create(
            names,
            descriptions,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        names = [[k, v] for k, v in self["name"].items()]
        descriptions = [[k, v] for k, v in self["description"].items()]
        self.peerplays.sport_update(
            self["id"],
            names=names,
            descriptions=descriptions,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )
