import folium
from folium.plugins import HeatMap
import os

def generate_heatmap(df):

    os.makedirs("templates", exist_ok=True)

    m = folium.Map(
        location=[df['Start_Lat'].mean(), df['Start_Lng'].mean()],
        zoom_start=5
    )

    heat_data = df[['Start_Lat', 'Start_Lng']].values.tolist()

    HeatMap(heat_data[:5000]).add_to(m)

    m.save("templates/heatmap.html")
