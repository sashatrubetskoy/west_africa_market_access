# Alexandr (Sasha) Trubetskoy
# January 2019
# trub@uchicago.edu

import json

with open('data/geojson/border_crossings.geojson') as f:
    bcs = json.load(f)

for feature in bcs['features']:
    feature['properties'] = {'border_cost': -1}

with open('data/geojson/border_crossings.geojson', 'w') as f:
    json.dump(bcs, f)