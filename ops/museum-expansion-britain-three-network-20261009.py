"""Keep Bristol's network authority and its specific museum distinct."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-three-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
IID='d55f4987-94f6-5e4c-8d9b-c2c1b1fa2daf'
def current(db):
 return dict(institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row'],counts=s.BASE.counts(db,IID))
def main():
 dest=RUN/'bristol-network-context-001.json.gz';assert not dest.exists();initial=m.load(RUN/'initial-scope-001.json.gz');arts=[v for v in initial['snapshot']['artworks'] if v['current_institution_id']==IID];assert len(arts)==123;ids={v['id'] for v in arts};assertions=[v for v in initial['snapshot']['assertions'] if v['artwork_id'] in ids and v['institution_id']==IID and v['review_state']=='accepted' and not v['superseded_by']];assert len(assertions)==123;refs={};rows=[]
 for h in assertions:
  e=json.loads(h['evidence_note']);p=m.ROOT/e['evidence_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==e['source_response_sha256'];refs[str(p)]=ref(p);rows.append(dict(artwork_id=h['artwork_id'],assertion_id=h['id'],source_url=h['source_url'],evidence=e,body_reference=refs[str(p)]))
 with m.connect() as db:
  state=current(db);assert state['counts']==dict(linked=123,eligible=111);assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot']
 old=m.RUN/'native/bristol/research-status-001.json'
 m.save(dest,dict(at=m.now(),network_state=state,rows=rows,body_references=list(refs.values()),prior_research_reference=ref(old),script_reference=ref(Path(__file__).resolve()),policy='The network named Bristol Museums is not an alias of one specific branch. All123 existing accepted network holdings remain untouched. Exact branch references in saved Wikidata need further object-level reconciliation against the accepted native network evidence before reassignment. No museum merge, duplicate artwork creation, or branch/display inference. The other27 Bristol records have no accepted network holding and receive separate identity review.'))
 print(json.dumps(dict(network_records=len(arts),native_bodies=len(refs),counts=state['counts'])),flush=True)
if __name__=='__main__':main()
