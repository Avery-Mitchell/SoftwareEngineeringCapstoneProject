import requests # for api calls 
import folium # for displaying the map from OpenStreetMap
import os # for accessing files that are saved by the program
import webbrowser # for opening stuff in the browser
import json # for using the landmarks json

def init_map(map_file, center_lat, center_long, zoom_level):
    # Create a Folium map
    map = folium.Map(location=[center_lat, center_long], zoom_start=zoom_level)

    with open('landmarks/landmarks.json') as f:
        landmarks = json.load(f)

    for landmark in landmarks:
        lat, lon, name, image = landmark["lat"], landmark["lon"], landmark["name"], landmark["image"]
    
        popup_content = f"<strong>{name}</strong><br><img src='{image}' width='100'/>"
    
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color='red')
        ).add_to(map)

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