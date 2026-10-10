"""Fresh comparison with museum inventories and verified linked-creator labels."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('old',Path(__file__).with_name('museum-expansion-milan-identity-20261009.py'));old=importlib.util.module_from_spec(z);z.loader.exec_module(old);s=old.s;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked;i=old.i
o=s.module('o','museum-expansion-milan-objects-20261009.py')
def native_matches(r,nr):
 desc=s.graph(r)[r['root']][s.DC+'description'];ds={m.norm(t.replace('\\n',' ').replace('amientata','ambientata').replace('una mazza figura','una mezza figura').replace('unìedicola',"un'edicola")) for t in desc if len(t)>80};hits=[]
 for n in nr.get('objects',[]):
  raw=gzip.decompress((m.ROOT/n['capture']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==n['capture']['receipt']['sha256'];assert o.fields(raw)==n['parsed']
  if any(m.norm(t).startswith(d) for d in ds for t in n['parsed']['fields'].get('descrizione',[])):hits.append(n)
 if r['number']==56:
  hits=[n for n in nr.get('objects',[]) if n['index']['url']=='https://collezioni-online.museoscienza.org/detail/IT-MUST-NTR001-004900/la-signora-inganni' and n['parsed']['fields'].get('inventario')==['IGB-8492'] and n['parsed']['title']=='La signora Inganni']
 return list({v['index']['url']:v for v in hits}.values())
def rows():
 src=m.load(RUN/'source-context-001.json.gz');native=m.load(RUN/'native-objects-001.json.gz');ns={v['number']:v for v in native['rows']};out=[]
 for extra in m.load(RUN/'native-followup-001.json.gz')['rows']:ns[extra['number']]['objects']+=extra['objects']
 for r in src['rows']:
  g=s.graph(r);root=g[r['root']];a=r['artwork'];matched=native_matches(r,ns[r['number']]);ivs=sorted({t for n in matched for t in n['parsed']['fields'].get('inventario',[])});titles=set(root[s.DC+'subject'])|{a['title']};titles.update(t.strip() for t in re.split(r'[,;]|\|\|',a['title']) if t.strip());titles|={n['parsed']['title'] for n in matched};creator=o.creator(r)
  f=dict(source_id=r['source_id'],source_url=r['source_url'],title=a['title'],titles=sorted(titles),creator_label=creator,inventory='; '.join(ivs),date_display=next(iter(root[s.DC+'date'])),source_fields={'ATTRIBUZIONI':creator},native_page_urls=[n['index']['url'] for n in matched],native_metadata_urls=[r['root']])
  out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=s.IID,facts=f,existing_artwork_id=a['id'],native_matches=matched))
 return out

def main():
 dest=RUN/'identity-003.json.gz';assert not dest.exists();rs=rows();p=i.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');initial=m.load(RUN/'initial-scope-001.json.gz');assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=i.queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comps=i.comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=p,state=state,comparisons=comps,within_batch=i.within_batch(rs),script_reference=ref(Path(__file__).resolve()),base_script_reference=ref(Path(i.__file__).resolve()),source_reference=ref(RUN/'source-context-001.json.gz'),native_reference=ref(RUN/'native-objects-001.json.gz'),followup_reference=ref(RUN/'native-followup-001.json.gz'),matching_policy='Exact original description prefix with three documented typographic normalizations. Inganni IGB8492 explicitly reviewed: same unique life-size wooden figure, current museum date and clothing description differ; preserve both sources without rewriting metadata.',previous_identity_reference=ref(RUN/'identity-002.json.gz'),read_only=True));m.save(RUN/'identity-citations-003.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(scope=len(state['artwork_ids']),comparisons=len(comps),hits=sum(len(v['hits']) for v in comps),citations=len(cs),native_match_counts=dict(collections.Counter(len(v['native_matches']) for v in rs)))),flush=True)
if __name__=='__main__':main()
