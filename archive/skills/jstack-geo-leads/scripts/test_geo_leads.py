#!/usr/bin/env python3
import csv,json,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]; script=root/"scripts"/"geo_leads.py"; ref=root/"references"
with tempfile.TemporaryDirectory() as d:
  d=Path(d); prepared=d/"input.json"
  subprocess.run([sys.executable,str(script),"prepare","--markets",str(ref/"markets-fixture.json"),"--output",str(prepared),"--max-total-charge-usd","0.5","--remaining-included-credit-usd","0.5"],check=True)
  payload=json.loads(prepared.read_text()); assert payload["searchStringsArray"]==["hotel in Mudgee NSW","boutique hotel in Mudgee NSW","resort in Mudgee NSW","hotel in Yallingup WA","boutique hotel in Yallingup WA","resort in Yallingup WA","lodge in Yallingup WA"]; assert payload["maxReviews"]==payload["maxImages"]==0 and not payload["scrapeContacts"] and not payload["scrapePlaceDetailPage"]
  output=d/"prefilter"; subprocess.run([sys.executable,str(script),"prefilter","--input",str(ref/"dataset-fixture.json"),"--lineage",str(ref/"lineage-fixture.json"),"--output-dir",str(output)],check=True)
  summary=json.loads((output/"prefilter-summary.json").read_text()); assert summary["raw_records"]==6 and summary["deduped_records"]==5; assert summary["outcome_counts"]=={"retain_for_manual_qualification":1,"excluded_chain_or_franchise":1,"excluded_closed":1,"excluded_obvious_single_unit_stay":1,"excluded_missing_website":1}
  first=list(csv.DictReader((output/"all-deduped-records.csv").open()))[0]; assert first["source_indexes"]=="0;1" and first["source_queries"]=="hotel in Yallingup WA | boutique hotel in Yallingup WA" and first["actor_id"]=="nwua9Gu5YrADL7ZDj" and first["run_id"]=="run-fixture"
print("PASS: capped input and lineage-preserving prefilter outputs verified")
