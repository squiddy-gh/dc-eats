"""Rebuild the 2025 NoVA Top 50 CSV from reviewed, source-linked records."""
import argparse,csv,json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(path):
 rows=json.loads(path.read_text(encoding='utf-8'))
 if len(rows)!=53 or len({r['restaurant_name'] for r in rows})!=50:raise ValueError('Expected 50 selections across 53 listed locations.')
 if [r['position'] for r in rows if r['position']]!=['No. '+str(i) for i in range(1,11)]:raise ValueError('Only the top ten have published numbered ranks.')
 for r in rows:
  if not all(r[k] for k in ['restaurant_name','address','cuisine','eat_this','source_url','narrative']):raise ValueError('Missing required field.')
  if r['hours_type']!='opening':raise ValueError('Opening hours required, not happy-hour times.')
  if bool(r['latitude'])!=bool(r['longitude']):raise ValueError('Incomplete coordinate pair.')
  if r['latitude'] and not (38<float(r['latitude'])<40 and -79<float(r['longitude'])<-76):raise ValueError('Out-of-region coordinates.')
  if r['business_status'] in ['permanently_closed','private_events_only'] and any(r[d+'_hours'] not in ['', 'Closed'] for d in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']):raise ValueError('Unavailable venue must not have public opening intervals.')
  for k,v in r.items():
   if any(x in v for x in ['\ufffd','â€™','â€¦','Ã©']):raise ValueError('Damaged encoding in '+k)
   r[k]=unicodedata.normalize('NFC',v)
 return rows

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--reviewed',type=Path,default=ROOT/'docs/top50_2025_reviewed.json')
 p.add_argument('--output',type=Path,default=ROOT/'data/northernvamag_50_best_restaurants_2025.csv')
 a=p.parse_args();rows=load(a.reviewed)
 with a.output.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} locations covering 50 selections to {a.output}')
