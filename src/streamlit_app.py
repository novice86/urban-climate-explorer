import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import numpy as np

# SETUP & DATA LOADING
st.set_page_config(page_title="Global City Climate Dashboard", layout="wide")
st.title("🌍 Global City Climate Analysis")
st.markdown("Explore temperature stability, extreme precipitation, and geographic climate trends across 139 global cities.")

# Cache the data so the app doesn't hit the database every time a slider moves
@st.cache_data
def load_data():
    with sqlite3.connect('../db/city_climate_data.db') as conn:
        df = pd.read_sql_query("SELECT * FROM city_climate_data", conn)
    return df

df = load_data()
conditions = [
    (df['lat'].abs() <= 23.5),                               # 0° to 23.5°
    (df['lat'].abs() > 23.5) & (df['lat'].abs() <= 40.0),    # 23.5° to 40°
    (df['lat'].abs() > 40.0) & (df['lat'].abs() <= 55.0),    # 40° to 55°
    (df['lat'].abs() > 55.0)                                 # 55° and above
]

choices = [
    'Tropical (0° - 23.5°)', 
    'Subtropical (23.5° - 40°)', 
    'Temperate (40° - 55°)', 
    'Subarctic & Polar (55°+)'
]

df['climate_zone'] = np.select(conditions, choices, default='Unknown')


# USER INTERACTION (SIDEBAR)
st.sidebar.header("Filter the Data")

# Slider for Population
min_pop = int(df["population"].min())
max_pop = int(df["population"].max())
selected_pop = st.sidebar.slider(
    "Minimum City Population",
    min_value=min_pop,
    max_value=max_pop,
    value=1_000_000,
    step=500_000
)

# Dropdown for Zones
zones = ["All"] + sorted(df['climate_zone'].unique().tolist())
selected_zone = st.sidebar.selectbox("Select a Climate Zone", zones)

# Apply Filters to create a working dataset for the charts
filtered_df = df[df["population"] >= selected_pop]
if selected_zone != "All":
    filtered_df = filtered_df[filtered_df['climate_zone'] == selected_zone]

st.sidebar.write(f"Cities matching criteria: {filtered_df['city'].nunique()}")

# Visualizations

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. The Latitude Effect")
    st.write("Does distance from the equator drive temperature drops?")
    yearly_df = filtered_df.groupby(['city', 'lat'])['mean_temp_F'].mean().reset_index()
    yearly_df['dist_from_equator'] = yearly_df['lat'].abs()
    
    fig1 = px.scatter(
        yearly_df, x='dist_from_equator', y='mean_temp_F', hover_name='city',
        labels={'dist_from_equator': 'Degrees from Equator', 'mean_temp_F': 'Mean Temp (°F)'},
        color='mean_temp_F', color_continuous_scale='Inferno'
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("2. Global Precipitation Map")
    st.write("Which cities receive the highest total annual precipitation?")
    rain_df = filtered_df.groupby(['city', 'lat', 'lng'])['precipitation_in'].sum().reset_index()
    
    fig2 = px.scatter_geo(
        rain_df, lat='lat', lon='lng', size='precipitation_in', hover_name='city',
        projection="natural earth", color='precipitation_in',
        color_continuous_scale=px.colors.sequential.Blues
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()


# A full-width chart for the final visualization
st.subheader("3. Seasonal Temperature Swings")
st.write("Compare monthly temperature profiles. Select cities below:")

# Multi-select for specific city comparison
available_cities = sorted(filtered_df['city'].unique())
# Default to a couple of cities if available to show immediate results
default_cities = available_cities[:2] if len(available_cities) >= 2 else available_cities
selected_cities = st.multiselect("Select Cities to Compare", available_cities, default=default_cities)

if selected_cities:
    city_trend_df = filtered_df[filtered_df['city'].isin(selected_cities)]
    fig3 = px.line(
        city_trend_df, x='month', y='mean_temp_F', color='city', markers=True,
        labels={'month': 'Month', 'mean_temp_F': 'Mean Temp (°F)'}
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Please select at least one city to view the seasonal trends.")


st.divider()

st.subheader("4. Heat vs. Moisture: The Climate Typology")
st.write("How does temperature relate to humidity? Bubble size represents total annual precipitation.")

# Aggregate data to annual averages and totals for a clean scatter plot
climate_scatter_df = filtered_df.groupby(['city', 'country']).agg(
    avg_temp=('mean_temp_F', 'mean'),
    avg_humidity=('humidity_percent', 'mean'),
    total_precip=('precipitation_in', 'sum')
).reset_index()

# Create the scatter plot
fig4 = px.scatter(
    climate_scatter_df, 
    x='avg_temp', 
    y='avg_humidity', 
    size='total_precip', 
    color='country',
    hover_name='city',
    labels={
        'avg_temp': 'Average Temperature (°F)', 
        'avg_humidity': 'Average Humidity (%)',
        'total_precip': 'Total Precipitation (in)'
    },
    size_max=40 # Keeps massive rain totals from covering the whole chart
)

st.plotly_chart(fig4, use_container_width=True)
