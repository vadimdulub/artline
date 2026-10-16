#!/usr/bin/env python3
"""Record national directory leads separately from verified artwork deliveries."""
import collections,csv,importlib.util
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('india-300-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

def run():
 plan,_=d.pinned('IN-wave1');summary=d.load(d.RUN/'production-verification.json')
 directory=d.load(d.RUN/'national-directory.json.gz')
 cross={v['record']['id']:v['code'] for v in d.load(d.RUN/'portal-directory-crosswalk.json')}
 selected=collections.defaultdict(list);held=collections.defaultdict(list)
 for r in plan['records']:selected[r['raw']['portal_museum_code']].append(r)
 for h in plan['held']:held[h['record']['raw']['portal_museum_code']].append(h)
 ledger=[]
 for entry in directory['records']:
  code=cross.get(entry['id']);works=selected[code];holds=held[code]
  ledger.append(dict(directory_id=entry['id'],name=entry['name'],city=entry['city'],state=entry['stateUt'],category=entry['museumType'],native_portal_code=code or '',native_profile_captured=bool(code),new_artworks=sum(not r['before'] for r in works),existing_artworks_enriched=sum(bool(r['before']) for r in works),production_artwork_ids=' | '.join(r['artwork_id'] for r in works),held_candidates=len(holds),held_reasons=' | '.join(sorted({h['reason'] for h in holds})),remaining_gap='More eligible object metadata and authentic images remain to be researched' if works else ('Photographic physical-object dates/versions unresolved; no records added' if code=='avm_pun' else 'Directory lead only; institution identity, eligible objects and source availability not yet individually researched')))
 assert len(ledger)==1192 and len({r['directory_id'] for r in ledger})==1192
 assert sum(r['new_artworks'] for r in ledger)==summary['verified_new_artworks']==350
 path=d.RUN/'national-directory-delivery-ledger.csv'
 assert not path.exists()
 with path.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(ledger)
 d.save(d.RUN/'coverage-summary.json',dict(at=d.now(),directory_entries=len(ledger),native_collection_profiles_captured=sum(r['native_profile_captured'] for r in ledger),museums_with_delivery=sum(bool(r['production_artwork_ids']) for r in ledger),new_artworks=350,existing_enriched=9,object_sources_captured=432,held=73,national_coverage_complete=False,images_attached=0,scope='Minimum 300 new Indian museum artworks achieved; broader India museum/artwork/image coverage remains open'))
 print('Directory ledger saved:',len(ledger),'entries; 10 delivered collections, 350 new artworks',flush=True)

if __name__=='__main__':run()
