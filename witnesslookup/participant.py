from .lookup import WitnessLookup


class WitnessLookupParticipants(WitnessLookup, dict):

    operation_update = ""
    operation_create = ""

    def __init__(self, sport, participants):
        self.identifier = "{}/{}".format(sport, participants)
        super(WitnessLookupParticipants, self).__init__()
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
