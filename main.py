import requests # for api calls 
import folium # for displaying the map from OpenStreetMap
from folium import IFrame, Popup, Element, FeatureGroup # for the legend and other overlays
from folium.plugins import Search # for the search bar
import os # for accessing files that are saved by the program
import webbrowser # for opening stuff in the browser
import json # for using the landmarks json

# TODO:
# - remove blue markers that appear from geojson
# - make the search bar look better

with open('api-key.txt', 'r') as z:
    WEATHER_API_KEY = z.read()

def get_current_weather(lat, lon):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}&aqi=no"
    response = requests.get(url)
    weather_data = response.json()

    # CHECK IF THE API CALL WAS SUCCESSFUL
    if response.status_code == 200 and "current" in weather_data:
        weather = {
            "temperature": weather_data["current"]["temp_f"],  # Temperature in Fahrenheit
            "description": weather_data["current"]["condition"]["text"],
            "humidity": weather_data["current"]["humidity"],
            "wind_speed": weather_data["current"]["wind_mph"]
        }
        return weather
    else:
        print("Error fetching weather data:", weather_data)
        return None

def init_map(map_file, center_lat, center_long, zoom_level):
    # CREATES THE MAP
    map = folium.Map(location=[center_lat, center_long], zoom_start=zoom_level)

    weather = get_current_weather(center_lat, center_long)

    # OPENS THE LANDMARKS JSON
    with open('landmarks/landmarks.json') as f:
        landmarks = json.load(f)

    # GENERATES THE LEGEND    
    def generate_legend_html(landmarks):
        legend_html = '''
        <div style="
            position: fixed; 
            bottom: 50px; left: 50px; width: 300px; height: 750px; 
            overflow-y: scroll; background-color: white;  
            border:2px solid grey; z-index:9999; font-size:14px;
            padding: 10px;
        ">
        <h2><b>Legend</b></h2>
        '''
        for idx, landmark in enumerate(landmarks, start=1):
            name = landmark["name"]
            lat = landmark["lat"]
            lon = landmark["lon"]
            color = "red"
            legend_html += f'<b>{idx}.</b> {name}<br>'
        legend_html += "</div>"
        return legend_html
    
    # MOVES MAP WHEN LEGEND IS CLICKED - NOT WORKING 
    pan_to_js = '''
    <script>
        var map = L.DomUtil.get('map');  
        function panToLocation(lat, lon) {
            map._leaflet_map.setView([lat, lon], 17);  
        }
    </script>
    '''

    # GENERATES WEATHER
    def generate_weather_html(weather):
        if weather:
            weather_html = f'''
            <div style="
                position: fixed; 
                bottom: 10px; right: 10px; width: 250px; height: 160px; 
                background-color: white; 
                border:2px solid grey; z-index:9999; font-size:14px;
                padding: 10px;
            ">
            <h2><b>Current Weather in Rolla</b></h2>
            <p>Temperature: {weather["temperature"]} °F</p>
            <p>Condition: {weather["description"]}</p>
            <p>Humidity: {weather["humidity"]}%</p>
            </div>
            '''
        else:
            weather_html = '''
            <div style="
                position: fixed; 
                bottom: 10px; right: 10px; width: 250px; height: auto; 
                background-color: white; 
                border:2px solid grey; z-index:9999; font-size:14px;
                padding: 10px;
            ">
            <h4>Weather Information Unavailable</h4>
            </div>
            '''
        return weather_html

    # ADDS WEATHER TO MAP
    weather_html = generate_weather_html(weather)
    map.get_root().html.add_child(folium.Element(weather_html))

    # ADDS LEGEND TO MAP
    map.get_root().html.add_child(folium.Element(pan_to_js))
    legend_html = generate_legend_html(landmarks)
    map.get_root().html.add_child(folium.Element(legend_html))

    # ADDS THE LEGEND ITEMS TO MAP
    for idx, landmark in enumerate(landmarks, start=1):
        lat = landmark["lat"]
        lon = landmark["lon"]
        name = landmark["name"]
        image = landmark["image"]
        
        icon_html = f'''
        <div style="
            background-color: red; 
            color: white; 
            font-weight: bold; 
            border-radius: 50%; 
            text-align: center; 
            width: 24px; 
            height: 24px; 
            line-height: 24px; 
            border: 2px solid white;">
            {idx}
        </div>
        '''
        icon = folium.DivIcon(html=icon_html)

        popup_content = f"<strong>{idx}. {name}</strong><br><img src='{image}' width='100'/>"
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            icon=icon
        ).add_to(map)

    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }

    for landmark in landmarks:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [landmark["lon"], landmark["lat"]]
            },
            "properties": {
                "name": landmark["name"],
                "image": landmark["image"]
            }
        }
        geojson_data["features"].append(feature)
    
    geojson_layer = folium.GeoJson(
        geojson_data,
        name="Landmarks",
        popup=None,
        tooltip=None
    ).add_to(map)

    Search(
        layer=geojson_layer,
        geom_type='Point',
        placeholder='Search bar...',
        collapsed=False,
        position='topright',
        search_label='name',
        move_to_location=True,
        zoom=17
    ).add_to(map)

    search_bar_css = """
    <style>
        .leaflet-control-search {
            font-size: 16px; /* Adjust font size */
            width: 275px; /* Adjust width */
        }
        .leaflet-control-search input {
            height: 30px; /* Adjust height of input box */
            font-size: 16px; /* Adjust font size of input text */
        }
        .leaflet-control-search .search-button {
            width: 30px; /* Adjust button size */
            height: 30px;
        }
    </style>
    """
    map.get_root().html.add_child(folium.Element(search_bar_css))

    map.save(map_file)
    webbrowser.open('file://' + os.path.realpath(map_file))

def main():
    center_latitude = 37.95618 # Coordinates for the center of MST
    center_longitude = -91.77618
    zoom_level = 17
    map_file = 'dynamic_map.html'
    init_map(map_file, center_latitude, center_longitude, zoom_level)
    
if __name__ == '__main__':
    main()