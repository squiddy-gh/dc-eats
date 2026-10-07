"""Apply reviewed Loudoun hours by exact name/address; preserve award rows.

python scripts/enrich_loudoun_hours.py --input data/best_of_loudoun.csv \
  --reviewed docs/loudoun_hours_2026.json --output data/best_of_loudoun.csv
This importer does not refresh the research date or scrape new schedules.
"""
import argparse,csv,json,re
from pathlib import Path
DAYS=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
EXTRA=[d+'_hours' for d in DAYS]+['hours_source_url','hours_checked_on','hours_notes']
def enrich(rows,reviewed):
 index={}
 for e in reviewed['records']:
  key=(e['name'],e['address'])
  if key in index:raise ValueError(f'Duplicate branch in review: {key}')
  if len(e['hours'])!=7:raise ValueError(f'Expected seven days: {key}')
  for h in e['hours']:
   if h not in ('','Closed') and not re.fullmatch(r'\d{2}:\d{2}-\d{2}:\d{2}(?: \(\+1 day\))?(?:; \d{2}:\d{2}-\d{2}:\d{2}(?: \(\+1 day\))?)*',h):raise ValueError(f'Invalid schedule: {h}')
   for hh,mm in re.findall(r'(\d{2}):(\d{2})',h):
    if int(hh)>23 or int(mm)>59:raise ValueError(f'Invalid clock: {h}')
  if any(e['hours']) and not e['hours_source_url'].startswith(('https://','http://')):raise ValueError(f'Missing hours source: {key}')
  index[key]=e
 result=[];seen=set()
 for row in rows:
  key=(row['name'],row['address']);seen.add(key)
  if key not in index:raise ValueError(f'Branch not reviewed: {key}')
  e=index[key];out=dict(row);out.update(zip(EXTRA[:7],e['hours']));out.update({f:e[f] for f in EXTRA[7:]});result.append(out)
 if seen!=set(index):raise ValueError('Reviewed branches and input branches differ')
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--reviewed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 with a.input.open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);fields=list(r.fieldnames);rows=list(r)
 for f in EXTRA:
  if f not in fields:fields.append(f)
 result=enrich(rows,json.loads(a.reviewed.read_text(encoding='utf-8')))
 with a.output.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
 print(f'Wrote {len(result)} award rows; preserved original fields and row order.')
if __name__=='__main__':main()
