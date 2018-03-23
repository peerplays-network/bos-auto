import json
import requests

files = [
    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-create-20172018.json",
    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-in_progress-2018-03-10t00112083z.json",
    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-finish-2018-03-10t021409751z.json",
    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-result-99-83.json",
    "test-data/2018-03-10t000000z-basketball-nba-regular-season-detroit-pistons-chicago-bulls-settle.json",
]

with open(files[1]) as fid:
    data = json.load(fid)

data = {'arguments': {'season': '2017/2018'},
        'unique_string': '2018-03-08t053000z-basketball-nba-regular-season-los-angeles-lakers-orlando-magic-create-20172018',
        'id': {'away': 'Orlando Magic',
               'start_time': '2018-03-08T05:30:00Z',
               'event_group_name': 'NBA Regular Season',
               'home': 'Los Angeles Lakers',
               'sport': 'Basketball'},
        'call': 'create',
        'timestamp': '2018-03-23T09:32:07.702624Z',
        'provider_info': {'bitArray': '00010000000', 'name': 'scorespro', 'source_file': '20180307-074329_7e133aa5-c6f8-4f17-9f45-dc1a64333d41.xml', 'match_id': '1487193', 'pushed': '2018-03-07T06:43:29.315Z', 'source': 'direct string input'}
        }

data = {'arguments': {'season': '2017/2018'}, 'unique_string': '2018-03-08t033000z-basketball-nba-regular-season-los-angeles-lakers-orlando-magic-create-20172018', 'id': {'away': 'Orlando Magic', 'start_time': '2018-03-08T03:30:00Z', 'event_group_name': 'NBA Regular Season', 'home': 'Los Angeles Lakers', 'sport': 'Basketball'}, 'call': 'create', 'timestamp': '2018-03-23T09:32:07.698359Z', 'provider_info': {'bitArray': '00010000000', 'name': 'scorespro', 'source_file': '20180307-133612_34ec1673-6eee-4763-aabc-a57fa499d7be.xml', 'match_id': '1487193', 'pushed': '2018-03-07T12:36:12.948Z', 'source': 'direct string input'}}

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
