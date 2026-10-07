"""Rebuild the Best of NoVA CSV from reviewed, source-linked branch records."""
import argparse,csv,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 rows=json.loads(path.read_text(encoding='utf-8'))
 if len({(r['category'],r['place'],r['restaurant_name']) for r in rows})!=61:raise ValueError('Expected 61 award entries.')
 if len({r['category'] for r in rows})!=31:raise ValueError('Expected 31 categories.')
 seen=set()
 for r in rows:
  key=tuple(r[k] for k in ('category','place','restaurant_name','address'))
  if key in seen:raise ValueError('Duplicate award/location: '+str(key))
  seen.add(key)
  if not r['address'] or not r['restaurant_name']:raise ValueError('Missing name/address.')
  if bool(r['latitude'])!=bool(r['longitude']):raise ValueError('Incomplete coordinate pair.')
  if r['latitude'] and not (38<float(r['latitude'])<40 and -79<float(r['longitude'])<-76):raise ValueError('Coordinates outside the region.')
  for k,v in r.items():
   if any(x in v for x in ('\ufffd','â€™','â€¦','Ã©')):raise ValueError('Damaged encoding in '+k)
   r[k]=unicodedata.normalize('NFC',v)
 return rows
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--reviewed',type=Path,default=ROOT/'docs/nova_2026_reviewed.json')
 parser.add_argument('--output',type=Path,default=ROOT/'data/northernvamag_best_of_nova_2026.csv')
 args=parser.parse_args();rows=load(args.reviewed)
 with args.output.open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]),quoting=csv.QUOTE_ALL);writer.writeheader();writer.writerows(rows)
 print(f'Saved {len(rows)} reviewed award/location rows to {args.output}')
