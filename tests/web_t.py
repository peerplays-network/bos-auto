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

with open(files[3]) as fid:
    data = json.load(fid)

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
