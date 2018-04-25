from .trigger import Trigger
from ..log import log


class InProgressTrigger(Trigger):
    """ The in progress trigger sets an event to in_play as soon as it starts
    """

    def _trigger(self, args):
        """ Set a BMG to ``in_progress``
        """
        log.info("Setting a event to 'in_progress'...")

        event = self.getEvent()

        event.update()
        event.status_update("in_progress")

    def testConditions(self, *args, **kwargs):
        """ The conditions are always true as we want the
            event to be opened as soon as possible
        """
        return True
