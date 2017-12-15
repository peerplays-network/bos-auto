from .lookup import Lookup


class LookupParticipants(Lookup, dict):
    """ Lookup Class for participants

        :param str sport: Identifier for sport
        :param str list_identifier: Identifier for the list of participants
    """

    operation_update = ""
    operation_create = ""

    def __init__(self, sport, list_identifier):
        self.identifier = "{}/{}".format(sport, list_identifier)
        super(LookupParticipants, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )

        if list_identifier in self.data["sports"][sport]["participants"]:
            dict.__init__(
                self,
                self.data["sports"][sport]["participants"][list_identifier]
            )

    def is_participant(self, name):
        """ See if we can find a particular participant in the list of
            participants (self)
        """
        parties = self.get("participants")
        for team in parties:
            if (
                name.lower() in [
                    x.lower() for x in team.get("name", {}).values()] or
                name.lower() in [
                    x.lower() for x in team.get("aliases", [])]
            ):
                return True
        return False
