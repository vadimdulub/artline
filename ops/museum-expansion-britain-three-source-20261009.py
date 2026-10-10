"""Verify wave78 and reconstruct Cardiff and Bristol' exact saved object evidence."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-britain-two-apply-20261008.py'));prior=importlib.util.module_from_spec(z);z.loader.exec_module(prior);m=prior.m;ref=prior.reference;checked=prior.checked;BASE=prior.s.BASE
RUN=m.RUN/'native/britain-three-holdings-20261009';CP=prior.RUN/'delivery-checkpoint-001.json';IIDS=['bbde7b48-7080-46aa-9933-19c42c1fa28e','6aaf0c6c-88e1-53f2-8455-9f894164db88'];QIDS=dict(zip(IIDS,['Q1321874','Q4968867']))
def snapshot(db,ids):
 out=BASE.snapshot(db,ids,IIDS[0]);out.pop('museum');out['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(IIDS,))];mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return {iid:BASE.counts(db,iid) for iid in IIDS}
def main():
 dest=RUN/'source-context-001.json.gz';assert not dest.exists();assert ref(CP)['sha256']=='3549d2a58984862b897a730fa68f00dd8ce49f4825a6f46819ca6ae6dc2d441c';cp=m.load(CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';result=prior.verify(db,p,d)
  ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(IIDS,IIDS))];snap=snapshot(db,ids);cs=counts(db);pending=[v for v in snap['assertions'] if v['institution_id'] in IIDS and v['review_state']=='review' and v['superseded_by'] is None and v['claim_type']=='holding'];arts={v['id']:v for v in snap['artworks']};painterids=sorted({v['artist_id'] for v in snap['artists']});painters=[v['row'] for v in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id',(painterids,))];authorities=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(painterids,))]
 m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',verified_existing_links=233,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=result,policy='Verified233 prior Laing and National Army links. Continue full goal with Cardiff and Bristol pending source-backed holdings. No repeated global blocker.'))
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=cs,painters=painters,creator_authorities=authorities,read_only=True));cache={};refs={};rows=[]
 for h in pending:
  n=json.loads(h['evidence_note']);assert n['scheme']=='wikidata';path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());cache[key]=(hashlib.sha256(raw).hexdigest(),json.loads(raw));refs[key]=ref(path)
  digest,data=cache[key];assert digest==n['source_response_sha256'];e=data['entities'][n['object_id']];assert e['id']==n['object_id'] and e['type']=='item';rows.append(dict(number=len(rows)+1,institution_id=h['institution_id'],museum_qid=QIDS[h['institution_id']],artwork=arts[h['artwork_id']],pending_assertion=h,original_evidence=n,source_id=n['object_id'],entity=e,body_reference=refs[key],raw_sha256=digest))
 m.save(dest,dict(at=m.now(),rows=rows,body_references=list(refs.values()),initial_reference=ref(RUN/'initial-scope-001.json.gz'),continuation_reference=ref(RUN/'continuation-001.json'),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='Exact saved secondary object records, not fresh museum confirmation. Check external IDs, referenced primary object IDs, creator authority, inventory, source chronology, holding qualifiers and physical identity before decisions; preserve all metadata and no display claims.'))
 print(json.dumps(dict(scope=len(ids),pending=len(rows),counts=cs,bodies=len(refs),creators=len(painters),prior_verified=233)),flush=True)
if __name__=='__main__':main()
