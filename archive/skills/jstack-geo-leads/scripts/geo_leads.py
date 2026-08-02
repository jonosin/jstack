#!/usr/bin/env python3
"""Prepare capped Apify Maps input and lineage-preserving map-level prefilter outputs."""
import argparse, csv, json, re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ACTOR = "compass/crawler-google-places"; ACTOR_ID = "nwua9Gu5YrADL7ZDj"
FAMILIES = ("hotel", "boutique hotel", "resort"); OPTIONAL = {"lodge", "retreat"}
CHAIN = re.compile(r"\b(accor|adagio|best western|big4|club wyndham|comfort inn|crowne plaza|discovery parks|four points|holiday inn|ihg|intercontinental|lancemore|mantra|marriott|mercure|mgallery|novotel|oaks|peppers|pullman|quest apartments|ramada|racv|rydges|sofitel|tasman holiday parks|travelodge|voco|wyndham)\b", re.I)
CHAIN_DOMAINS = ("accor.com", "bestwestern.com", "big4.com.au", "discoveryholidayparks.com.au", "ihg.com", "lancemore.com.au", "mantrahotels.com", "marriott.com", "oakshotels.com", "peppers.com.au", "racv.com.au", "ramada.com", "rydges.com", "tasmanholidayparks.com", "travelodge.com.au", "wyndhamhotels.com")
IRRELEVANT = {"bar", "bistro", "cabin rental agency", "cafe", "culinary school", "day spa", "golf club", "pub", "restaurant", "spa", "travel agency", "winery"}; SINGLE = re.compile(r"\b(cottage|holiday home|tiny house|tiny home|villa)\b", re.I)
FIELDS = ("prefilter_outcome", "prefilter_rule", "property", "website", "website_domain", "locality", "address", "category", "google_place_id", "google_cid", "google_maps_url", "source_query", "source_queries", "scraped_at", "source_dataset", "source_indexes", "duplicate_source_indexes", "dedupe_key", "raw_record_count", "actor_id", "actor", "run_id", "dataset_id", "run_status", "actual_cost_usd", "website_status", "direct_booking_or_enquiry_status", "room_count_status", "business_qualification_status", "geo_pain_status")
def norm(v): return re.sub(r"[^a-z0-9]+", " ", (v or "").lower()).strip()
def domain(v): return urlparse(v if "://" in (v or "") else f"https://{v}").netloc.lower().removeprefix("www.")
def key(r):
    if r.get("placeId"): return f"place_id:{r['placeId'].strip()}"
    if r.get("cid"): return f"cid:{str(r['cid']).strip()}"
    if domain(r.get("website") or ""): return f"domain:{domain(r['website'])}"
    return f"name_locality:{norm(r.get('title'))}|{norm(r.get('city') or r.get('address'))}"
def classify(r):
    title, cat, web = r.get("title") or "", norm(r.get("categoryName")), domain(r.get("website") or "")
    if r.get("permanentlyClosed") or r.get("temporarilyClosed"): return "excluded_closed", "closed_flag"
    if not r.get("website"): return "excluded_missing_website", "website_blank"
    if CHAIN.search(title) or any(web == x or web.endswith(f".{x}") for x in CHAIN_DOMAINS): return "excluded_chain_or_franchise", "chain_name_or_domain"
    if cat in IRRELEVANT: return "excluded_irrelevant", f"category:{cat}"
    if SINGLE.search(title) or cat in {"cottage", "villa"}: return "excluded_obvious_single_unit_stay", "single_unit_name_or_category"
    return "retain_for_manual_qualification", "no_map_level_exclusion"
def prepare(a):
    markets = json.loads(a.markets.read_text())
    if not isinstance(markets, list) or not markets or len(markets) > 10: raise SystemExit("markets must be a non-empty JSON array of at most 10 approved markets")
    if a.max_total_charge_usd <= 0 or a.max_total_charge_usd > a.remaining_included_credit_usd: raise SystemExit("maxTotalChargeUsd must be positive and no greater than remaining included credit")
    queries=[]
    for item in markets:
        market=item.get("market", "").strip() if isinstance(item,dict) else ""; extras=item.get("extra_query_families",[]) if isinstance(item,dict) else []
        if not market or not isinstance(extras,list) or any(x not in OPTIONAL for x in extras): raise SystemExit("each market needs market and optional lodge/retreat extra_query_families")
        for family in (*FAMILIES,*extras):
            q=f"{family} in {market}"
            if q not in queries: queries.append(q)
    payload={"searchStringsArray":queries,"maxCrawledPlacesPerSearch":a.max_crawled_places_per_search,"maxReviews":0,"maxImages":0,"scrapeContacts":False,"scrapeImageAuthors":False,"scrapePlaceDetailPage":False,"scrapeReviewsPersonalData":False,"skipClosedPlaces":True}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2)+"\n"); print(json.dumps({"actor":ACTOR,"actor_id":ACTOR_ID,"query_count":len(queries),"max_total_charge_usd":a.max_total_charge_usd,"input":str(a.output)},indent=2))
def prefilter(a):
    records=json.loads(a.input.read_text()); lineage=json.loads(a.lineage.read_text())
    if not isinstance(records,list): raise SystemExit("input must be a JSON array of dataset items")
    groups={}
    for i,r in enumerate(records): groups.setdefault(key(r),[]).append(i)
    rows=[]
    for k,indexes in groups.items():
        r=records[indexes[0]]; outcome,rule=classify(r); queries=list(dict.fromkeys(records[i].get("searchString") or "" for i in indexes if records[i].get("searchString")))
        rows.append(dict(zip(FIELDS,(outcome,rule,r.get("title") or "",r.get("website") or "",domain(r.get("website") or ""),r.get("city") or "",r.get("address") or "",r.get("categoryName") or "",r.get("placeId") or "",str(r.get("cid") or ""),r.get("url") or "",r.get("searchString") or ""," | ".join(queries),r.get("scrapedAt") or "",str(a.input),";".join(map(str,indexes)),";".join(map(str,indexes[1:])),k,str(len(indexes)),lineage.get("actor_id", ""),lineage.get("actor", ""),lineage.get("run_id", ""),lineage.get("dataset_id", ""),lineage.get("status", ""),str(lineage.get("actual_cost_usd", "")),"not_checked","not_checked","not_checked","not_checked","not_checked"))))
    rows.sort(key=lambda x:int(x["source_indexes"].split(";",1)[0])); a.output_dir.mkdir(parents=True,exist_ok=True)
    for name, subset in (("all-deduped-records.csv",rows),("candidates-for-manual-qualification.csv",[r for r in rows if r["prefilter_outcome"]=="retain_for_manual_qualification"]),("excluded-at-map-prefilter.csv",[r for r in rows if r["prefilter_outcome"]!="retain_for_manual_qualification"])):
        with (a.output_dir/name).open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(subset)
    summary={"source_dataset":str(a.input),"lineage":{x:lineage.get(x) for x in ("actor","actor_id","run_id","dataset_id","status")},"raw_records":len(records),"deduped_records":len(rows),"duplicate_raw_records_collapsed":len(records)-len(rows),"outcome_counts":dict(Counter(r["prefilter_outcome"] for r in rows)),"lineage_note":"Displayed fields use first raw occurrence; source indexes and queries retain duplicates."}
    (a.output_dir/"prefilter-summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(json.dumps(summary,indent=2))
def main():
    p=argparse.ArgumentParser(); subs=p.add_subparsers(dest="command",required=True)
    x=subs.add_parser("prepare"); x.add_argument("--markets",type=Path,required=True); x.add_argument("--output",type=Path,required=True); x.add_argument("--max-crawled-places-per-search",type=int,default=12); x.add_argument("--max-total-charge-usd",type=float,required=True); x.add_argument("--remaining-included-credit-usd",type=float,required=True)
    y=subs.add_parser("prefilter"); y.add_argument("--input",type=Path,required=True); y.add_argument("--lineage",type=Path,required=True); y.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args(); (prepare if a.command=="prepare" else prefilter)(a)
if __name__=="__main__": main()
