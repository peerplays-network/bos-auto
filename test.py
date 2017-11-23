from pprint import pprint
from getpass import getpass
from bookie_lookup.eventgroup import LookupEventGroup


if __name__ == "__main__":
    eventgroup = LookupEventGroup("AmericanFootball", "NFL#RegSeas")
    eventgroup.peerplays.wallet.unlock("posaune")
    eventgroup.sport.update()
    eventgroup.update()
    # Rules
    for r in eventgroup.sport.rules:
        r.update()
    pprint(dict(eventgroup))
    for event in eventgroup.events:
        print("EVENT")
        print("=" * 80)
        pprint(dict(event))
#        event.update()
        for bmg in event.bettingmarketgroups:
            print("BMG")
            print("=" * 80)
#            bmg.update()
#            pprint(dict(bmg.items()))
            for bm in bmg.bettingmarkets:
                print("BM")
                print("=" * 80)
                pprint(dict(bm))
#                bm.update()
#                pprint(dict(bm.items()))
                break
            break
        break

    pprint(eventgroup.proposal_buffer.json())
#    eventgroup.broadcast()

    """
    w = WitnessLookup()
    w.peerplays.wallet.unlock(getpass())
    w.peerplays.nobroadcast = True
    w.peerplays.bundle = True
    # for sport in w.list_sports():
    sport = WitnessLookupSport("Football")
    sport.update()
    for e in sport.eventgroups:
        e.update()
    for r in sport.rules:
        r.update()

    w.broadcast()
    """

    """
    for b in sport.bettingmarketgroups:
        b.update()
    for p in sport.participants:
        p.update()
    """

    """
    # sport.update()
    # eventgroup = WitnessLookupEventGroup("AmericanFootball", "NFL#PreSeas")
    # eventgroup.update()
    """

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
