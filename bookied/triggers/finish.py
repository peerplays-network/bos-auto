from .trigger import Trigger
from ..log import log
from .. import exceptions


class FinishTrigger(Trigger):

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
        return 2

    def testConditions(self, *args, **kwargs):
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents
        finish_incidents = incidents.get("finish", {}).get("incidents")
        if finish_incidents and len(finish_incidents) >= self.testThreshold():
            return True
        else:
            log.info(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)))
            raise exceptions.InsufficientIncidents
