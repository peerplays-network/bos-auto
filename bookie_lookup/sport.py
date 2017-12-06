from peerplays.sport import Sports, Sport
from .lookup import Lookup
from .eventgroup import LookupEventGroup
from .rule import LookupRules
from .bettingmarketgroup import LookupBettingMarketGroup
from .participant import LookupParticipants
from .exceptions import ObjectNotFoundInLookup


class LookupSport(Lookup, dict):
    """ Lookup Class for a Sport

        :param str sport: Identifier for the Sport

    """

    operation_update = "sport_update"
    operation_create = "sport_create"

    def __init__(self, sport):
        self.identifier = sport
        super(LookupSport, self).__init__()

        if sport.lower() in [x.lower() for x in self.data["sports"]]:
            # Easy, the sports name is the key
            dict.__init__(self, self.data["sports"][sport])
        else:
            found = False
            # Load from identifier
            for name, s in self.data["sports"].items():
                if (
                    # Name
                    name.lower() == sport.lower() or
                    # Identifier
                    s.get("identifier", "").lower() == sport.lower() or
                    # List of languages
                    sport.lower() in [
                        x.lower()for x in s.get("name", {}).values()] or
                    # List of aliases
                    sport.lower() in [
                        x.lower() for x in s.get("aliases", [])]
                ):
                    found = True
                    dict.__init__(self, s)

            if not found:
                raise ObjectNotFoundInLookup("Not Found: {}".format(
                    sport))

    @property
    def eventgroups(self):
        """ Return instances of LookupEventGroup for all event groups in this
            sport
        """
        for e in self["eventgroups"]:
            yield LookupEventGroup(
                self.identifier, e)

    @property
    def rules(self):
        """ Return instances of LookupRules for all rules in this sport
        """
        for e in self["rules"]:
            yield LookupRules(
                self.identifier, e)

    @property
    def participants(self):
        """ Return instances of LookupParticipants for each participant in this
            sport
        """
        for e in self["participants"]:
            yield LookupParticipants(
                self.identifier, e)

    @property
    def bettingmarketgroups(self):
        """ Return isntances of LookupBettingMarketGroup for each betting market
            group of this sport
        """
        for e in self["bettingmarketgroups"]:
            yield LookupBettingMarketGroup(
                self.identifier, e)

    def test_operation_equal(self, sport):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """
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
        """ Try to find an id for the object of the  lookup on the
            blockchain

            ... note:: This only checks if a sport exists with the same name in
                       **ENGLISH**!
        """
        sports = Sports(peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))
        for sport in sports:
            if en_descrp in sport["name"]:
                return sport["id"]

    def is_synced(self):
        """ Test if data on chain matches lookup
        """
        if "id" in self:
            sport = Sport(self["id"])
            if self.test_operation_equal(sport):
                return True
        return False

    def propose_new(self):
        """ Propose operation to create this object
        """
        return self.peerplays.sport_create(
            self.names,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer)

    def propose_update(self):
        """ Propose to update this object to match  lookup
        """
        return self.peerplays.sport_update(
            self["id"],
            names=self.names,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer)

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
