"""Reparse pinned facts with evidenced city/range resolutions and extra Vicenza."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-italy-fourth-facts-20261008.py'));base=importlib.util.module_from_spec(z);z.loader.exec_module(base)
m=base.m;RUN=base.RUN;ref=base.ref;checked=base.checked;d=base.d;a=base.a;c=base.c;body=base.body
original_parse=base.parse

def cities():
 x=m.load(RUN/'address-cities-001.json');raw=body(x['receipt_reference'],x['body_reference']);rows=[{k:v['value'] for k,v in r.items()} for r in json.loads(raw)['results']['bindings']];assert rows==x['triples'];return rows

def parse(row,b,page):
 r=original_parse(row,b,page);v=r['facts'];resolutions=[];issues=r['issues'];uri='https://w3id.org/arco/resource/'+r['source_id'];g=base.graph_for(b,uri);root=g[uri]
 if 'html_museum_city_conflict' in issues and not v['source_fields'].get('INDIRIZZO') and v['authority']:
  addresses=root[a.LOC+'hasCulturalPropertyAddress'];actual={x['o'] for x in cities() if x['s'] in addresses and x['p']=='https://w3id.org/italia/onto/CLV/hasCity'};expected=set(v['authority']['address_city_uris'])
  if len(addresses)==1 and len(actual)==1 and actual<=expected and root[a.DC+'coverage']=={v['authority']['catalogue_city']}:
   issues.remove('html_museum_city_conflict');resolutions.append(dict(issue='html_museum_city_conflict',basis='HTML street address absent, not contradictory. Exact current museum URI and HTML museum link/name agree; the explicitly linked object address gives the expected city URI, also matching literal object coverage.',city_uris=sorted(actual),source_reference=ref(RUN/'address-cities-001.json')))
 # Six literal slash ranges have independent, identical structured endpoints.
 match=re.fullmatch(r'(\d{4})\s*/\s*(\d{4})',v['date_display'] or '')
 if match and set(issues)>={'creation_date_review','html_graph_date_conflict'}:
  first,last=map(int,match.groups());dates=root[a.DC+'date'];dt=a.numeric_date(next(iter(dates),''))
  if 1000<=first<last<=1970 and len(dates)==1 and dt and dt[:2]==(first,last):
   issues.remove('creation_date_review');issues.remove('html_graph_date_conflict');v.update(first=first,last=last,date_precision='range');resolutions.append(dict(issue='slash_creation_range',basis='Literal HTML four-digit slash endpoints equal the structured object hyphen-range endpoints. Preserve the slash date display and both source values.',html=v['date_display'],structured=sorted(dates)))
 if r['number']==11 and issues==['custody_narrative_review'] and v['current_location_source_notes']==['stanze del deposito'] and root[a.DC+'description']=={'n.p'}:
  issues.remove('custody_narrative_review');resolutions.append(dict(issue='custody_narrative_review',basis='Literal stanze del deposito is a storage-room note inside the exact verified current museum location; it does not name an external deposit. Preserve storage context and make no display claim.'))
 if resolutions:r['source_issue_resolutions']=resolutions
 r['state']='candidate' if not issues else 'source_review';return r
base.parse=parse

def build(final=True):
 rows,refs=base.build();discovery=m.load(RUN/'five-museum-discovery-002.json.gz');by={r['number']:r for r in discovery['rows']}
 for path in sorted((RUN/'extra-current-001/batches').glob('*.json.gz')):
  b=base.validated_batch(path);refs.append(ref(path));b['_path']=path
  for n in b['numbers']:
   page=next((p for p in b.get('pages',[]) if p['number']==n),None)
   if b['source_state']!='captured' or not page or 'error' in page:rows.append(dict(by[n],state='source_failure',issues=[b.get('error') or (page or {}).get('error') or 'missing_page']));continue
   rows.append(parse(by[n],b,page))
 for hit in m.load(RUN/'source-aliases-002.json.gz')['known']:
  if hit['number']>=619:rows.append(dict(by[hit['number']],state='source_review',issues=['existing_source_identity'],existing_source_hits=hit['hits']))
 rows.sort(key=lambda v:v['number']);assert len(rows)==len({r['number'] for r in rows})
 if final:assert len(rows)==len(by)==698
 return rows,refs

def main():
 dest=RUN/'native-candidates-002.json.gz';assert not dest.exists();x=m.load(RUN/'extra-source-capture-001.json');assert not x['requests_stopped'];rows,refs=build()
 m.save(dest,dict(at=m.now(),rows=rows,dependencies=refs+[ref(RUN/n) for n in ['native-candidates-001.json.gz','five-museum-discovery-002.json.gz','source-aliases-002.json.gz','extra-source-capture-001.json','address-cities-001.json']],parser_reference=ref(Path(__file__).resolve()),base_parser_reference=ref(Path(base.__file__).resolve()),policy='No source facts invented. Missing HTML addresses resolved only by exact linked address-city URI and agreeing museum/name/coverage evidence. Explicit slash ranges retained verbatim and parsed only when structured endpoints agree. Museum storage is not current display. All candidates still require physical identity and editorial review.'))
 print(json.dumps(dict(rows=len(rows),states=collections.Counter(r['state'] for r in rows),by_museum={name:collections.Counter(r['state'] for r in rows if r['museum']['name']==name) for name in sorted({r['museum']['name'] for r in rows})},resolved=sum('source_issue_resolutions' in r for r in rows))))
if __name__=='__main__':main()
