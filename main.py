import http.server
import socketserver
import json
import folium
from folium.plugins import Search
import os
import webbrowser
from urllib.parse import urlparse, parse_qs
import requests

PORT = 8000

# --- LOAD API KEYS ---
with open('weatherapi.txt', 'r') as z:
    WEATHER_API_KEY = z.read()

with open('directionsapi.txt', 'r') as z:
    DIRECTIONS_API_KEY = z.read().strip()

# --- LOAD LANDMARKS JSON ---
def load_landmarks():
    with open('landmarks/landmarks.json') as f:
        return json.load(f)

# --- GENERATE LEGEND HTML
def generate_legend_html(landmarks):
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 20px; left: 10px; 
        width: 300px; height: 400px; 
        background-color: rgba(255, 255, 255, 1); 
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
            Legend
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
        color = "green"  # Placeholder color

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

# --- GETS WEATHER INFORMATION ---
def get_current_weather(lat, lon):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}&aqi=no"
    response = requests.get(url)
    weather_data = response.json()

    # CHECK IF THE API CALL WAS SUCCESSFUL
    if response.status_code == 200 and "current" in weather_data:
        weather = {
            "temperature": weather_data["current"]["temp_f"],  
            "description": weather_data["current"]["condition"]["text"],
            "humidity": weather_data["current"]["humidity"],
            "wind_speed": weather_data["current"]["wind_mph"]
        }
        return weather
    else:
        print("Error fetching weather data:", weather_data)
        return None
    
# --- GENERATES WEATHER HTML ---
def generate_weather_html(weather):
    if weather:
        weather_html = f'''
        <div style="
            position: fixed; 
            bottom: 10px; right: 10px; 
            width: 260px; 
            background-color: rgba(255, 255, 255, 1); 
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
                Current Weather in Rolla
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
                <strong>Temperature:</strong> {weather["temperature"]} *F
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
            background-color: rgba(0, 0, 0, 0.2); 
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
                Weather Unavailable
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

# --- ADDS LOCATIONS TO DICTIONARY ---
LOCATIONS = {landmark["name"]: (landmark["lat"], landmark["lon"]) for landmark in load_landmarks()}

# --- HANDLES USER INPUT AND CALLS FUNCTIONS ---
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.serve_map_with_navigation()
        elif self.path.startswith("/navigate"):
            self.handle_navigation()
        elif self.path.startswith("/remove_route"):
            self.remove_route()
        else:
            super().do_GET()

# --- SERVES MAP HTML WITH NAVIGATION INPUT ---
    def serve_map_with_navigation(self):
        map_file = "map.html"

        # CREATES MAP IF IT DOESN'T EXIST
        if not os.path.exists(map_file):
            self.create_map_with_navigation(map_file)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-store")  
        self.end_headers()

        with open(map_file, "r", encoding="utf-8") as f:
            self.wfile.write(f.read().encode("utf-8"))

# --- HANDLES USER INPUT FOR NAVIGATION DROP DOWN ---
    def handle_navigation(self):
        query_components = parse_qs(urlparse(self.path).query)
        start_name = query_components.get("start", [None])[0]
        end_name = query_components.get("end", [None])[0]

        if start_name and end_name:
            start_coords = LOCATIONS.get(start_name)
            end_coords = LOCATIONS.get(end_name)

            # ADDS COORDINATES TO MAP IF THEY EXIST
            if start_coords and end_coords:
                map_file = "map.html"
                self.add_route_to_map(start_coords, end_coords, map_file)

                # SERVES UPDATED MAP
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return

        # RETURNS TO MAP IF ERROR OCCURS
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

# --- REMOVES ROUTE FROM MAP ---
    def remove_route(self):
        map_file = "map.html"
        # CREATES CLEAN MAP
        self.create_map_with_navigation(map_file)
        
        # SERVES CLEAN MAP
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

# --- CREATES MAP WITH NAVIGATION INPUT
    def create_map_with_navigation(self, map_file):
        map = folium.Map(location=[37.95618, -91.77618], zoom_start=17) # MST'S COORDINATES

        # ADDS WEATHER TO THE MAP
        weather = get_current_weather(37.95618, -91.77618)
        weather_html = generate_weather_html(weather)
        map.get_root().html.add_child(folium.Element(weather_html))
        print("Weather successfully added")

        # ADDS LEGEND TO THE MAP
        landmarks = load_landmarks()
        legend_html = generate_legend_html(landmarks)
        map.get_root().html.add_child(folium.Element(legend_html))
        for idx, landmark in enumerate(landmarks, start=1):
            name = landmark["name"]
            lat = landmark["lat"]
            lon = landmark["lon"]

            folium.Marker(
                location=[lat, lon],
                popup=f"{idx}. {name}", 
                icon=folium.DivIcon(html=f'<div style="font-size: 16px; color: green; font-weight: bold;">{idx}</div>') 
            ).add_to(map)

        # NAVIGATION DROP DOWN HTML
        form_html = '''
                <div style="position: fixed; top: 10px; left: 10px; z-index: 9999; background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 8px rgba(255,255,255,0.9); width: 300px; font-family: Arial, sans-serif">
                    <form action="/navigate" method="GET" style="display: flex; flex-direction: column; gap: 15px;">
                        <<h3 style="font-size: 18px; text-align: center; margin-bottom: 10px;">Navigation</h3>
                        
                        <label for="start" style="font-size: 14px; font-weight: bold;">Start:</label>
                        <select name="start" id="start" style="padding: 8px; font-size: 14px; border-radius: 5px; border: 1px solid #ccc; background-color: #f9f9f9;">
                            {start_options}
                        </select>
                        
                        <label for="end" style="font-size: 14px; font-weight: bold;">End:</label>
                        <select name="end" id="end" style="padding: 8px; font-size: 14px; border-radius: 5px; border: 1px solid #ccc; background-color: #f9f9f9;">
                            {end_options}
                        </select>
                        
                        <button type="submit" style="padding: 10px 20px; font-size: 16px; font-weight: bold; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; transition: background-color 0.3s;">
                            Get Route
                        </button>
                    </form>
                    
                    <form action="/remove_route" method="GET" style="margin-top: 15px;">
                        <button type="submit" style="padding: 10px 20px; font-size: 16px; font-weight: bold; background-color: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; transition: background-color 0.3s;">
                            Remove Route
                        </button>
                    </form>
                </div>
            '''
        
        # SEARCH BAR
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
            placeholder='Enter Location Here',
            collapsed=False,
            position='topright',
            search_label='name',
            move_to_location=True,
            zoom=17
        ).add_to(map)

        search_bar_css = """
            <style>
                .leaflet-control-search {
                    font-family: Arial, sans-serif; 
                    font-size: 16px; 
                    width: 325px; 
                    background-color: rgba(255, 255, 255, 0.9); 
                    border-radius: 50px; 
                    padding: 5px; 
                }
                .leaflet-control-search input {
                    width: 250px; 
                    height: 35px; 
                    font-size: 14px; 
                    border: 1px solid #ccc; 
                    border-radius: 4px;
                    padding-left: 10px; 
                    outline: none; 
                }
                .leaflet-control-search input:focus {
                    border-color: #057d25; 
                    box-shadow: 0 0 4px #057d25; 
                }
                .leaflet-control-search .search-button {
                    width: 30px; 
                    height: 30px;
                    background-color: #057d25; 
                    border: none; 
                    border-radius: 50%; 
                    margin-left: 10px; 
                    cursor: pointer; 
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .leaflet-control-search .search-button:hover {
                    background-color: #057d25; 
                }
                .leaflet-control-search .search-button:before {
                    content: ""; 
                    font-size: 18px; 
                    color: green; 
                    text-shadow: none; 
                }
            </style>
            """

        # ADDING HTML ELEMENTS
        start_options = ''.join([f'<option value="{name}">{name}</option>' for name in LOCATIONS])
        end_options = start_options

        form_element = form_html.format(start_options=start_options, end_options=end_options)
        map.get_root().html.add_child(folium.Element(form_element))
        map.get_root().html.add_child(folium.Element(search_bar_css))

        map.save(map_file)

# --- ADDS WALKING ROUTE TO MAP ---
    def add_route_to_map(self, start_coords, end_coords, map_file):
        print(f"Fetching walking route from {start_coords} to {end_coords}")

        url = "https://api.openrouteservice.org/v2/directions/foot-walking"

        # API REQUEST MESSAGE
        payload = {
            "coordinates": [
                [start_coords[1], start_coords[0]],  # [LONGITUDE, LATITUDE]
                [end_coords[1], end_coords[0]]
            ],
            "instructions": False  # TURN BY TURN INSTRUCTIONS DISABLES
        }
        headers = {
            "Authorization": DIRECTIONS_API_KEY,
            "Content-Type": "application/json"
        }

        # API CALL
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching route: {response.text}")
            return

        # ROUTE GEOMETRY
        data = response.json()
        from polyline import decode
        encoded_polyline = data["routes"][0]["geometry"]
        route = decode(encoded_polyline)  # DECODES TO LIST OF [LATITUDEs, LONGITUDES]

        # LOAD / CREATE NEW MAP
        if os.path.exists(map_file):
            with open(map_file, "r") as f:
                existing_map_html = f.read()
            map = folium.Map(location=start_coords, zoom_start=17)

            # START AND END MARKERS
            folium.Marker(start_coords, popup="Start", icon=folium.Icon(color="green")).add_to(map)
            folium.Marker(end_coords, popup="End", icon=folium.Icon(color="red")).add_to(map)

            # ROUTE AS POLYLINE
            folium.PolyLine(route, color="blue", weight=5).add_to(map)

            # NAVIGATION DROP DOWN HTML
            form_html = '''
                <div style="position: fixed; top: 10px; left: 10px; z-index: 9999; background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 8px rgba(255,255,255,0.9); width: 300px; font-family: Arial, sans-serif;">
                    <form action="/navigate" method="GET" style="display: flex; flex-direction: column; gap: 15px;">
                        <h3 style="font-size: 18px; text-align: center; margin-bottom: 10px;">Navigation</h3>
                        
                        <label for="start" style="font-size: 14px; font-weight: bold;">Start:</label>
                        <select name="start" id="start" style="padding: 8px; font-size: 14px; border-radius: 5px; border: 1px solid #ccc; background-color: #f9f9f9;">
                            {start_options}
                        </select>
                        
                        <label for="end" style="font-size: 14px; font-weight: bold;">End:</label>
                        <select name="end" id="end" style="padding: 8px; font-size: 14px; border-radius: 5px; border: 1px solid #ccc; background-color: #f9f9f9;">
                            {end_options}
                        </select>
                        
                        <button type="submit" style="padding: 10px 20px; font-size: 16px; font-weight: bold; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; transition: background-color 0.3s;">
                            Get Route
                        </button>
                    </form>
                    
                    <form action="/remove_route" method="GET" style="margin-top: 15px;">
                        <button type="submit" style="padding: 10px 20px; font-size: 16px; font-weight: bold; background-color: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; transition: background-color 0.3s;">
                            Remove Route
                        </button>
                    </form>
                </div>
            '''
            start_options = ''.join([f'<option value="{name}">{name}</option>' for name in LOCATIONS])
            end_options = start_options

            form_element = form_html.format(start_options=start_options, end_options=end_options)
            map.get_root().html.add_child(folium.Element(form_element))

            map.save(map_file)
        else:
            print("Map file not found.")

        print(f"Map with route saved to {map_file}")


# --- STARTS SERVER ---
def run_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at port {PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()

# --- RUNS SERVER ---
run_server()
