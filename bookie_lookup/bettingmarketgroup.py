from .lookup import Lookup
from .rule import LookupRules
from peerplays.event import Event
from peerplays.asset import Asset
from peerplays.rule import Rules
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)


class LookupBettingMarketGroup(Lookup, dict):

    operation_update = "betting_market_group_update"
    operation_create = "betting_market_group_create"

    def __init__(self, bmg, event):
        Lookup.__init__(self)
        self.identifier = "{}/{}".format(
            event["name"]["en"],
            bmg["name"]["en"]
        )
        self.event = event
        self.parent = event
        dict.__init__(
            self,
            bmg
        )
        # FIXME: Figure out if the name has a variable
        # FIXME: Figure out if this is a dynamic bmg

    @property
    def sport(self):
        return self.parent.sport

    @property
    def rules(self):
        assert self["rules"] in self.sport["rules"]
        return LookupRules(self.sport["identifier"], self["rules"])

    def test_operation_equal(self, bmg):
        def is_update(bmg):
            return any([x in bmg for x in [
                "betting_market_group_id", "new_description",
                "new_event_id", "new_rules_id"]])

        lookupdescr = self.names
        chainsdescr = [[]]
        prefix = "new_" if is_update(bmg) else ""
        chainsdescr = bmg[prefix + "description"]
        rules_id = bmg[prefix + "rules_id"]
        event_id = bmg[prefix + "event_id"]
        if is_update(bmg):
            frozen = bmg["frozen"]
            delay_bets = bmg["delay_bets"]
        else:
            frozen = False
            delay_bets = False

        if rules_id[0] == 1:
            rules = Rules(rules_id)
        if event_id[0] == 1:
            rules = Event(event_id)

        if (all([a in chainsdescr for a in lookupdescr]) and
                all([b in lookupdescr for b in chainsdescr]) and
                (event_id == self.event.id) and
                (rules_id == self.rules.id) and
                (self.get("frozen", False) == frozen) and
                (self.get("delay_bets", False) == delay_bets)
            ):
            return True

    def find_id(self):
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        if self.parent.id[0] == "0":
            return

        bmgs = BettingMarketGroups(
            event_id=self.parent.id,
            peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))

        for bmg in bmgs:
            if en_descrp in bmg["description"]:
                return bmg["id"]

    def is_synced(self):
        if "id" in self:
            bmg = BettingMarketGroup(self["id"])
            if self.test_operation_equal(bmg):
                return True
        return False

    def propose_new(self):
        asset = Asset(
            self["asset"],
            peerplays_instance=self.peerplays)
        self.peerplays.betting_market_group_create(
            self.names,
            event_id=self.event.id,
            rules_id=self.rules.id,
            asset=asset["id"],
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        asset = Asset(
            self["asset"],
            peerplays_instance=self.peerplays)
        self.peerplays.betting_market_group_update(
            self.id,
            self.names,
            event_id=self.event.id,
            rules_id=self.rules.id,
            frozen=self.get("frozen", False),
            delay_bets=self.get("delay_bets", False),
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def bettingmarkets(self):
        from pprint import pprint
        from .bettingmarket import LookupBettingMarket
        for market in self["bettingmarkets"]:
            yield LookupBettingMarket(market, self)

    @property
    def names(self):
        return [
            [
                k,
                v
            ] for k, v in self["name"].items()
        ]
