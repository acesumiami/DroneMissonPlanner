import gradio as gr
import json

def process_polygon(geojson_str):
    print("PROCESSING POLYGON")
    if not geojson_str:
        return "No polygon received"

    geojson = json.loads(geojson_str)

    # Example: count vertices
    coords = geojson["geometry"]["coordinates"][0]
    num_vertices = len(coords)

    return f"Polygon received with {num_vertices} vertices"

HTML_IFRAME = """
<iframe id="mapframe"
    style="width:100%; height:520px; border:none;"
    srcdoc='
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-draw/dist/leaflet.draw.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-draw/dist/leaflet.draw.js"></script>
    </head>
    <body style="margin:0;">
        <div id="map" style="height:100vh;"></div>
        <script>
            console.log("MAP")

            var map = L.map("map").setView([37.7749, -122.4194], 13);
            console.log("ADDED SCRIPT")
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors"
            }).addTo(map);

            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);

            var drawControl = new L.Control.Draw({
                edit: { featureGroup: drawnItems },
                draw: { polygon: true }
            });
            map.addControl(drawControl);

            map.on("draw:drawstop", function (event) {
                console.log("STOP", event, drawnItems)

            }); 
            console.log("Continue?")

            map.on(L.Draw.Event.CREATED, function (event) {
                drawnItems.clearLayers();
                drawnItems.addLayer(event.layer);

                var geojson = event.layer.toGeoJSON();

                window.parent.postMessage(
                    { type: "polygon", value: geojson },
                    "*"
                );
            });

            window.addEventListener("message", function(event) {
                console.log("MESSAGE")
                if (event.data.type === "polygon") {

                    const textbox = document.querySelector("#polygon_box textarea");
                    textbox.value = JSON.stringify(event.data.value);
                    textbox.dispatchEvent(new Event("input", { bubbles: true }));

                    // Trigger hidden button click
                    const btn = document.querySelector("#trigger_button button");

                    console.log("Polygon received");
                    console.log(document.querySelector("#trigger_button button"));


                    btn.click();
                }
            });
        </script>
    </body>
    </html>
    '>
</iframe>
"""



with gr.Blocks() as demo:
    gr.Markdown("## Draw a Polygon")

    polygon_box = gr.Textbox(
        elem_id="polygon_box",
        visible=False
    )

    result = gr.Textbox(label="Result")

    trigger = gr.Button(
        visible=False,
        elem_id="trigger_button"
    )

    trigger.click(
        process_polygon,
        inputs=polygon_box,
        outputs=result
    )

    gr.HTML(HTML_IFRAME)

demo.launch()