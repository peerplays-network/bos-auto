from .trigger import Trigger
from ..log import log
from .. import exceptions
from bookied_sync.event import LookupEvent
from . import SKIP_DYNAMIC_BMS


class CreateTrigger(Trigger):
    """ This trigger inherits class:`Trigger` and deals with create incidents
        that are fired by the data proxy when new events are announced.
    """
    def _trigger(self, args):
        """ Trigger the 'create' message
        """
        log.info("Creating a new event ...")

        # Let's see if we can find an Event in the Lookup
        event = self.getIncidentEvent()
        if not event:
            return

        # Set parameters
        season = args.get("season")
        if isinstance(season, str):
            season = {"en": season}
        if (
            event["season"] and
            event["season"].get("en") != season.get("en")
        ):
            err = "Seasons don't match: {} != {}".format(
                season.get("en"),
                event["season"].get("en"))
            log.critical(err)
            raise Exception(err)
        event["season"] = season
        event["status"] = "upcoming"

        # Update event
        event.update()

        # Create Betting market Groups
        self.createBmgs(event)

        return True

    def createBmgs(self, event):
        """ Go through all Betting Market groups and create them
        """
        for bmg in event.bettingmarketgroups:

            # Skip dynamic bmgs
            if SKIP_DYNAMIC_BMS and bmg["dynamic"]:
                log.info("Skipping dynamic BMG: {}".format(
                    str(bmg.identifier)))
                continue
            bmg.update()
            self.createBms(bmg)

    def createBms(self, bmg):
        """ Go through all betting markets and create them
        """
        log.info("Updating Betting Markets ...")
        for bm in bmg.bettingmarkets:
            log.info(
                "Updating Betting Market {} ...".format(
                    bm["description"].get("en")
                ))
            bm.update()

    def getIncidentEvent(self):
        """ Does not throw in all cases but returns None in case of error
        """
        # Obtain event
        try:
            return self.getEvent()
        except exceptions.EventDoesNotExistException:
            try:
                log.info("Creating event with teams {} in group {}.".format(
                    str(self.teams),
                    self.eventgroup.identifier))
                return self.createEvent()
            except exceptions.EventCannotOpenException as e:
                msg = (
                    "The event with teams {} in group {} cannot open yet: {}"
                    .format(
                        str(self.teams),
                        self.eventgroup.identifier,
                        str(e)))
                log.info(msg)
                raise exceptions.EventCannotOpenException(msg)

    def createEvent(self):
        """ Create event
        """
        event = LookupEvent(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )

        # This tests for leadtime_max
        if not event.can_open:
            can_open_by = event.can_open_by
            self.set_incident_status(
                status_name="postponed",
                status_expiration=can_open_by)
            raise exceptions.EventCannotOpenException(
                "Can only open after {}".format(
                    str(can_open_by)))

        return event

    def testThreshold(self):
        """ The threshold that needs to be crossed in order to create an event
            on chain.

            .. alert:: This is temporary set to be ``2`` until we have an
                easier way to identify how many data proxies send data to us
        """
        return 2

    def testConditions(self, *args, **kwargs):
        """ The test conditions for creating the event are as this:

            * Do more incidents propose the creation of the event than
                ``testThreshold``

               -> Create the event

        """
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents("No incident found")
        create_incidents = incidents.get("create", {}).get("incidents")
        if len(create_incidents) >= self.testThreshold():
            return True
        else:
            msg = "Insufficient incidents for {}({})".format(
                self.__class__.__name__, str(self.teams))
            log.info(msg)
            raise exceptions.InsufficientIncidents(msg)
