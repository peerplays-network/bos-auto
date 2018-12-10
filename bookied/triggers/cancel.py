from .trigger import Trigger
from ..log import log
from .. import exceptions


class CancelTrigger(Trigger):
    """ The in progress trigger sets an event to in_play as soon as it starts
    """

    def _trigger(self, args):
        """ Set a BMG to ``in_progress``
        """
        log.info("Cancel event ...")
        event = self.getEvent()
        event.status_update("canceled")

    def testThreshold(self):
        """ The threshold that needs to be crossed in order to cancel an event
            on chain.

            .. alert:: This is temporary set to be ``2`` until we have an
                easier way to identify how many data proxies send data to us
        """
        return 2

    def testConditions(self, *args, **kwargs):
        """ The test conditions for canceling the event are as this:

            * Do more incidents propose the creation of the event than
                ``testThreshold``

               -> cancel the event

        """
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents
        cancel_incidents = incidents.get("canceled", {}).get("incidents")
        if cancel_incidents and len(cancel_incidents) >= self.testThreshold():
            return True
        else:
            log.info(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)))
            raise exceptions.InsufficientIncidents
