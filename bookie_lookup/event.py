import datetime
from .lookup import Lookup
from .sport import LookupSport
from .eventgroup import LookupEventGroup
from .bettingmarketgroup import LookupBettingMarketGroup
from peerplays.event import Event, Events
from peerplays.utils import formatTime, parse_time
# from . import log


def subsitution(teams, scheme):
    class Teams:
        home = " ".join([
            x.capitalize() for x in teams[0].split(" ")])
        away = " ".join([
            x.capitalize() for x in teams[1].split(" ")])

    ret = dict()
    for lang, name in scheme.items():
        ret[lang] = name.format(
            teams=Teams
        )
    return ret


class LookupEvent(Lookup, dict):
    """ Lookup Class for an Event

        :param list teams: Teams (first element is **HomeTeam**)
        :param str eventgroup_identifier: Identifier of the event group
        :param str sport_identifier: Identifier of the sport
        :param list season: Internationalized string for the season
        :param datetime.datetime start_time: Datetime the event starts
               (required when creating an event)
        :param dict extra_data: Optionally provide additional data that is
               stored in the same dictionary

        ... note:: Please note that the list of teams begins with the **home**
                   team! Only two teams per event are supported!
    """

    operation_update = "event_update"
    operation_create = "event_create"

    def __init__(
        self,
        teams,
        eventgroup_identifier,
        sport_identifier,
        season={},
        start_time=None,
        id=None,
        extra_data={},
        **kwargs
    ):
        Lookup.__init__(self)

        # Also store all the stuff in kwargs
        dict.__init__(self, extra_data)
        dict.update(self, {
            "teams": teams,
            "eventgroup_identifier": eventgroup_identifier,
            "sport_identifier": sport_identifier,
            "season": season,
            "start_time": start_time,
            "id": id})

        # Define "id" if not present
        self["id"] = self.get("id", None)

        if not len(self["teams"]) == 2:
            raise ValueError(
                "Only matches with two players are allowed! "
                "Here: {}".format(str(self["teams"]))
            )

        self.parent = self.eventgroup
        self.identifier = "{}/{}/{}".format(
            self.parent["name"]["en"],
            teams[0],
            teams[1])

        if start_time and not isinstance(
            self["start_time"], datetime.datetime
        ):
            raise ValueError(
                "'start_time' must be instance of datetime.datetime()")

        if not isinstance(self["season"], dict):
            raise ValueError(
                "'season' must be (language) dictionary")

        if not self.test_teams_valid():
            raise ValueError(
                "Team names not known: {}".format(
                    str(self["teams"])))

        # Initialize name key
        dict.update(self, dict(name=self.names_json))

    def test_teams_valid(self):
        return all(
            self.participants.is_participant(t)
            for t in self["teams"]
        )

    @classmethod
    def find_event(
        cls,
        sport_identifier,
        eventgroup_identifier,
        teams,
        start_time
    ):
        """ This class method is used to find an event by providing:

            :param str sport_identifier: Identifier string for the sport
            :param str eventgroup_identifier: Identifier string for the eventgroup/league
            :param list teams: list of teams
            :param datetime.datetime start_time: Time of start

        """
        sport = LookupSport(sport_identifier)
        eventgroup = LookupEventGroup(sport, eventgroup_identifier)
        events = Events(eventgroup.id)  # This is a pypeerplays class!
        # Format teams into proper names according to event scheme
        names = subsitution(teams, eventgroup["eventscheme"]["name"])
        names = [[k, v] for k, v in names.items()]
        for event in events:
            if (
                any([x in event["name"] for x in names]) and
                formatTime(start_time) == event["start_time"]
            ):
                return cls(
                    id=event["id"],
                    teams=teams,
                    eventgroup_identifier=eventgroup_identifier,
                    sport_identifier=sport_identifier,
                    start_time=start_time,
                    season={x[0]: x[1] for x in event["season"]}
                )

    @property
    def sport(self):
        """ Return LookupSport instance for this event
        """
        return LookupSport(self["sport_identifier"])

    @property
    def teams(self):
        """ Return the list of teams

            ... note:: The first element is the **home** team!

        """
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
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """
        lookupnames = self.names
        lookupseason = self.season
        chainsnames = [[]]
        chainseason = [[]]
        if "name" in event:
            chainsnames = event["name"]
            event_group_id = event["event_group_id"]
            chainseason = event["season"]
        elif "new_name" in event:
            chainsnames = event["new_name"]
            event_group_id = event["new_sport_id"]
            chainseason = event["new_season"]
        else:
            raise ValueError

        parts = event_group_id.split(".")
        assert len(parts) == 3,\
            "{} is a strange sport object id".format(event_group_id)
        if int(parts[0]) == 0:
            event_group_id = ""

        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames]) and
                (lookupseason and  # only test if a season is provided
                    all([b in lookupseason for b in chainseason]) and
                    all([b in chainseason for b in lookupseason])) and
                (not event_group_id or self.parent_id == event_group_id)):
            return True

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

        events = Events(
            self.parent_id,
            peerplays_instance=self.peerplays)

        # FIXME: Might be we also need to look for season
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))

        for event in events:
            if en_descrp in event["name"]:
                return event["id"]

    def is_synced(self):
        """ Test if data on chain matches lookup
        """
        if "id" in self and self["id"]:
            event = Event(self["id"])
            if self.test_operation_equal(event):
                return True
        return False

    def propose_new(self):
        """ Propose operation to create this object
        """
        return self.peerplays.event_create(
            self.names,
            self.season,
            self["start_time"],
            event_group_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        """ Propose to update this object to match  lookup
        """
        return self.peerplays.event_update(
            self["id"],
            self.names,
            self.season,
            self["start_time"],
            event_group_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def participants(self):
        """ Return content of participants in this event
        """
        from .participant import LookupParticipants
        name = self.eventgroup["participants"]
        return LookupParticipants(
            self["sport_identifier"], name)

    def lookup_bettingmarketgroups(self):
        """ Return content of betting market groups
        """
        names = self.eventgroup["bettingmarketgroups"]
        for name in names:
            yield self.eventgroup.sport["bettingmarketgroups"][name]

    @property
    def names(self):
        """ Properly format names for internal use
        """
        return [
            [
                k,
                v
            ] for k, v in self.names_json.items()
        ]

    @property
    def names_json(self):
        """ This property derives the names for each language provided in the
            eventscheme and fills in the variables.

            :rtype dict
        """
        teams = self["teams"]
        scheme = self.eventscheme.get("name", {})
        return subsitution(teams, scheme)

    @property
    def season(self):
        """ Properly format season for internal use
        """
        return [
            [
                k,
                v
            ] for k, v in self["season"].items()
        ]

    @property
    def eventscheme(self):
        """ Obtain Event scheme from event group
        """
        return self.eventgroup["eventscheme"]

    @property
    def bettingmarketgroups(self):
        """ Return instances of LookupBettingMarketGroup for this event
        """
        for bmg in self.lookup_bettingmarketgroups():
            yield LookupBettingMarketGroup(bmg, event=self)
