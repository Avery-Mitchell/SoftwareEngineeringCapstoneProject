import requests # for api calls 
import folium # for displaying the map from OpenStreetMap
from folium import IFrame, Popup, Element # for the legend and other overlays
import os # for accessing files that are saved by the program
import webbrowser # for opening stuff in the browser
import json # for using the landmarks json

# TODO:
# - need to fix legend functionality - either label each location with num or add the ability to click

def init_map(map_file, center_lat, center_long, zoom_level):
    # CREATES THE MAP
    map = folium.Map(location=[center_lat, center_long], zoom_start=zoom_level)

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
        <h4>Legend</h4>
        '''
        for idx, landmark in enumerate(landmarks):
            name = landmark["name"]
            lat = landmark["lat"]
            lon = landmark["lon"]
            color = "red"
            legend_html += f'''
                <i class="fa fa-map-marker fa-2x" style="color:{color}; cursor: pointer;" 
                onclick="panToLocation({lat}, {lon})"></i> 
                <span style="cursor: pointer;" onclick="panToLocation({lat}, {lon})">{name}</span><br>
            '''
        legend_html += "</div>"
        return legend_html
    
    pan_to_js = '''
    <script>
        var map = L.DomUtil.get('map');  
        function panToLocation(lat, lon) {
            map._leaflet_map.setView([lat, lon], 17);  
        }
    </script>
    '''

    map.get_root().html.add_child(folium.Element(pan_to_js))
    legend_html = generate_legend_html(landmarks)
    map.get_root().html.add_child(folium.Element(legend_html))

    # ADDS THE LEGEND ITEMS TO THE MAP
    for idx, landmark in enumerate(landmarks):
        lat = landmark["lat"]
        lon = landmark["lon"]
        name = landmark["name"]
        image = landmark["image"]
        color = "red"

        popup_content = f"<strong>{name}</strong><br><img src='{image}' width='100'/>"
    
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=color)
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