"""Pinned primary context for same-creator candidate collisions; read-only."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-verbania-identity-20261008.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
def main():
 dest=RUN/'comparison-source-context-001.json.gz';assert not dest.exists();x=m.load(RUN/'identity-001.json.gz');cs=m.load(RUN/'identity-citations-001.json.gz')['citations'];own={v['existing_artwork_id'] for v in x['rows']};aids={h['id'] for c in x['comparisons'] for h in c['hits'] if h['same_creator']} - own;rows=[];cache={};refs={};digests={};facts=[]
 for c in cs:
  if c['entity_id'] not in aids:continue
  try:n=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(n,dict):continue
  if n.get('facts'):facts.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],facts=n['facts'],source_url=c['source_url']));continue
  if not n.get('evidence_path') or not n.get('source_response_sha256') or 'HistoricOrArtisticProperty/' not in str(n.get('object_id','')):continue
  path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());digests[key]=hashlib.sha256(raw).hexdigest();cache[key]=collections.defaultdict(list)
   for v in json.loads(raw)['results']['bindings']:cache[key][v.get('root',{}).get('value')].append({k:y['value'] for k,y in v.items()})
   refs[key]=ref(path)
  assert digests[key]==n['source_response_sha256'];root='https://w3id.org/arco/resource/'+n['object_id'];vs=cache[key][root];assert vs
  fields=collections.defaultdict(set)
  for v in vs:
   if v['s']==root:fields[v['p']].add(v['o'])
  rows.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_id=n['object_id'],source_url=c['source_url'],body_reference=refs[key],raw_sha256=n['source_response_sha256'],root_fields={k:sorted(v) for k,v in fields.items()},triples=vs))
 m.save(dest,dict(at=m.now(),requested_ids=sorted(aids),rows=rows,citation_fact_contexts=facts,body_references=list(refs.values()),identity_reference=ref(RUN/'identity-001.json.gz'),citations_reference=ref(RUN/'identity-citations-001.json.gz'),script_reference=ref(Path(__file__).resolve()),read_only=True))
 print(json.dumps(dict(requested=len(aids),contexts=len(rows),facts=len(facts),bodies=len(refs))),flush=True)
if __name__=='__main__':main()
