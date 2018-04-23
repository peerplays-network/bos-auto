from .trigger import Trigger
from ..log import log
from .. import exceptions


class InProgressTrigger(Trigger):

    def _trigger(self, args):
        """ Set a BMG to ``in_progress``
        """
        log.info("Setting a event to 'in_progress'...")

        event = self.getEvent()

        # event["status"] = "in_progress"
        event.update()
        event.status_update("in_progress")

    def testConditions(self, *args, **kwargs):
        return True
