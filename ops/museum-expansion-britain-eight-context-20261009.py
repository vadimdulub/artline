"""Reconstruct pinned raw evidence for returned existing comparison objects."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref

def main():
 dest=RUN/'comparison-source-context-001.json.gz';assert not dest.exists();x=m.load(RUN/'identity-001.json.gz');cs=m.load(RUN/'identity-citations-001.json.gz')['citations'];own={v['existing_artwork_id'] for v in x['rows']};wanted={h['id'] for c in x['comparisons'] for h in c['hits'] if h['same_creator'] and h['id'] not in own};cache={};refs={};rows=[]
 for c in cs:
  if c['entity_id'] not in wanted:continue
  try:n=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(n,dict):continue
  if n.get('evidence_path') and n.get('scheme')=='wikidata':path=m.ROOT/n['evidence_path'];digest=n['source_response_sha256'];qid=n['object_id']
  elif n.get('entity_receipt') and re.fullmatch(r'Q\d+',c['source_record_id'] or ''):
   receipt=n['entity_receipt'];path=m.ROOT/'docs/research/uk-painters-20260920/captures'/(hashlib.sha256(receipt['url'].encode()).hexdigest()+'.json');digest=receipt['sha256'];qid=c['source_record_id']
  else:continue
  key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest;cache[key]=(digest,json.loads(raw));refs[key]=ref(path)
  actual,data=cache[key];assert actual==digest;e=data['entities'][qid];assert e['id']==qid;rows.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_url=c['source_url'],source_id=qid,entity=e,body_reference=refs[key],raw_sha256=digest))
 m.save(dest,dict(at=m.now(),requested_ids=sorted(wanted),rows=rows,body_references=list(refs.values()),identity_reference=ref(RUN/'identity-001.json.gz'),citations_reference=ref(RUN/'identity-citations-001.json.gz'),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='Exact saved original Wikidata entity bodies reconstructed and hashes verified. All comparison citations retained separately, including primary museum/WikiArt evidence. Source identity and differing dimensions aid physical-version review, never quota-based selection.'));print(json.dumps(dict(requested=len(wanted),contexts=len(rows),artworks=len({v['artwork_id'] for v in rows}),bodies=len(refs))),flush=True)
if __name__=='__main__':main()
