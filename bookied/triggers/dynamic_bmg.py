import math
import statistics

from datetime import datetime, timedelta
from dateutil.parser import parse

from bookied_sync import comparators
from bookied_sync.event import LookupEvent
from bookied_sync.bettingmarketgroup import LookupBettingMarketGroup
from bookied_sync.bettingmarket import LookupBettingMarket

from .trigger import Trigger
from .. import exceptions
from ..log import log
from ..utils import dList2Dict
from ..config import loadConfig

MIN_AGE_INCIDENT = 1


config = loadConfig()


def obtain_participant_side(participant, teams):
    if participant not in teams:
        raise exceptions.InvalidParticipantException
    return "home" if teams.index(participant) == 0 else "away"


class DynamicBmgTrigger(Trigger):
    """ This trigger inherits class:`Trigger` and deals with the dynamic_bmgs
        trigger.
    """

    def _trigger(self, args):
        """ Trigger the 'dynamic' message
        """
        self.event = self.getEvent()
        self.teams = self.event.teams

        on_chain_bmgs = self.get_onchain_bmgs()
        incident_types = self.incident["arguments"]["types"]

        # We need to deal with each of the incidents individually
        log.debug("Testing incidents and existing BMGs")
        log.debug("Number of types in the incident:  {}".format(len(incident_types)))
        log.debug("Number of existing on-chain BMGs: {}".format(len(on_chain_bmgs)))

        types_done = list()
        for incident_type in incident_types:
            # This type of incident has multiple incident types, we go through
            # all of them individually

            # Let's see if we can find the corresponding BMG on chain already
            exists_on_chain = False
            for chain_bmg in on_chain_bmgs:

                # Test if we may have a dynamic BMG of that group on chain already:
                if chain_bmg.is_dynamic() and chain_bmg.is_dynamic_type(
                    incident_type["type"]
                ):
                    exists_on_chain = True
                    # We *DO* have this on chain already!
                    log.info(
                        "A dynamic BMG of type {} exists for event {} already".format(
                            incident_type["type"], self.event.identifier
                        )
                    )

            # Let's skip if we have we this type exists on chain already, or
            # we've already worked on one that is similar
            if exists_on_chain or incident_type["type"] in types_done:
                log.info("Already found BMGs on chain.. Aborting")
                continue

            # ... else, we create the BMG and corresponding BMs
            log.info("Creating dynamic BMGs ...")
            try:
                self.createBmg(self.event, incident_type)
            except Exception as e:
                # If an exception is raised, let's log and continue
                log.critical("{}: {}".format(e.__class__.__name__, str(e)))

            types_done.append(incident_type["type"])

    def createBmg(self, event, incident_type):
        """ Go through all Betting Market groups and create the one that
            matches the type in the incident together with the corresponding
            betting markets.

            This method is called for each type in the incident, that means, if
            an incident contains a handicap and an over under, this method will
            be called
        """
        assert "type" in incident_type
        assert "value" in incident_type
        typ = incident_type["type"]

        # Let's find the BM according to bookiesports
        bmgs = list(event.bettingmarketgroups)
        log.debug("Expected number of BMGs: {}".format(len(bmgs)))
        for bmg in bmgs:

            # Only do dynamic ones here
            if not bmg.get("dynamic"):
                log.debug("BMG is not dynamic: {}".format(bmg.identifier))
                continue

            # We only deal with the one corresponding with the incident_type
            if not LookupBettingMarketGroup.is_dynamic_type(bmg["dynamic"], typ):
                log.debug("BMG {} is not of type {}".format(bmg.identifier, typ))
                continue

            # If incident is a Overunder BMG
            if LookupBettingMarketGroup.is_ou_type(
                bmg.get("dynamic")
            ) and LookupBettingMarketGroup.is_ou_type(typ):
                self.updateOverUnderBMg(bmg)
                self.createBms(bmg)
                return

            # If incident is a Handicap BMG
            elif LookupBettingMarketGroup.is_hc_type(
                bmg.get("dynamic")
            ) and LookupBettingMarketGroup.is_hc_type(typ):
                self.updateHandicapBMg(bmg, incident_type)
                self.createBms(bmg)
                return

            else:
                log.error(
                    "BMG is could not be classified: {} - Type: {}".format(
                        bmg.identifier, (typ or "empty string")
                    )
                )

    def updateOverUnderBMg(self, bmg):
        """ This method creates a BMG for OverUnder
        """
        log.debug("BMG is dynamic Over/Under: {}".format(bmg.identifier))

        # Let's obtain the overunder value
        overunder = self.median_value("ou")

        # Set Overunder
        bmg.set_overunder(overunder)

        # We use fuzzy arguments by defining and injecting our own
        # test_operation_equal_search and find_id_search comparators.
        # This allows us to select what to actually look for.
        fuzzy_args = {
            "test_operation_equal_search": [
                # The following keys are required
                comparators.cmp_required_keys(
                    [  # other for updates with new_*
                        "betting_market_group_id",
                        "new_description",
                        "new_event_id",
                        "new_rules_id",
                    ],
                    [  # or as actual creates
                        "betting_market_group_id",
                        "description",
                        "event_id",
                        "rules_id",
                    ],
                ),
                # The status needs to match, if not update
                comparators.cmp_status(),
                # The status needs to match
                comparators.cmp_event(),
                # The description must have a _dynamic attribute
                comparators.cmp_description("_dynamic"),
                # The fuzzy comparator takes the fuzzyness from config
                # and tries to find the bmgs for handicap and over
                # under dynamic factors but allows some fuzzyness for
                # the actual value
                comparators.cmp_dynamic_bmg_fuzzy(
                    config["dynamic"]["overunder"]["fuzzy_value"]
                ),
            ],
            # We identify the bmg by comparing
            "find_id_search": [
                # parent event id
                comparators.cmp_event(),
                # comparing type of dynamic
                comparators.cmp_description("_dynamic"),
                # fuzzy matching of dynamic value
                comparators.cmp_dynamic_bmg_fuzzy(
                    config["dynamic"]["overunder"]["fuzzy_value"]
                ),
            ],
        }
        bmg.update(**fuzzy_args)

    def updateHandicapBMg(self, bmg, incident_type):
        """ This method creates a BMG for Hanidcap
        """
        log.debug("BMG is dynamic Handicap: {}".format(bmg.identifier))

        # Identify which player has the handicap
        side = obtain_participant_side(incident_type["participant"], self.teams)

        # Set handicap
        handicap = round(self.median_value("hc", side=side))
        bmg.set_handicaps(**{side: handicap})

        # We use fuzzy arguments by defining and injecting our own
        # test_operation_equal_search and find_id_search comparators.
        # This allows us to select what to actually look for.
        fuzzy_args = {
            "test_operation_equal_search": [
                # The following keys are required
                comparators.cmp_required_keys(
                    [  # other for updates with new_*
                        "betting_market_group_id",
                        "new_description",
                        "new_event_id",
                        "new_rules_id",
                    ],
                    [  # or as actual creates
                        "betting_market_group_id",
                        "description",
                        "event_id",
                        "rules_id",
                    ],
                ),
                # The status needs to match, if not update
                comparators.cmp_status(),
                # The status needs to match
                comparators.cmp_event(),
                # The description must have a _dynamic attribute
                comparators.cmp_description("_dynamic"),
                # The fuzzy comparator takes the fuzzyness from config
                # and tries to find the bmgs for handicap and over
                # under dynamic factors but allows some fuzzyness for
                # the actual value
                comparators.cmp_dynamic_bmg_fuzzy(
                    config["dynamic"]["handicap"]["fuzzy_value"]
                ),
            ],
            # We identify the bmg by comparing
            "find_id_search": [
                # parent event id
                comparators.cmp_event(),
                # comparing type of dynamic
                comparators.cmp_description("_dynamic"),
                # fuzzy matching of dynamic value
                comparators.cmp_dynamic_bmg_fuzzy(
                    config["dynamic"]["handicap"]["fuzzy_value"]
                ),
            ],
        }
        bmg.update(**fuzzy_args)

    def createBms(self, bmg):
        """ Go through all betting markets and create them
        """
        log.debug("Updating Betting Markets ...")
        for bm in bmg.bettingmarkets:
            log.debug(
                "Updating Betting Market {} ...".format(bm["description"].get("en"))
            )
            bm.update()

    def testConditions(self, *args, **kwargs):
        """ The test conditions for creating the event are as this:

            For this trigger, the threshold is based on time. After receiving
            the first incident, we wait time X (config) per type. If passed, we
            continue, else we only store.

        """
        # We test if the incident we received is X hours old
        # This happens if the incident is retriggered after being postpond
        my_time = parse(self.incident["timestamp"]).replace(tzinfo=None)
        time_limit = datetime.utcnow() - timedelta(
            seconds=config["conditions"]["dynamic_bmgs"]["incident-min-age"]
        )

        # We only allow this trigger if it is older than x hours
        if my_time <= time_limit:
            return True

        else:
            msg = "Incident not old enough {}({})".format(
                self.__class__.__name__, str(self.teams)
            )
            log.info(msg)
            raise exceptions.PostPoneIncidentException(msg)

    def median_value(self, type, side=None):
        """ This method is used to obtain the median value of all incidents
            that provide a value for a certain incident type. This ensure that
            multiple incident providers with different opinion about the
            dynamic market will result in just the median to be created.
        """
        log.debug("Obtaining median value of incidents")

        # Get all incidents for the current event
        incidents = self.get_all_incidents()

        # We raise if no incident is found, this should really not happen.
        # Also, there should be multiple incidents matching this query
        # according to testConditions()
        if not incidents:
            raise exceptions.InsufficientIncidents("No incident found")

        # Let's resolve the dynamic incidents
        dynamic_incidents = incidents.get("dynamic_bmgs", {}).get("incidents", [])
        incidents = [self.storage.resolve_to_incident(x) for x in dynamic_incidents]

        # Obtain those incidents that have our type
        values = list()
        for incident in incidents:

            for incident_type in incident["arguments"]["types"]:

                # Same type?
                if not LookupBettingMarketGroup.is_dynamic_type(
                    incident_type["type"], type
                ):
                    # .. of skip, if not
                    continue

                # Let's see if this is handicap type
                if LookupBettingMarketGroup.is_hc_type(type):
                    log.debug(
                        "Dealing with Handicap value: {}".format(incident_type["value"])
                    )

                    # Correct team orientation?
                    this_side = obtain_participant_side(
                        incident_type["participant"], self.teams
                    )
                    # If sides don't match, we need to invert values
                    if this_side == side:
                        values.append(float(incident_type["value"]))
                    else:
                        values.append(-float(incident_type["value"]))

                # let's see if this is over under type
                elif LookupBettingMarketGroup.is_ou_type(type):
                    log.debug(
                        "Dealing with over/under value: {}".format(
                            incident_type["value"]
                        )
                    )

                    # store value
                    values.append(float(incident_type["value"]))

        if values:
            log.debug("Obtaining median ({}) for values: {}".format(type, str(values)))
            return statistics.median(values)
        else:
            log.warning("No values could be processed for type {}!".format(type))
