import json
import requests

files = [
    "test-data/2018-02-26t003000z-hockey-nhl-regular-season-new-york-rangers-detroit-red-wings-create-20172018.json",
    "test-data/2018-02-26t003000z-hockey-nhl-regular-season-new-york-rangers-detroit-red-wings-finish-2018-02-26t033744406z.json",
    "test-data/2018-02-26t003000z-hockey-nhl-regular-season-new-york-rangers-detroit-red-wings-in_progress-2018-02-26t005049592z.json",
    "test-data/2018-02-26t003000z-hockey-nhl-regular-season-new-york-rangers-detroit-red-wings-result-3-2.json",
]

with open(files[0]) as fid:
    data = json.load(fid)

x = requests.post(
    # "http://94.130.229.63:8011/trigger",
    "http://localhost:8010/trigger",
    json=data,
    headers={'Content-Type': 'application/json'}
)

print(x.text)
