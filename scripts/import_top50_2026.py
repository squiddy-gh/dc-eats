"""Build the 2026 NoVA Top 50 CSV, preserving the separate 2025 edition."""
import csv, json, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["restaurant_name","position","category","cuisine","price","eat_this","address","latitude","longitude","website","phone","business_status","monday_hours","tuesday_hours","wednesday_hours","thursday_hours","friday_hours","saturday_hours","sunday_hours","hours_type","hours_notes","narrative","narrative_type","narrative_source_url","source_url","details_source_url","hours_source_url","hours_checked_on","coordinates_source_url","coordinates_matched_address","data_notes"]

def load(path):
    rows=json.loads(path.read_text(encoding="utf-8"))
    if len({r["restaurant_name"] for r in rows}) != 50:
        raise ValueError("Expected exactly 50 restaurant selections.")
    if [r["position"] for r in rows if r["position"]] != [f"No. {i}" for i in range(1,11)]:
        raise ValueError("Expected published ranks No. 1 through No. 10.")
    for row in rows:
        if not all(row.get(k) for k in ["restaurant_name","address","latitude","longitude","cuisine","eat_this","source_url"]):
            raise ValueError(f"Missing required map field for {row.get('restaurant_name')}.")
        if not (38 < float(row["latitude"]) < 40 and -79 < float(row["longitude"]) < -76):
            raise ValueError(f"Out-of-region coordinates for {row['restaurant_name']}.")
        for key,value in row.items(): row[key]=unicodedata.normalize("NFC",str(value))
    return rows

if __name__ == "__main__":
    reviewed=ROOT/"docs/top50_2026_reviewed.json"; output=ROOT/"data/northernvamag_50_best_restaurants_2026.csv"
    rows=load(reviewed)
    with output.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,quoting=csv.QUOTE_ALL); writer.writeheader(); writer.writerows(rows)
    print(f"Saved {len(rows)} locations covering 50 selections to {output}")
