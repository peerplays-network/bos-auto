from .lookup import Lookup
from .rule import LookupRules
from .exceptions import MissingMandatoryValue
from peerplays.event import Event
from peerplays.rule import Rule
from peerplays.asset import Asset
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)


class LookupBettingMarketGroup(Lookup, dict):
    """ Lookup Class for betting market groups

        :param dict bmg: Lookup content (files) for the BMG
        :param LookupEvent event: Parent LookupEvent for BMG
        :param dict extra_data: Optionally provide additional data that is
               stored in the same dictionary

    """

    operation_update = "betting_market_group_update"
    operation_create = "betting_market_group_create"

    def __init__(
        self,
        bmg,
        event,
        extra_data={}
    ):
        Lookup.__init__(self)
        self.identifier = "{}/{}".format(
            event.names_json["en"],
            bmg["description"]["en"]
        )
        self.event = event
        self.parent = event
        dict.__init__(self, extra_data)
        dict.update(
            self,
            bmg
        )
        for mandatory in [
            "description",
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
        """ Return the sport for this BMG
        """
        return self.parent.sport

    @property
    def rules(self):
        """ Return instance of LookupRules for this BMG
        """
        assert self["rules"] in self.sport["rules"]
        return LookupRules(self.sport["identifier"], self["rules"])

    def test_operation_equal(self, bmg):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """
        def is_update(bmg):
            return any([x in bmg for x in [
                "betting_market_group_id", "new_description",
                "new_event_id", "new_rules_id"]])

        def is_create(bmg):
            return any([x in bmg for x in [
                "description", "event_id", "rules_id"]])

        if not is_create(bmg) and not is_update(bmg):
            raise ValueError

        lookupdescr = self.description
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
        """ Try to find an id for the object of the  lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
        """
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        parent_id = self.parent.id
        if parent_id[0] == "0" or parent_id[:4] == "1.10":
            return

        bmgs = BettingMarketGroups(
            self.parent.id,
            peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.description))

        for bmg in bmgs:
            if en_descrp in bmg["description"]:
                return bmg["id"]

    def is_synced(self):
        """ Test if data on chain matches lookup
        """
        if "id" in self:
            bmg = BettingMarketGroup(self["id"])
            if self.test_operation_equal(bmg):
                return True
        return False

    def propose_new(self):
        """ Propose operation to create this object
        """
        asset = Asset(
            self["asset"],
            peerplays_instance=self.peerplays)
        return self.peerplays.betting_market_group_create(
            self.description,
            event_id=self.event.id,
            rules_id=self.rules.id,
            asset=asset["id"],
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        """ Propose to update this object to match  lookup
        """
        return self.peerplays.betting_market_group_update(
            self.id,
            self.description,
            event_id=self.event.id,
            rules_id=self.rules.id,
            frozen=self.get("frozen", False),
            delay_bets=self.get("delay_bets", False),
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def bettingmarkets(self):
        """ Return instances of LookupBettingMarket for this BMG
        """

        from .bettingmarket import LookupBettingMarket

        # Allow to overwrite the variables that might be in the betting market
        # definition (such as home team and away team names)
        class Teams:
            home = " ".join([
                x.capitalize() for x in self.event["teams"][0].split(" ")])
            away = " ".join([
                x.capitalize() for x in self.event["teams"][1].split(" ")])

        for market in self["bettingmarkets"]:
            description = dict()

            # Overwrite the description with with proper replacement of variables
            for k, v in market["description"].items():
                description[k] = v.format(
                    teams=Teams
                )
            yield LookupBettingMarket(
                description=description,
                bmg=self
            )

    @property
    def description(self):
        """ Properly format description for internal use
        """
        return [
            [
                k,
                v
            ] for k, v in self["description"].items()
        ]
