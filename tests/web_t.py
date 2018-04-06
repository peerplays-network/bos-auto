import json
import requests

files = [
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-in_progress-2018-03-10t00112083z.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-finish-2018-03-10t021409751z.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-result-99-83.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-settle.json",
    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-create-2018-true.json",
    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-in_progress-2018-03-30t001546z-true.json",
    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-finish-2018-03-30t0245021991483z.json",
    "lsports/2018-03-30t000000z-basketball-nba-finals-san-antonio-spurs-oklahoma-city-thunder-result-103-99.json",
]

with open(files[0]) as fid:
    data = json.load(fid)

# data = {'timestamp': '2018-04-05T08:06:50.263129Z', 'arguments': {'season': '2017/2018'}, 'id': {'home': 'Everton', 'event_group_name': 'EPL', 'away': 'Southampton', 'sport': 'Soccer', 'start_time': '2018-05-05T18:30:00Z'}, 'provider_info': {'source': 'event_id=2523107', 'source_file': '20180405-100650_2fb170be-4b76-4d3e-9f2a-ad04e7da1f1c.json', 'pushed': '2018-04-05T10:06:49Z', 'name': 'enetpulse'}, 'unique_string': '2018-05-05t183000z-soccer-epl-everton-southampton-create-20172018', 'call': 'create'}
# data = {'unique_string': '2018-05-06t173000z-soccer-epl-chelsea-liverpool-create-20172018', 'timestamp': '2018-04-05T08:07:10.883827Z', 'call': 'create', 'arguments': {'season': '2017/2018'}, 'id': {'start_time': '2018-05-06T17:30:00Z', 'event_group_name': 'EPL', 'sport': 'Soccer', 'home': 'Chelsea', 'away': 'Liverpool'}, 'provider_info': {'name': 'enetpulse', 'source': 'event_id=2523106', 'source_file': '20180405-100710_843e198b-2afc-4b77-a42b-19f8dcf27123.json', 'pushed': '2018-04-05T10:07:10Z'}}
# data = {'timestamp': '2018-04-05T08:07:48.839263Z', 'arguments': {'season': '2017/2018'}, 'id': {'home': 'Manchester City', 'event_group_name': 'EPL', 'away': 'Brighton', 'sport': 'Soccer', 'start_time': '2018-05-09T21:00:00Z'}, 'provider_info': {'source': 'event_id=2523048', 'source_file': '20180405-100748_23f38c31-b527-4a75-a2dd-1795b7e24041.json', 'pushed': '2018-04-05T10:07:48Z', 'name': 'enetpulse'}, 'unique_string': '2018-05-09t210000z-soccer-epl-manchester-city-brighton-create-20172018', 'call': 'create'}
data = {'call': 'in_progress', 'provider_info': {'match_id': '1448259', 'source_file': '20180406-044125_449a5fc6-b913-4a00-8a6c-a868a5878648.xml', 'pushed': '2018-04-06T02:41:25.867Z', 'bitArray': '00000001100', 'source': 'direct string input', 'name': 'scorespro'}, 'unique_string': '2018-04-06t023000z-ice-hockey-nhl-regular-season-los-angeles-kings-minnesota-wild-in_progress-2018-04-06t02411167z', 'timestamp': '2018-04-06T02:41:25.915925Z', 'id': {'away': 'Minnesota Wild', 'start_time': '2018-04-06T02:30:00Z', 'event_group_name': 'NHL Regular Season', 'home': 'Los Angeles Kings', 'sport': 'Ice Hockey'}, 'arguments': {'whistle_start_time': '2018-04-06T02:41:11.67Z'}}

data.update(dict(
    approver="init1",
    proposer="init0",
))
x = requests.post(
    #"http://94.130.229.63:8011/trigger",
    "http://localhost:8010/trigger",
    json=data,
    headers={'Content-Type': 'application/json'}
)


print(x.text)
