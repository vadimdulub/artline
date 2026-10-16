#!/usr/bin/env python3
"""Report this campaign's verified deliveries separately from nationwide leads."""
import collections
import csv
import importlib.util
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('switzerland-india-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

def run():
 plans=[d.load(d.RUN/phase/'plan.json.gz') for phase in ['CH-wave1','CH-wave2','CH-wave3']]
 receipts=[d.load(d.RUN/phase/'applied.json') for phase in ['CH-wave1','CH-wave2','CH-wave3']]
 directory=d.load(d.RUN/'CH/directory.json.gz')['records']
 delivered=collections.defaultdict(list);held=collections.defaultdict(list);collections_seen=collections.defaultdict(list)
 for plan in plans:
  for r in plan['records']:delivered[r['raw']['directory_id']].append(r)
  for r in plan['held']:held[r['record']['raw']['directory_id']].append(r)
 for path in (d.RUN/'CH/collection-discovery').glob('*.json.gz'):
  record=d.load(path)
  for museum in record['museums']:collections_seen[museum['directory_id']].append(record)
 ledger=[]
 for entry in directory:
  did=entry['directory_id'];detail=d.load(d.RUN/'CH/directory-details'/(did+'.json.gz'))
  native=d.load(d.RUN/'CH/native-sites'/(did+'.json.gz'))
  works=delivered[did];pages=collections_seen[did]
  ledger.append(dict(directory_id=did,name=entry['name'],locality=entry['locality'],primary_category=entry['primary_category'],art_tagged='57' in entry['category_ids'],directory_url=entry['directory_url'],directory_identity_checked=detail.get('evidence',{}).get('status')==200,native_url=native.get('website'),native_result=native['result'],native_error=native.get('error'),collection_pages_captured=sum(bool(p.get('evidence',{}).get('status')==200) for p in pages),collection_urls=' | '.join(p['url'] for p in pages),country_status='CH individually verified with production city link' if works else 'Directory lead; individual country and venue reconciliation pending',production_artwork_ids=' | '.join(r['artwork_id'] for r in works),new_artworks=sum(not r['before'] for r in works),existing_artworks_enriched=sum(bool(r['before']) for r in works),held_object_candidates=len(held[did]),held_reasons=' | '.join(r['reason'] for r in held[did]),remaining_gap='Broader object and image coverage pending' if works else 'No object delivered in this campaign; eligible source objects and institution identity still require review'))
 out=d.RUN/'CH/directory-delivery-ledger.csv'
 with out.open('w',newline='') as handle:
  writer=csv.DictWriter(handle,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(ledger)
 totals=dict(at=d.now(),sequence=['Switzerland','Argentina','Uruguay','Paraguay'],india='deferred following explicit user clarification',directory_entries=len(directory),directory_identities_checked=sum(r['directory_identity_checked'] for r in ledger),art_tagged_entries=sum(r['art_tagged'] for r in ledger),native_outcomes=dict(collections.Counter(r['native_result'] for r in ledger)),collection_urls=len({p['url'] for pp in collections_seen.values() for p in pp}),museums_with_campaign_delivery=sum(bool(r['production_artwork_ids']) for r in ledger),new_artworks=sum(r['new_artworks'] for r in receipts),existing_enriched=sum(r['existing_records_enriched'] for r in receipts),new_institutions=sum(r['new_institutions'] for r in receipts),new_holdings=sum(r['holding_assertions'] for r in receipts),new_citations=sum(r['source_citations'] for r in receipts),new_primary_images=1,held_object_candidates=sum(len(q['held']) for q in plans),coverage_complete=False,remaining_scope='Nationwide institution research is indexed; complete artwork coverage is not established. Directory includes neighbouring-country leads and multiple venues. Argentina, Uruguay and Paraguay production coverage remains in continuation work.',local_database_changes=0)
 d.save(d.RUN/'CH-breadth-summary.json',totals)
 d.save(d.RUN/'sequence-confirmation.json',dict(at=d.now(),user_answer='Argentina, then Uruguay and Paraguay',sequence=totals['sequence'],strategy='Broad coverage first, then deepen',supersedes='India as next country',research_preserved=True))
 print(totals,flush=True)

if __name__=='__main__':run()
