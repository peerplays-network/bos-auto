class EventDoesNotExistException(Exception):
    """ An event does not exist
    """
    pass


class EventGroupClosedException(Exception):
    """ The event group is closed and no events can open
    """
    pass


class EventCannotOpenException(Exception):
    """ An event cannot be opened yet, possibly due to
        leadtime_Max setting
    """
    pass


class InsufficientIncidents(Exception):
    """ Insufficient incidents to make a decision
    """
    pass


class InsufficientEqualResults(Exception):
    """ Inconsistent result incidents that don't allow
        us to make a decision
    """
    pass


class TooManyDifferentResultsOverThreshold(Exception):
    """ To many different results appear to be above the required threshold.
        This should never have happend unless the thresholds are too low
    """
    pass


class CreateIncidentTooOldException(Exception):
    """ The create incident tries to create an event in the past
    """
    pass
