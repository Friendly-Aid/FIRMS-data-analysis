import os
import io
import requests
import zipfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

base_url = "https://www2.census.gov/geo/tiger/TIGER2024/PLACE"

r = requests.get(base_url, verify=False)

with open(f"{os.getcwd()}\\Place", 'wb') as f:
    f.write(r.content)