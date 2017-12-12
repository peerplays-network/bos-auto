import json
import requests

files = [
    "2017-12-03-1800-american-football-regular-season-miami-dolphins-denver-broncos-create-2017-12-03t213508636000.json",
    "2017-12-03-1800-american-football-regular-season-miami-dolphins-denver-broncos-in_progress-2017-12-03t190045669000.json",
    "2017-12-03-1800-american-football-regular-season-miami-dolphins-denver-broncos-finish-2017-12-03t222316292000.json",
    "2017-12-03-1800-american-football-regular-season-miami-dolphins-denver-broncos-result-35-9.json",
]

with open("test-scraping-data/{}".format(
    files[3]
)) as fid:
    data = json.load(fid)

x = requests.post(
    #"http://94.130.229.63:8011",
    "http://localhost:8010",
    json=data,
    headers={'Content-Type': 'application/json'}
)

print(x.text)
