"""Reconstruct historical catalogue context and museum-local inventory collisions."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-italy-third-supplement-20261008.py'));s=importlib.util.module_from_spec(s);s.__spec__.loader.exec_module(s)
m=s.m;RUN=s.RUN;ref=s.ref
def main():
 dest=RUN/'comparison-source-context-001.json.gz';assert not dest.exists();x=m.load(RUN/'selected-identity-003.json.gz');cs=m.load(RUN/'selected-citations-003.json.gz')['citations'];aids={h['id'] for c in x['comparisons'] for h in c['hits'] if h['same_museum'] or h['same_creator']};rows=[];cache={};refs={}
 for c in cs:
  if c['entity_id'] not in aids:continue
  try:n=json.loads(c['evidence_note'] or '')
  except (ValueError,TypeError):continue
  if not isinstance(n,dict) or not n.get('evidence_path') or not n.get('source_response_sha256') or not str(n.get('object_id','')).startswith('HistoricOrArtisticProperty/'):continue
  path=m.ROOT/n['evidence_path']
  if str(path) not in cache:
   raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==n['source_response_sha256'];cache[str(path)]=json.loads(raw)['results']['bindings'];refs[str(path)]=ref(path)
  else:assert hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()==n['source_response_sha256']
  root='https://w3id.org/arco/resource/'+n['object_id'];vs=[{k:v['value'] for k,v in v.items()} for v in cache[str(path)] if v.get('root',{}).get('value')==root];assert vs
  inv=sorted({v['o'] for v in vs if v['p'].split('/')[-1] in ['inventoryIdentifier','alternativeInventoryNumber']})
  fields=collections.defaultdict(set)
  for v in vs:
   if v['s']==root:fields[v['p']].add(v['o'])
  rows.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_id=n['object_id'],source_url=c['source_url'],body_reference=refs[str(path)],raw_sha256=n['source_response_sha256'],inventory=inv,root_fields={k:sorted(v) for k,v in fields.items()},triples=vs))
 by=collections.defaultdict(list)
 for v in rows:by[v['artwork_id']].append(v)
 originals={r['number']:r for r in m.load(RUN/'native-candidates-002.json.gz')['rows']};hits=[]
 for c in x['comparisons']:
  row=originals[c['number']];tokens=s.i.invparts(row['facts']['inventory'])
  for h in c['hits']:
   if not h['same_museum']:continue
   for ctx in by[h['id']]:
    overlap=tokens&set().union(*(s.i.invparts(v) for v in ctx['inventory']))
    if overlap:hits.append(dict(number=c['number'],artwork_id=h['id'],source_id=ctx['source_id'],overlap=sorted(overlap),body_reference=ctx['body_reference']))
 m.save(dest,dict(at=m.now(),rows=rows,body_references=list(refs.values()),identity_reference=ref(RUN/'selected-identity-003.json.gz'),citations_reference=ref(RUN/'selected-citations-003.json.gz'),script_reference=ref(Path(__file__).resolve()),museum_local_inventory_hits=hits,read_only=True,policy='Actual pinned historical RDF response bodies reconstructed for pertinent existing records. Inventory comparisons scoped by museum plus comparison-only Pisa collection scope; generic inventory values are not global object identifiers.'))
 print(json.dumps(dict(contexts=len(rows),bodies=len(refs),inventory_hits=hits)),flush=True)
if __name__=='__main__':main()
