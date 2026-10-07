# Northern Virginia Magazine happy hours 2026

Source: [57 Great Happy Hours Spots in Northern Virginia](https://northernvirginiamag.com/food-and-drink/2026/07/31/great-happy-hours-spots-in-northern-virginia/), published July 31, 2026. Venue details checked October 7, 2026.

The file is named `nothernvamag_great_happy_hours_2026.csv` as requested. It has 58 rows covering the article's 57 entries: Open Road and Heirloom share an article entry and address but have different schedules, so they have separate rows. Locavore & Folklore retains its combined listing and common schedule. `category` identifies the article's geographic section; `place` is Featured, not a ranking or award. No additional branches outside the article were added.

57 venues have phone numbers and 51 have coordinates. The Spot at Belmont Bay's phone could not be verified. Seven uncertain geocoding results are blank. Exact street-address matches can identify a shared building rather than an individual suite; retained matched addresses make those results reviewable. Existing repository coordinates are explicitly labeled. OpenStreetMap-derived data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), under ODbL. Lookup results were cached and rate-limited per the [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/).

The daily `monday_hours` through `sunday_hours` columns contain **happy-hour offer windows**, marked by `hours_type=happy_hour`. They are not restaurant operating hours. `Not offered` means no listed happy-hour offer that day, not that the restaurant is closed. Blank means unresolved availability. The raw article schedule is retained in `happy_hour_schedule`; current verified schedules and notes may differ. Exact closing boundaries are exclusive. All-day offers are bounded by verified service hours, never interpreted as 24-hour service.

Important differences and restrictions:

- Makers Union's current Ashburn page lists 15:00–18:00, with Power Hour 15:00–16:00, superseding the article's 16:00–19:00.
- Joon's current official site says Monday closed. Thursday all-day uses its published 11:30–22:00 service window and source-linked reservation schedule. Weekend kitchen breaks affect some food items.
- Surreal's current operator page conflicts with the article's Sunday/Monday offers. Monday is unavailable and Sunday's offer is withheld; Tuesday–Friday follows the article.
- Salt's official location page lists 17:00–19:00 Monday–Thursday and 16:00–19:00 Friday, differing from the article and separate menu page. The location page is used.
- Sfoglina's dedicated happy-hour menu and article say 15:00–19:00, while its homepage says 15:00–18:00. The dedicated menu is used and the disagreement is noted.
- Claire's current official site includes Friday happy hour, extending the article's Tuesday–Thursday schedule.
- Parallel includes both Crazy Hour and regular Happy Hour. Makers Union's separate Thursday martini promotion does not extend the core happy-hour filter.
- Backyard Grill's filter follows drink offers; appetizer hours are narrower. Red Rocks uses its fixed 14:00–22:00 food window; earlier beer offers are described but not inferred from unverified opening times.
- Lazy Dog's late-night food offers run Sunday–Thursday until midnight; its official location page says drink specials end at 18:00.
- Dok Khao explicitly excludes holidays. The filter uses recurring weekly hours and does not automatically establish holiday availability.

Addresses were checked against venue pages where available. Salt is on Wilson Boulevard rather than the article's Washington Boulevard; Aroma Latin Fusion and Dok Khao are at 15200 Potomac Town Place rather than 1500/5200. Menu URLs are stored separately from business websites. Some magazine menu links are broken; current official menu/venue pages replace those where found.

Narratives are original factual venue summaries based on linked sources, not copied magazine reviews. UTF-8 with BOM and NFC normalization preserve accents and curly apostrophes. Phone numbers favor individual venue pages; source-linked business directories fill a few gaps. BJ's phone comes from a local venue directory and needs reconfirmation.

Rebuild with `python scripts/import_happy_hours.py`. The importer validates and exports `docs/happy_hours_2026_reviewed.json`; it does not refresh live sites or advance the recorded check date. Refresh by reviewing linked sources and updating those records. The Pages package includes the CSV. Deployment remains manual.
