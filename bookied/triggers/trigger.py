from ..log import log
from .. import exceptions
from dateutil.parser import parse
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent
from bos_incidents import factory
from bookiesports.normalize import IncidentsNormalizer, NotNormalizableException
from peerplaysapi.exceptions import UnhandledRPCError
from peerplays.bettingmarketgroup import BettingMarketGroups


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

        # Incident Storage
        if "storage" in kwargs and kwargs["storage"]:
            self.storage = kwargs["storage"]
        else:
            self.storage = factory.get_incident_storage(
                kwargs.get("mongodb", None),
                purge=kwargs.get("purge", False))

        # Normalize incident
        self.normalizer = IncidentsNormalizer(
            chain=lookup_instance._network_name)
        self.normalize(message)

        # Try obtain the sport
        self.sport = LookupSport(self.id.get("sport"))

        # Given the sport, try to obtain the league (event group)
        self.eventgroup = LookupEventGroup(
            self.sport,
            self.id.get("event_group_name"))

        self.event = None  # Will be filled in after receiving a trigger

        # Get Teams from query
        self.teams = [
            self.id.get("home"),
            self.id.get("away")]

        # Get start time from query
        self.start_time = parse(
            self.id.get("start_time", ""))

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

            # Store in object
            self.event = event

            eventgroup = event.eventgroup
            if not eventgroup.is_open:
                log.debug("Skipping not-yet-open BMG: {}".format(
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

    def normalize(self, *args, **kwargs):
        try:
            message = self.normalizer.normalize(self.message, errorIfNotFound=True)
        except NotNormalizableException as e:
            self.set_incident_status(status_name="not normalizable")
            raise e
        if message != self.message:
            try:
                self.storage.delete_incident(self.message)
            except Exception:
                pass
            self.message = message
            self.store_incident()

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

    def get_incident_status(self):
        """ Get the current status of an **event** in the incidents storage
        """
        event = self.storage.get_event_by_id(
            self.id,
            False)
        return event.get(self.call, {}).get("status", None)

    def broadcast(self):
        """ This method broadcasts the updates to the chain
        """
        """
        try:
        """
        return self.lookup.broadcast()
        """
        except UnhandledRPCError as e:
            if "Proposed operation is already pending for approval" in str(e):
                raise exceptions.ProposalAlreadyExistsOrIsPendingException()
            else:
                raise e
        """

    def store_incident(self):
        """ This call stores the incident in the incident-store (bos-incident)
        """
        self.storage.insert_incident(self.message)

    def get_onchain_bmgs(self):
        """ Returns a list of BettingMarketGroups of the event that already
            exist on the Blockchain
        """
        if not self.event:
            self.event = self.getEvent()
            if not self.event:
                return []
        return BettingMarketGroups(self.event.id)

    # Methods that need to be overwritten by trigger
    def testConditions(self, *args, **kwargs):
        """ Test If we can actually call the trigger. This method is called
            from trigger() and is supposed to be overwritten by the actual
            trigger.
        """
        pass

    def _trigger(self, *args, **kwargs):
        """ To be implemented by the sub class
        """
        pass
