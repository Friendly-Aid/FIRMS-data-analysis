import os
import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")

@st.cache_data(show_spinner=False)
def load_data():
    url=r'https://github.com/Friendly-Aid/BigProject_1/raw/refs/heads/master/risk_app/fire_data_enriched.csv.xz'
    return pd.read_csv(url,compression='xz',parse_dates=['acq_date'], low_memory=False)
    #path = os.path.join(os.getcwd(), "fire_data_enriched.csv.xz")
    #df = pd.read_csv(path, parse_dates=["acq_date"], low_memory=False)
    #return df

data = load_data()
st.title("Wildfire Risk Matrix Explorer")

month_names = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# === TOP ROW: STATE / COUNTY / PLACE ===
col1, col2, col3 = st.columns(3)

with col1:
    state_options = sorted(data['state_name'].dropna().unique())
    selected_state = st.selectbox("State", [""] + state_options, index=0)

if selected_state:
    county_options = sorted(data[data['state_name'] == selected_state]['county_name'].dropna().unique())
    county_disabled = False
else:
    county_options = []
    county_disabled = True

with col2:
    selected_county = st.selectbox("County", [""] + county_options, index=0, disabled=county_disabled)

if selected_state and selected_county:
    place_options = sorted(
        data[
            (data['state_name'] == selected_state) &
            (data['county_name'] == selected_county)
        ]['place_name'].dropna().unique()
    )
    place_disabled = False
else:
    place_options = []
    place_disabled = True

with col3:
    selected_place = st.selectbox("Place", [""] + place_options, index=0, disabled=place_disabled)

# === SECOND ROW: MONTH(S) + DAY ===
col4, col5 = st.columns([2, 1])

with col4:
    selected_months = st.multiselect("Month(s)", month_names)

with col5:
    if len(selected_months) == 1:
        day_disabled = False
    else:
        day_disabled = True
    selected_day = st.number_input(
        "Day", min_value=1, max_value=31, step=1,
        value=None, placeholder="e.g. 15", disabled=day_disabled
    )

# === RISK MATRIX GENERATION ===
def get_risk_matrix(df, state, county=None, place=None, months=None, day=None):
    month_map = {name.lower(): idx+1 for idx, name in enumerate(month_names)}

    if months:
        months = [month_map[m.lower()] for m in months if m.lower() in month_map]

    filtered = df[df['state_name'] == state].copy()
    filtered['year'] = filtered['acq_date'].dt.year
    filtered['month'] = filtered['acq_date'].dt.month
    filtered['day'] = filtered['acq_date'].dt.day

    filtered = filtered[
        (filtered['year'] != filtered['year'].max()) &
        (filtered['year'] != filtered['year'].min())
    ]
    total_years = (filtered['year'].max() - filtered['year'].min()) + 1
    total_periods = total_years

    if county:
        filtered = filtered[filtered['county_name'] == county]
    if place:
        filtered = filtered[filtered['place_name'] == place]

    if months:
        filtered = filtered[filtered['month'].isin(months)]
        if len(months) == 1 and day:
            filtered = filtered[filtered['day'] == day]
            filtered = filtered.drop_duplicates(
                subset=['month', 'year', 'day', 'fire_count_binned', 'cluster_confidence_binned']
            )
        else:
            filtered = filtered.drop_duplicates(
                subset=['month', 'year', 'fire_count_binned', 'cluster_confidence_binned']
            )
            total_periods = len(months) * total_years
    else:
        filtered = filtered.drop_duplicates(
            subset=['year', 'fire_count_binned', 'cluster_confidence_binned']
        )

    grouped = (
        filtered.groupby(['fire_count_binned', 'cluster_confidence_binned'])
        .size()
        .reset_index(name='count')
    )
    grouped['frequency'] = round((grouped['count'] / total_periods) * 100, 2)
    grouped.drop('count', axis=1, inplace=True)

    pivot = pd.pivot_table(
        grouped,
        index='cluster_confidence_binned',
        columns='fire_count_binned',
        values='frequency',
        aggfunc='mean'
    ).fillna(0)

    # Force full grid
    all_sizes = ["Small", "Medium", "Large"]
    all_confidence = ["High", "Nominal", "Low"]
    pivot = pivot.reindex(index=all_confidence, columns=all_sizes, fill_value=0)

    pivot.index.name = None
    pivot.columns.name = None

    styled = (
        pivot.style
        .format("{:.2f}%")
        .set_table_styles([
            {'selector': 'td, th', 'props': 'border: 2px solid #333333; text-align: center;'},
            {'selector': 'th', 'props': 'background-color: #555555; color: white;'}
        ])
    )
    return styled

# === DISPLAY MATRIX ===
if selected_state:
    matrix = get_risk_matrix(
        data,
        selected_state,
        selected_county or None,
        selected_place or None,
        selected_months,
        selected_day
    )
    st.subheader("Risk Matrix")
    st.write(matrix)
