from .lookup import Lookup
from peerplays.rule import Rules, Rule


class LookupRules(Lookup, dict):
    """ Lookup Class for Rule

        :param str sport: Sport Identifier
        :param str rules: Rules Identifier
    """

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

    def test_operation_equal(self, operation):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """
        lookupnames = self.descriptions
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

    def find_id(self):
        """ Try to find an id for the object of the  lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
        """
        rules = Rules(peerplays_instance=self.peerplays)
        for rule in rules:
            if (
                ["en", self["name"]["en"]] in rule["name"]
            ):
                return rule["id"]

    def is_synced(self):
        """ Test if data on chain matches lookup
        """
        if "id" in self:
            sport = Rule(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        """ Propose operation to create this object
        """
        return self.peerplays.betting_market_rules_create(
            self.names,
            self.descriptions,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        """ Propose to update this object to match  lookup
        """
        return self.peerplays.betting_market_rules_update(
            self["id"],
            names=self.names,
            descriptions=self.descriptions,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def names(self):
        """ Properly format names for internal use
        """
        return [
            [
                k,
                v
            ] for k, v in self["name"].items()
        ]

    @property
    def descriptions(self):
        """ Properly format descriptions for internal use
        """
        return [
            [
                k,
                v
            ] for k, v in self["description"].items()
        ]
