# DC Eats map

Serve this directory with `python -m http.server 8000`, then open `http://localhost:8000/`. The static app reads all four CSVs directly from `data/`.

Use **List** to select All lists or one dining guide. Filters reflect published fields: cuisine where present, Michelin stars (including zero-star selections), and Loudoun category and award. Search matches names, addresses, and dishes. Clear filters keeps the selected list; View results fits the map to current matches.

Pins use each guide's color and symbol. Michelin-starred restaurants have a numbered star. Repeated dishes, awards, and memberships at the same named location and rounded coordinates share a pin; exact duplicate entries are suppressed on the map. Clicking opens an address linked to Google Maps, cuisine when available, narrative, website, phone, and published weekly hours. CSV text is rendered as text, and external links accept only HTTP(S).

**Locate me** requests browser location only after clicking. It marks the position and reported accuracy without storing the position. This requires HTTPS (including GitHub Pages) or localhost and browser permission. Denials, timeouts, unavailable location, and unsupported contexts have visible messages. The app does not geocode restaurants.

**Open now** uses `America/New_York`, including daylight saving time, regardless of the visitor's device timezone. The clock and opening status refresh every minute. CSV data bypasses the browser cache and reloads when Open now is selected, when returning to the tab, and every five minutes, so an already-open page can pick up updated schedules. It accepts 12-hour and 24-hour schedules, split service, and overnight intervals including the previous day's service after midnight. Closing times are exclusive. Empty or unrecognized hours remain unknown and are excluded; a missing previous-day schedule can make early-morning closure uncertain. Best of Loudoun includes researched hours where verified; incomplete days remain unknown. Source URLs, research dates, and limitations are stored in the CSV. Holidays and sold-out closures may differ from regular hours. Dataset notes appear in weekly-hours details.

Rows with missing, invalid, or out-of-area coordinates (outside 38–40° N, 79–76° W) are skipped and counted. CSV failures are shown. An internet connection is needed for Leaflet and OpenStreetMap tiles; Leaflet CSS is local and map attribution remains visible.

Run logic tests with `node --test tests/map.test.mjs` (Node 22.7 or newer).
