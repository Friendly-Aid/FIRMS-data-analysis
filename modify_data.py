#import libraries
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import requests
from datetime import timedelta

#set file paths
data_file = os.path.join(os.getcwd(), "data", "fire_archive_M-C61_626683.csv.xz")
states_file = os.path.join(os.getcwd(), "us_states.geojson")

#check if geojson file exists and if not download it
if not os.path.exists(states_file):
    print("Downloading US states boundaries...")
    states_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    response = requests.get(states_url)
    with open(states_file, 'wb') as f:
        f.write(response.content)

states_gdf = gpd.read_file(states_file)
states_gdf = states_gdf.to_crs(epsg=4326) #set how to read file

print("Loading fire data...")
data = pd.read_csv(data_file)

#convert acq_date and acq_time into acq_datetime
data['acq_date'] = pd.to_datetime(data['acq_date'])
data['acq_datetime'] = data['acq_date'] + pd.Series(
    [timedelta(minutes=i % 100, hours=i // 100) for i in data['acq_time']])

data.drop(['acq_time', 'acq_date', 'instrument'], axis=1, inplace=True) #drop useless columns

data['confidence_binned']=pd.cut(data['confidence'],bins=[-1,30,80,101],labels=['Low','Nominal','High']) #bin data confidence

geometry = [Point(xy) for xy in zip(data['longitude'], data['latitude'])] #compine latitude and longitude for grouped coordinates
fire_gdf = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326") #get geographical data

print("Mapping fire points to states...")
fire_with_states = gpd.sjoin(fire_gdf, states_gdf, how="left", predicate="within") #combine original data with new mapped points data

output_file = os.path.join(os.getcwd(), "fire_data_transformed.csv") #output file path

fire_with_states.drop(columns='geometry', inplace=True) #dropping undesired column

fire_with_states.to_csv(output_file, index=False) #write modified data file to computer

print(f"✅ Done! Output saved to: {output_file}")