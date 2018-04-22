from ..log import log
from .. import exceptions
from dateutil.parser import parse
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent
from bos_incidents import factory
from bos_incidents.exceptions import *   # FIXME


class Trigger():
    """ This class is used to deal with Messages that have been received by any
        means and need processing thru bookied-sync
    """
    def __init__(
        self,
        message,
        lookup_instance=None,
    ):
        self.message = message
        self.lookup = lookup_instance

        # Obtain data for unique key
        # The "id" contains everything we need to identify an individual event
        # which itself contains at least the sport, and the teams

        # Get the id (internally used only)
        self.id = message.get("id")

        # Try obtain the sport
        try:
            self.sport = LookupSport(self.id.get("sport"))
        except Exception as e:
            # err = "Sport {} not found".format(self.id.get("sport"))
            # log.warning(err)
            raise e

        # Given the sport, try to obtain the league (event group)
        try:
            self.eventgroup = LookupEventGroup(
                self.sport,
                self.id.get("event_group_name"))
        except Exception as e:
            # err = "Event group {} not found".format(
            #     self.id.get("event_group_name"))
            # log.warning(err)
            raise e

        # Get Teams from query
        self.teams = [
            self.id.get("home"),
            self.id.get("away")]

        # Get start time from query
        self.start_time = parse(
            self.id.get("start_time", ""))

        # Invident Storage
        self.storage = factory.get_incident_storage()

    @property
    def incident(self):
        return self.message

    @property
    def call(self):
        return self.message.get("call").lower()

    def getEvent(self):
        """ Get an event from the lookup
        """
        event = LookupEvent.find_event(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )

        if event:

            eventgroup = event.eventgroup
            if not eventgroup.is_open:
                log.info("Skipping not-yet-open BMG: {}".format(
                    str(eventgroup.identifier)))
                raise exceptions.EventGroupClosedException

            return event

        else:
            raise exceptions.EventDoesNotExistException

    def trigger(self, *args, **kwargs):
        """ Forward a trigger to the actual trigger implementation
            in the subclass
        """
        # Test if I am supposed to proceed with this
        if not self.testConditions():
            return

        self._trigger(*args, **kwargs)

        # unless _trigger raises an exception
        self.set_incident_status(status_name="done")

    def _trigger(self, *args, **kwargs):
        """ To be implemented by the sub class
        """
        pass

    def get_all_incidents(self):
        try:
            return self.storage.get_event_by_id(self.message)
        except Exception:
            # log.critical("Trying to read data that should exist, but doesn't!")
            return

    def set_incident_status(self, **kwargs):
        self.storage.update_event_status_by_id(
            self.id,
            call=self.call,
            **kwargs)

    def testConditions(self, *args, **kwargs):
        """ Test If we can actually call the trigger. This method is called
            from trigger() and is supposed to be overwritten by the actual
            trigger.
        """
        pass
