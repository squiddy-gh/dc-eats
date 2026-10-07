# Michelin Washington DC Area import

Captured September 27, 2026. Source: [Michelin Washington D.C. Area](https://guide.michelin.com/us/en/area-united-states-washington-dc-area/restaurants).

## Contents and repository integration

Copy this package's `data/`, `scripts/`, `tests/`, and `docs/` folders into the dc-eats repository. All files are additions. No existing data or map files need to be replaced.

The repository is `squiddy-gh/dc-eats`, identified from the earlier restaurant-map chat. Its local September 20 working copy was inspected: it uses `data/`, lowercase underscore CSV names, and separate source files. This package follows those conventions and uses the exact 18-column schema requested for Michelin. Live GitHub access was unavailable (the browser was signed out and the private repository returned 404), so the current remote tree could not be verified. Nothing was committed, pushed, or merged.

`data/michelin_dc_area_2026.csv` contains one row per Michelin detail URL, sorted by restaurant name. The year identifies this capture, not a claimed Michelin guide edition. UTF-8 encoding, comma delimiter, LF newlines, standard CSV quoting. Accents, apostrophes, dollar signs, and international phone prefixes are preserved. Missing values are empty cells.

`data/michelin_dc_area_2026.snapshot.json` preserves the listing URLs, page counts, extracted fields, award evidence, and capture timestamp for reproducible validation. It contains short narrative excerpts, not full reviews.

The existing map has a fixed list of three CSV sources. This new file will not automatically appear as a map layer. It needs geocoding first, then a source entry and `row.narrative` support in the popup normalizer. Those map changes are outside this harvest and have not been made.

## Validation

- Three listing pages: 48 + 48 + 14 = **110** restaurants.
- **110** detail pages read; 110 unique detail URLs; listing and detail sets agree.
- Stars: **89 zero-star, 18 one-star, 3 two-star, 0 three-star** restaurants.
- No missing names, addresses, cuisines, prices, narratives, or source URLs.
- **102** phone numbers, **109** websites, **100** complete Monday–Sunday schedules.
- Latitude and longitude are intentionally blank in all 110 rows for the existing geocoder.
- CSV serialization is verified by reading back every field. The test suite checks count mismatch, duplicates, unknown awards, conflicting responsive badges, partial schedules, and closed versus unknown hours.

Star counts come only from each restaurant's own `.data-sheet__badge-container`, not generic page membership, recommendation cards, or footer icons. Responsive layouts repeat the same badges; the parser verifies agreement and uses one count. Bib Gourmand symbols are not Michelin stars. An absent award container is an error, while an existing container with no star symbols is zero stars. Schema changes may require updating the scraper.

Spot checks include The Inn at Little Washington (two stars, 309 Middle St., Washington, VA, 22747, USA; +1 540-675-3800; official website), Café Riggs (zero stars), minibar by José Andrés (two stars and weekly hours), and Unconventional Diner (Bib Gourmand, zero stars).

The browser initially exposed incomplete content on some pages. A second extraction pass captured the final fields above. Missing values mean not available in the captured Michelin detail DOM, not proof that the restaurant has no phone, website, or operating hours. Refreshes may expose different content or require a free Michelin login. No login barriers were bypassed.

## Field semantics and gaps

- `michelin_stars`: integer 0–3. Zero includes Michelin Selected and Bib Gourmand; the requested schema does not add a separate distinction column. Badge evidence is in the snapshot.
- `price`: Michelin's literal `$`–`$$$$` category, not an estimated dollar amount.
- Daily hours preserve Michelin's local-time display. Multiple sessions are separated by `; `. `closed` means explicitly closed that day; blank means unavailable.
- `narrative`: a short Michelin excerpt of at most 20 source words, with an ellipsis when shortened. Read the complete copyrighted review through `michelin_url`.
- Phone and website values are taken only from Michelin. No outside-source enrichment was substituted.

Missing weekly schedules: Bar del Monte; Café Riggs; Elcielo Bistró DC; Hank’s Oyster Bar; Maison Bar à Vins; MITA; Providencia; Rye Bunny; The Inn at Little Washington; Your Only Friend.

Missing phone numbers: Astoria DC; Bar del Monte; La'Shukran; Oyster Oyster; Providencia; Reveler's Hour; Rye Bunny; Yellow.

Missing website: Shōtō.

The machine-readable `docs/michelin_validation.json` lists gaps by field and restaurant.

## Reproduce the existing CSV offline

From the repository root, using Python 3.10 or later (no third-party Python dependencies):

```sh
python scripts/import_michelin.py data/michelin_dc_area_2026.snapshot.json
python -m unittest discover -s tests -p test_michelin_import.py -v
```

The importer validates the entire snapshot before replacing the output CSV. It rejects incomplete listing coverage, duplicates, invalid stars, inconsistent badges, malformed URLs, and partial weekly schedules. It writes to a temporary file and replaces the CSV only after a successful round trip. Do not run it over a geocoded CSV unless you intend to reset coordinates to the snapshot's blank values; use `--output` to write a separate refresh for comparison.

## Refresh from Michelin

Use Node.js 20+ and Playwright. Install Playwright in the repository or a separate tooling environment; no package manifest from the repository is overwritten by this package:

```sh
npm install --no-save playwright
npx playwright install chromium
node scripts/scrape_michelin.mjs work/michelin_snapshot.json
python scripts/import_michelin.py work/michelin_snapshot.json --output data/michelin_dc_area_2026.csv
```

If Michelin requires login, rerun with `--login` and sign in manually in the opened browser. The script does not store credentials or browser sessions. If challenged or blocked, stop and resolve access normally; there is no bypass logic. The scraper follows actual pagination links, discovers the advertised count dynamically, excludes cards beyond each page's advertised result range, fetches details sequentially with a one-second interval, and stops on errors without replacing the final CSV.

The extraction selectors were exercised against all 110 live pages through the available browser. The offline importer and tests were run successfully. The standalone Playwright collector was syntax-checked but was not run end-to-end in this environment; direct HTTP downloads were blocked, so this capture used the in-app browser with the same extraction function. Review the next refresh's missing-field report before accepting it.
