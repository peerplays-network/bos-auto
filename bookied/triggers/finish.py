from .trigger import Trigger
from ..log import log


class FinishTrigger(Trigger):

    def _trigger(self, args):
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

    def testThreshold(self):
        return 2

    def testConditions(self, *args, **kwargs):
        incidents = self.get_all_incidents()
        finish_incidents = incidents.get("finish", {}).get("incidents")
        if len(finish_incidents) >= self.testThreshold():
            return True
        else:
            log.warning(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)
            ))
            return False
        return False
