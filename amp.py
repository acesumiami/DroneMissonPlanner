import gradio as gr
from amp_background import *
from Mission import Mission
from MissionWriter import MissionWriter
import tempfile, json
import time

html_code = """
<div id="map" style="height:500px;"></div>
"""

def process_json(data, alt, fov, v_res, h_res, progress=gr.Progress()):
    progress(0, desc="Starting")

    poly, points, path, directions = get_paths_for_data(data, altitude=alt, fov=fov, v_res=v_res, h_res=h_res, seperate_paths=True, progress=progress)
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.tight_layout()
    show_results(poly, points, path, directions, (fig, ax), progress=progress)

    # yield (fig, gr.update(interactive=True), True, path)
    t = time.localtime()
    print(
        f"Finish creating plot for mission with {len(points)} points. {t.tm_mon}-{t.tm_mday}-{t.tm_hour}:{t.tm_min}:{t.tm_sec}"
    )
    return (fig, gr.update(interactive=True), True, (path, directions))

def export_mission(params):
    mission, direction = params
    mission = Mission(mission, 40, 2, 30, directions=direction)
    writer = MissionWriter()
    res = writer.compile(mission)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".plan", mode="w")
    json.dump(res, tmp, indent=2)
    tmp.close()
    t = time.localtime()
    print(
        f"Exported mission with {len(params[0])} points. {t.tm_mon}-{t.tm_mday}-{t.tm_hour}:{t.tm_min}:{t.tm_sec}"
    )

    return tmp.name  # Return file path


with gr.Blocks() as demo:
    finished_state = gr.State(False)
    mission_state = gr.State([])
    # Map container
    map_html = gr.HTML(html_code)

    with gr.Row():
        alt = gr.Number(value=60, label="Altitude (m)", visible=True, interactive=True)
        fov = gr.Number(value=53.3, label="FOV (°)", visible=True, interactive=True)
        v_res = gr.Number(value=5460, label="Vertical Resolution", visible=True, interactive=True)
        h_res = gr.Number(value=8192, label="Horizontal Resolution", visible=True, interactive=True)
    # Hidden textbox to receive JS data
    hidden = gr.Textbox(label="Shape Summary", visible=True, interactive=False, elem_id="data_dest")
    output = gr.Plot()
    export_button = gr.Button("Export", interactive=False)

    # JS sets value into hidden
    # hidden.change(lambda x: process_json(x, alt=alt, fov=fov, v_res=v_res, h_res=h_res), hidden, [output, export_button, finished_state, mission_state])
    hidden.change(
        process_json,
        inputs=[hidden, alt, fov, v_res, h_res],
        outputs=[output, export_button, finished_state, mission_state]
    )
    export_button.click(export_mission, mission_state, gr.File(label="Download JSON"))

demo.queue()
demo.launch(share=True, js="""
x = async () => {
// Wait until #map exists
function waitForElement(id) {
    return new Promise(resolve => {
        const interval = setInterval(() => {
            const el = document.getElementById(id);
            if (el) {
                clearInterval(interval);
                resolve(el);
            }
        }, 100);
    });
}
            
const mapElement = await waitForElement("map");


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
            }).setView([25.731499, -80.162699], 18);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors",
                maxZoom: 22,       // The maximum zoom the layer will allow
                maxNativeZoom: 19  // The magic trick (see below)
            }).addTo(map);

            var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri',
                maxZoom: 22,       // The maximum zoom the layer will allow
                maxNativeZoom: 19  // The magic trick (see below)
            });
            satellite.addTo(map);

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
}
x()
""")
