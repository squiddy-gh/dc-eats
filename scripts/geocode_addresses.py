#!/usr/bin/env python3
"""Geocode street addresses from a CSV file without an API key.

Uses the OpenStreetMap Nominatim service. The public service is intended for
moderate use, so requests are spaced by at least one second and successful
results are cached locally.

Usage:
    python geocode_addresses.py addresses.csv --output addresses-geocoded.csv
    python geocode_addresses.py addresses.csv --address-column "Street Address"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "csv-address-geocoder/1.0"
DEFAULT_DELAY = 1.1
OUTPUT_FIELDS = ["street address", "city", "state", "zip code", "latitude", "longitude"]
STREET_SUFFIXES = (
    "alley|aly|avenue|ave|boulevard|blvd|circle|cir|court|ct|drive|dr|highway|hwy|"
    "junction|jct|lane|ln|parkway|pkwy|place|pl|road|rd|square|sq|street|st|"
    "terrace|ter|trail|trl|turnpike|tpke|way"
)
UNIT_MARKER_PATTERN = re.compile(
    r"\b(?:apartment|apt|suite|ste|unit|floor|fl|building|bldg|room|rm|lot|trailer|trlr)\.?\s*"
    r"[#A-Za-z0-9-]+\b\s*",
    re.IGNORECASE,
)
UNMARKED_UNIT_PATTERN = re.compile(
    rf"(\b(?:{STREET_SUFFIXES})\.?)\s+(?:#?\d+[A-Za-z]?|[A-Za-z])\s+(?=[A-Za-z])",
    re.IGNORECASE,
)


def normalize_address(value: str) -> str:
    """Normalize an address for cache keys and duplicate detection."""
    return " ".join(value.split()).strip().casefold()


def simplify_address_for_lookup(address: str) -> str:
    """Remove unit text that can prevent a street-level geocoding match."""
    simplified = UNIT_MARKER_PATTERN.sub("", address)
    simplified = UNMARKED_UNIT_PATTERN.sub(r"\1 ", simplified)
    simplified = " ".join(simplified.split()).strip(" ,")
    return re.sub(r"\s+,", ",", simplified)


def find_address_column(fieldnames: list[str], requested: str | None) -> str:
    if requested:
        if requested in fieldnames:
            return requested
        raise ValueError(
            f"Address column {requested!r} was not found. Available columns: {', '.join(fieldnames)}"
        )

    candidates = {"address", "street address", "full address", "street_address"}
    for fieldname in fieldnames:
        if fieldname.strip().casefold() in candidates:
            return fieldname
    raise ValueError(
        "Could not identify an address column. Use --address-column to specify one. "
        f"Available columns: {', '.join(fieldnames)}"
    )


def load_cache(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read cache file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Cache file {path} must contain a JSON object")
    return {key: value for key, value in data.items() if isinstance(value, dict)}


def save_cache(path: Path, cache: dict[str, dict[str, str]]) -> None:
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def geocode_address(address: str, user_agent: str, countrycodes: str | None) -> dict[str, str]:
    params = f"q={quote_plus(address)}&format=jsonv2&addressdetails=1&limit=1"
    if countrycodes:
        params += f"&countrycodes={quote_plus(countrycodes)}"

    request = Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            results = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Nominatim returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Nominatim request failed: {exc}") from exc

    if not isinstance(results, list) or not results:
        return {field: "" for field in OUTPUT_FIELDS}

    result = results[0]
    address_data = result.get("address", {}) if isinstance(result, dict) else {}
    if not isinstance(address_data, dict):
        address_data = {}

    house_number = str(address_data.get("house_number", "")).strip()
    road = str(address_data.get("road", "")).strip()
    street = " ".join(part for part in (house_number, road) if part)
    city = next(
        (
            value.strip()
            for key in ("city", "town", "village", "municipality", "hamlet")
            if isinstance(value := address_data.get(key), str) and value.strip()
        ),
        "",
    )
    latitude = result.get("lat", "") if isinstance(result, dict) else ""
    longitude = result.get("lon", "") if isinstance(result, dict) else ""

    try:
        latitude = f"{float(latitude):.5f}"
        longitude = f"{float(longitude):.5f}"
    except (TypeError, ValueError):
        latitude = longitude = ""

    return {
        "street address": street,
        "city": city,
        "state": str(address_data.get("state", "")).strip(),
        "zip code": str(address_data.get("postcode", "")).strip(),
        "latitude": latitude,
        "longitude": longitude,
    }


def has_coordinates(result: dict[str, str]) -> bool:
    return bool(result.get("latitude") and result.get("longitude"))


def process_csv(
    input_path: Path,
    output_path: Path,
    address_column: str | None,
    cache_path: Path,
    delay: float,
    user_agent: str,
    countrycodes: str | None,
) -> int:
    with input_path.open(newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = reader.fieldnames or []
        source_column = find_address_column(fieldnames, address_column)
        rows = list(reader)

    cache = load_cache(cache_path)
    output_rows: list[dict[str, str]] = []
    last_request = 0.0
    failures = 0

    for index, row in enumerate(rows, start=2):
        original_address = (row.get(source_column) or "").strip()
        key = normalize_address(original_address)
        if not key:
            result = {field: "" for field in OUTPUT_FIELDS}
        elif key in cache and has_coordinates(cache[key]):
            result = cache[key]
        else:
            wait = delay - (time.monotonic() - last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                lookup_address = simplify_address_for_lookup(original_address)
                result = geocode_address(lookup_address, user_agent, countrycodes)
                if not has_coordinates(result):
                    failures += 1
                    if lookup_address != original_address:
                        print(
                            f"Info: row {index}: no match after removing sub-address text from {original_address!r}",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            f"Warning: row {index}: no geocoding result for {original_address!r}",
                            file=sys.stderr,
                        )
                elif lookup_address != original_address:
                    print(
                        f"Info: row {index}: ignored sub-address text for lookup: {lookup_address}",
                        file=sys.stderr,
                    )
                cache[key] = result
                last_request = time.monotonic()
                save_cache(cache_path, cache)
            except RuntimeError as exc:
                print(f"Warning: row {index}: {exc}", file=sys.stderr)
                result = {field: "" for field in OUTPUT_FIELDS}
                result["street address"] = original_address
                failures += 1

        output_rows.append(result)
        print(f"Processed {index - 1}/{len(rows)}: {original_address or '(blank)'}")

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {output_path}")
    if failures:
        print(f"Completed with {failures} lookup failure(s); failed rows have blank coordinates.", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode addresses in a CSV using OpenStreetMap Nominatim.")
    parser.add_argument("input", type=Path, help="Input CSV containing an address column")
    parser.add_argument("--output", type=Path, help="Output CSV (default: <input>-geocoded.csv)")
    parser.add_argument("--address-column", help="Input column containing the complete street address")
    parser.add_argument("--cache", type=Path, default=Path(".geocode-cache.json"), help="JSON cache file")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between uncached requests (default: 1.1)")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="Descriptive User-Agent sent to Nominatim")
    parser.add_argument("--countrycodes", default="us", help="Comma-separated country codes, or empty for worldwide")
    args = parser.parse_args()

    if args.delay < 1.0:
        parser.error("--delay must be at least 1.0 seconds for the public Nominatim service")
    output_path = args.output or args.input.with_name(f"{args.input.stem}-geocoded.csv")
    try:
        return process_csv(
            args.input,
            output_path,
            args.address_column,
            args.cache,
            args.delay,
            args.user_agent,
            args.countrycodes or None,
        )
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())