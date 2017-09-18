from .lookup import WitnessLookup
from peerplays.rule import Rules, Rule
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)


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
            # freeze = ""
            # delay_bets = ""
        elif "new_description" in bmg:
            chainsdescr = bmg["new_description"]
            rulesid = bmg["new_rules_id"]
            # freeze = bmg["freeze"]
            # delay_bets = bmg["delay_bets"]
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
        pass
        # names = [[k, v] for k, v in self["name"].items()]
        # descriptions = [[k, v] for k, v in self["description"].items()]
        # self._use_proposal_buffer()
        # FIXME here!
        # self.peerplays.sport_update(
        #    self["id"],
        #    names=names,
        #    descriptions=descriptions,
        #    account=self.proposing_account)
