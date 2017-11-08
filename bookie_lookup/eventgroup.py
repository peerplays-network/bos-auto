import sys
from .lookup import Lookup, LookupDatabaseConfig
from peerplays.eventgroup import EventGroups, EventGroup
from . import log

try:
    from bookied_scrapers.sinks.mysql_data_sink import MysqlDataSink
    from bookied_scrapers.sinks.db_data_sink_model import RawGameInfo, RawEvent, RawMarketsInfo, ResolvedGameEvent
    from playhouse.shortcuts import model_to_dict
except ImportError:
    log.error("Please install bookied-scrapers")
    sys.exit(1)


class LookupEventGroup(Lookup, dict):

    operation_update = "event_group_update"
    operation_create = "event_group_create"

    def __init__(self, sport, eventgroup):
        from .sport import LookupSport
        self.sport_name = sport
        self.sport = LookupSport(sport)
        self.parent = self.sport
        self.eventgroup = eventgroup
        self.identifier = "{}/{}".format(self.sport_name, eventgroup)
        super(LookupEventGroup, self).__init__()
        assert sport in self.data["sports"], "Sport {} not avaialble".format(
            sport
        )
        assert eventgroup in self.data["sports"][sport]["eventgroups"], \
            "Eventgroup {} not avaialble in sport {}".format(
                eventgroup, sport)
        dict.__init__(
            self,
            self.data["sports"][sport]["eventgroups"][eventgroup]
        )

    def test_operation_equal(self, eventgroup):
        lookupnames = self.names
        chainsnames = [[]]
        if "name" in eventgroup:
            chainsnames = eventgroup["name"]
            sport_id = eventgroup["sport_id"]
        elif "new_name" in eventgroup:
            chainsnames = eventgroup["new_name"]
            sport_id = eventgroup["new_sport_id"]
        else:
            raise ValueError

        parts = sport_id.split(".")
        assert len(parts) == 3,\
            "{} is a strange sport object id".format(sport_id)
        if int(parts[0]) == 0:
            sport_id = ""

        if (all([a in chainsnames for a in lookupnames]) and
                all([b in lookupnames for b in chainsnames]) and
                (not sport_id or self.parent.id == sport_id)):
            return True

    def find_id(self):
        # In case the parent is a proposal, we won't
        # be able to find an id for a child
        if self.parent.id[0] == "0":
            return

        egs = EventGroups(
            self.parent.id,
            peerplays_instance=self.peerplays)
        en_descrp = next(filter(lambda x: x[0] == "en", self.names))

        for eg in egs:
            if (
                en_descrp in eg["name"] and
                self.parent.id == eg["sport_id"]
            ):
                return eg["id"]

    def is_synced(self):
        if "id" in self and self["id"]:
            eventgroup = EventGroup(self["id"])
            if self.test_operation_equal(eventgroup):
                return True
        return False

    def propose_new(self):
        return self.peerplays.event_group_create(
            self.names,
            sport_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        return self.peerplays.event_group_update(
            self["id"],
            names=self.names,
            sport_id=self.parent_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    @property
    def events(self):
        from .event import LookupEvent

        MysqlDataSink(
            LookupDatabaseConfig.name,
            LookupDatabaseConfig.user,
            LookupDatabaseConfig.password)
        events = (
            ResolvedGameEvent.select(
                ResolvedGameEvent
            ).where(
                (ResolvedGameEvent.game == self.sport["identifier"]) &
                (ResolvedGameEvent.league == self.eventgroup)
            )
        )
        for e in events:
            event = model_to_dict(e)
            # set name
            event.update({"name": {"en": event["teams"]}})

            # eventgroup_name
            event.update({"eventgroup_identifier": event["league"]})

            # sport
            event.update({"sport_identifier": event["game"]})

            # id
            event.update({"id": None})

            # searson
            event.update({"season": []})

            yield LookupEvent(event)

    @property
    def names(self):
        return [
            [
                k,
                v
            ] for k, v in self["name"].items()
        ]
