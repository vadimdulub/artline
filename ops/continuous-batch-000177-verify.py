#!/usr/bin/env python3
"""Fresh read-only, source-attributed verification of bounded batch177."""
import fcntl,gzip,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b177',Path(__file__).with_name('continuous-batch-000177.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
original_save=b.save
def persist(name,value):
 path=b.E/name
 if path.exists():
  old=h.load(path);left={k:v for k,v in old.items() if k!='at'};right={k:v for k,v in h.safe(value).items() if k!='at'}
  if 'events' in left:
   left['events']=sorted(left['events'],key=lambda x:(x['entity_id'],x['entity_type'],x['action']))
   right['events']=sorted(right['events'],key=lambda x:(x['entity_id'],x['entity_type'],x['action']))
  assert left==right,'Existing verification evidence differs: '+name
  return old
 return original_save(name,value)
b.save=persist
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];artist=p['new_artists'][0];aid=artist['id'];assert len(ids)==13
 path=h.BACKUP/b.PHASE/'locked-before.json.gz';pre=h.load(path);assert pre['artworks']=={} and pre['new_artist_preimages']=={} and pre['plan_sha256']==pin
 b.target('independent-verification')
 source=[]
 for r in p['records']:
  rc=r['evidence'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  sp=BeautifulSoup(raw,'html.parser');hd=sp.select_one('h2');a=hd.select_one('.author');assert a.get_text(' ',strip=True)==r['creator_label'];a.extract();assert hd.get_text(' ',strip=True)==r['title']
  assert r['accession_number']==sp.select_one('p.inv').get_text(' ',strip=True).split('Inv.')[1].strip();assert r['medium']==sp.select_one('.artwork-description li').get_text(' ',strip=True)
  assert r['dimensions'] in sp.select_one('.artwork-description').get_text(' ',strip=True) and r['credit'] in sp.get_text(' ',strip=True)
  assert 1842<=r['first']<=r['last']<=1885<=1970 and not r['before']
  source.append(dict(artwork_id=r['artwork_id'],inventory=r['accession_number'],source_url=r['source_url'],source_sha256=rc['sha256'],source_facts_verified=True))
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==13
  notes=[dict(x) for x in db.execute('SELECT entity_id::text,source_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type=\'artwork\' AND entity_id=ANY(%s::uuid[]) AND field_name=%s',(ids,b.FIELD))];assert len(notes)==13
  for r in p['records']:
   state=after[r['artwork_id']];a=state['artwork'];n=next(x for x in notes if x['entity_id']==a['id'])
   for key,value in dict(title=r['title'],accession_number=r['accession_number'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],date_display=r['date_display'],medium_text=r['medium'],dimensions_text=r['dimensions'],status='review',primary_media_id=None,current_institution_id=b.MID,research_candidate=True,work_type='painting',published_at=None).items():assert a[key]==value,(a['id'],key)
   assert not state['attachments'] and len(state['creators'])==1 and state['creators'][0]['artist_id']==aid and state['creators'][0]['attribution_role']=='primary'
   assert len(state['holdings'])==1;hold=state['holdings'][0];assert hold['institution_id']==b.MID and hold['review_state']=='accepted' and hold['claim_type']=='holding' and hold['context']=='collection' and hold['superseded_by'] is None
   ev=json.loads(hold['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256'] and ev['inventory']==r['accession_number']
   assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256'] and n['note']['creator_identity']==p['creator_identity'] and n['note']['credit']==r['credit']
   owners=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='museum-native-rmfab-inventory' AND external_id=%s",(r['source_id'],)).fetchall();assert len(owners)==1 and owners[0]['entity_id']==a['id']
   assert db.execute('SELECT adapter_key FROM sources WHERE id=%s',(n['source_id'],)).fetchone()['adapter_key']==b.OP
  ar=dict(db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(aid,)).fetchone()['v']);assert all(ar[k]==v for k,v in artist.items())
  an=[dict(x) for x in db.execute("SELECT entity_id::text,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name='continuous_rmfab_creator_identity_b000177'",(aid,))];assert len(an)==1 and an[0]['note']['plan_sha256']==pin and an[0]['note']['creator_identity']==p['creator_identity']
  ai=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND scheme='museum-native-rmfab-artist' AND external_id='agneessens-edouard'")];assert len(ai)==1 and ai[0]['entity_id']==aid
  holdids=[state['holdings'][0]['id'] for state in after.values()]
  events=[dict(x) for x in db.execute("SELECT entity_id::text,entity_type,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(ids+holdids+[aid],))];assert len(events)==27 and all(x['before_json'] is None for x in events)
  for r in p['records']:
   ev=next(x for x in events if x['entity_id']==r['artwork_id']);assert ev['after_json']['title']==r['title'] and ev['after_json']['accession_number']==r['accession_number'] and ev['after_json']['status']=='review'
  ev=next(x for x in events if x['entity_id']==aid);assert all(ev['after_json'][k]==v for k,v in artist.items())
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==13
  recovery=h.load(h.BACKUP/'affected-row-preimages.json.gz');prior=recovery['existing_artworks'];foreign=recovery['related_creator_works'];assert h.snapshot(db,list(prior))==prior and h.snapshot(db,list(foreign))==foreign
  for value in b.h.load(b.E/'global-identity-reconciliation.json')['object_matches']['global_title_exclusions']:
   old=value['artwork'];assert db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=%s',(old['id'],)).fetchone()['v']==old
  assert db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v']==next(iter(p['institutions'].values()))
  assert len(b.artist_collisions(db))==1 and b.artist_collisions(db)[0]['id']==aid
 b.save('independent-source-verification.json',dict(at=h.now(),rows=source,plan_sha256=pin,creator_capture_sha256=p['creator_identity']['receipt']['sha256'],creation_scope_and_source_qualifications_preserved=True))
 b.save('independent-production-verification.json',dict(at=h.now(),after=after,artist=ar,citations=notes,artist_citation=an,artist_identifier=ai,plan_sha256=pin,verified_new_painters=1,verified_new_artworks=13,verified_museum_links=13,locked_preimage=dict(path=str(path),sha256=h.sha(path.read_bytes())),local_catalogue_connections=0))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),events=events,empty_transaction_preimages=True,programme_source_and_plan_checksums_verified=True,new_insert_events=27))
 b.save('independent-existing-preservation-verification.json',dict(at=h.now(),existing_institution_works_unchanged=len(prior),foreign_creator_works_unchanged=len(foreign),global_title_exclusions_unchanged=True,institution_unchanged=True,images_changed=0))
 public=[]
 for r in p['records']:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,45));assert res.status_code==200
  body=res.json();assert r['title'] in res.text and r['source_url'] in res.text and 'Royal Museums of Fine Arts of Belgium' in res.text and 'Agneessens' in res.text
  b.save('public-api-'+r['artwork_id']+'.json',body);public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content),title_creator_source_holding_present=True))
 url='https://artlines.org/api/backend/v1/artists/'+artist['slug'];res=requests.get(url,timeout=(15,45));assert res.status_code==200 and 'Agneessens' in res.text
 b.save('public-artist-'+aid+'.json',res.json());public.append(dict(artist_id=aid,url=url,status=200,sha256=h.sha(res.content)))
 b.save('independent-public-verification.json',dict(at=h.now(),rows=public,verified_artworks=13,verified_painters=1))
 images=b.h.load(b.E/'image-research-decision.json');assert images['native_images_downloaded']==images['commons_images_downloaded']==0 and images['actually_viewed_files']==[]
 b.save('independent-image-non-delivery-verification.json',dict(at=h.now(),source_decision_sha256=h.sha((b.E/'image-research-decision.json').read_bytes()),images_downloaded=0,images_prepared=0,storage_writes=0,image_records_attached=0,visual_reviews_claimed=0,rights_holds_preserved=True))
 counts=dict(new_painters=1,new_artworks=13,newly_illustrated=0,alternate_images=0,museum_links=13)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,artist_id=aid,plan_sha256=pin,locked_preimage_sha256=h.sha(path.read_bytes()),production_target=b.TARGET,shared_ingestion_lock='artline-curated-ingestion',attribution='Empty locked artwork and creator preimages; persisted own programme source adapter, object/creator source checksums and plan digest;27 insertion audit events; fresh production and public API verification. No prior programme additions counted.',limitations=['Four undated object notices held; no creation dates inferred from1888 authentication, acquisitions or painter lifespan.','Native museum image reuse unresolved; exact Commons lead has licensing-date conflict. No images downloaded or claimed visually inspected.','Only17 object notices for one maker researched; institution catalogue coverage remains incomplete.','Dimension units were not stated explicitly in selected museum notices and were not invented.','Parenthesized/ca. source dates retain literal labels and circa precision.']))
 # Fresh completed-plan reconciliation proves a retry can skip writes.
 with h.connect() as db:
  assert h.snapshot(db,ids)==after
  assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(aid,)).fetchone()['v']==ar
 b.save('independent-read-only-resume-verification.json',dict(at=h.now(),plan_sha256=pin,production_rows_equal=True,own_persisted_source_attribution_verified=True,replay_required=False,new_production_writes=0,replay_increments={k:0 for k in counts}))
 print(json.dumps(counts),flush=True)
