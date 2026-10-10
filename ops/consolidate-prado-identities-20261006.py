#!/usr/bin/env python3
"""Consolidate two source-proven duplicate authorities without deleting records."""
import argparse, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('prado',ROOT/'ops/expand-prado-catalogue-20261006.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r
RUN=m.RUN/'duplicate-consolidation';BACKUP=m.BACKUP/'duplicate-consolidation'
PAIRS=[
 {'canonical':'06b0c9ef-9eef-5500-bccd-936d78c3b88d','duplicate':'d27fb2f2-5a8b-5761-ab89-f8567824fef4','accession':'P002046','native':'692c695b-db26-4586-90e7-7d5dcfd468f7','equivalent_qid':'Q59771009','old_qid':'Q106984304','basis':'Commons Meiren-jacob-prado.jpg explicitly links Q106984304 to museum image P02046.jpg. Same maker Q16580735 and 43 × 51 cm panel/canvas dimensions as Prado P002046, native 692c695b-db26-4586-90e7-7d5dcfd468f7 / Q59771009. Source date disagreement (1685 versus circa 1700) retained; exact inventory establishes identity.'},
 {'canonical':'99df111f-3a75-5aa2-bd88-6cde830a492a','duplicate':'31ed0e0c-1ba2-5488-97d9-db859f78b1d6','accession':'P006808','native':'e26fe741-6063-413d-99b8-4cdb8914ff38','equivalent_qid':'Q59859661','old_qid':'Q110498012','basis':'Commons Arando la tierra (Asturias), por Ventura Álvarez.jpg explicitly links Q110498012 to museum native e26fe741-6063-413d-99b8-4cdb8914ff38. Same creator Q17600410, date 1910, and 198 × 294 cm as Prado P006808 / Q59859661.'},
]
def snapshot(db,ids):
 return {table:db.execute(query,(ids,)).fetchall() for table,query in {
  'artworks':'SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',
  'identifiers':"SELECT to_jsonb(e) data FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",
  'citations':"SELECT to_jsonb(c) data FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",
  'locations':'SELECT to_jsonb(l) data FROM artwork_location_assertions l WHERE artwork_id=ANY(%s::uuid[]) ORDER BY id',
  'creators':'SELECT to_jsonb(c) data FROM artwork_artists c WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id',
  'images':'SELECT to_jsonb(c) data FROM artwork_media c WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',
 }.items()}
def plan():
 ids=[p[k]for p in PAIRS for k in ('canonical','duplicate')]
 with r.connect('production')as db:before=snapshot(db,ids)
 artworks={x['data']['id']:x['data']for x in before['artworks']}
 sid=r.load(m.RUN/'production-plan.json.gz')['source_id']
 for p in PAIRS:
  old,new=artworks[p['canonical']],artworks[p['duplicate']]
  assert old['primary_media_id'] and new['primary_media_id']is None
  assert old['status']==new['status']=='review' and old['current_institution_id']==new['current_institution_id']==m.MUSEUM
  assert new['accession_number']==p['accession'] and new['created_by']==m.ACTOR
  assert {(x['data']['scheme'],x['data']['external_id'])for x in before['identifiers']if x['data']['entity_id']==p['duplicate']}=={('wikidata',p['equivalent_qid']),('prado-native-object',p['native'])}
  assert any(x['data']['entity_id']==p['canonical'] and x['data']['scheme']=='wikidata' and x['data']['external_id']==p['old_qid']for x in before['identifiers'])
  assert all(x['data']['source_id']==sid for x in before['citations']if x['data']['entity_id']==p['duplicate'])
  assert not any(x['data']['artwork_id']==p['duplicate']for x in before['images'])
 evidence={f:r.sha((m.RUN/f).read_bytes()) for f in ('post-import-duplicate-file-evidence.json','post-import-duplicate-identity-evidence.json')}
 data={'at':r.now(),'pairs':PAIRS,'source_id':sid,'before':before,'evidence_sha256':evidence,'policy':'Preserve original illustrated canonical artwork unchanged. Move exact native identifier and imported source citation to canonical identity; retain alternate Wikidata authority separately. Archive only the two duplicates created by this import, with explicit duplicate-of citations; reject only their imported holding assertions. No deletion, image replacement, date rewrite or publication.'}
 r.save_gz(RUN/'plan.json.gz',data);r.save_gz(BACKUP/'plan.json.gz',data);r.save(RUN/'pin.json',{'sha256':r.sha((RUN/'plan.json.gz').read_bytes())});print('Pinned 2 exact identity consolidations',flush=True)
def apply():
 pin=r.load(RUN/'pin.json');assert pin['sha256']==r.sha((RUN/'plan.json.gz').read_bytes())
 plan=r.load(RUN/'plan.json.gz');ids=[p[k]for p in PAIRS for k in ('canonical','duplicate')];sid=plan['source_id']
 urls={x['source_id']:x['object']['url']for x in r.load(m.RUN/'production-plan.json.gz')['records']}
 assert r.load(m.BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
 for f,digest in plan['evidence_sha256'].items():assert r.sha((m.RUN/f).read_bytes())==digest
 with r.connect('production',readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='10s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  before=snapshot(db,ids);assert before==plan['before'],'Source records changed after pinned identity plan'
  r.save_gz(BACKUP/'locked-before.json.gz',before)
  for p in PAIRS:
   old,new=p['canonical'],p['duplicate']
   assert db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND scheme='prado-native-object' AND external_id=%s AND source_id=%s",(old,new,p['native'],sid)).rowcount==1
   assert db.execute("UPDATE external_identifiers SET entity_id=%s,scheme='prado-wikidata-equivalent' WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata' AND external_id=%s AND source_id=%s",(old,new,p['equivalent_qid'],sid)).rowcount==1
   assert db.execute("UPDATE citations SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s",(old,new,sid)).rowcount==1
   assert db.execute("UPDATE artwork_location_assertions SET review_state='rejected',evidence_note=evidence_note || %s WHERE artwork_id=%s AND source_id=%s AND claim_type='holding' AND review_state='accepted'",(' Duplicate import identity consolidated into '+old+'. Underlying Prado collection connection retained on the canonical record; this assertion belongs to the duplicate row.',new,sid)).rowcount==1
   assert db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND status='review' AND primary_media_id IS NULL",(m.ACTOR,new)).rowcount==1
   for aid,field in ((old,'duplicate_identity_consolidation'),(new,'duplicate_of')):
    m.insert(db,'citations',{'entity_type':'artwork','entity_id':aid,'field_name':field,'source_id':sid,'source_record_id':p['native'],'source_url':urls[p['native']],'evidence_note':json.dumps({'canonical_artwork_id':old,'archived_duplicate_id':new,'basis':p['basis'],'policy':plan['policy'],'evidence_sha256':plan['evidence_sha256'],'plan_sha256':pin['sha256']},ensure_ascii=False),'retrieved_at':r.now(),'created_by':m.ACTOR})
  after=snapshot(db,ids);oldart={x['data']['id']:x['data']for x in before['artworks']};newart={x['data']['id']:x['data']for x in after['artworks']}
  for p in PAIRS:
   assert newart[p['canonical']]==oldart[p['canonical']]
   a,b=newart[p['duplicate']],oldart[p['duplicate']];allowed={'status','current_institution_id','updated_at','updated_by','revision'}
   assert {k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in b.items()if k not in allowed}
   assert a['status']=='archived' and a['current_institution_id']is None and a['primary_media_id']is None
  assert before['images']==after['images'] and before['creators']==after['creators']
 r.save_gz(RUN/'after.json.gz',after);r.save_gz(BACKUP/'after.json.gz',after)
 r.save(RUN/'applied.json',{'at':r.now(),'plan_sha256':pin['sha256'],'canonical_records_preserved':2,'new_duplicates_archived':2,'records_deleted':0,'images_changed':0,'published':0,'local_database_writes':0,'canonical_map':{p['duplicate']:p['canonical']for p in PAIRS}})
 print('Consolidated 2 duplicate imports; existing artworks and images preserved.',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply']);globals()[parser.parse_args().command]()
