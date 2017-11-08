from peerplays.sport import Sports, Sport
from .lookup import Lookup
from .eventgroup import LookupEventGroup
from .rule import LookupRules
from .bettingmarketgroup import LookupBettingMarketGroup
from .participant import LookupParticipants


class LookupSport(Lookup, dict):

    operation_update = "sport_update"
    operation_create = "sport_create"

    def __init__(self, sport):
        self.identifier = sport
        super(LookupSport, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        if sport in self.data["sports"]:
            # Load from name
            dict.__init__(self, self.data["sports"][sport])
        else:
            # Load from identifier
            for s in self.data["sports"]:
                if s["identifier"] == sport:
                    dict.__init__(self, s)

    @property
    def eventgroups(self):
        for e in self["eventgroups"]:
            yield LookupEventGroup(
                self.identifier, e)

    @property
    def rules(self):
        for e in self["rules"]:
            yield LookupRules(
                self.identifier, e)

    @property
    def participants(self):
        for e in self["participants"]:
            yield LookupParticipants(
                self.identifier, e)

    @property
    def bettingmarketgroups(self):
        for e in self["bettingmarketgroups"]:
            yield LookupBettingMarketGroup(
                self.identifier, e)

    def test_operation_equal(self, sport):
        lookupnames = self.names
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
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))
        for sport in sports:
            if en_descrp in sport["name"]:
                return sport["id"]

    def is_synced(self):
        if "id" in self:
            sport = Sport(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        return self.peerplays.sport_create(
            self.names,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer)

    def propose_update(self):
        return self.peerplays.sport_update(
            self["id"],
            names=self.names,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer)

    @property
    def names(self):
        return [
            [
                k,
                v
            ] for k, v in self["name"].items()
        ]
