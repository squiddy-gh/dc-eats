# Northern Virginia Magazine Best of NoVA 2026

Source: [magazine food awards](https://northernvirginiamag.com/food-and-drink/2026/06/12/best-of-nova-2026-dig-into-northern-virginias-best-food/). Business details checked October 7, 2026.

The CSV contains 125 award/location rows representing all 61 award entries in 31 categories, including NoVA Wars: Italian Edition. A business with multiple verified branches gets a row for each branch within the article's named Northern Virginia cities. Repeat awards remain separate rows. This is not a count of unique restaurants.

Coverage: 119 rows have phone numbers; 114 have some daily hours, including 109 with all seven days; 111 have coordinates. Unknown fields remain blank. A blank day is unknown, not closed. `Closed` is used for explicit closure; `24 hours` and overnight schedules are supported by the map. Opening/last-seating times alone are insufficient to establish closing time. Hours can change and are not guarantees of service.

Business websites and individual location pages were preferred. A small number of records use source-linked directories or reservation listings when official details were unavailable. Per-row source links and notes identify limitations. Conflicting hours were withheld, including Agora Tysons, Yoder's, Call Your Mother Reston, and Sense of Thai Chantilly. Flavor Hive's Potomac Yard branch is temporarily closed; its hours remain unknown. Velocity's Manassas location and S&P Burger's current location need further confirmation. Alexandria's farmers' market is temporarily on North Royal Street and Tavern Square; its precise point remains unverified.

Narratives are original short factual summaries, not copied magazine reviews, and are labeled accordingly. Some runner-up records have only a brief category-based description because the article supplies no narrative. Text is NFC-normalized UTF-8 with a BOM for Excel.

Coordinates come from existing repository records, official structured location data, or cached exact-address lookups. Geocoding matches are recorded for review; 14 rows remain unlocated. OpenStreetMap lookup data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), under ODbL. Lookups followed the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/); the public app does not call the geocoder.

Rebuild with `python scripts/import_nova.py`. The importer validates the reviewed records and preserves their check dates; it does not pretend to refresh live websites. To refresh, review the linked sources, edit `docs/nova_2026_reviewed.json`, and rerun. The map and Pages package include this CSV; deployment remains a manual workflow action.
