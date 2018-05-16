from ..log import log
from .. import exceptions
from dateutil.parser import parse
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent
from bos_incidents import factory


class Trigger():
    """ This class is used to deal with Messages that have been received by any
        means and need processing thru bookied-sync
    """
    def __init__(
        self,
        message,
        lookup_instance,
        config,
        **kwargs
    ):
        self.message = message
        self.lookup = lookup_instance
        self.config = config

        # Obtain data for unique key
        # The "id" contains everything we need to identify an individual event
        # which itself contains at least the sport, and the teams

        # Get the id (internally used only)
        self.id = message.get("id")

        # Try obtain the sport
        self.sport = LookupSport(self.id.get("sport"))

        # Given the sport, try to obtain the league (event group)
        self.eventgroup = LookupEventGroup(
            self.sport,
            self.id.get("event_group_name"))

        # Get Teams from query
        self.teams = [
            self.id.get("home"),
            self.id.get("away")]

        # Get start time from query
        self.start_time = parse(
            self.id.get("start_time", ""))

        # Invident Storage
        self.storage = factory.get_incident_storage(
            kwargs.get("mongodb", None),
            purge=kwargs.get("purge", False))

    @property
    def incident(self):
        """ Return the incident message
        """
        return self.message

    @property
    def call(self):
        """ Return the trigger/call name
        """
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
        self.testConditions()

        # Execute the actual Trigger
        self._trigger(*args, **kwargs)

        # if a proposal is going to be published, let's enable
        # blocking so we can obtain the proposal id
        # FIXME: This can be optimized for speed by putting this into
        # an independent thread or throwing it into the redis queue
        # so the worker can continue with other incidents
        if self.lookup.proposal_operations():
            self.lookup.set_blocking(True)
        else:
            self.lookup.set_blocking(False)

        # Broadcast that stuff
        transactions = self.broadcast()

        # Obtain data from the blockchain
        proposal_ids = [x.get_proposal_id() for x in transactions]
        actions = [x.action() for x in transactions]

        # unless _trigger raises an exception
        self.set_incident_status(
            status_name="done",
            status_add=dict(
                proposals=proposal_ids,
                actions=actions,
            )
        )

        return transactions

    def _trigger(self, *args, **kwargs):
        """ To be implemented by the sub class
        """
        pass

    def get_all_incidents(self):
        """ Let's get all the incidents for an event
        """
        return self.storage.get_event_by_id(self.message)

    def set_incident_status(self, **kwargs):
        """ We here set the status of an **event** in the incidents storage
        """
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

    def broadcast(self):
        """ This method broadcasts the updates to the chain
        """
        return self.lookup.broadcast()

    def store_incident(self):
        """ This call stores the incident in the incident-store (bos-incident)
        """
        self.storage.insert_incident(self.message)
