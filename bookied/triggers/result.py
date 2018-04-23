from .trigger import Trigger
from . import (
    SKIP_DYNAMIC_BMS,
)
from bookied_sync.bettingmarketgroupresolve import (
    LookupBettingMarketGroupResolve
)
from ..log import log
from .. import exceptions


class TooManyDifferentResultsOverThreshold(Exception):
    pass


_SCORE_SEPARATOR = "::"


class ResultTrigger(Trigger):

    def _trigger(self, args):
        """ Publish results to a BMG and set to ``finish``.
        """
        log.info(
            "Finishing an event by setting it to "
            "'finished' (with results)...")

        event = self.getEvent()

        event.status_update(
            "finished",
            scores=[str(self.home_score), str(self.away_score)]
        )

        log.info("Settling betting market groups...")

        self.resolve_bgms(event)

    def resolve_bgms(self, event):
        for bmg in event.bettingmarketgroups:

            # Skip dynamic bmgs
            if SKIP_DYNAMIC_BMS and bmg["dynamic"]:
                log.info("Skipping dynamic BMG: {}".format(
                    str(bmg.identifier)))
                continue

            # Skip those bmgs that coudn't be found
            if not bmg.find_id():
                log.error("BMG could not be found: {}".format(
                    str(bmg.identifier)))
                continue

            settle = LookupBettingMarketGroupResolve(
                bmg,
                [self.home_score, self.away_score]
            )
            settle.update()

    def testThreshold(self):
        return 2

    def testThresholdPercentage(self):
        return 51

    def count_score(self, scores):
        from collections import Counter
        ret = Counter()
        for i in range(len(scores)):
            ret[scores[i]] += 1
        return ret

    def testConditions(self, *args, **kwargs):
        incidents = self.get_all_incidents()
        if not incidents:
            raise exceptions.InsufficientIncidents
        result_incidents = incidents.get("result", {}).get("incidents")
        if result_incidents and len(result_incidents) < self.testThreshold():
            log.info(
                "Insufficient incidents for {}({})".format(
                    self.__class__.__name__,
                    str(self.teams)))
            raise exceptions.InsufficientIncidents

        # Figure out the most "probable" result
        scores = ["{}{}{}".format(
            x["arguments"]["away_score"],
            _SCORE_SEPARATOR,
            x["arguments"]["home_score"]
        ) for x in result_incidents]
        scores = self.count_score(scores)

        # Threshold scaled by number of scores
        threshold = len(scores) * self.testThresholdPercentage() / 100

        # Valid results filtered by threshold
        valid_results = dict({k: v for k, v in scores.items() if v >= threshold})

        if not valid_results:
            raise exceptions.InsufficientEqualResults

        # Raise if multiple results are valid
        if len(valid_results) > 1:
            raise TooManyDifferentResultsOverThreshold(valid_results)
        elif len(valid_results) < 1:
            raise exceptions.InsufficientEqualResults
        else:
            result = list(valid_results.keys())[0]
            self.away_score, self.home_score = result.split(_SCORE_SEPARATOR)
            return True
