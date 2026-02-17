import gradio as gr

html_code = """
<div id="map" style="height:500px;"></div>
"""

def process_json(x):
    print("recieved json", x)
    return x

with gr.Blocks() as demo:

    # Map container
    map_html = gr.HTML(html_code)

    # Hidden textbox to receive JS data
    hidden = gr.Textbox(visible=True, elem_id="data_dest")
    output = gr.Textbox(label="Received Data")

    # JS sets value into hidden
    hidden.change(lambda x: process_json(x), hidden, output)

demo.launch(js="""
/* 1. Load Leaflet CSS */
var leafletCss = document.createElement('link');
leafletCss.rel = 'stylesheet';
leafletCss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
document.head.appendChild(leafletCss);

/* 2. Load Leaflet Draw CSS */
var drawCss = document.createElement('link');
drawCss.rel = 'stylesheet';
drawCss.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css';
document.head.appendChild(drawCss);

/* 3. Load Leaflet JS */
var leafletJs = document.createElement('script');
leafletJs.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
leafletJs.onload = function() {

    /* 4. Load Leaflet Draw JS */
    var drawJs = document.createElement('script');
    drawJs.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js';
    drawJs.onload = function() {

        /* 5. Initialize the map */
        setTimeout(function() {  // small delay to ensure DOM is ready
            var map = L.map("map",{
                zoomControl: true,       // removes zoom buttons
                attributionControl: false // removes attribution text
            }).setView([25.731499, -80.162699], 26);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors"
            }).addTo(map);

            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
            var items = []

            var drawControl = new L.Control.Draw({
                edit: { featureGroup: drawnItems },
                draw: { polygon: true, rectangle: true, circle: false, marker: false, polyline: false }
            });
            map.addControl(drawControl);

            map.on("draw:created", function(e) {
                var type = e.layerType;
                var layer = e.layer;
                drawnItems.addLayer(layer);
                console.log("Created", drawnItems);

                var geojson = drawnItems.toGeoJSON();
                // Send GeoJSON as string to hidden textbox
                var hidden = document.querySelector('#data_dest textarea');
                hidden.value = JSON.stringify(geojson, null, 2);

                // Trigger Gradio change event
                hidden.dispatchEvent(new Event('input'));
            });
        }, 500);
    };
    document.body.appendChild(drawJs);
            
    var style = document.createElement('style');
    style.innerHTML = `
    .leaflet-control-zoom-in, .leaflet-control-zoom-out {
        color: #000000 !important;            /* bright icon/text */
        border: 1px solid #444 !important;    /* subtle border */
    }
            
    .leaflet-control-zoom-in span, .leaflet-control-zoom-out span {
        color: #000000 !important;            /* bright icon/text */
    }

    /* Hover effect */
    .leaflet-control-zoom-in:hover, .leaflet-control-zoom-out:hover {
        background-color: #333 !important;
        color: #ffffaa !important;
    }
    `;
    document.head.appendChild(style);
};
document.body.appendChild(leafletJs);
""")
