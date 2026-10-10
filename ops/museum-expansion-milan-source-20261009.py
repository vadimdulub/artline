"""Verify wave79 and reconstruct Milan's exact saved national-catalogue evidence."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
prior=module('prior','museum-expansion-britain-three-apply-20261009.py');m=prior.m;ref=prior.reference;checked=prior.checked;BASE=prior.s.BASE
RUN=m.RUN/'native/milan-holdings-20261009';CP=prior.RUN/'delivery-checkpoint-001.json';IID='07cb8446-a063-416d-9f23-bb2280532f6e'
AUTH=m.ROOT/'docs/research/artwork-locations-20261004/arco-institution-resolutions-20261005b.json';authority=next(v for v in m.load(AUTH) if v['institution']['id']==IID);MURI=authority['source_institution_uri']
DC='http://purl.org/dc/elements/1.1/';LOC='https://w3id.org/arco/ontology/location/';CD='https://w3id.org/arco/ontology/context-description/';DD='https://w3id.org/arco/ontology/denotative-description/';LABEL='http://www.w3.org/2000/01/rdf-schema#label';CORE='https://w3id.org/arco/ontology/core/'
def snapshot(db,ids):
 out=BASE.snapshot(db,ids,IID);mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return BASE.counts(db,IID)
def graph(v):
 g=collections.defaultdict(lambda:collections.defaultdict(set))
 for t in v['triples']:g[t['s']][t['p']].add(t['o'])
 return g
def main():
 dest=RUN/'source-context-001.json.gz';assert not dest.exists();assert ref(CP)['sha256']=='dc18a40380accfd7a3bc9171274433d9818357ace77614c014b55e4fd857de06';cp=m.load(CP)
 for dep in cp['artifacts']:checked(dep)
 for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 p,d=prior.validate_plan()
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';verified=prior.verify(db,p,d)
  ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))];snap=snapshot(db,ids);cs=counts(db);pending=[v for v in snap['assertions'] if v['institution_id']==IID and v['review_state']=='review' and v['superseded_by'] is None and v['claim_type']=='holding'];arts={v['id']:v for v in snap['artworks']};source_ids=sorted({json.loads(v['evidence_note'])['object_id'] for v in pending});aliases=sorted(set(source_ids)|{v.split('/')[-1] for v in source_ids})
  ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(aliases,)).fetchall();cits=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) ORDER BY entity_id,source_record_id,source_url",(aliases,)).fetchall()
 m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',verified_existing_links=155,previous_checkpoint=ref(CP),artifact_pins_verified=len(cp['artifacts']),external_pins_verified=len(cp['external_artifacts']),verification=verified,policy='Previous Cardiff/Bristol155 links verified. Continue full goal through Milan exact primary evidence; preserve all earlier museum queues and access holds. No repeated global blocker.'))
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=cs,read_only=True));cache={};references={};rows=[]
 for h in pending:
  n=json.loads(h['evidence_note']);assert n['source_class']=='primary_museum_catalogue' and n['scheme']=='arco-object';path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());cache[key]=(hashlib.sha256(raw).hexdigest(),[{k:y['value'] for k,y in t.items()} for t in json.loads(raw)['results']['bindings']]);references[key]=ref(path)
  digest,triples=cache[key];assert digest==n['source_response_sha256'];root='https://w3id.org/arco/resource/'+n['object_id'];vs=[v for v in triples if v.get('root')==root];assert vs
  hits=[v for v in ex if v['external_id'] in {n['object_id'],n['object_id'].split('/')[-1]}]+[v for v in cits if v['source_record_id'] in {n['object_id'],n['object_id'].split('/')[-1]}]
  rows.append(dict(number=len(rows)+1,artwork=arts[h['artwork_id']],pending_assertion=h,original_evidence=n,source_id=n['object_id'],source_url=h['source_url'],root=root,triples=vs,body_reference=references[key],raw_sha256=digest,identity_hits=hits))
 m.save(dest,dict(at=m.now(),rows=rows,body_references=list(references.values()),authority=authority,authority_reference=ref(AUTH),initial_reference=ref(RUN/'initial-scope-001.json.gz'),script_reference=ref(Path(__file__).resolve()),continuation_reference=ref(RUN/'continuation-001.json'),policy='Exact original primary response hashes verified. Review institutional holding separately from owner/legal labels. Preserve dates,qualifications,images,status and source capture dates;no current-display claim. All individual physical identities and custody qualifications need review.',read_only=True))
 print(json.dumps(dict(scoped=len(ids),pending=len(rows),counts=cs,bodies=len(references),museum_uri=MURI)),flush=True)
if __name__=='__main__':main()
