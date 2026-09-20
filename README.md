# DC Eats map

Open `index.html` through a local web server to explore three restaurant lists on a Leaflet/OpenStreetMap map. For example, from the repository root run `python -m http.server 8000`, then visit `http://localhost:8000/`.

The page reads the CSV files in `data/` directly, so updates to those files appear on reload. Each list has its own color and can be shown or hidden using the map layer control. Rows without valid coordinates are skipped, counted in the status text, and reported in the browser console. A failed CSV request is also shown in the status text. The map uses the coordinates already present in the source files and does not send addresses to a geocoder.

An internet connection is needed for the Leaflet library and OpenStreetMap map tiles. OpenStreetMap attribution remains visible on the map.

