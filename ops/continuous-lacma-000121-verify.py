"""Independent batch verification and narrowly scoped queue checkpoint."""
import runpy,json,fcntl,datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
v=runpy.run_path('ops/continuous-lacma-000121-delivery.py');globals().update({k:v[k] for k in ['h','b','E','R','ROOT','save','PHASE','FIELD']})
p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
prepath=h.BACKUP/PHASE/'locked-before.json.gz';pre=h.load(prepath);assert pre['artworks']=={} and pre['plan_sha256']==pin
source=[]
for r in p['records']:
 raw=(ROOT/r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256']
 t=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 assert all(x in t for x in [r['title'],r['creator_label'],r['date_display'],r['accession_number'],r['medium'],r['dimensions'],r['credit']])
 assert r['first']<=r['last']<=1970 and not r['before']
 source.append(dict(artwork_id=r['artwork_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],native_id=r['source_id'],accession=r['accession_number'],passed=True))
save('independent-source-verification.json',dict(at=h.now(),records=source,plan_sha256=pin))
with h.connect() as db:
 after=h.snapshot(db,ids);assert len(after)==4
 notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD))];assert len(notes)==4
 for r in p['records']:
  state=after[r['artwork_id']];a=state['artwork'];n=next(x for x in notes if x['entity_id']==a['id'])
  assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['medium_text'],a['dimensions_text'],a['date_precision'])==(r['title'],r['accession_number'],r['first'],r['last'],r['medium'],r['dimensions'],r['precision'])
  assert a['status']=='review' and a['primary_media_id'] is None and a['current_institution_id']==r['institution_id'] and not state['attachments']
  assert state['creators']==[] and a['unlinked_creator_label']==r['creator_label']
  assert len(state['holdings'])==1 and state['holdings'][0]['review_state']=='accepted' and state['holdings'][0]['claim_type']=='holding'
  ev=json.loads(state['holdings'][0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
  assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256']
  assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
  assert db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme='museum-native-lacma' AND external_id=%s",(r['source_id'],)).fetchone()['entity_id']==a['id']
 holds=[v['holdings'][0]['id'] for v in after.values()]
 events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(ids+holds,))]
 assert len(events)==8 and all(x['before_json'] is None for x in events)
 for aid,old in pre['artists'].items():assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(aid,)).fetchone()['v']==old
 prior=h.load(E/'global-related-work-reconciliation.json')['states'];assert h.snapshot(db,list(prior))==prior
 assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==4
save('independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,after=after,citations=notes,transaction_preimages=dict(path=str(prepath),sha256=h.sha(prepath.read_bytes())),verified_new_artworks=4,verified_museum_links=4,existing_artists_and_candidate_works_unchanged=True,images_changed=0))
save('independent-audit-history-verification.json',dict(at=h.now(),events=events,empty_transaction_preimages=True,programme_source_and_plan_checksums_verified=True))
public=[]
for r in p['records']:
 url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=40);assert res.status_code==200
 assert r['title'] in res.text and r['source_url'] in res.text and 'Los Angeles County Museum of Art' in res.text
 save('public-api-'+r['artwork_id']+'.json',res.json());public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content)))
save('independent-public-verification.json',dict(at=h.now(),records=public))
