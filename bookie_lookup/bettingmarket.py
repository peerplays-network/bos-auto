from .lookup import Lookup
from .rule import LookupRules
from peerplays.bettingmarket import (
    BettingMarket, BettingMarkets)
from peerplays.bettingmarketgroup import (
    BettingMarketGroup, BettingMarketGroups)


class LookupBettingMarket(Lookup, dict):
    operation_update = "betting_market_update"
    operation_create = "betting_market_create"

    def __init__(self, market, bmg):
        Lookup.__init__(self)
        self.identifier = "{}/{}".format(
            bmg["name"]["en"],
            market["name"]["en"]
        )
        self.bmg = bmg
        self.parent = bmg
        dict.__init__(
            self,
            market
        )
        # FIXME: Figure out if the name has a variable
        # FIXME: Figure out if this is a dynamic bmg

        # First team is Home Team, second is away team
        self["HomeTeam"] = self.event["teams"][0]
        self["AwayTeam"] = self.event["teams"][1]

    @property
    def event(self):
        return self.parent.event

    @property
    def group(self):
        return self.parent

    def test_operation_equal(self, bmg):
        def is_update(bmg):
            return any([x in bmg for x in [
                "new_group_id", "new_description",
                "betting_market_id"]])

        def is_create(bmg):
            return any([x in bmg for x in [
                "group_id", "description"]])

        if not is_create(bmg) and not is_update(bmg):
            raise ValueError

        lookupdescr = self.description
        chainsdescr = [[]]
        prefix = "new_" if is_update(bmg) else ""
        chainsdescr = bmg[prefix + "description"]
        group_id = bmg[prefix + "group_id"]

        test_group = group_id[0] == 1
        if test_group:
            BettingMarketGroup(group_id)

        if (all([a in chainsdescr for a in lookupdescr]) and
                all([b in lookupdescr for b in chainsdescr]) and
                (not test_group or group_id == self.group.id)):
            return True
        return False

    def find_id(self):
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        if self.parent.id[0] == "0":
            return

        bms = BettingMarkets(
            self.parent.id,
            peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.description))

        for bm in bms:
            if en_descrp in bm["description"]:
                return bm["id"]

    def is_synced(self):
        if "id" in self:
            bmg = BettingMarket(self["id"])
            if self.test_operation_equal(bmg):
                return True
        return False

    def propose_new(self):
        return self.peerplays.betting_market_create(
            description=self.description,
            payout_condition=[],
            group_id=self.parent.id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        return self.peerplays.betting_market_update(
            self.id,
            payout_condition=[],
            description=self.description,
            group_id=self.parent.id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def description(self):
        """ This method ensures that the description has the proper format as
            well as the proper string replacements for teams
        """
        return [
            [
                k,
                v.format(**self)   # replace variables
            ] for k, v in self["name"].items()
        ]
