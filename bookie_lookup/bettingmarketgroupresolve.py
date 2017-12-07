from .lookup import Lookup
from .rule import LookupRules
from .exceptions import MissingMandatoryValue
from peerplays.event import Event
from peerplays.rule import Rule
from peerplays.asset import Asset
from peerplays.bettingmarketgroup import (
    BettingMarketGroups, BettingMarketGroup)


class LookupBettingMarketGroupResolve(Lookup, dict):
    """ Lookup Class for Resolving BettingMarketGroups
    """

    operation_update = None
    operation_create = "betting_market_group_resolve"

    def __init__(
        self,
        bmg,
        result,
        extra_data={}
    ):
        Lookup.__init__(self)
        self.identifier = "{}/result".format(
            bmg["description"]["en"],
        )
        self.parent = bmg
        dict.__init__(self, extra_data)
        dict.update(
            self,
            bmg
        )
        assert isinstance(result, list) and len(result) == 2, \
            "Result must be a list of length 2."
        dict.update(self, {
            "result": result
        })

    @property
    def bmg(self):
        """ The BMG is the parent
        """
        return self.parent

    @property
    def markets(self):
        """ The BMG is the parent
        """
        return self.parent.bettingmarkets

    @property
    def sport(self):
        """ Return the sport for this BMG
        """
        return self.parent.sport

    @property
    def rules(self):
        """ Return instance of LookupRules for this BMG
        """
        assert self["rules"] in self.sport["rules"]
        return LookupRules(self.sport["identifier"], self["rules"])

    @property
    def resolutions(self):
        """ This property constructs the resultions array to be used in the
            transactions. It takes the following form

            ... code-block: js

                [
                    ["1.21.257", "win"],
                    ["1.21.258", "not_win"],
                    ["1.21.259", "cancel"],
                ]

        """
        grading = self.rules.get("grading")
        assert grading, "Rules {} have no grading!?".format(self.rules["identifier"])
        assert "metric" in grading
        assert "resolutions" in grading

        # Define variables we want to use when grading

        class Result:
            hometeam = (self["result"][0])
            awayteam = float(self["result"][1])
            total = sum([float(x) for x in self["result"]])

            # aliases
            home = hometeam
            away = awayteam

        def return_metric(s):
            if not isinstance(s, str):
                raise ValueError(
                    "metric must be string, was {}".format(
                        type(s)
                    ))
            try:
                metric = eval(s.format(result=Result))
            except Exception:
                raise Exception("Cannot evaluate metric '{}' -> '{}'".format(
                    s, s.format(result=Result)))
            return metric

        def evaluate_metric(equation, metric):
            if not isinstance(equation, str):
                raise ValueError(
                    "equation must be string, was {}".format(
                        type(equation)
                    ))
            try:
                metric = eval(equation.format(metric=metric))
            except Exception:
                raise Exception("Cannot evaluate metric '{}' -> '{}'".format(
                    equation, equation.format(result=Result)))
            return metric

        metric = return_metric(grading.get("metric", ""))
        bettingmarkets = self.markets
        ret = []
        for market in grading.get("resolutions", []):
            bettingmarket = next(bettingmarkets)
            resolved = {
                key: evaluate_metric(option, metric)
                for key, option in market.items()
            }
            # The resolved dictionary looks like this
            # {'win': False, 'not_win': True, 'void': False}
            # we now need to ensure that only one of those options is 'true'
            assert sum(resolved.values()) == 1, \
                "Multiple options resolved to 'True': {}".format(
                    str(resolved))

            ret.extend([
                [bettingmarket.id, key]
                for key, value in resolved.items() if value
            ])

        return ret

    def test_operation_equal(self, resolve):
        """ This method checks if an object or operation on the blockchain
            has the same content as an object in the  lookup
        """

        lookupresults = self.resolutions
        chainsresults = resolve["resolutions"]
        bmg_id = resolve["betting_market_group_id"]

        # Test if BMG exists
        # only if the id starts with 1.
        test_bmg = bmg_id[0] == 1
        if test_bmg:
            BettingMarketGroup(bmg_id)

        if (
            all([a in chainsresults for a in lookupresults]) and
            all([b in lookupresults for b in chainsresults]) and
            (not test_bmg or bmg_id == self.parent.id)
        ):
            return True
        return False

    def find_id(self):
        """ Market resolve operations do not have their own ids
        """
        pass

    def is_synced(self):
        """ Here, we need to figure out if the market has already been resolved
        """
        # FIXME  / TODO
        return False

    def propose_new(self):
        """ This call proposes the resolution of the betting market group
        """
        return self.peerplays.betting_market_resolve(
            self.parent.id,
            self.resolutions,
            account=self.proposing_account,
            append_to=Lookup.proposal_buffer
        )

    def propose_update(self):
        """ There is no such thing as an updated resolution
        """
        pass
