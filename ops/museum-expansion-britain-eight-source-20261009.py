"""Verify wave86; read Southampton and Edinburgh pending object evidence without mutation."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-guildhall-apply-20261009.py'));prior=importlib.util.module_from_spec(z);z.loader.exec_module(prior);m=prior.m;ref=prior.reference;checked=prior.checked;BASE=prior.s.prior.s.BASE
RUN=m.RUN/'native/britain-eight-holdings-20261009';CP=prior.RUN/'delivery-checkpoint-001.json';IIDS=['f751c09d-2023-5b1b-935b-3aae9a3f842a','9c814fd2-038c-582e-b2b0-9dc8c2e0a00b'];QIDS=dict(zip(IIDS,['Q7569107','Q65081638']));NETWORK=None;PROTECT_IIDS=IIDS
def snapshot(db,ids):
 out=BASE.snapshot(db,ids,IIDS[0]);out.pop('museum');out['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(PROTECT_IIDS,))];mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return {iid:BASE.counts(db,iid) for iid in IIDS}
def main():
 dest=RUN/'source-context-001.json.gz';assert not dest.exists();assert ref(CP)['sha256']=='750a1c67d27e1633509c5758bdf1c248b0c08e856f2b071d66e2fdc84f92988b';cp=m.load(CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';result=prior.verify(db,p,d);ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(IIDS,IIDS))];snap=snapshot(db,ids);cs=counts(db);painterids=sorted({v['artist_id'] for v in snap['artists']});painters=[v['row'] for v in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id',(painterids,))];authorities=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(painterids,))]
 m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',verified_new_records=22,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=result,policy='Freshly verified22 Guildhall additions. Concrete prior progress. Continue the full museum goal; no repeated global blocker.'))
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=cs,painters=painters,creator_authorities=authorities,read_only=True,script_reference=ref(Path(__file__).resolve())));groups=collections.defaultdict(list)
 for h in snap['assertions']:
  if h['institution_id'] in IIDS and h['review_state']=='review' and h['superseded_by'] is None and h['claim_type']=='holding':groups[(h['artwork_id'],h['institution_id'])].append(h)
 arts={v['id']:v for v in snap['artworks']};cache={};refs={};rows=[];duplicates=[];held=[]
 for (aid,iid),hs in sorted(groups.items()):
  options=[]
  for h in hs:
   try:n=json.loads(h['evidence_note'])
   except (json.JSONDecodeError,TypeError):continue
   if n.get('scheme')=='wikidata' and n.get('evidence_path'):options.append((h,n))
  if len(options)!=1:held.append(dict(artwork_id=aid,institution_id=iid,assertions=hs,reason='No unique structured saved-source assertion'));continue
  h,n=options[0];extra=[v for v in hs if v['id']!=h['id']]
  if extra:duplicates.append(dict(artwork_id=aid,selected_assertion_id=h['id'],additional_assertions=extra))
  path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=path.read_bytes();raw=gzip.decompress(raw) if path.suffix=='.gz' else raw;cache[key]=(hashlib.sha256(raw).hexdigest(),json.loads(raw));refs[key]=ref(path)
  digest,data=cache[key];assert digest==n['source_response_sha256'];e=data['entities'][n['object_id']];assert e['id']==n['object_id'] and e['type']=='item';rows.append(dict(number=len(rows)+1,institution_id=iid,museum_qid=QIDS[iid],artwork=arts[aid],pending_assertion=h,additional_pending_assertions=extra,original_evidence=n,source_id=n['object_id'],entity=e,body_reference=refs[key],raw_sha256=digest))
 m.save(dest,dict(at=m.now(),rows=rows,source_holds=held,body_references=list(refs.values()),initial_reference=ref(RUN/'initial-scope-001.json.gz'),continuation_reference=ref(RUN/'continuation-001.json'),script_reference=ref(Path(__file__).resolve()),duplicate_pending_assertions=duplicates,read_only=True,policy='Saved exact secondary object evidence only; not fresh native confirmation. Preserve all metadata and unknown dates. Multiple historical assertions stay with one object. Museum holdings do not establish current display.'))
 print(json.dumps(dict(scope=len(ids),pending_objects=len(groups),selected=len(rows),source_holds=len(held),pending_assertions=sum(len(v) for v in groups.values()),counts=cs,bodies=len(refs),creators=len(painters),prior_verified=22)),flush=True)
if __name__=='__main__':main()
