"""Reconstruct pinned historical source context for every returned comparison."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-italy-fifth-identity-20261008.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
def main():
 dest=RUN/'comparison-source-context-001.json.gz';assert not dest.exists();x=m.load(RUN/'selected-identity-001.json.gz');cs=m.load(RUN/'selected-citations-001.json.gz')['citations'];aids={h['id'] for c in x['comparisons'] for h in c['hits']}|set(x['state']['scoped_ids'])|set(x['state']['related_collection_scope']['artwork_ids']);rows=[];cache={};refs={};digests={};newfacts=[]
 for c in cs:
  if c['entity_id'] not in aids:continue
  try:n=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(n,dict):continue
  if n.get('facts'):newfacts.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_id=c['source_record_id'],facts=n['facts'],source_url=c['source_url']));continue
  if not n.get('evidence_path') or not n.get('source_response_sha256') or not str(n.get('object_id','')).startswith('HistoricOrArtisticProperty/'):continue
  path=m.ROOT/n['evidence_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());digests[key]=hashlib.sha256(raw).hexdigest();cache[key]=collections.defaultdict(list)
   for v in json.loads(raw)['results']['bindings']:cache[key][v.get('root',{}).get('value')].append({k:y['value'] for k,y in v.items()})
   refs[key]=ref(path)
  assert digests[key]==n['source_response_sha256'];root='https://w3id.org/arco/resource/'+n['object_id'];vs=cache[key][root];assert vs
  inv=sorted({v['o'] for v in vs if v['p'].split('/')[-1] in ['inventoryIdentifier','alternativeInventoryNumber']});fields=collections.defaultdict(set)
  for v in vs:
   if v['s']==root:fields[v['p']].add(v['o'])
  rows.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_id=n['object_id'],source_url=c['source_url'],body_reference=refs[key],raw_sha256=n['source_response_sha256'],inventory=inv,root_fields={k:sorted(v) for k,v in fields.items()},triples=vs))
 by=collections.defaultdict(list)
 for v in rows:by[v['artwork_id']].append(v)
 museums=collections.defaultdict(set)
 for v in x['state']['artworks']:museums[v['current_institution_id']].add(v['id'])
 for v in x['state']['museum_assertions']:museums[v['institution_id']].add(v['artwork_id'])
 for parent,children in s.s.RELATEDMAP.items():museums[parent].update(v['id'] for v in x['state']['related_collection_scope']['membership'] if v['institution_id'] in children)
 hits=[]
 for r in x['rows']:
  tokens=s.i.invparts(r['facts']['inventory'])
  for aid in sorted(museums[r['institution_id']]):
   for ctx in by[aid]:
    overlap=tokens&set().union(*(s.i.invparts(v) for v in ctx['inventory']))
    if overlap:hits.append(dict(number=r['number'],artwork_id=aid,source_id=ctx['source_id'],overlap=sorted(overlap),body_reference=ctx['body_reference']))
 m.save(dest,dict(at=m.now(),rows=rows,citation_fact_contexts=newfacts,body_references=list(refs.values()),identity_reference=ref(RUN/'selected-identity-001.json.gz'),citations_reference=ref(RUN/'selected-citations-001.json.gz'),script_reference=ref(Path(__file__).resolve()),museum_local_inventory_hits=hits,read_only=True,policy='All returned comparison hits and collection scopes receive available pinned original RDF context. Source-body digests verified, not inferred from database date display. Newer structured citation facts retained separately. Inventories compared only within documented related collection scopes.'))
 print(json.dumps(dict(contexts=len(rows),structured_contexts=len(newfacts),bodies=len(refs),inventory_hits=hits)),flush=True)
if __name__=='__main__':main()
