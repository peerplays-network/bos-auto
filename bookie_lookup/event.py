import re
import sys
import datetime
from .lookup import Lookup
from .sport import LookupSport
from peerplays.event import Event, Events
from peerplays.eventgroup import EventGroup
from .eventgroup import LookupEventGroup
from .bettingmarketgroup import LookupBettingMarketGroup
from . import log


class MissingMandatoryValue(Exception):
    pass


class LookupEvent(Lookup, dict):

    operation_update = "event_update"
    operation_create = "event_create"

    def __init__(self, *args, **kwargs):
        Lookup.__init__(self)

        # Initialise our 'dict'
        if len(args) == 1 and isinstance(args[0], dict):
            dict.__init__(self, args[0])
        elif len(args) == 0 and isinstance(kwargs, dict):
            dict.__init__(self, **kwargs)
        else:
            raise ValueError

        for mandatory in [
            "name",
            "teams",
            "eventgroup_identifier",
            "sport_identifier",
            "season",
            "start_time"
        ]:
            if mandatory not in self:
                raise MissingMandatoryValue(
                    "A value for '{}' is mandatory".format(
                        mandatory
                    )
                )

        if not isinstance(self["start_time"], datetime.datetime):
            raise ValueError("'start_time' must be instance of datetime.datetime()")

        self.parent = self.eventgroup
        self.identifier = "{}/{}".format(
            self.parent["name"]["en"], self["name"]["en"])

        teams = re.split(r"[:@]", self["teams"])
        assert len(teams) == 2, (
            "Only matches with two players are allowed! "
            "Here: {}".format(str(teams))
        )
        self["teams"] = [t.strip() for t in teams]

    @property
    def sport(self):
        return LookupSport(self["sport_identifier"])

    @property
    def teams(self):
        return self["teams"]

    @property
    def eventgroup(self):
        """ Get the event group that corresponds to this event
        """
        sport = LookupSport(self["sport_identifier"])
        return(LookupEventGroup(
            sport["identifier"],
            self["eventgroup_identifier"]))

    def test_operation_equal(self, event):
        # FIXME: This might need additional data to ensure the events are equal
        # start_time, is_live_market
        lookupnames = self.names
        chainsnames = [[]]
        if "name" in event:
            chainsnames = event["name"]
            event_group_id = event["event_group_id"]
        elif "new_name" in event:
            chainsnames = event["new_name"]
            event_group_id = event["new_sport_id"]
        else:
            raise ValueError

        parts = event_group_id.split(".")
        assert len(parts) == 3,\
            "{} is a strange sport object id".format(event_group_id)
        if int(parts[0]) == 0:
            event_group_id = ""

        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames]) and
                (not event_group_id or self.parent_id == event_group_id)):
            return True

    def find_id(self):
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        if self.parent.id[0] == "0":
            return

        events = Events(
            self.parent_id,
            peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))

        for event in events:
            if en_descrp in event["name"]:
                return event["id"]

    def is_synced(self):
        if "id" in self and self["id"]:
            event = Event(self["id"])
            if self.test_operation_equal(event):
                return True
        return False

    def propose_new(self):
        return self.peerplays.event_create(
            self.names,
            self.season,
            self["start_time"],
            event_group_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        return self.peerplays.event_update(
            self["id"],
            self.names,
            self.season,
            self["start_time"],
            event_group_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def lookup_participants(self):
        name = self.eventgroup["participants"]
        return self.eventgroup.sport["participants"][name]["participants"]

    def lookup_bettingmarketgroups(self):
        names = self.eventgroup["bettingmarketgroups"]
        for name in names:
            yield self.eventgroup.sport["bettingmarketgroups"][name]

    @property
    def names(self):
        return [
            [
                k,
                v
            ] for k, v in self["name"].items()
        ]

    @property
    def season(self):
        return [
            [
                k,
                v
            ] for k, v in self["season"].items()
        ]

    @property
    def eventscheme(self):
        return self.eventgroup["eventscheme"]

    @property
    def bettingmarketgroups(self):
        for bmg in self.lookup_bettingmarketgroups():
            yield LookupBettingMarketGroup(bmg, event=self)
