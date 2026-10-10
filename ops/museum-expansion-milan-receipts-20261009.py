"""Reconstruct additional unresolved ArCo comparison leads from original receipts."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-milan-identity-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref

def main():
 dest=RUN/'comparison-receipt-context-001.json.gz';assert not dest.exists();i=m.load(RUN/'identity-001.json.gz');own={v['existing_artwork_id'] for v in i['rows']};ids={h['id'] for c in i['comparisons'] for h in c['hits'] if h['same_creator']}-own;cs=m.load(RUN/'identity-citations-001.json.gz')['citations'];out=[];cache={};refs={};literal=[]
 for c in cs:
  if c['entity_id'] not in ids:continue
  try:v=json.loads(c['evidence_note'] or '')
  except(ValueError,TypeError):
   if c['field_name']=='research_details':literal.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_url=c['source_url'],evidence_note=c['evidence_note']))
   continue
  if not isinstance(v,dict) or not v.get('source_receipt') or 'HistoricOrArtisticProperty/' not in v.get('external_id',''):continue
  rc=v['source_receipt'];path=m.ROOT/rc['body_path'];key=str(path)
  if key not in cache:
   raw=gzip.decompress(path.read_bytes());cache[key]=(hashlib.sha256(raw).hexdigest(),[{k:y['value'] for k,y in r.items()} for r in json.loads(raw)['results']['bindings']]);refs[key]=ref(path)
  digest,triples=cache[key];assert digest==rc['sha256'];root='https://w3id.org/arco/resource/'+v['external_id'];ts=[t for t in triples if t.get('root')==root];assert ts
  fields=collections.defaultdict(set)
  for t in ts:
   if t['s']==root:fields[t['p']].add(t['o'])
  out.append(dict(artwork_id=c['entity_id'],citation_id=c['id'],source_id=v['external_id'],source_url=c['source_url'],root=root,root_fields={k:sorted(v) for k,v in fields.items()},triples=ts,body_reference=refs[key],raw_sha256=digest,source_outcome=v.get('source_outcome'),identity_hold=v.get('identity_hold')))
 m.save(dest,dict(at=m.now(),rows=out,literal_primary_citation_context=literal,body_references=list(refs.values()),identity_reference=ref(RUN/'identity-001.json.gz'),citations_reference=ref(RUN/'identity-citations-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Comparison leads remain unresolved; reconstruct exact saved response, not an accepted association. Literal earlier native material/dimension citations remain evidence, not newly retrieved facts.'))
 print(json.dumps(dict(rows=len(out),bodies=len(refs),literal_citations=len(literal))),flush=True)
if __name__=='__main__':main()
