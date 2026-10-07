"""Validate a browser harvest and atomically write the DC Eats CSV (stdlib only)."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

DAYS = 'monday tuesday wednesday thursday friday saturday sunday'.split()
FIELDS = ['restaurant_name', 'michelin_stars', 'address', 'latitude', 'longitude',
          'phone', 'website', 'cuisine', 'price', *[d + '_hours' for d in DAYS],
          'narrative', 'michelin_url']


def validate(data):
    rows = data['records']
    expected = data['expected_count']
    if not isinstance(expected, int) or expected < 1 or len(rows) != expected:
        raise ValueError(f'Expected {expected} restaurants, got {len(rows)}')
    urls = [r['michelin_url'] for r in rows]
    if len(set(urls)) != len(urls):
        raise ValueError('Duplicate restaurant URLs')
    listing = {r['url'] for r in data['allLinks']}
    if set(urls) != listing or len(listing) != expected:
        raise ValueError('Detail rows do not match the complete listing')
    for row in rows:
        for field in ['restaurant_name', 'address', 'cuisine', 'price', 'michelin_url']:
            if not row.get(field):
                raise ValueError(f'Missing {field}: {row.get("restaurant_name")}')
        stars = row.get('michelin_stars')
        if type(stars) is not int or not 0 <= stars <= 3:
            raise ValueError('Missing or invalid star count')
        badges = row.get('badges')
        if not badges:
            raise ValueError('Missing award-container evidence')
        for group in badges:
            if sum('/michelin-star_' in src for src in group) != stars:
                raise ValueError('Conflicting responsive award badges')
        url = urlparse(row['michelin_url'])
        if url.scheme != 'https' or url.hostname != 'guide.michelin.com' or '/restaurant/' not in url.path:
            raise ValueError('Unexpected source URL')
        if row.get('website') and urlparse(row['website']).scheme not in ('https', 'http'):
            raise ValueError('Unexpected website URL')
        present_days = [bool(row.get(d + '_hours')) for d in DAYS]
        if any(present_days) and not all(present_days):
            raise ValueError(f'Partial weekly hours: {row["restaurant_name"]}')
        if row.get('price') not in ['$', '$$', '$$$', '$$$$']:
            raise ValueError('Unrecognized price category')
    return rows


def excerpt(text):
    # Short attributed excerpts only; full reviews remain on Michelin's site.
    words = text.split()
    return ' '.join(words[:20]) + (' …' if len(words) > 20 else '')


def export(data, destination):
    source_rows = validate(data)
    rows = [{field: r.get(field, '') for field in FIELDS} for r in source_rows]
    for row in rows:
        row['narrative'] = excerpt(row['narrative'])
    rows.sort(key=lambda row: (row['restaurant_name'].casefold(), row['michelin_url']))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.tmp')
    with temporary.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    with temporary.open(newline='', encoding='utf-8') as stream:
        readback = list(csv.DictReader(stream))
    if len(readback) != len(rows) or any(list(r) != FIELDS for r in readback):
        raise ValueError('CSV round-trip failed')
    for before, after in zip(rows, readback):
        if any(str(before[f]) != after[f] for f in FIELDS):
            raise ValueError('CSV field changed during serialization')
    temporary.replace(destination)
    return {
        'captured_at': data['captured_at'], 'source': data['listing_url'],
        'expected_count': data['expected_count'], 'rows': len(rows),
        'unique_urls': len({r['michelin_url'] for r in rows}),
        'star_counts': dict(sorted(Counter(r['michelin_stars'] for r in rows).items())),
        'missing_by_field': {f: [r['restaurant_name'] for r in rows if r[f] == ''] for f in FIELDS},
        'narrative_policy': 'At most 20 source words plus an ellipsis; see michelin_url for full review',
        'csv_round_trip': 'passed',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/michelin_dc_area_2026.csv'))
    parser.add_argument('--report', type=Path, default=Path('docs/michelin_validation.json'))
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text(encoding='utf-8'))
    report = export(data, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Validated and wrote {report["rows"]} restaurants to {args.output}')


if __name__ == '__main__':
    main()
