"""Reconstruct selected ArCo facts from pinned HTTP bodies, without DB writes."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-italy-second-capture-v2-20261008.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
d=c.d;m=d.m;a=d.arco;RUN=d.RUN;ref=d.ref;checked=d.checked
def body(receipt_ref,body_ref):
 receipt=m.load(checked(receipt_ref));raw=gzip.decompress(checked(body_ref).read_bytes())
 assert receipt['status']==200 and len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256']
 return raw
def validated_batch(path):
 b=m.load(path)
 if b['source_state']!='captured':return b
 triples=[]
 for part in b['graph_components']:
  raw=body(part['receipt_reference'],part['body_reference']);data=json.loads(raw)
  rows=[{k:v['value'] for k,v in row.items()} for row in data['results']['bindings']]
  assert len(rows)==part['rows']<10000 and all(v['s'] in part['subjects'] for v in rows)
  receipt=m.load(checked(part['receipt_reference']))
  query='SELECT DISTINCT ?s ?p ?o WHERE { VALUES ?s { '+' '.join('<'+v+'>' for v in part['subjects'])+' } ?s ?p ?o } ORDER BY ?s ?p ?o LIMIT 10000'
  assert receipt['params']['query']==query
  triples+=rows
 assert triples==b['triples']
 for p in b['pages']:
  if 'error' in p:continue
  assert a.fields(body(p['receipt_reference'],p['body_reference']))==p['fields'];checked(p['text_reference'])
 return b
def graph_for(b,uri):
 roots=[v for v in b['triples'] if v['s']==uri]
 children={v['o'] for v in roots if v['p'] in c.LINKS}
 measures={v['o'] for v in b['triples'] if v['s'] in children and v['p']==a.DD+'hasMeasurement'}
 return a.graph_map([dict(v,root=uri) for v in b['triples'] if v['s'] in {uri}|children|measures],uri)
def parse(row,b,page):
 uri='https://w3id.org/arco/resource/'+row['index_record']['source_record_id'];g=graph_for(b,uri);root=g[uri];f=page['fields'];issues=[]
 def require(ok,reason):
  if not ok:issues.append(reason)
 kinds=root[a.DC+'type'];dates=root[a.DC+'date'];cities=root[a.DC+'coverage']
 require(len(kinds)==1 and kinds<={'dipinto','disegno','stampa','acquerello'},'object_type_review')
 dt=a.numeric_date(f.get('date'));require(dt is not None,'creation_date_review')
 require(len(dates)==1 and dt==a.numeric_date(next(iter(dates),'')),'html_graph_date_conflict')
 current=[u for u in root[a.LOC+'hasTimeIndexedTypedLocation'] if a.LOC+'CurrentPhysicalLocation' in g[u][a.LOC+'hasLocationType']]
 authorities=[x for x in row['authority_candidates'] if cities=={x['catalogue_city']} and len(current)==1 and g[current[0]][a.LOC+'hasCulturalInstituteOrSite']=={x['source_institution_uri']}]
 require(len(authorities)==1,'unique_museum_and_city_review');authority=authorities[0] if len(authorities)==1 else None
 if authority:
  names={m.norm(v) for v in authority['source_names']};mu=authority['source_institution_uri']
  require(bool(names&{m.norm(v) for v in g[mu][a.LABEL]}),'museum_label_conflict')
  require(m.norm(f.get('LUOGO DI CONSERVAZIONE')) in names,'html_museum_label_conflict')
  require(any(u.rstrip('/').endswith('/'+mu.removeprefix('https://w3id.org/arco/resource/')) for u in f.get('museum_links',[])),'html_museum_identity_conflict')
  require(' '.join(authority['catalogue_city'].split()) in ' '.join((f.get('INDIRIZZO') or '').split()),'html_museum_city_conflict')
 soup=c.BeautifulSoup(body(page['receipt_reference'],page['body_reference']),'html.parser')
 rdf_links=[v['href'] for v in soup.select('a[href]') if v.get_text(' ',strip=True)=='RDF']
 complete_links=[v['href'] for v in soup.select('a[href]') if v.get_text(' ',strip=True)=='SCHEDA COMPLETA']
 national_code=f.get('CODICE DI CATALOGO NAZIONALE')
 identifier_equal=national_code in root['https://w3id.org/arco/ontology/arco/uniqueIdentifier']
 # Lombardia notices deliberately omit the national identifier field; the
 # page's explicit RDF link provides its exact (not title-inferred) identity.
 if not national_code and '/resource/Lombardia/' in uri:identifier_equal=rdf_links==[uri]
 require(identifier_equal,'catalogue_identifier_conflict')
 kind=next(iter(kinds),'');require(f.get('OGGETTO')==kind,'html_type_or_component_review')
 rights=root[a.DC+'rights'];require(m.norm(f.get('CONDIZIONE GIURIDICA')) in {m.norm(v) for v in rights},'html_legal_status_conflict')
 allowed={'proprieta stato','proprieta ente pubblico territoriale','proprieta ente pubblico non territoriale','proprieta ente religioso cattolico','detenzione stato'}
 require(bool(rights) and all(m.norm(v) in allowed for v in rights),'legal_status_review')
 custody=' '.join(root[a.DC+'description']|rights|set().union(*(g[u][a.CORE+'specifications'] for u in current)))
 require(not re.search(r'\b(deposito|prestito|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b',m.norm(custody)),'custody_narrative_review')
 require(not any(values for key,values in root.items() if key.endswith(('/isPartOf','/hasPart'))),'component_or_ensemble_review')
 categories=sorted(v for k,vs in root.items() if k.endswith('/hasCulturalPropertyCataloguingCategory') for v in vs)
 require(not any(re.search(r'insieme|serie|complesso|scomparto|elemento|pendant',v,re.I) for v in categories),'cataloguing_category_review')
 require(len(root[a.CD+'hasDating'])==1,'multiple_creation_phases_review')
 title_values=root[a.CD+'title']|root[a.CD+'subject'];title_keys={m.norm(v) for v in title_values}
 title_keys|={m.norm(t+'. '+u) for t in root[a.CD+'title'] for u in root[a.CD+'subject']}
 require(bool(f.get('title')) and m.norm(f.get('title')) in title_keys,'html_graph_title_conflict')
 inventory=set().union(*(g[u][a.CD+'inventoryIdentifier'] for u in root[a.CD+'hasInventorySituation']))|root['https://w3id.org/arco/ontology/arco-lite/alternativeInventoryNumber']
 creator=f.get('ATTRIBUZIONI') or f.get('AMBITO CULTURALE') or None
 qs={q.strip() for label in root[a.LABEL] for q in re.findall(r'\(([^()]*(?:attribuit|bottega|scuola|ambito|cerchia|seguace|maniera|copia|copista)[^()]*)\)',label,re.I)}
 missing=sorted(q for q in qs if creator and q not in creator)
 if missing:creator+='; '+'; '.join(missing)
 measures=[]
 for coll in sorted(root[a.DD+'hasMeasurementCollection']):
  for node in sorted(g[coll][a.DD+'hasMeasurement']):
   measures.append(dict(collection=coll,node=node,types=sorted(g[node][a.DD+'hasMeasurementType']),value_nodes=sorted(g[node][a.DD+'hasValue']),literal_labels=sorted(g[node][a.LABEL]),collection_notes=sorted(g[coll][a.CORE+'note'])))
 facts=dict(title=f.get('title'),titles=sorted(title_values|{f.get('title') or ''}),source_id=row['index_record']['source_record_id'],source_url=row['index_record']['source_url'],creator_label=creator,first=dt[0] if dt else None,last=dt[1] if dt else None,date_precision=dt[2] if dt else None,date_display=f.get('date'),work_type={'dipinto':'painting','disegno':'drawing','stampa':'print','acquerello':'watercolor'}.get(kind),medium=f.get('MATERIA E TECNICA') or None,dimensions_text=f.get('MISURE') or None,inventory='; '.join(sorted(inventory)) or None,object_form=None,source_fields=f,root_fields={k:sorted(v) for k,v in sorted(root.items())},measurements=measures,authority=authority,cataloguing_categories=categories,credit_line=f.get('CONDIZIONE GIURIDICA'),metadata_license=f.get('LICENZA METADATI'),native_page_urls=[],native_metadata_urls=[uri],wikidata_ids=[],native_object_id=row['index_record']['source_record_id'])
 facts.update(native_page_urls=complete_links,page_identity=dict(national_code=national_code,rdf_links=rdf_links,exact_identity_equal=identifier_equal))
 return dict(row,source_id=facts['source_id'],facts=facts,issues=issues,state='candidate' if not issues else 'source_review',source_reference=ref(b['_path']) if '_path' in b else None,page_reference=page,retrieved_at=page['retrieved_at'])
def build(final=True):
 discovery=m.load(RUN/'five-museum-discovery-001.json.gz');by={r['number']:r for r in discovery['rows']};out=[];refs=[]
 for path in sorted((RUN/'current-002/batches').glob('*.json.gz')):
  b=validated_batch(path);refs.append(ref(path));b['_path']=path
  for n in b['numbers']:
   page=next((p for p in b.get('pages',[]) if p['number']==n),None)
   if b['source_state']!='captured' or not page or 'error' in page:out.append(dict(by[n],state='source_failure',issues=[b.get('error') or (page or {}).get('error') or 'missing_page']));continue
   out.append(parse(by[n],b,page))
 if final:assert len(out)==len(by)
 return out,refs
def main():
 dest=RUN/'native-candidates-001.json.gz';assert not dest.exists();manifest=m.load(RUN/'source-capture-002.json');assert not manifest['requests_stopped'];rows,refs=build()
 m.save(dest,dict(at=m.now(),rows=rows,dependencies=refs+[ref(RUN/'source-capture-002.json'),ref(RUN/'five-museum-discovery-001.json.gz')],parser_reference=ref(Path(__file__).resolve()),policy='Literal source facts reconstructed from verified response bodies. Detenzione Stato is custody, never ownership. Historical custody qualifiers/components remain review; dimensions await explicit value/unit nodes. No candidate is approved by parsing.'))
 print(json.dumps(dict(rows=len(rows),states=collections.Counter(r['state'] for r in rows),issues=collections.Counter(v for r in rows for v in r['issues']))),flush=True)
if __name__=='__main__':main()
