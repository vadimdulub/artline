"""Check selected exact source identities across current and historical domains."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-italy-fourth-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def aliases(row):
 rid=row['index_record']['source_record_id'];root='https://w3id.org/arco/resource/'+rid
 urls={root,root.replace('https:','http:')}
 urls|={protocol+'://'+host+'/detail/'+rid+slash for protocol in ['https','http'] for host in ['catalogo.cultura.gov.it','catalogo.beniculturali.it'] for slash in ['','/']}
 return dict(ids={rid,rid.split('/')[-1],root,root.replace('https:','http:')},urls=urls)
def main():
 x=d.m.load(d.RUN/'five-museum-discovery-002.json.gz');ids=sorted({v for r in x['rows'] for v in aliases(r)['ids']});urls=sorted({v for r in x['rows'] for v in aliases(r)['urls']})
 with d.m.connect() as db:
  ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s)) ORDER BY entity_id,scheme,external_id",(ids,urls)).fetchall()
  ci=db.execute("SELECT entity_id::text,field_name,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND (source_record_id=ANY(%s) OR source_url=ANY(%s)) ORDER BY entity_id,source_record_id,source_url,field_name",(ids,urls)).fetchall()
 known=[];remaining=[]
 for row in x['rows']:
  a=aliases(row);hits=[v for v in ex if v['external_id'] in a['ids'] or v['canonical_url'] in a['urls']]+[v for v in ci if v['source_record_id'] in a['ids'] or v['source_url'] in a['urls']]
  if hits:known.append(dict(number=row['number'],source_record_id=row['index_record']['source_record_id'],hits=hits))
  else:remaining.append(row['number'])
 d.m.save(d.RUN/'source-aliases-002.json.gz',dict(at=d.m.now(),candidate_reference=d.ref(d.RUN/'five-museum-discovery-002.json.gz'),known=known,capture_numbers=remaining,external_identifiers=ex,citations=ci,query_reference=d.ref(Path(__file__).resolve()),read_only=True))
 print(json.dumps(dict(selected=len(x['rows']),existing_source_objects=len(known),source_capture_candidates=len(remaining))),flush=True)
if __name__=='__main__':main()
