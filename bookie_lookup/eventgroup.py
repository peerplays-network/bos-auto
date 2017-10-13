import sys
from .lookup import Lookup
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
        lookupnames = [[k, v] for k, v in self["name"].items()]
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
                (sport_id and self["sport_id"] == sport_id)):
            return True

    def find_id(self):
        if "sport_id" in self and self["sport_id"]:
            egs = EventGroups(
                self["sport_id"],
                peerplays_instance=self.peerplays)
            for eg in egs:
                if (
                    ["en", self["name"]["en"]] in eg["name"] and
                    self["sport_id"] == eg["sport_id"]
                ):
                    return eg["id"]

    def is_synced(self):
        if "id" in self:
            eventgroup = EventGroup(self["id"])
            if self.test_operation_equal(eventgroup):
                return True
        return False

    def propose_new(self):
        sport_id = self.obtain_parent_id(self.sport)
        names = [[k, v] for k, v in self["name"].items()]
        self.peerplays.event_group_create(
            names,
            sport_id=sport_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        sport_id = self.obtain_parent_id(self.sport)
        names = [[k, v] for k, v in self["name"].items()]
        self.peerplays.event_group_update(
            self["id"],
            names=names,
            sport_id=sport_id,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def find_event(self):
        pass

    def list_events(self):
        class Db:
            name = "db_peerplays"
            user = "peerplays"
            password = "I<3storage"

        MysqlDataSink(Db.name, Db.user, Db.password)
        """
        events = (
            RawEvent.select(
                RawEvent, RawGameInfo
            ).join(
                RawGameInfo
            ).where(
                (RawGameInfo.game == self.sport_name) &
                (RawGameInfo.league == self.eventgroup)
            ).order_by(RawEvent.update_time.desc()))
        """
        events = (
            ResolvedGameEvent.select(
                ResolvedGameEvent
            ).where(
                (ResolvedGameEvent.game == self.sport["identifier"]) &
                (ResolvedGameEvent.league == self.eventgroup)
            )
        )
        from pprint import pprint
        from .event import LookupEvent
        ret = list()
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

            ret.append(LookupEvent(event))
        return ret
