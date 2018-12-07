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
        """ Trigger the 'create' message
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
            exists_on_chain = False
            for chain_bmg in on_chain_bmgs:

                # Test if we may have a dynamic BMG of that group on chain already:
                description = dList2Dict(chain_bmg["description"])
                if (
                    "_dynamic" in description and
                    description["_dynamic"] and
                    LookupBettingMarketGroup.is_dynamic_type(description["_dynamic"], incident_type["type"])
                ):
                    exists_on_chain = True
                    # We *DO* have this on chain already!
                    log.info("A dynamic BMG of type {} exists for event {} already".format(
                        incident_type["type"], self.event.identifier
                    ))

            # Dot not dublicate efforts
            if not exists_on_chain and incident_type["type"] not in types_done:
                log.info("Creating dynamic BMGs ...")
                self.createBmgs(self.event, incident_type)
                types_done.append(incident_type["type"])
            else:
                log.info("Already found BMGs on chain.. Aborting")
                # just return, the worker will set the incident status to done

    def median_value(self, t, side=None):
        log.debug("Obtaining median value of incidents")
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents("No incident found")
        dynamic_incidents = incidents.get("dynamic_bmgs", {}).get("incidents", [])
        incidents = [self.storage.resolve_to_incident(x) for x in dynamic_incidents]
        # Obtain incidents that have an OU for this event in it
        values = list()
        for incident in incidents:
            for incident_type in incident["arguments"]["types"]:
                # Same type?
                if LookupBettingMarketGroup.is_dynamic_type(incident_type["type"], t):

                    if LookupBettingMarketGroup.is_hc_type(t):

                        # Correct team orientation?
                        this_side = obtain_participant_side(incident_type["participant"], self.teams)
                        # If sides don't match, we need to invert values
                        if this_side == side:
                            values.append(float(incident_type["value"]))
                        else:
                            values.append(-float(incident_type["value"]))
                        log.debug("Dealing with Handicap value: {}".format(incident_type["value"]))

                    elif LookupBettingMarketGroup.is_ou_type(t):
                        values.append(float(incident_type["value"]))
                        log.debug("Dealing with over/under value: {}".format(incident_type["value"]))

                    else:
                        log.error("Type '{}' isn't known!".format(t))
                else:
                    log.error("Not same type: {} != {}".format(incident_type["type"], t))

        if values:
            log.debug("Obtaining median ({}) for values: {}".format(t, str(values)))
            return statistics.median(values)
        else:
            log.warning("No values could be processed for type {}!".format(t))

    def createBmgs(self, event, incident_type):
        """ Go through all Betting Market groups and create them
        """
        assert "type" in incident_type
        assert "value" in incident_type
        typ = incident_type["type"]

        # Let's find the BM according to bookiesports
        bmgs = list(event.bettingmarketgroups)
        log.debug("Expected number of BMGs: {}". format(len(bmgs)))
        for bmg in bmgs:

            # Only do dynamic ones here
            if (not bmg["dynamic"] or not LookupBettingMarketGroup.is_dynamic_type(bmg["dynamic"], typ)):
                log.debug("BMG is not dynamic: {}".format(bmg.identifier))
                continue

            # If this is a Overunder BMG
            if(LookupBettingMarketGroup.is_ou_type(bmg.get("dynamic")) and LookupBettingMarketGroup.is_ou_type(typ)):
                log.debug("BMG is dynamic Over/Under: {}".format(bmg.identifier))

                # Let's obtain the overunder value
                # overunder = math.floor(self.median_value("ou")) + 0.5
                overunder = self.median_value("ou")  # The rounding will need to happen somewhere else!

                # Set Overunder
                bmg.set_overunder(overunder)

                # Update and crate BMs
                fuzzy_args = {
                    "test_operation_equal_search": [
                        comparators.cmp_required_keys([
                            "betting_market_group_id", "new_description",
                            "new_event_id", "new_rules_id"
                        ], [
                            "betting_market_group_id", "description",
                            "event_id", "rules_id"
                        ]),
                        comparators.cmp_status(),
                        comparators.cmp_event(),
                        comparators.cmp_description("_dynamic"),
                        comparators.cmp_fuzzy(config["dynamic"]["overunder"]["fuzzy_value"]),
                    ],
                    "find_id_search": [
                        comparators.cmp_event(),
                        comparators.cmp_fuzzy(config["dynamic"]["overunder"]["fuzzy_value"]),
                        comparators.cmp_description("_dynamic"),
                    ]
                }
                bmg.update(**fuzzy_args)
                self.createBms(bmg)
                return

            # If this is a Handicap BMG
            elif(LookupBettingMarketGroup.is_hc_type(bmg.get("dynamic")) and LookupBettingMarketGroup.is_hc_type(typ)):
                log.debug("BMG is dynamic Handicap: {}".format(bmg.identifier))

                # Identify which player has the handicap
                side = obtain_participant_side(incident_type["participant"], self.teams)

                # Set handicap
                handicap = round(self.median_value("hc", side=side))
                bmg.set_handicaps(**{side: handicap})

                # Update and crate BMs
                fuzzy_args = {
                    "test_operation_equal_search": [
                        comparators.cmp_required_keys([
                            "betting_market_group_id", "new_description",
                            "new_event_id", "new_rules_id"
                        ], [
                            "betting_market_group_id", "description",
                            "event_id", "rules_id"
                        ]),
                        comparators.cmp_status(),
                        comparators.cmp_event(),
                        comparators.cmp_description("_dynamic"),
                        comparators.cmp_fuzzy(config["dynamic"]["handicap"]["fuzzy_value"]),
                    ],
                    "find_id_search": [
                        comparators.cmp_event(),
                        comparators.cmp_fuzzy(config["dynamic"]["handicap"]["fuzzy_value"]),
                        comparators.cmp_description("_dynamic"),
                    ]
                }
                bmg.update(**fuzzy_args)
                self.createBms(bmg)
                return

            else:
                log.error("BMG is could not be classified: {} - Type: {}".format(
                    bmg.identifier, (typ or "empty string")))

    def createBms(self, bmg):
        """ Go through all betting markets and create them
        """
        log.debug("Updating Betting Markets ...")
        for bm in bmg.bettingmarkets:
            log.debug(
                "Updating Betting Market {} ...".format(
                    bm["description"].get("en")
                ))
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
        time_limit = (datetime.utcnow() - timedelta(
            seconds=config["conditions"]["dynamic_bmgs"]["incident-min-age"])
        )

        # We only allow this trigger if it is older than x hours
        if my_time <= time_limit:
            return True

        else:
            msg = "Incident not old enough {}({})".format(
                self.__class__.__name__, str(self.teams))
            log.info(msg)
            raise exceptions.PostPoneIncidentException(msg)
