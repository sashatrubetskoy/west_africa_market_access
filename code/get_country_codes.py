# Alexandr (Sasha) Trubetskoy
# January 2019
# trub@uchicago.edu

import json

with open('data/geojson/admin2_poly.geojson', 'r') as f:
    admin2_poly = json.load(f)

for feature in admin2_poly['features']:
    other_tags = {eval(kv.split('=>')[0]): eval(kv.split('=>')[1]) for kv in feature['properties']['other_tags'].split(',')}
    iso3 = other_tags['ISO3166-1:alpha3']
    feature['properties']['iso3'] = iso3

with open('data/geojson/admin2_poly.geojson', 'w') as f:
    json.dump(admin2_poly, f)