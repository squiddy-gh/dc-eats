# DC Eats map

Serve this directory with `python -m http.server 8000`, then open `http://localhost:8000/`. The static app reads all four CSVs directly from `data/`.

Use **List** to select All lists or one dining guide. Filters reflect published fields: cuisine where present, Michelin stars (including zero-star selections), and Loudoun category and award. Search matches names, addresses, and dishes. Clear filters keeps the selected list; View results fits the map to current matches.

Pins use each guide's color and symbol. Michelin-starred restaurants have a numbered star. Repeated dishes, awards, and memberships at the same named location and rounded coordinates share a pin; exact duplicate entries are suppressed on the map. Clicking opens an address linked to Google Maps, cuisine when available, narrative, website, phone, and published weekly hours. CSV text is rendered as text, and external links accept only HTTP(S).

**Locate me** requests browser location only after clicking. It marks the position and reported accuracy without storing the position. This requires HTTPS (including GitHub Pages) or localhost and browser permission. Denials, timeouts, unavailable location, and unsupported contexts have visible messages. The app does not geocode restaurants.

**Open now** uses `America/New_York`, including daylight saving time, regardless of the visitor's device timezone. The clock and opening status refresh every minute. CSV data bypasses the browser cache and reloads when Open now is selected, when returning to the tab, and every five minutes, so an already-open page can pick up updated schedules. It accepts 12-hour and 24-hour schedules, split service, and overnight intervals including the previous day's service after midnight. Closing times are exclusive. Empty or unrecognized hours remain unknown and are excluded; a missing previous-day schedule can make early-morning closure uncertain. Best of Loudoun includes researched hours where verified; incomplete days remain unknown. Source URLs, research dates, and limitations are stored in the CSV. Holidays and sold-out closures may differ from regular hours. Dataset notes appear in weekly-hours details.

Rows with missing, invalid, or out-of-area coordinates (outside 38–40° N, 79–76° W) are skipped and counted. CSV failures are shown. An internet connection is needed for Leaflet and OpenStreetMap tiles; Leaflet CSS is local and map attribution remains visible.

Run logic tests with `node --test tests/map.test.mjs` (Node 22.7 or newer).

## Trial deployment with GitHub Pages

The workflow in `.github/workflows/pages-trial.yml` deploys only when you manually run it. It tests the map and CSV data, then publishes the app assets and four restaurant CSVs. Research scripts, notes, and geocoding caches are excluded.

1. Commit and push the workflow, `scripts/build_pages.py`, `tests/map.test.mjs`, and the current app and all four CSVs to `main`. Include `data/michelin_dc_area_2026.csv` if it has not yet been committed.
2. On GitHub, open **Settings → Pages** and choose **GitHub Actions** as the publishing source. See [GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
3. Open **Actions → Trial deployment to GitHub Pages → Run workflow**, choose `main`, and run it.
4. When it succeeds, open the URL shown by the deployment. The expected project address is https://squiddy-gh.github.io/dc-eats/.

Each manual run updates this repository's Pages site at the same address; it does not create a separate preview per run. Pushing changes alone does not deploy. No personal access token or additional secret is needed; the workflow uses GitHub's built-in permissions.

For a local check of exactly what will be published, run `python scripts/build_pages.py --output _site`, then `python -m http.server 8000 --directory _site`. The output folder must be new or empty. On subsequent checks, use another empty output folder. GitHub runners start with a fresh checkout for each deployment.
