from .trigger import Trigger
from ..log import log
from .. import exceptions


class InProgressTrigger(Trigger):

    def _trigger(self, args):
        """ Set a BMG to ``in_progress``
        """
        log.info("Setting a event to 'in_progress'...")

        try:
            event = self.getEvent()
        except exceptions.EventDoesNotExistException:
            log.info(
                "Trying to set an event in_progress that cound't be found"
            )
            return
        except exceptions.EventGroupClosedException:
            return

        # event["status"] = "in_progress"
        event.update()
        event.status_update("in_progress")

    def testConditions(self, *args, **kwargs):
        return True
