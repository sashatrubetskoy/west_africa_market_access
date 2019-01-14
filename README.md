West Africa market access notes  
Alexandr Trubetskoy (trub@uchicago.edu)  
January 2019

# Introduction
### What is the Market Access (MA) model?
"Market Access" is a measure of the ability of a city to trade with the rest of the economy. Total Market Access is a combination of Firm Market Access (ability to export) and Consumer Market Access (ability to import).

Cities will have more Market Access if they are better connected to other cities by roads, railways and sea ports.

The access that firms in City A have to consumers City B is estimated by taking the "market size" (GDP) of City B and dividing it by how much it costs to export from City A by City B. By summing this measure across all other cities in the economy, we get the Firm Market Access (FMA) of City A.

Consumer Market Access (CMA) is calculated in a similar manner, except import costs are used instead of export costs.

Trade costs include: 
- Raw transport cost (distance multiplied by unit cost)
- Tariffs
- Customs processing fees
- Handling charges at ports
- Switching costs between road/rail.

This cost can be expressed in terms of money (USD) or time (hours).

The total Market Access is calculated by taking a weighted sum of CMA and FMA, by default: MA = (0.65 * CMA) + (0.35 * FMA)

Higher MA is associated with population growth in the long run. See Reed and Trubetskoy (2018) for a more formal explanation.

### When should I use this model?
This model can be used to get a first order approximation of which cities will be impacted the most by trade cost reductions.

Trade cost reductions can take the form of:
- Infrastructure improvements (road, rail, sea)
- Tariff reductions
- Border/customs streamlining
- Improved technology (faster trains, cheaper fuel, etc.)

As discussed by Reed and Trubetskoy (2018), the model is particularly useful for ranking effects, for instance ranking transport corridor proposals by how much they would improve market access.

# Quick instructions
Use these instructions if you are not changing any underlying data. This workflow was designed to be run on MacOS using Terminal and QGIS 3. All commands are run from within the top directory.

1. Install necessary packages by running:

	```
	brew install osmium-tool
	brew install gdal
	```
	```
	chmod 777 code/install_packages.sh
	./code/install_packages.sh
	```

2. Download clean data [from here](https://drive.google.com/file/d/1oXpSUBRRdheKoaMUzubv90aFr5fZcOuK/view?usp=sharing), unzip, save as `data` in main directory.

3. Update parameters as necessary. (`parameters/*.csv`) 

4. Make cost matrix by running:

	```
	python code/get_cost_matrix.py -o data/csv/my_cost_matrix_filename.csv
	```

5. Get market access by running:
	
	```
	python code/get_ma.py \
	    -i data/csv/my_cost_matrix_filename.csv \
	    -o output/my_market_access_filename.csv
	```
	
# Spatial data checklist
- [ ] border\_crossings.geojson

    * "border_cost" - if -1, it defaults to WDI.

- [ ] cities.geojson

    * "GDP" Size of city market. Lines 66-67 in get_ma.py

- [ ] ports.geojson

    * (no attributes are needed, only geometry is important)

- [ ] roads.geojson

    * "length" - length of line feature in meters
    * "quality" - 1 to 4, make sure it matches parameters/transport_costs.csv

- [ ] sea_links.geosjon

    * "length" - length of line feature in meters
    * "quality" - should be set to "sea" or otherwise match parameters/transport_costs.csv

# Workflow details
## Preparation
### Installing necessary packages
This workflow was designed to be run on MacOS using Terminal and QGIS 3. All commands are run from within the top directory.

To install the following necessary packages, run the associated command in Terminal:

- [Osmium](https://osmcode.org/osmium-tool/manual.html) - `brew install osmium-tool`
- [Ogr2ogr](https://wiki.openstreetmap.org/wiki/OGR) (part of GDAL) - `brew install gdal`

>Note: If you are using ArcGIS instead of QGIS and are having trouble with reading GeoJSON, Ogr2ogr is extremely helpful for converting to .shp and back:
>
>```
>ogr2ogr -f "ESRI Shapefile" shp_result.shp my_geojson.geojson
>ogr2ogr -f GeoJSON geojson_result.geojson my_shp.shp
>```

### How to download and prepare OSM road network data
**1. Download latest OpenStreetMap data** on Africa, in PBF format, using the [GeoFabrik server](http://download.geofabrik.de/africa.html). Store at `data/pbf/africa-latest.osm.pbf`.

**2. Extract roads and borders** from the PBF file to a geoJSON file as described below.

- 2.a. Take the OSM file from step 1 and extract only West Africa. **Run:**
    
   ```
	osmium extract -p data/geojson/extraction_area.geojson data/pbf/africa-latest.osm.pbf -o data/pbf/west_africa.pbf
   ```
    
    where:
    
   - `data/geojson/extraction_area.geojson` is a single polygon marking our area of interest (i.e. West Africa), with a buffer of approx. 100 km to ensure all features are captured; 
   - `data/pbf/africa-latest.osm.pbf` is the raw OSM file;
   - `data/pbf/west_africa.pbf` is the output location.
    
- 2.b. Take the West Africa file and extract roads. To extract all roads of "secondary" class or higher, **run:**
    
    ```
    osmium tags-filter data/pbf/west_africa.pbf \
        w/highway=motorway w/highway=motorway_link \
        w/highway=trunk w/highway=trunk_link \
        w/highway=primary w/highway=primary_link \
        w/highway=secondary w/highway=secondary_link \
        -o data/pbf/west_africa_roads.pbf
    ```
    
- 2.c. Take the West Africa file and extract country polygons and borders (important to use OSM borders so that they match the road data). **Run:**
   
   ```
	osmium tags-filter data/pbf/west_africa.pbf boundary=administrative -o data/pbf/admin.pbf
   osmium tags-filter data/pbf/admin.pbf admin_level=2 -o data/pbf/admin2.pbf
   ```
    
- 2.d. Convert all your extractions to GeoJSON format. **Run:**
  
  ```
  ogr2ogr -f GeoJSON data/geojson/west_africa_roads.geojson data/pbf/west_africa_roads.pbf lines
  ogr2ogr -f GeoJSON data/geojson/admin2_lines.geojson data/pbf/admin2.pbf lines
  ogr2ogr -f GeoJSON data/geojson/admin2_poly.geojson data/pbf/admin2.pbf multipolygons
  ```
  
**3. Simplify the road network.** I use [Mapshaper](https://mapshaper.org/) with the "Visvalingam effective area" setting at 10%.

**4. Consolidate "\_link" classes.** Within the OSM `highway` attribute, remove "\_link" from the OSM class, so that "motorway\_link" becomes "motorway".

**5. Dissolve the road network** by OSM `highway` attribute. Store the simplified, dissolved network at `data/geojson/west_africa_roads_simp.geojson`.

**6. Split roads by country:**
    
- 6.a. ISO3 country codes are easier to deal with than the default country names. To add country codes to the `admin2_poly` file, **run:** 
    
    ```
    python code/get_country_codes.py
    ```
    
- 6.b. Using GIS software, **calculate the Intersect** between `west_africa_roads_simp` and `admin2_poly`, so that the road network is broken up by country, and country codes are joined to the road features.

**7. Split roads at intersections.** In QGIS 3 this can be done with GRASS *v.clean*, or by running *Multipart to singleparts* and then *Split with lines* on itself. 

Store the result of steps 6 and 7 at `data/geojson/roads.geojson`.

**8. Calculate road quality.** The conversion from OSM class to road quality (explained in section "Road quality") is specified in the file `parameters/road_quality.csv`. To calculate road quality from OSM classification, **run:**

```
python code/get_road_quality.py
```

This changes the file  `data/geojson/roads.geojson` in-place. It does not generate a new file.

**8A. (optional) Make manual changes to the road network.** Any manual changes to the network should be made at this point. This can include adding or removing features from the network, or manually changing the road quality of some features. 

Modify  `data/geojson/roads.geojson` as needed.

**9. Extract border crossings.** Do this by calculating the Intersect of `data/geojson/roads.geojson` and `data/geojson/admin2_lines.geojson` (from step 2.d.). 

Save the output as `data/geojson/border_crossings.geojson`.

Then run:

```
python code/clean_border_crossings.py
```

### Create sea link data
Sea links will probably have to be created manually. Ensure that the endpoint vertices of the sea links correspond exactly to city points. Save the sea link line file as `geojson/sea_links.geojson`.

Then create the port locations file. We want a file that marks which cities are the endpoints of sea connections. This can be done by taking a very small (a few meters) buffer of `geojson/sea_links.geojson` and select cities that are within this buffer. Export these cities to `geojson/ports.geojson`.

### Create city data
Cities must have a population or GDP attribute as well as X, Y coordinates in degrees. The city points must be saved as `csv/cities.csv`.

## Calculating cost matrix
### Install required packages
Many python packages are required. The correct versions can be installed by running this command from the top directory:

```
chmod 777 install_packages.sh
./install_packages.sh
```

### Set parameters
When crossing an international border, two costs are incurred: a tariff or duty on the goods ("tariff"); and a border compliance cost ("border cost").

**Tariffs** for importing into countries are specified at `parameters/tariffs.csv`. By default these tariffs are based on Doing Business Indicators 2015 data. Tariffs are levied only at the final country of destination.

**Border costs** between countries are stored in `parameters/border_costs.csv`. The default values provided come from adding "border compliance" and "documentary compliance" from Doing Business Indicators 2015, and dividing by $50,000 (standard container value) to get an ad valorem border cost.

To edit border costs for an individual border crossing, open `geojson/border_crossings.geojson` in a GIS program and change the "border_cost" attribute from -1 (default value) to the desired value. If other costs are ad valorem, ensure that your new value is also ad valorem.

Note that tariffs and border costs are not symmetrical.

**Transport costs** are stored in `parameters/transport_costs.csv` and represent the cost to travel one kilometer. 

Default values are based on standard ad valorem costs to move one $50,000 container a distance of one kilometer, for sea and motorway travel. Lower quality roads are extrapolated using the basic assumption of doubling cost for every decrease in quality rating.

**Other cost parameters** are stored in `parameters/other_cost_parameters.csv`. The default values are as follows:

Parameter | Description | Default value
--- | --- | ---
Shipment value | The value of a single shipping container. Used to convert costs to *ad valorem*. | 50,000 USD
Switching fee | Cost to switch between road and rail. | 25 USD
Port fee | Cost of switching to/from sea travel. | 200 USD


### Run cost matrix calculation
When all the parameters have been set, run:

```
python get_cost_matrix.py -o csv/cost_matrix.csv
```

with the desired output location after `-o`.

## Calculating market access
### Set parameters
These parameters are stored in `parameters/market_access_parameters.csv`

Parameter | Description | Default value
--- | --- | ---
Theta | Trade elasticity between cities | 5.03
Alpha | Share of income paid to land | 0.05
Beta | Labor share of market | 0.65

## Road quality
This section explains and the road classification used by this market access program. The user must input road speeds into the program based on this classification.

 In order to perform the market access analysis, it is important that roads be classified according to their speed, which depends on road quality. OSM road classifications often do not correspond with the physical quality of the road, especially in less developed regions. However, the OSM classifications are usually fairly consistent _within_ each country.

We create a consistent road quality classification scheme by converting OSM road classes to a simplified, four-class system. 

**If using this code for other regions:** This classification scheme was developed for OSM data on West Africa and may not apply to other regions.

### Quality score: 4 ★★★★
Best quality roadway. Paved, marked, well-maintained, with both directions separated by a median. Allows highest speeds.

Autoroute du Nord, Cote d'Ivoire | Lagos-Ibadan Expressway, Nigeria
--- | ---
<img src="http://news.educarriere.ci/actu-images/fb/actu_image_20216_fb.jpg" alt="drawing" width="300"/> | <img src="https://www.von.gov.ng/wp-content/uploads/2018/05/Lagos-Road.jpg" alt="drawing" width="300"/>

### Quality score: 3 ★★★☆
Second best quality roadway. Paved, usually marked, usually well-maintained. Allows medium speeds.

N2 Mamou-Timbo, Guinea | N12 Goaso-Bibiani, Ghana
--- | ---
<img src="http://mw2.google.com/mw-panoramio/photos/medium/835370.jpg" alt="drawing" width="300"/> | <img src="https://cdn.pbrd.co/images/HSXJDzq.png" alt="drawing" width="300"/>

### Quality score: 2 ★★☆☆
The most common class of road connecting towns in West Africa. Unpaved. Can be gravel or packed dirt, in decent condition. Allows low speed trucks. 

Boundiali-Odienné, Cote d'Ivoire | Road near San, Mali
--- | ---
<img src="https://africaengineering.tn/wp-content/uploads/2017/03/AF_88-1024x683.jpg" alt="drawing" width="300"/> | <img src="http://farm4.static.flickr.com/3082/2613950402_3aa7bc9ac5.jpg?v=0" alt="drawing" width="300"/>

### Quality score: 1 ★☆☆☆
Lowest quality. Dirt track. Virtually unusable for most vehicles, esp. during rainy season.

Kenema-Monrovia road, Sierra Leone | N15, Cameroon
--- | ---
<img src="https://i.pinimg.com/originals/72/ac/3c/72ac3c853370c351172ba13a27ad7b98.jpg" alt="drawing" width="300"/> | <img src="https://www.dangerousroads.org/images/stories/__Roads00000av/N15.jpg" alt="drawing" width="300"/>

### Conversion from OSM to quality score, by country
This conversion scheme was created by manually comparing OSM roads with publicly available satellite imagery from 2018. 

For example, OSM class "trunk" in Gambia was converted to a quality score of 3. "n/a" indicates that this OSM class is not present in the data for the given country.

| Country | motorway | trunk | primary | secondary | tertiary |
| --- | --- | --- | --- | --- | --- |
| Benin | n/a | n/a | 3 | 1 | n/a |
| Burkina Faso | n/a | 3 | 2 | 2 | n/a |
| Cameroon | n/a | 2 | 2 | 1 | n/a |
| Gambia | n/a | 3 | 3 | 2 | n/a |
| Ghana | n/a | 3 | 2 | 2 | n/a |
| Guinea | n/a | 3 | 2 | 1 | 1 |
| Guinea Bissau | n/a | n/a | 3 | 2 | 2 |
| Ivory Coast | 4 | 3 | 2 | 1 | n/a |
| Liberia | n/a | 3 | 2 | 1 | n/a |
| Mali | n/a | 3 | 3 | 2 | n/a |
| Mauritania | n/a | 3 | 3 | 2 | n/a |
| Niger | n/a | 3 | 2 | 1 | n/a |
| Nigeria | 4 | 3 | 2 | 1 | n/a |
| Senegal | 4 | 3 | 3 | 2 | n/a |
| Sierra Leone | n/a | 3 | 2 | 2 | 1 |
| Togo | n/a | 3 | 2 | 1 | n/a |
