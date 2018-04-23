import json
import requests
from pprint import pprint

files = [
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-in_progress-2018-03-10t00112083z.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-finish-2018-03-10t021409751z.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-result-99-83.json",
#    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-settle.json",
#    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-create-2018-true.json",
#    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-in_progress-2018-03-30t001546z-true.json",
#    "lsports/2018-03-30t000000z-basketball-nba-san-antonio-spurs-oklahoma-city-thunder-finish-2018-03-30t0245021991483z.json",
#    "lsports/2018-03-30t000000z-basketball-nba-finals-san-antonio-spurs-oklahoma-city-thunder-result-103-99.json",
    "lsports/create.1.json",
    "lsports/create.2.json",
]

with open(files[1]) as fid:
    data = json.load(fid)

# data = {'timestamp': '2018-04-05T08:06:50.263129Z', 'arguments': {'season': '2017/2018'}, 'id': {'home': 'Everton', 'event_group_name': 'EPL', 'away': 'Southampton', 'sport': 'Soccer', 'start_time': '2018-05-05T18:30:00Z'}, 'provider_info': {'source': 'event_id=2523107', 'source_file': '20180405-100650_2fb170be-4b76-4d3e-9f2a-ad04e7da1f1c.json', 'pushed': '2018-04-05T10:06:49Z', 'name': 'enetpulse'}, 'unique_string': '2018-05-05t183000z-soccer-epl-everton-southampton-create-20172018', 'call': 'create'}
# data = {'unique_string': '2018-05-06t173000z-soccer-epl-chelsea-liverpool-create-20172018', 'timestamp': '2018-04-05T08:07:10.883827Z', 'call': 'create', 'arguments': {'season': '2017/2018'}, 'id': {'start_time': '2018-05-06T17:30:00Z', 'event_group_name': 'EPL', 'sport': 'Soccer', 'home': 'Chelsea', 'away': 'Liverpool'}, 'provider_info': {'name': 'enetpulse', 'source': 'event_id=2523106', 'source_file': '20180405-100710_843e198b-2afc-4b77-a42b-19f8dcf27123.json', 'pushed': '2018-04-05T10:07:10Z'}}
# data = {'timestamp': '2018-04-05T08:07:48.839263Z', 'arguments': {'season': '2017/2018'}, 'id': {'home': 'Manchester City', 'event_group_name': 'EPL', 'away': 'Brighton', 'sport': 'Soccer', 'start_time': '2018-05-09T21:00:00Z'}, 'provider_info': {'source': 'event_id=2523048', 'source_file': '20180405-100748_23f38c31-b527-4a75-a2dd-1795b7e24041.json', 'pushed': '2018-04-05T10:07:48Z', 'name': 'enetpulse'}, 'unique_string': '2018-05-09t210000z-soccer-epl-manchester-city-brighton-create-20172018', 'call': 'create'}
# data = {'call': 'in_progress', 'provider_info': {'match_id': '1448259', 'source_file': '20180406-044125_449a5fc6-b913-4a00-8a6c-a868a5878648.xml', 'pushed': '2018-04-06T02:41:25.867Z', 'bitArray': '00000001100', 'source': 'direct string input', 'name': 'scorespro'}, 'unique_string': '2018-04-06t023000z-ice-hockey-nhl-regular-season-los-angeles-kings-minnesota-wild-in_progress-2018-04-06t02411167z', 'timestamp': '2018-04-06T02:41:25.915925Z', 'id': {'away': 'Minnesota Wild', 'start_time': '2018-04-06T02:30:00Z', 'event_group_name': 'NHL Regular Season', 'home': 'Los Angeles Kings', 'sport': 'Ice Hockey'}, 'arguments': {'whistle_start_time': '2018-04-06T02:41:11.67Z'}}
# data = {'call': 'result', 'provider_info': {'match_id': '1448259', 'source_file': '20180406-071941_6e8aec89-3755-4086-98bb-50734f0a012e.xml', 'pushed': '2018-04-06T05:19:41.254Z', 'bitArray': '00000000100', 'source': 'direct string input', 'name': 'scorespro'}, 'unique_string': '2018-04-06t023000z-ice-hockey-nhl-regular-season-los-angeles-kings-minnesota-wild-result-4-5', 'timestamp': '2018-04-06T05:19:41.300992Z', 'id': {'away': 'Minnesota Wild', 'start_time': '2018-04-06T02:30:00Z', 'event_group_name': 'NHL Regular Season', 'home': 'Los Angeles Kings', 'sport': 'Ice Hockey'}, 'arguments': {'away_score': '4', 'home_score': '5'}}
# data = {'call': 'finish', 'provider_info': {'match_id': '1448259', 'source_file': '20180406-072011_40c75ab5-fedd-414b-9ef0-fceab35e66a8.xml', 'pushed': '2018-04-06T05:20:11.737Z', 'bitArray': '00000001000', 'source': 'direct string input', 'name': 'scorespro'}, 'unique_string': '2018-04-06t023000z-ice-hockey-nhl-regular-season-los-angeles-kings-minnesota-wild-finish-2018-04-06t051959929z', 'timestamp': '2018-04-06T05:20:11.76941Z', 'id': {'away': 'Minnesota Wild', 'start_time': '2018-04-06T02:30:00Z', 'event_group_name': 'NHL Regular Season', 'home': 'Los Angeles Kings', 'sport': 'Ice Hockey'}, 'arguments': {'whistle_end_time': '2018-04-06T05:19:59.929Z'}}
# data = {"timestamp": "2018-03-20T08:29:57.511111Z", "id": {"sport": "Soccer", "start_time": "2018-04-08T20:45:00Z", "away": "Espanyol", "home": "Valencia", "event_group_name": "LaLiga"}, "provider_info": {"source": "event_id=2580840", "name": "enetpulse", "source_file": "20180320-092957_e1d2bfc5-e2e6-41b0-89b4-4423ef52ef04.json", "pushed": "2018-03-20T09:29:57Z"}, "unique_string": "2018-04-08t204500z-soccer-primera-division-valencia-espanyol-create-20172018", "arguments": {"season": "2017/2018"}, "call": "create"}
# data = {"provider_info": {"name": "enetpulse", "source": "event_id=2523110", "pushed": "2018-04-05T10:06:41Z", "source_file": "20180405-100641_ecede1d9-4317-4576-9122-b302c2a2d0fe.json"}, "unique_string": "2018-05-05t133000z-soccer-epl-stoke-crystal-palace-create-20172018", "arguments": {"season": "2017/2018"}, "call": "create", "id": {"home": "Stoke", "sport": "Soccer", "event_group_name": "EPL", "start_time": "2018-05-05T13:30:00Z", "away": "Crystal Palace"}, "timestamp": "2018-04-05T08:06:41.508809Z"}

data.update(dict(
    approver="init0",
    proposer="init0",
))

pprint(data)
x = requests.post(
    #"http://94.130.229.63:8011/trigger",
    "http://localhost:8010/trigger",
    json=data,
    headers={'Content-Type': 'application/json'}
)


print(x.text)
