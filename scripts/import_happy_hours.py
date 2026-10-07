"""Rebuild the happy-hour CSV from reviewed, source-linked venue records."""
import argparse,csv,json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 rows=json.loads(path.read_text(encoding='utf-8'))
 if len(rows)!=58 or len({r['restaurant_name'] for r in rows})!=58:raise ValueError('Expected 58 distinct venues in 57 article entries.')
 if {r['hours_type'] for r in rows}!={'happy_hour'}:raise ValueError('Expected happy-hour schedules.')
 for r in rows:
  if not all(r[k] for k in ['restaurant_name','address','website','menu_url','source_url','narrative']):raise ValueError('Missing required venue field.')
  if bool(r['latitude'])!=bool(r['longitude']):raise ValueError('Incomplete coordinate pair.')
  if r['latitude'] and not (38<float(r['latitude'])<40 and -79<float(r['longitude'])<-76):raise ValueError('Coordinates outside the region.')
  for k,v in r.items():
   if any(x in v for x in ('\ufffd','â€™','â€¦','Ã©')):raise ValueError('Damaged encoding in '+k)
   r[k]=unicodedata.normalize('NFC',v)
 return rows
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--reviewed',type=Path,default=ROOT/'docs/happy_hours_2026_reviewed.json')
 parser.add_argument('--output',type=Path,default=ROOT/'data/nothernvamag_great_happy_hours_2026.csv')
 args=parser.parse_args();rows=load(args.reviewed)
 with args.output.open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]),quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
 print(f'Saved {len(rows)} reviewed happy-hour venues to {args.output}')
