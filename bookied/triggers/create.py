from .trigger import Trigger
from ..log import log
from .. import exceptions
from bookied_sync.event import LookupEvent


class CreateTrigger(Trigger):

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

    def createBmgs(self, event):
        # Go through all Betting Market groups
        for bmg in event.bettingmarketgroups:

            # Skip dynamic bmgs
            if SKIP_DYNAMIC_BMS and bmg["dynamic"]:
                log.info("Skipping dynamic BMG: {}".format(
                    str(bmg.identifier)))
                continue
            bmg.update()
            self.createBMs(bmg)

        log.info(event.proposal_buffer.json())

    def createBms(self, bmg):
        # Go through all betting markets
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
            event = self.getEvent()
        except exceptions.EventDoesNotExistException:
            try:
                log.info("Creating event with teams {} in group {}.".format(
                    str(self.teams),
                    self.eventgroup.identifier))
                event = self.createEvent()
            except exceptions.EventCannotOpenException:
                log.warning("The event with teams {} in group {} cannot open yet.".format(
                    str(self.teams),
                    self.eventgroup.identifier))
                return
        except exceptions.EventGroupClosedException:
            log.warning("The event group {} is not open yet.".format(
                self.eventgroup.identifier))
            return


    def createEvent(self):
        """ Create event
        """
        event = LookupEvent(
            teams=self.teams,
            start_time=self.start_time,
            eventgroup_identifier=self.eventgroup.identifier,
            sport_identifier=self.sport.identifier
        )
        if not event.can_open:
            raise exceptions.EventCannotOpenException()
        return event

    def testThreshold(self):
        return 2

    def testConditions(self, *args, **kwargs):
        # TODO: Test for "within lead_time_max"
        incidents = self.get_all_incidents()
        create_incidents = incidents.get("create", {}).get("incidents")
        if len(create_incidents) >= self.testThreshold():
            return True
        else:
            log.warning(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)
            ))
            return False
        return False
