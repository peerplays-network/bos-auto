from .log import log
from dateutil.parser import parse
from bookied_sync.sport import LookupSport
from bookied_sync.eventgroup import LookupEventGroup
from bookied_sync.event import LookupEvent
from bookied_sync.bettingmarketgroupresolve import (
    LookupBettingMarketGroupResolve
)
from . import exceptions


class Process():
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
            """
            log.error("Event could not be found: {}".format(
                str(dict(
                    teams=self.teams,
                    start_time=self.start_time,
                    eventgroup_identifier=self.eventgroup.identifier,
                    sport_identifier=self.sport.identifier
                ))))
            """
            raise exceptions.EventDoesNotExistException

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

    def create(self, args):
        """ Process the 'create' message
        """
        log.info("Creating a new event ...")

        season = args.get("season")
        if isinstance(season, str):
            season = {"en": season}

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

        # Set parameters
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
        # TODO: Test for "within lead_time_max"
        event.update()

        # Go through all Betting Market groups
        for bmg in event.bettingmarketgroups:
            # Skip dynamic bmgs
            if bmg["dynamic"]:
                log.info("Skipping dynamic BMG: {}".format(
                    str(bmg.identifier)))
                continue

            bmg.update()
            # Go through all betting markets
            log.info("Updating Betting Markets ...")
            for bm in bmg.bettingmarkets:
                log.info(
                    "Updating Betting Market {} ...".format(
                        bm["description"].get("en")
                    ))
                bm.update()

        log.debug(event.proposal_buffer.json())

    def in_progress(self, args):
        """ Set a BMG to ``in_progress``
        """
        log.info("Setting a event to 'in_progress'...")

        try:
            event, event_exists = self.getEvent()
        except exceptions.EventDoesNotExistException:
            try:
                log.info("Event could not be found, proposing to create it...")
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

        # event["status"] = "in_progress"
        event.update()
        event.status_update("in_progress")

    def finish(self, args):
        """ Set a BMG to ``finish``.
        """
        log.info(
            "Finishing an event by setting it to 'finished'"
            " (without results)...")

        try:
            event = self.getEvent()
        except Exception:
            return
        event.status_update(
            "finished",
            scores=[]
        )

    def result(self, args):
        """ Publish results to a BMG
        """
        log.info(
            "Finishing an event by setting it to "
            "'finished' (with results)...")

        home_score = args.get("home_score")
        away_score = args.get("away_score")

        try:
            event = self.getEvent()
        except Exception:
            return

        event.status_update(
            "finished",
            scores=[str(home_score), str(away_score)]
        )

        log.info("Settling betting market groups...")

        for bmg in event.bettingmarketgroups:

            # Skip those bmgs that coudn't be found
            if not bmg.find_id():
                log.error("BMG could not be found: {}".format(
                    str(bmg.identifier)))
                continue

            settle = LookupBettingMarketGroupResolve(
                bmg,
                [home_score, away_score]
            )
            settle.update()

        # This happens automatically
        # event.status_update("settled")
