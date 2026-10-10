"""Reconstruct pending Verbania holdings from exact saved national-catalogue responses."""
import collections,csv,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('start',Path(__file__).with_name('museum-expansion-italy-sixth-start-20261008.py'));start=importlib.util.module_from_spec(z);z.loader.exec_module(start)
prior=start.prior;m=prior.m;ref=prior.reference;checked=prior.checked;RUN=m.RUN/'native/verbania-holdings-20261008';IID='ded6b5bc-f6d7-535e-8bbe-f2b4d6fdc839';MURI='https://w3id.org/arco/resource/CulturalInstituteOrSite/6cd6b176cc4bb2ad912a2ae88e91ba6a';BASE=prior.snapshot.__globals__['prior'].prior.base
DC='http://purl.org/dc/elements/1.1/';LOC='https://w3id.org/arco/ontology/location/';CD='https://w3id.org/arco/ontology/context-description/';DD='https://w3id.org/arco/ontology/denotative-description/';LABEL='http://www.w3.org/2000/01/rdf-schema#label';CORE='https://w3id.org/arco/ontology/core/'
def snapshot(db,ids):
 out=BASE.snapshot(db,ids,IID);mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return BASE.counts(db,IID)
def graph(v):
 g=collections.defaultdict(lambda:collections.defaultdict(set))
 for t in v['triples']:g[t['s']][t['p']].add(t['o'])
 return g
def main():
 dest=RUN/'source-context-001.json.gz';assert not dest.exists();cont=m.load(start.RUN/'continuation-001.json');assert cont['verified_new']==211;checked(cont['previous_checkpoint'])
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id',(IID,IID))];snap=snapshot(db,ids);cs=counts(db)
  pending=[v for v in snap['assertions'] if v['institution_id']==IID and v['review_state']=='review' and v['superseded_by'] is None and v['claim_type']=='holding'];arts={v['id']:v for v in snap['artworks']};source_ids=sorted({json.loads(v['evidence_note'])['object_id'] for v in pending});aliases=sorted(set(source_ids)|{v.split('/')[-1] for v in source_ids})
  ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(aliases,)).fetchall();cits=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) ORDER BY entity_id,source_record_id,source_url",(aliases,)).fetchall()
 initial=dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=cs,read_only=True);m.save(RUN/'initial-scope-001.json.gz',initial)
 cache={};references={};rows=[]
 for h in pending:
  n=json.loads(h['evidence_note']);assert n['source_class']=='primary_museum_catalogue' and n['scheme']=='arco-object';path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());cache[key]=(hashlib.sha256(raw).hexdigest(),[{k:y['value'] for k,y in t.items()} for t in json.loads(raw)['results']['bindings']]);references[key]=ref(path)
  digest,triples=cache[key];assert digest==n['source_response_sha256'];root='https://w3id.org/arco/resource/'+n['object_id'];vs=[v for v in triples if v.get('root')==root];assert vs
  hits=[v for v in ex if v['external_id'] in {n['object_id'],n['object_id'].split('/')[-1]}]+[v for v in cits if v['source_record_id'] in {n['object_id'],n['object_id'].split('/')[-1]}]
  rows.append(dict(number=len(rows)+1,artwork=arts[h['artwork_id']],pending_assertion=h,original_evidence=n,source_id=n['object_id'],source_url=h['source_url'],root=root,triples=vs,body_reference=references[key],raw_sha256=digest,identity_hits=hits))
 authority_path=m.ROOT/'docs/research/artwork-locations-20261004/arco-institution-resolutions-20261005b.json';authorities=[v for v in m.load(authority_path) if v['institution']['id']==IID];assert len(authorities)==1 and authorities[0]['source_institution_uri']==MURI
 m.save(dest,dict(at=m.now(),rows=rows,body_references=list(references.values()),authority=authorities[0],authority_reference=ref(authority_path),initial_reference=ref(RUN/'initial-scope-001.json.gz'),script_reference=ref(Path(__file__).resolve()),continuation_reference=ref(start.RUN/'continuation-001.json'),policy='Exact original response hashes verified. Reconsider private ownership only as a separate concept from the source-recorded holding. No implication of ownership, current public display or new date metadata. All individual physical identities and custody qualifiers require review.',read_only=True))
 print(json.dumps(dict(scoped=len(ids),pending=len(rows),counts=cs,bodies=len(references))),flush=True)
if __name__=='__main__':main()
