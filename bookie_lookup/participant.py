from .lookup import Lookup


class LookupParticipants(Lookup, dict):
    """ Lookup Class for participants

        :param str sport: Identifier for sport
        :param str participants: Identifier for Participants
    """

    operation_update = ""
    operation_create = ""

    def __init__(self, sport, participants):
        self.identifier = "{}/{}".format(sport, participants)
        super(LookupParticipants, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert participants in self.data["sports"][sport]["participants"], \
            "Participants {} not avaialble in sport {}".format(
                participants, sport)
        # This is a list and not a dictionary!
        dict.__init__(
            self,
            self.data["sports"][sport]["participants"][participants]
        )
