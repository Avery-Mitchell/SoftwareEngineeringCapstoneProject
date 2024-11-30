import requests # for api calls 
import folium # for displaying the map from OpenStreetMap
from folium import IFrame, Popup, Element, FeatureGroup # for the legend and other overlays
from folium.plugins import Search, PolyLineFromEncoded, MousePosition # for the search bar and route navigation
import os # for accessing files that are saved by the program
import webbrowser # for opening stuff in the browser
import json # for using the landmarks json
import polyline

# TODO:
# - remove blue markers that appear from geojson

with open('weatherapi.txt', 'r') as z:
    WEATHER_API_KEY = z.read()

with open('directionsapi.txt', 'r') as z:
    DIRECTIONS_API_KEY = z.read()

def get_route(DIRECTIONS_API_KEY, start_coords, end_coords):
    url = "https://api.openrouteservice.org/v2/directions/foot-walking"
    headers = {
        "Authorization": DIRECTIONS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [start_coords, end_coords],
        "instructions": "false"
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        encoded_polyline = data['routes'][0]['geometry']
        decoded_polyline = polyline.decode(encoded_polyline)
        return decoded_polyline
    else:
        print("Error fetching walking route:", response.json())
        return None

def calculate_route(map, start_coords, end_coords):
    route_coords = get_route(DIRECTIONS_API_KEY, start_coords, end_coords)
    if route_coords:
        folium.PolyLine(
            route_coords,
            color="blue",
            weight=5,
            opacity=0.8
        ).add_to(map)
        print("Route added to the map.")
    else:
        print("Failed to fetch or draw route.")

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
            bottom: 50px; left: 50px; 
            width: 300px; height: 400px; 
            background-color: rgba(255, 255, 255, 0.9); 
            border-radius: 10px; 
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); 
            z-index: 9999; 
            font-family: Arial, sans-serif; 
            padding: 15px; 
            overflow-y: auto;
        ">
            <h3 style="
                margin: 0 0 10px 0; 
                font-size: 18px; 
                color: #333; 
                text-align: center;
            ">
                🗺️ Legend
            </h3>
            <hr style="
                margin: 10px 0; 
                border: none; 
                border-top: 1px solid #ddd;
            ">
        '''
        for idx, landmark in enumerate(landmarks, start=1):
            name = landmark["name"]
            lat = landmark["lat"]
            lon = landmark["lon"]
            color = "red"  # Placeholder color

            legend_html += f'''
            <div style="
                margin-bottom: 10px; 
                padding: 10px; 
                background-color: rgba(240, 240, 240, 0.9); 
                border-radius: 5px; 
                border-left: 4px solid {color}; 
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            ">
                <strong style="font-size: 14px; color: #333;">{idx}. {name}</strong>
            </div>
            '''

        legend_html += '</div>'
        return legend_html
    
    # GENERATES WEATHER
    def generate_weather_html(weather):
        if weather:
            weather_html = f'''
            <div style="
                position: fixed; 
                bottom: 10px; right: 10px; 
                width: 260px; 
                background-color: rgba(255, 255, 255, 0.9); 
                border-radius: 10px; 
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); 
                z-index: 9999; 
                font-family: Arial, sans-serif; 
                padding: 15px; 
            ">
                <h3 style="
                    margin: 0; 
                    font-size: 18px; 
                    color: #333;
                    text-align: center;
                ">
                    🌤 Current Weather in Rolla
                </h3>
                <hr style="
                    margin: 10px 0; 
                    border: none; 
                    border-top: 1px solid #ddd;
                ">
                <p style="
                    margin: 5px 0; 
                    font-size: 14px; 
                    color: #555;
                ">
                    <strong>Temperature:</strong> {weather["temperature"]} °F
                </p>
                <p style="
                    margin: 5px 0; 
                    font-size: 14px; 
                    color: #555;
                ">
                    <strong>Condition:</strong> {weather["description"]}
                </p>
                <p style="
                    margin: 5px 0; 
                    font-size: 14px; 
                    color: #555;
                ">
                    <strong>Humidity:</strong> {weather["humidity"]}%
                </p>
                <p style="
                    margin: 5px 0; 
                    font-size: 14px; 
                    color: #555;
                ">
                    <strong>Wind Speed:</strong> {weather["wind_speed"]} mph
                </p>
            </div>
            '''
        else:
            weather_html = '''
            <div style="
                position: fixed; 
                bottom: 10px; right: 10px; 
                width: 260px; 
                background-color: rgba(255, 255, 255, 0.9); 
                border-radius: 10px; 
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); 
                z-index: 9999; 
                font-family: Arial, sans-serif; 
                padding: 15px; 
            ">
                <h3 style="
                    margin: 0; 
                    font-size: 18px; 
                    color: #333;
                    text-align: center;
                ">
                    🚫 Weather Unavailable
                </h3>
                <p style="
                    margin: 5px 0; 
                    font-size: 14px; 
                    color: #555;
                    text-align: center;
                ">
                    Unable to fetch weather information at this time.
                </p>
            </div>
            '''
        return weather_html

    # ADDS WEATHER TO MAP
    weather_html = generate_weather_html(weather)
    map.get_root().html.add_child(folium.Element(weather_html))

    # ADDS LEGEND TO MAP
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
        /* Main container for the search control */
        .leaflet-control-search {
            font-family: Arial, sans-serif; /* Use a clean, modern font */
            font-size: 16px; /* Adjust font size */
            width: 325px; /* Make the search bar container wider */
            background-color: rgba(255, 255, 255, 0.9); /* Semi-transparent background */
            border-radius: 8px; /* Add rounded corners */
            padding: 5px; /* Add padding inside the container */
        }
        
        /* Input box styling */
        .leaflet-control-search input {
            width: 250px; /* Make the text input box wider */
            height: 35px; /* Adjust height of input box */
            font-size: 14px; /* Adjust font size of input text */
            border: 1px solid #ccc; /* Light gray border */
            border-radius: 4px; /* Rounded corners */
            padding-left: 10px; /* Add padding inside */
            outline: none; /* Remove default outline */
        }
        .leaflet-control-search input:focus {
            border-color: #007bff; /* Highlighted border color on focus */
            box-shadow: 0 0 4px #007bff; /* Subtle glow effect */
        }
        
        /* Search button styling */
        .leaflet-control-search .search-button {
            width: 30px; /* Slightly larger button size */
            height: 30px; /* Make button size proportional */
            background-color: #007bff; /* Blue background */
            border: none; /* Remove border */
            border-radius: 50%; /* Circular button */
            margin-left: 10px; /* Increase space between input and button */
            cursor: pointer; /* Pointer cursor on hover */
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .leaflet-control-search .search-button:hover {
            background-color: #0056b3; /* Darker blue on hover */
        }
        .leaflet-control-search .search-button:before {
            content: ""; /* Use a magnifying glass icon */
            font-size: 18px; /* Adjust icon size */
            color: white; /* White icon color */
            text-shadow: none; /* Ensure no drop shadow on the icon */
        }
    </style>
    """

    # HTML for navigation bar
    nav_bar_html = """
    <div style="
        position: fixed;
        top: 10px; left: 50%; transform: translateX(-50%);
        background-color: rgba(255, 255, 255, 0.8); padding: 10px;
        z-index: 9999; font-family: Arial, sans-serif; border-radius: 5px;">
        <form id="routeForm">
            <label for="startLocation">Start Location (lat, lon):</label><br>
            <input type="text" id="startLocation" name="startLocation" placeholder="Enter coordinates (e.g. 37.95618, -91.77618)" required><br><br>
            <label for="endLocation">End Location (lat, lon):</label><br>
            <input type="text" id="endLocation" name="endLocation" placeholder="Enter coordinates (e.g. 37.9525, -91.7745)" required><br><br>
            <button type="button" onclick="getRoute()">Get Walking Directions</button>
        </form>
    </div>
    <script>
        function getRoute() {
            var startLoc = document.getElementById("startLocation").value.split(',');
            var endLoc = document.getElementById("endLocation").value.split(',');

            if (startLoc.length === 2 && endLoc.length === 2) {
                var startLat = parseFloat(startLoc[0].trim());
                var startLon = parseFloat(startLoc[1].trim());
                var endLat = parseFloat(endLoc[0].trim());
                var endLon = parseFloat(endLoc[1].trim());

                if (!isNaN(startLat) && !isNaN(startLon) && !isNaN(endLat) && !isNaN(endLon)) {
                    window.selectedStart = [startLon, startLat];
                    window.selectedEnd = [endLon, endLat];

                    // Update the map with new markers
                    var startMarker = L.marker(window.selectedStart).addTo(map);
                    startMarker.bindPopup('Start Location').openPopup();

                    var endMarker = L.marker(window.selectedEnd).addTo(map);
                    endMarker.bindPopup('End Location').openPopup();

                    // Call Python function to calculate the route
                    google.colab.kernel.invokeFunction('calc_route', [window.selectedStart, window.selectedEnd], {});
                } else {
                    alert("Please enter valid coordinates.");
                }
            } else {
                alert("Please enter both start and end coordinates in the correct format.");
            }
        }
    </script>
    """

    map.get_root().html.add_child(Element(nav_bar_html))

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