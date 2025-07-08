import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# ---- Load GeoJSON files ----
with open("us_states.geojson") as f:
    states_geo = json.load(f)
with open("us_cities.geojson") as f:
    cities_geo = json.load(f)
with open("us_spots.geojson") as f:
    spots_geo = json.load(f)

# ---- Session state for navigation ----
if "level" not in st.session_state:
    st.session_state.level = "country"
    st.session_state.selected_state = None
    st.session_state.selected_city = None

def go_back():
    if st.session_state.level == "city":
        st.session_state.level = "state"
        st.session_state.selected_city = None
    elif st.session_state.level == "state":
        st.session_state.level = "country"
        st.session_state.selected_state = None

# ---- UI ----
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
st.title("US Map Drill‑down")

if st.session_state.level != "country":
    st.button("◀️ Back", on_click=go_back)

# ---- Map setup ----
bounds = [[49.38, -124.7], [24.5, -66.9]]  # Contiguous
m = folium.Map(zoom_control=False, scrollWheelZoom=False,
               zoomSnap=False, drag=False)

if st.session_state.level == "country":
    m.fit_bounds(bounds)
    def style(x): return {"fillColor":"#fff","color":"#000","weight":1}
    folium.GeoJson(
        states_geo, style_function=style,
        highlight_function=lambda x: {"weight":2,"color":"blue"},
        tooltip=folium.GeoJsonTooltip(fields=["name"])
    ).add_to(m)

elif st.session_state.level == "state":
    state = st.session_state.selected_state
    feature = next(f for f in states_geo["features"] if f["properties"]["name"]==state)
    coords = feature["geometry"]["coordinates"]
    m.fit_bounds(folium.GeoJson(feature).get_bounds())
    for f in cities_geo["features"]:
        if f["properties"]["state"]==state:
            folium.Marker(
                location=[*f["geometry"]["coordinates"][::-1]],
                tooltip=f["properties"]["name"]
            ).add_to(m)

else:  # city level
    city = st.session_state.selected_city
    feat = next(f for f in cities_geo["features"] if f["properties"]["name"]==city)
    m.fit_bounds(folium.GeoJson(feat).get_bounds())
    for f in spots_geo["features"]:
        if f["properties"]["city"]==city:
            folium.Marker(
                location=[*f["geometry"]["coordinates"][::-1]],
                popup=f["properties"]["name"]
            ).add_to(m)

# ---- Click handling ----
res = st_folium(m, height=600, width=1000)

if res and res.get("last_object_clicked"):
    props = res["last_object_clicked"]["properties"]
    if st.session_state.level == "country":
        st.session_state.selected_state = props["name"]
        st.session_state.level = "state"
    elif st.session_state.level == "state":
        st.session_state.selected_city = props["name"]
        st.session_state.level = "city"
