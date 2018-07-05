import math
import statistics
from .trigger import Trigger
from .. import exceptions
from ..log import log
from bookied_sync.event import LookupEvent
from datetime import datetime, timedelta
from dateutil.parser import parse
from pprint import pprint
from ..utils import dList2Dict
MIN_AGE_INCIDENT = 1


def is_type(x, typ):
    if is_hc(typ):
        return is_hc(x)
    else:
        return is_ou(x)


def is_hc(x):
    return x == "hc" or x == "1x2_hc"


def is_ou(x):
    return x == "ou"


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
        log.info("Looking up event to create ")
        self.event = self.getEvent()
        self.teams = self.event.teams

        on_chain_bmgs = self.get_onchain_bmgs()
        incident_types = self.incident["arguments"]["types"]

        # We need to deal with each of the incidents individually
        types_done = list()
        for incident_type in incident_types:
            exists_on_chain = False
            for chain_bmg in on_chain_bmgs:

                # Test if we may have a dynamic BMG of that group on chain already:
                description = dList2Dict(chain_bmg["description"])
                if (
                    "_dynamic" in description and
                    description["_dynamic"] and
                    is_type(description["_dynamic"], incident_type["type"])
                ):
                    exists_on_chain = True
                    # We *DO* have this on chain already!
                    log.info("A dynamic BMG of type {} exists for event {} already".format(
                        incident_type["type"], self.event.identifier
                    ))

            # Dot not dublicate efforts
            if not exists_on_chain and incident_type["type"] not in types_done:
                self.createBmgs(self.event, incident_type)
                types_done.append(incident_type["type"])

    def median_value(self, t, side=None):
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
                if is_type(incident_type["type"], t):

                    if is_hc(t):
                        # Correct team orientation?
                        this_side = obtain_participant_side(incident_type["participant"], self.teams)
                        # If sides don't match, we need to invert values
                        if this_side == side:
                            values.append(float(incident_type["value"]))
                        else:
                            values.append(-float(incident_type["value"]))

                    elif is_ou(t):
                        values.append(float(incident_type["value"]))

        print(values, statistics.median(values))
        return statistics.median(values)

    def createBmgs(self, event, incident_type):
        """ Go through all Betting Market groups and create them
        """
        assert "type" in incident_type
        assert "value" in incident_type
        typ = incident_type["type"]
        value = incident_type["value"]

        # Let's find the BM according to bookiesports
        for bmg in event.bettingmarketgroups:

            # Only do dynamic ones here
            if (not bmg["dynamic"] or not is_type(bmg["type"], typ)):
                continue

            # If this is a Overunder BMG
            if(is_ou(bmg.get("type")) and is_ou(typ)):

                # Let's obtain the overunder value
                overunder = round(self.median_value("ou")) + 0.5

                # Set Overunder
                bmg.set_overunder(overunder)

                # Update and crate BMs
                bmg.update()
                self.createBms(bmg)
                return

            # If this is a Handicap BMG
            elif(is_hc(bmg.get("type")) and is_hc(typ)):
                # Identify which player has the handicap
                side = obtain_participant_side(incident_type["participant"], self.teams)

                # Set handicap
                handicap = round(self.median_value("hc", side=side))
                bmg.set_handicaps(**{side: handicap})

                # Update and crate BMs
                bmg.update()
                self.createBms(bmg)
                return

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

    def testConditions(self, *args, **kwargs):
        """ The test conditions for creating the event are as this:

            For this trigger, the threshold is based on time. After receiving
            the first incident, we wait time X (config) per type. If passed, we
            continue, else we only store.

        """
        # We test if the incident we received is X hours old
        # This happens if the incident is retriggered after being postpond
        my_time = parse(self.incident["timestamp"]).replace(tzinfo=None)
        time_limit = (datetime.utcnow() - timedelta(hours=MIN_AGE_INCIDENT))

        # We only allow this trigger if it is older than x hours
        if my_time <= time_limit:
            return True

        else:
            msg = "Incident not old enough {}({})".format(
                self.__class__.__name__, str(self.teams))
            log.info(msg)
            raise exceptions.PostPoneIncidentException(msg)
