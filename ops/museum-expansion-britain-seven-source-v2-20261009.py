"""Reuse verified scope; reconcile duplicate historical pending assertions before parsing."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-seven-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked;IIDS=s.IIDS;QIDS=s.QIDS;snapshot=s.snapshot;counts=s.counts;PROTECT_IIDS=s.PROTECT_IIDS;BASE=s.BASE;prior=s.prior;CP=s.CP
def main():
 dest=RUN/'source-context-001.json.gz';assert not dest.exists();initial=m.load(RUN/'initial-scope-001.json.gz')
 with m.connect() as db:
  assert snapshot(db,initial['scoped_ids'])==initial['snapshot'];assert counts(db)==initial['counts']
 groups=collections.defaultdict(list)
 for h in initial['snapshot']['assertions']:
  if h['institution_id'] in IIDS and h['review_state']=='review' and h['superseded_by'] is None and h['claim_type']=='holding':groups[(h['artwork_id'],h['institution_id'])].append(h)
 arts={v['id']:v for v in initial['snapshot']['artworks']};rows=[];cache={};refs={};duplicates=[]
 for (aid,iid),hs in sorted(groups.items()):
  options=[]
  for h in hs:
   try:n=json.loads(h['evidence_note'])
   except json.JSONDecodeError:continue
   if n.get('scheme')=='wikidata' and n.get('evidence_path'):options.append((h,n))
  assert len(options)==1;h,n=options[0];extra=[v for v in hs if v['id']!=h['id']]
  if extra:duplicates.append(dict(artwork_id=aid,selected_assertion_id=h['id'],additional_assertions=extra))
  path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());cache[key]=(hashlib.sha256(raw).hexdigest(),json.loads(raw));refs[key]=ref(path)
  digest,data=cache[key];assert digest==n['source_response_sha256'];e=data['entities'][n['object_id']];assert e['id']==n['object_id'] and e['type']=='item';rows.append(dict(number=len(rows)+1,institution_id=iid,museum_qid=QIDS[iid],artwork=arts[aid],pending_assertion=h,additional_pending_assertions=extra,original_evidence=n,source_id=n['object_id'],entity=e,body_reference=refs[key],raw_sha256=digest))
 assert len(rows)==201 and len(duplicates)==1
 m.save(dest,dict(at=m.now(),rows=rows,body_references=list(refs.values()),initial_reference=ref(RUN/'initial-scope-001.json.gz'),continuation_reference=ref(RUN/'continuation-001.json'),script_reference=ref(Path(__file__).resolve()),duplicate_pending_assertions=duplicates,read_only=True,policy='201 objects with202 pending assertions. Fanny Keats has two historical pending claims; preserve both and reconcile their supersession only if object approved. Exact saved secondary evidence,not fresh native confirmation. No database edits.'));print(json.dumps(dict(scope=len(arts),pending_objects=len(rows),pending_assertions=sum(len(v) for v in groups.values()),counts=initial['counts'],bodies=len(refs),duplicate_pending=len(duplicates))),flush=True)
if __name__=='__main__':main()
