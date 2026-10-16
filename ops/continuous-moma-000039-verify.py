#!/usr/bin/env python3
"""Source reparse and independent production, attribution, audit and public checks."""
import csv,gzip,importlib.util,json,re,sys
import requests
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-moma-batch-000039.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E

def source():
 plan,pin=h.pinned(b.PHASE);records=[];d=h.load(E/'source-dataset-verification.json');assert 1<=len(plan['records'])<=50 and not plan['new_institutions']
 for name,rc in d['receipts'].items():assert h.sha(Path(rc['path']).read_bytes())==rc['sha256'] and rc['status']==200
 with Path(d['receipts']['Artworks.csv']['path']).open(encoding='utf-8-sig',newline='') as f:allrows=list(csv.DictReader(f))
 originals={r['ObjectID']:r for r in allrows};assert len(originals)==len(allrows)
 with Path(d['receipts']['Artists-full.csv']['path']).open(encoding='utf-8-sig',newline='') as f:ar={r['ConstituentID']:r for r in csv.DictReader(f)}
 acccounts={r['accession_number']:sum(o['AccessionNumber']==r['accession_number'] for o in allrows) for r in plan['records']}
 for r in plan['records']:
  oid=r['source_id'];o=originals[oid];assert r['raw']==o and h.load(Path(r['evidence_file']))==o
  assert h.sha(Path(r['evidence_file']).read_bytes())==r['evidence']['sha256']
  assert r['evidence']['dataset_sha256']==d['receipts']['Artworks.csv']['sha256'] and r['evidence']['artist_dataset_sha256']==d['receipts']['Artists-full.csv']['sha256']
  assert r['source_url']==(o['URL'] or d['receipts']['Artworks.csv']['url'])
  if o['URL']:assert o['URL']=='https://www.moma.org/collection/works/'+oid
  else:assert o['Cataloged']=='N' and 'Public URL is empty' in r['source_notes']
  assert acccounts[r['accession_number']]==1 and re.fullmatch(r'\d+\.\d{4}',r['accession_number']) and not r['before']
  assert not any(re.match('^'+re.escape(r['accession_number'])+r'[.a-zA-Z,;/\-]',x['AccessionNumber']) for x in allrows)
  date=o['Date'].strip().strip('()');month=r'(January|February|March|April|May|June|July|August|September|October|November|December)'
  match=re.fullmatch(month+r'\s+(?:\d{1,2},?\s+)?((?:18|19)\d{2})',date);assert match
  year=int(match[2]);assert r['first']==r['last']==year<=1970 and r['precision']=='exact'
  assert (r['title'],r['accession_number'],r['date_display'],r['medium'],r['dimensions'],r['creator_label'])==(o['Title'],o['AccessionNumber'],o['Date'],o['Medium'],o['Dimensions'],o['Artist'])
  assert o['Classification']=='Drawing' and r['source_type']=='drawing' and r['holding_confidence']>=.8
  authority=r['creator_authority']['native_authority'];assert ar[o['ConstituentID']]==authority and authority['DisplayName']==o['Artist']
  reconciliation=next(x for x in h.load(E/'global-identity-reconciliation.json')['records'] if x['native_id']==oid);assert reconciliation['decision']=='selected' and r['artist_id']==reconciliation['artist_id']
  if r['artist_id']:
   artist=plan['artists'][r['artist_id']];assert h.norm(artist['display_name'])==h.norm(o['Artist']) or any(x['id']==r['artist_id'] for x in reconciliation['artist_matches'])
   assert (not artist['birth_year'] or artist['birth_year']<=year) and (not artist['death_year'] or year<=artist['death_year'])
  records.append(dict(artwork_id=r['artwork_id'],source_id=oid,source_sha256=r['evidence']['sha256'],accession_number=r['accession_number'],date_display=r['date_display'],year=year,artist_id=r['artist_id'],creator_label=r['creator_label'],same_native_creator=True,simple_standalone_inventory=True))
 h.save(E/'independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,official_csv_rows_reparsed=True,source_object_and_artist_hashes_verified=True,no_images_requested=True,no_current_display_assertions=True))
 h.save(E/'actual-visual-review.json',dict(at=h.now(),prepared_images=0,actually_viewed_images=[],status='not_applicable_metadata_only',reason='Official MoMA dataset excludes images; registry image restriction retained. No visual review claimed.'))
 print('SOURCE VERIFIED',len(records),flush=True)

def production():
 plan,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in plan['records']];lockedpath=h.BACKUP/b.PHASE/'locked-before.json.gz';locked=h.load(lockedpath);assert locked['artworks']=={} and locked['plan_sha256']==pin
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  after=h.snapshot(db,ids);assert len(after)==len(ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256,evidence_note::jsonb->'evidence'->>'sha256' source_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(citations)==len(ids) and all(x['plan_sha256']==pin for x in citations)
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(events)==len(ids) and {x['entity_id'] for x in events}==set(ids) and all(x['before_json'] is None for x in events)
  holdings=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='location_assertion' AND entity_id=ANY(%s::uuid[])",([h.uid('holding/'+r['key']) for r in plan['records']],))]
  artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(plan['artists']),))};assert artists==locked['artists']==plan['artists']
  for r in plan['records']:
   state=after[r['artwork_id']];a=state['artwork'];assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None and a['research_candidate']
   assert (a['title'],a['accession_number'],a['date_display'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['dimensions_text'],a['medium_text'])==(r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'])
   assert a['current_institution_id']==r['institution_id'] and not state['attachments']
   assert a['unlinked_creator_label']==(None if r['artist_id'] else r['creator_label'])
   assert len(state['creators'])==(1 if r['artist_id'] else 0)
   if r['artist_id']:assert state['creators'][0]['artist_id']==r['artist_id'] and state['creators'][0]['attribution_role']=='primary'
   hs=state['holdings'];assert len(hs)==1 and hs[0]['claim_type']=='holding' and hs[0]['review_state']=='accepted' and hs[0]['institution_id']==r['institution_id'] and not hs[0]['superseded_by']
   ev=json.loads(hs[0]['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
   native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='moma-object' AND external_id=%s",(r['source_id'],)).fetchall();assert len(native)==1 and native[0]['entity_id']==r['artwork_id']
   inv=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(r['institution_id'],r['accession_number'])).fetchall();assert len(inv)==1 and inv[0]['id']==r['artwork_id']
   cit=next(x for x in citations if x['entity_id']==r['artwork_id']);assert cit['source_record_id']==r['source_id'] and cit['source_sha256']==r['evidence']['sha256']
   audit=next(x for x in events if x['entity_id']==r['artwork_id']);assert audit['after_json']['slug']==a['slug']
  scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
 h.save(E/'independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,transaction_preimages=str(lockedpath),transaction_preimages_sha256=h.sha(lockedpath.read_bytes()),empty_locked_preimages_verified=True,rows=after,citations=citations,creation_scope=scope,new_review_artworks=len(ids),accepted_holdings=len(ids),creator_links_verified=sum(bool(r['artist_id']) for r in plan['records']),unchanged_existing_creators=len(artists),local_database_connections=0))
 h.save(E/'independent-audit-history-verification.json',dict(at=h.now(),artwork_insert_events=events,holding_events=holdings,attribution='Empty locked preimages and exact programme plan/source checksums in live citations, unique insert audit rows. Previous campaigns and replayed receipts excluded.'))
 publics=[]
 for aid in ids:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;rr=requests.get(url,timeout=(15,45));rr.raise_for_status();obj=rr.json();assert obj['id']==aid and obj['title']==after[aid]['artwork']['title']
  p=b.D/'public-api'/(aid+'.json');h.save(p,obj);publics.append(dict(artwork_id=aid,url=url,status=rr.status_code,response_sha256=h.sha(rr.content),capture_path=str(p),capture_sha256=h.sha(p.read_bytes())))
 h.save(E/'independent-public-verification.json',dict(at=h.now(),rows=publics,unified_catalogue_visibility_verified=True))
 h.save(E/'independent-no-image-changes-verification.json',dict(at=h.now(),production_ids=ids,primary_media_all_null=True,attachments_all_empty=True,image_writes=0,images_viewed=0,moma_image_restriction_preserved=True))
 counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
 h.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,production_target=b.base.target(),attribution='Pinned official source data, empty transaction preimages, exact live programme citations, source checksum matches, insert audits, accepted holdings and public API verified independently.'))
 print(json.dumps(counts),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
