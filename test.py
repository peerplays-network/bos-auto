from getpass import getpass
from witnesslookup.lookup import WitnessLookup
from witnesslookup.sport import WitnessLookupSport


if __name__ == "__main__":
    w = WitnessLookup()
    w.peerplays.wallet.unlock(getpass())
    w.peerplays.nobroadcast = True
    w.peerplays.bundle = True
    # for sport in w.list_sports():
    sport = WitnessLookupSport("Soccer")
    sport.update()
    for e in sport.eventgroups:
        e.update()
    for r in sport.rules:
        r.update()

    w.broadcast()

    """
    for p in sport.participants:
        p.update()
    for b in sport.bettingmarketgroups:
        b.update()
    """
    # sport.update()
    # eventgroup = WitnessLookupEventGroup("AmericanFootball", "NFL#PreSeas")
    # eventgroup.update()

    """
    print(json.dumps(w, indent=4))
    print(json.dumps(w.data, indent=4))
    print(w.list_sports())
    print(WitnessLookupSport("AmericanFootball"))
    print(WitnessLookupEventGroup("AmericanFootball", "NFL#PreSeas"))
    print(WitnessLookupBettingMarketGroup(
        "AmericanFootball", "NFL_HCP_2017-18_1")
    )
    print(WitnessLookupParticipants("AmericanFootball", "NFL_Teams_2017-18"))
    print(WitnessLookupRules("AmericanFootball", "R_NFL_MO_1"))
    """
