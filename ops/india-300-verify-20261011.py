#!/usr/bin/env python3
"""Verify delivered object IDs, evidence, dates, geography and local read-only parity."""
import collections,importlib.util,json
from pathlib import Path

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=module('d','india-300-delivery-20261011.py')
m=module('m','cesi-top100-20261010.py')

def run():
 phase='IN-wave1';plan,digest=d.pinned(phase);receipt=d.load(d.RUN/phase/'applied.json')
 assert receipt['plan_sha256']==digest
 rows=plan['records'];ids=[r['artwork_id'] for r in rows];newids=[r['artwork_id'] for r in rows if not r['before']]
 assert len(newids)>=300 and len(ids)==len(set(ids))
 with d.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  state=d.snapshot(db,ids)
  identifiers=list(db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)))
  citations=list(db.execute("SELECT entity_id::text,id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='india_minimum_300_museum_coverage_20261011'",(ids,)))
  institutionids=sorted({r['institution_id'] for r in rows})
  museums=list(db.execute("SELECT i.id::text,i.name,i.slug,p.country_code,p.name city,(SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived') active_artworks FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[])",(institutionids,)))
  assert len(museums)==10 and all(i['country_code']=='IN' and i['active_artworks'] for i in museums)
  assert len(state)==len(ids) and len(citations)==len(ids)
  for r in rows:
   v=state[r['artwork_id']];a=v['artwork']
   assert a['current_institution_id']==r['institution_id']
   holding=[h for h in v['holdings'] if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by']]
   assert holding and {h['institution_id'] for h in holding}=={r['institution_id']}
   assert sum(e['entity_id']==a['id'] and e['scheme']==r['scheme'] and e['external_id']==r['source_id'] for e in identifiers)==1
   assert sum(c['entity_id']==a['id'] and c['source_record_id']==r['source_id'] and c['source_url']==r['source_url'] for c in citations)==1
   if r['before']:
    assert v==r['before'],'Existing metadata, images, creator links and holdings must remain unchanged'
   else:
    assert a['status']=='review' and a['research_candidate'] and a['published_at'] is None and a['primary_media_id'] is None
    assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(r['first'],r['last'],r['precision'])
    assert a['creation_year_end'] is None or a['creation_year_end']<=1970
    assert len(v['holdings'])==1 and len(v['attachments'])==0
    assert a['accession_number']==r['accession_number']
    if r['artist_id']:assert len(v['creators'])==1 and v['creators'][0]['artist_id']==r['artist_id']
    else:assert not v['creators'] and a['unlinked_creator_label']==((r['creator_label'] or '').strip() or None)
  d.save(d.BACKUP/phase/'verified-after.json.gz',dict(at=d.now(),plan_sha256=digest,artworks=state,museums=museums))
 with m.connect(local=True) as db:
  assert db.execute('SHOW default_transaction_read_only').fetchone()['default_transaction_read_only']=='on'
  local={table:db.execute('SELECT count(*) n FROM '+table).fetchone()['n'] for table in ['artworks','institutions','artists']}
 assert local==d.load(d.RUN/'local-readonly-baseline.json')['counts']
 summary=dict(at=d.now(),target='production',plan_sha256=digest,verified_new_artworks=len(newids),verified_existing_enriched=len(ids)-len(newids),verified_total_records=len(ids),minimum_new_artworks=300,minimum_met=True,museums=museums,new_institutions=receipt['new_institutions'],new_holdings=receipt['holding_assertions'],new_citations=len(citations),new_creator_links=receipt['new_creator_links'],new_by_museum=dict(collections.Counter(r['museum'] for r in rows if not r['before'])),new_date_decisions=dict(collections.Counter(r['date_decision'] for r in rows if not r['before'])),new_work_types=dict(collections.Counter(d.worktype(r) for r in rows if not r['before'])),held=len(plan['held']),existing_metadata_images_creators_and_holdings_unchanged=True,publication_changes=0,current_display_claims=0,new_images=0,local_readonly_counts=local,local_database_unchanged=True,nationwide_artwork_coverage_complete=False)
 d.save(d.RUN/'production-verification.json',summary)
 print(json.dumps(summary),flush=True)

if __name__=='__main__':run()
