"""Rebuild the 2026 Washington Post Top 40 CSV from reviewed source-linked records."""
import argparse,csv,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DAYS=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

def load(path):
 rows=json.loads(path.read_text(encoding='utf-8'))
 if len(rows)!=40 or len({r['restaurant_name'] for r in rows})!=40:raise ValueError('Expected 40 distinct restaurant selections.')
 if [r['position'] for r in rows]!=['No. '+str(i) for i in range(1,41)]:raise ValueError('Expected unique published ranks 1-40.')
 for r in rows:
  if not all(r[k] for k in ['restaurant_name','address','cuisine','narrative','source_url']):raise ValueError('Missing required selection field.')
  if r['hours_type']!='opening':raise ValueError('Expected opening schedules.')
  if bool(r['latitude'])!=bool(r['longitude']):raise ValueError('Incomplete coordinate pair.')
  if r['latitude'] and not (38<float(r['latitude'])<40 and -79<float(r['longitude'])<-76):raise ValueError('Out-of-region coordinates.')
  if r['phone'] and not re.fullmatch(r'\d{3}-\d{3}-\d{4}',r['phone']):raise ValueError('Malformed phone.')
  for day in DAYS:
   h=r[day+'_hours']
   if h not in ['', 'Closed'] and not all(re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d-(?:[01]\d|2[0-3]):[0-5]\d(?: \(\+1 day\))?',x) for x in h.split('; ')):raise ValueError('Malformed hours: '+h)
  for k,v in r.items():
   if any(x in v for x in ['\ufffd','â€™','â€¦','Ã©']):raise ValueError('Damaged encoding in '+k)
   r[k]=unicodedata.normalize('NFC',v)
 return rows

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--reviewed',type=Path,default=ROOT/'docs/wapo_40_2026_reviewed.json')
 p.add_argument('--output',type=Path,default=ROOT/'data/wapo_40_best_restaurants_dc_2026.csv')
 a=p.parse_args();rows=load(a.reviewed)
 with a.output.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(rows)
 print(f'Saved {len(rows)} ranked restaurants to {a.output}')
