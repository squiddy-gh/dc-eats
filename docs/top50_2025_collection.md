# Northern Virginia Magazine: 50 Best Restaurants of 2025

Source: https://northernvirginiamag.com/food-and-drink/reviews/2025/10/24/the-50-best-restaurants-in-northern-virginia-of-2025/

Collected October 7, 2026. The CSV has 53 location rows covering all 50 selections. CHĪKO, Sense of Thai, and Thompson Italian each name two cities and have two branch rows. Other chain locations are not added.

The magazine ranks only the first ten. `position` contains “No. 1” through “No. 10”; the other forty positions are blank. `category` distinguishes Top 10 from Top 50 (unranked). Cuisine, price notation, and `eat_this` retain the article’s classifications and dish recommendations, including accented characters. `$$$$*` denotes the article’s prix-fixe price notation. Recommendations describe the 2025 selection; current menus may differ.

The CSV is UTF-8 with a BOM for Excel, Unicode NFC, quoted fields, and CRLF lines. Narratives are original factual venue summaries, identified by `narrative_type`, rather than copies of the magazine’s reviews. Source links are recorded for selection, narrative, contacts, hours, and coordinates.

All 53 rows have coordinates. Coordinates are reused from reviewed records at the same location, obtained from official map links or structured data, or geocoded against a specific street address. Building matches can identify another tenant; they are address-level map points, not necessarily the restaurant entrance. Café Colline matches the named restaurant under a street alias; Alias matches its former street address in Vint Hill; Ometeo matches its name and house number on Capital One Drive. Geocoder ZIP/locality labels may differ from the postal address. No house numbers are removed during address comparison.

Phone is available for 52 rows; Alias’s former phone is withheld. Forty active locations have complete seven-day opening schedules. Additional venues have partial schedules or confirmed closed days; unknown days remain blank. Hours are current research, not reconstructed 2025 hours. Previous happy-hour schedules are never reused as opening hours. Sources and limitations appear in each row’s `hours_notes`.

Alias closed permanently on January 18, 2026. Its former website now redirects to unrelated content, so that link is withheld. Carmello’s currently offers private dining and events by appointment only. Both historical selections remain visible and labeled on the map, but are excluded from Open now regardless of weekly hours.

2941, Field & Main, Ellie Bird, Trio Grill, Trummer’s, and Vermilion publish service starts, last seatings, or incomplete closing times. These are explained in notes and not converted into guessed full-day ranges. Agora and Sense of Thai’s Chantilly branch retain unresolved schedule conflicts from the earlier reviewed collection. Modan uses its venue-managed OpenTable schedule. Chosun Hwaro and Local Provisions use corroborated secondary schedules. Padaek uses the municipal Arlington tourism listing because its article-linked website is parked. Wren and Ometeo include bar availability after the kitchen closes, with the kitchen cutoff in notes. Roberto’s daily columns describe dining hours, with earlier aperitivo service noted separately.

To rebuild without network access: `python scripts/import_top50.py`. Edit `docs/top50_2025_reviewed.json` after checking the row’s source links, then run the importer. It validates selection count, ranks, required fields, encoding, coordinate pairs, and historical availability flags. This reproduces the reviewed collection; it does not imply that changing hours were freshly checked.

The map’s cuisine dropdown indexes the article’s exact labels, including Modern Indian and Mesoamerican Fusion. Popups display rank and highlighted Eat this after location, hours, and contact links, before the narrative. The seventh CSV is included in the existing manual GitHub Pages packaging workflow.
