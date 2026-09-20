# DC Eats map

Open `index.html` through a local web server to explore three restaurant lists on a Leaflet/OpenStreetMap map. For example, from the repository root run `python -m http.server 8000`, then visit `http://localhost:8000/`.

The page reads the CSV files in `data/` directly, so updates to those files appear on reload. Each list has its own color and can be shown or hidden using the map layer control. Rows with missing, invalid, or out-of-area coordinates (outside 38–40° N, 79–76° W) are skipped, counted in the status text, and reported in the browser console. A failed CSV request is also shown in the status text. The map uses the coordinates already present in the source files and does not send addresses to a geocoder.

An internet connection is needed for the Leaflet script and OpenStreetMap map tiles. Leaflet's stylesheet is bundled locally so tiles and controls remain positioned correctly. OpenStreetMap attribution remains visible on the map.

