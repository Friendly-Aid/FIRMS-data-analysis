#import libraries
import os #os for path
import pandas as pd #pandas for dataframe
import geopandas as gpd #geopandas for geographical data
from shapely.geometry import Point #shapely for getting states from polygons
import requests #requests to get polygon files
from datetime import timedelta #datetime for datetime modification of data

data_file = os.path.join(os.getcwd(), "data", "fire_archive_M-C61_626683.csv.xz") #data file path
states_file = os.path.join(os.getcwd(), "us_states.geojson") #geographical data file path

if not os.path.exists(states_file): #check if file path and download it if it doesn't
    print("Downloading US states boundaries...")
    states_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json" #file url
    response = requests.get(states_url) #get file
    with open(states_file, 'wb') as f: #open file with write bytes
        f.write(response.content) #write file

states_gdf = gpd.read_file(states_file) #geopandas read file
states_gdf = states_gdf.to_crs(epsg=4326) #set how to read file

print("Loading fire data...")
data = pd.read_csv(data_file) #load data

#convert acq_date and acq_time into acq_datetime
data['acq_date'] = pd.to_datetime(data['acq_date'])
data['acq_datetime'] = data['acq_date'] + pd.Series(
    [timedelta(minutes=i % 100, hours=i // 100) for i in data['acq_time']])

data.drop(['acq_time', 'acq_date', 'instrument'], axis=1, inplace=True) #drop useless columns

data['confidence_binned']=pd.cut(data['confidence'],bins=[-1,30,80,101],labels=['Low','Nominal','High']) #bin data confidence

geometry = [Point(xy) for xy in zip(data['longitude'], data['latitude'])] #compine latitude and longitude for grouped coordinates
fire_gdf = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326") #get geographical data

print("Mapping fire points to states...")
fire_with_states = gpd.sjoin(fire_gdf, states_gdf, how="left", predicate="within") #combine original data with new data

output_file = os.path.join(os.getcwd(), "fire_data_transformed.csv") #output file path

# Drop the geometry column before saving CSV, keep all other columns (including the joined ones like 'name')
fire_with_states.drop(columns='geometry', inplace=True) #dropping undesired column

fire_with_states.to_csv(output_file, index=False) #write modified data file to computer

print(f"✅ Done! Output saved to: {output_file}")
