#!/usr/bin/env python3
"""Apply reviewed, branch-specific enrichment; stdlib only, no network access.

Usage: python scripts/enrich_cheap_eats.py --input PATH_TO_EXISTING_CSV
Run from the package/repository root. Source data is reviewed separately;
this script does not pretend to scrape heterogeneous sites automatically.
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
FIELDS = ['restaurant_name', 'address', 'latitude', 'longitude', 'phone', 'website',
          *[d+'_hours' for d in DAYS], 'narrative', 'source_url', 'short_description']
ARTICLE = 'https://washingtonian.com/2026/08/27/best-cheap-eats-around-the-dc-area/'
MARKERS = ('Ã', 'Â', 'â€', 'â€™', 'â€œ', 'â€¦', '\ufffd')
HOURS = re.compile(r'(?:[0-2]\d:[0-5]\d-[0-2]\d:[0-5]\d(?: \(\+1 day\))?)(?:; [0-2]\d:[0-5]\d-[0-2]\d:[0-5]\d(?: \(\+1 day\))?)*\Z')

def clean(value):
    """Repair reversible UTF-8-as-Western-text corruption, preserving accents."""
    value = value or ''
    for _ in range(2):
        score = sum(value.count(m) for m in MARKERS)
        if not score:
            break
        candidates = []
        for encoding in ('cp1252', 'latin1'):
            try:
                candidate = value.encode(encoding).decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if sum(candidate.count(m) for m in MARKERS) < score:
                candidates.append(candidate)
        if not candidates:
            break
        value = candidates[0]
    return unicodedata.normalize('NFC', ' '.join(value.split()))

def key(row):
    return clean(row.get('original_name', row.get('restaurant_name', ''))), clean(row['address'])

def enrich(original, enrichment):
    index = {key(r): r for r in enrichment}
    if len(index) != len(enrichment):
        raise ValueError('Duplicate enrichment branch keys')
    seen = set()
    output, evidence = [], []
    for before in original:
        k = key(before)
        if k in seen:
            raise ValueError(f'Duplicate input branch: {k}')
        seen.add(k)
        if k not in index:
            raise ValueError(f'Unreviewed input branch: {k}')
        e = index[k]
        if len(e['hours']) != 7:
            raise ValueError(f'Expected seven daily hours: {k}')
        row = {f: '' for f in FIELDS}
        row.update(restaurant_name=clean(e.get('restaurant_name', k[0])),
                   address=before['address'], latitude=before['latitude'], longitude=before['longitude'],
                   phone=e['phone'], website=e.get('website', before.get('website', before.get('website_address', ''))),
                   narrative=clean(e['narrative']), source_url=ARTICLE,
                   short_description=clean(before.get('short_description', '')))
        row.update(zip([d+'_hours' for d in DAYS], e['hours']))
        if not row['narrative'].endswith(('.', '!', '?')) or row['narrative'].endswith('...'):
            raise ValueError(f'Incomplete narrative: {k}')
        if any(m in v for v in row.values() for m in MARKERS):
            raise ValueError(f'Unresolved character corruption: {k}')
        for h in e['hours']:
            if h not in ('', 'Closed') and not HOURS.fullmatch(h):
                raise ValueError(f'Invalid hours: {k}: {h}')
            for hh in re.findall(r'(\d\d):', h):
                if int(hh) > 23:
                    raise ValueError(f'Invalid clock hour: {h}')
        if row['phone'] and not re.fullmatch(r'\d{3}-\d{3}-\d{4}', row['phone']):
            raise ValueError(f'Invalid phone: {k}')
        output.append(row)
        evidence.append(dict(restaurant_name=row['restaurant_name'], address=row['address'],
                             phone_source=e['phone_source'], hours_source=e['hours_source'],
                             narrative_source=e['narrative_source'], notes=' | '.join(e['notes'])))
    if seen != set(index):
        raise ValueError('Input omits reviewed branches; reconcile before rebuilding')
    return output, evidence

def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--enrichment', type=Path, default=Path('sources/cheap_eats_2026_enrichment.json'))
    parser.add_argument('--output', type=Path, default=Path('data/washingtonian_best_cheap_eats_2026.csv'))
    args = parser.parse_args()
    with args.input.open(encoding='utf-8-sig', newline='') as stream:
        original = list(csv.DictReader(stream))
    reviewed = json.loads(args.enrichment.read_text(encoding='utf-8'))
    output, evidence = enrich(original, reviewed['records'])
    write_csv(args.output, FIELDS, output)
    write_csv(args.output.parent / 'washingtonian_best_cheap_eats_2026_sources.csv', list(evidence[0]), evidence)
    report = dict(checked_on=reviewed['checked_on'], rows=len(output),
                  narratives=sum(bool(r['narrative']) for r in output),
                  phones=sum(bool(r['phone']) for r in output),
                  complete_weekly_hours=sum(all(r[d+'_hours'] for d in DAYS) for r in output),
                  populated_day_fields=sum(bool(r[d+'_hours']) for r in output for d in DAYS),
                  coordinates_preserved=all((a['latitude'], a['longitude'])==(b['latitude'], b['longitude']) for a,b in zip(original,output)),
                  encoding='UTF-8 with BOM', columns=FIELDS)
    (args.output.parent/'washingtonian_best_cheap_eats_2026_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
