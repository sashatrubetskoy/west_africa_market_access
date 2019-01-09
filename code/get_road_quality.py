import json
import pandas as pd

qualities = pd.read_csv('parameters/road_quality.csv').set_index('code')

with open('data/geojson/roads.geojson', 'r') as f:
    roads = json.load(f)

for i, feature in enumerate(roads['features']):
    print('Feature {} of {}...'.format(i+1, len(roads['features'])))
    country = feature['properties']['iso3']
    osm_highway = feature['properties']['highway']
    
    feature['properties']['quality'] = int(qualities.loc[country, osm_highway])


with open('data/geojson/roads.geojson', 'w') as f:
    json.dump(roads, f)