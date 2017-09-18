from peerplays.sport import Sports, Sport
from .lookup import WitnessLookup
from .eventgroup import WitnessLookupEventGroup
from .rule import WitnessLookupRules
from .bettingmarketgroup import WitnessLookupBettingMarketGroup
from .participant import WitnessLookupParticipants


class WitnessLookupSport(WitnessLookup, dict):

    operation_update = "sport_update"
    operation_create = "sport_create"

    def __init__(self, sport):
        self.identifier = sport
        super(WitnessLookupSport, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        dict.__init__(self, self.data["sports"][sport])

    @property
    def eventgroups(self):
        for e in self["eventgroups"]:
            yield WitnessLookupEventGroup(
                self.identifier, e)

    @property
    def rules(self):
        for e in self["rules"]:
            yield WitnessLookupRules(
                self.identifier, e)

    @property
    def participants(self):
        for e in self["participants"]:
            yield WitnessLookupParticipants(
                self.identifier, e)

    @property
    def bettingmarketgroups(self):
        for e in self["bettingmarketgroups"]:
            yield WitnessLookupBettingMarketGroup(
                self.identifier, e)

    def test_operation_equal(self, sport):
        lookupnames = [[k, v] for k, v in self["name"].items()]
        chainsnames = [[]]
        if "name" in sport:
            chainsnames = sport["name"]
        elif "new_name" in sport:
            chainsnames = sport["new_name"]
        else:
            raise ValueError
        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames])):
            return True

    def find_id(self):
        sports = Sports(peerplays_instance=self.peerplays)
        for sport in sports:
            if (
                ["en", self["name"]["en"]] in sport["name"]
            ):
                return sport["id"]

    def is_synced(self):
        if "id" in self:
            sport = Sport(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        names = [[k, v] for k, v in self["name"].items()]
        self._use_proposal_buffer()
        self.peerplays.sport_create(
            names,
            account=self.proposing_account)

    def propose_update(self):
        names = [[k, v] for k, v in self["name"].items()]
        self._use_proposal_buffer()
        self.peerplays.sport_update(
            self["id"],
            names=names,
            account=self.proposing_account)
