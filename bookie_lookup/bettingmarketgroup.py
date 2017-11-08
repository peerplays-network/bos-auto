from .lookup import Lookup
from .rule import LookupRules
from peerplays.event import Event
from peerplays.rule import Rule
from peerplays.asset import Asset
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)


class MissingMandatoryValue(Exception):
    pass


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
        for mandatory in [
            "name",
            "asset",
            "bettingmarkets",
            "rules",
        ]:
            if mandatory not in self:
                raise MissingMandatoryValue(
                    "A value for '{}' is mandatory".format(
                        mandatory
                    )
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

        def is_create(bmg):
            return any([x in bmg for x in [
                "description", "event_id", "rules_id"]])

        if not is_create(bmg) and not is_update(bmg):
            raise ValueError

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

        # Test if Rules and Events exist
        # only if the id starts with 1.
        test_rule = rules_id[0] == 1
        if test_rule:
            Rule(rules_id)

        test_event = event_id[0] == 1
        if test_event:
            Event(event_id)

        if (
            all([a in chainsdescr for a in lookupdescr]) and
            all([b in lookupdescr for b in chainsdescr]) and
            (not test_event or event_id == self.event.id) and
            (not test_rule or rules_id == self.rules.id) and
            (self.get("frozen", False) == frozen) and
            (self.get("delay_bets", False) == delay_bets)
        ):
            return True
        return False

    def find_id(self):
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        if self.parent.id[0] == "0":
            return

        bmgs = BettingMarketGroups(
            self.parent.id,
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
        return self.peerplays.betting_market_group_create(
            self.names,
            event_id=self.event.id,
            rules_id=self.rules.id,
            asset=asset["id"],
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        return self.peerplays.betting_market_group_update(
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
