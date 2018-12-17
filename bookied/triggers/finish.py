from .trigger import Trigger
from ..log import log
from .. import exceptions


class FinishTrigger(Trigger):
    """ The finish trigger merely sets an event to finished on whistle time
    """

    def _trigger(self, args):
        """ Set a BMG to ``finish``.
        """
        log.info(
            "Finishing an event by setting it to 'finished'"
            " (without results)...")

        event = self.getEvent()

        event.status_update(
            "finished",
            scores=[]
        )

        return True

    def testThreshold(self):
        """ The threshold that needs to be crossed in order to finish an event
            on chain.

            .. alert:: This is temporary set to be ``2`` until we have an
                easier way to identify how many data proxies send data to us
        """
        return 2

    def testConditions(self, *args, **kwargs):
        """ The test conditions for finishing the event are as this:

            * Do more incidents propose the creation of the event than
                ``testThreshold``

               -> Finish the event

        """
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents
        finish_incidents = incidents.get("finish", {}).get("incidents", [])
        if not finish_incidents:
            raise exceptions.InsufficientIncidents
        provider_hashes = set()
        for incident in finish_incidents:
            provider_hash = incident.get("provider_info", {}).get("name", None)
            if provider_hash is not None:
                provider_hashes.add(provider_hash)
        if len(provider_hashes) >= self.testThreshold():
            return True
        else:
            log.info(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)))
            raise exceptions.InsufficientIncidents
