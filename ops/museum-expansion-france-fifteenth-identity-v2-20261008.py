"""Supplemental read-only identity; search aliases never rewrite catalogue facts."""
import copy, functools, importlib.util, json, re, runpy
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=module('base','museum-expansion-france-fifteenth-identity-20261008.py')
f=base.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NOTES=RUN/'working-notes-through-650-001.py';notes=runpy.run_path(str(NOTES))
CONTEXT=RUN/'paris-object-context-checked-001.json.gz';native=m.load(CONTEXT);bycontext={r['number']:r for r in native['rows']}
base.SUPPLEMENTAL_TERMS.update(notes['SUPPLEMENTAL_TERMS'])
base.TITLE_ALIASES.update({m.norm(k):v for k,v in notes['TITLE_ALIASES'].items()})
base.title_forms.cache_clear()
ANNOTATION=re.compile(r'\s*\((?:Numéro d.inventaire|Autres? n[°o]?|Ancien(?:ne)?(?: numéro)?(?: d.inventaire)?)[^)]*\)',re.I)
def inventory_parts(value):
 return [ANNOTATION.sub('',v).strip() for v in (value or '').split(';') if ANNOTATION.sub('',v).strip()]
def accession_tokens(value):
 # Numeric parenthetical subnumbers designate actual leaves and must survive.
 return {m.norm(v).replace(' ','') for v in inventory_parts(value) if m.norm(v)}
base.m.acc=accession_tokens
OLD_TITLE=base.title_forms
@functools.lru_cache(maxsize=150000)
def title_forms(title):
 out=set(OLD_TITLE(title))
 for v in list(out):
  stripped=re.sub(r'\([^)]*\)|\[[^]]*\]',' ',v);stripped=re.sub(r'\s+',' ',stripped).strip(' .,;:')
  if len(m.norm(stripped))>=3:out.add(stripped)
  core=re.sub(r"^portrait(?: présumé)?(?: en buste)?\s+(?:de |du |d[’'])",'',stripped,flags=re.I)
  if len(m.norm(core))>=3:out.add(core)
  out.update(base.TITLE_ALIASES.get(m.norm(stripped),[]))
 return tuple(sorted(out))
base.title_forms=title_forms
OLD_TERMS=base.terms
def terms(v):
 out=set(OLD_TERMS(v))
 out.update(v.get('comparison_creator_terms',[]))
 return sorted(out)
base.terms=terms;base.i.search_terms=terms
RELATED={164:['969.004.001'],171:['1900,1231.997'],176:['G988.18.50'],196:['2002.157.6'],218:['1920.1203','1993.1002'],222:['EST251'],223:['EST253'],257:['62.650.139','1924.724'],313:[],319:['896.1.112'],321:['2011.0.259'],330:['RF 37078'],467:['J247'],480:['J185'],482:['85.SA.50','E00029'],492:['1960.6.12'],642:['E.Cl. 12024'],644:['CL 53','DS 755','E.Cl. 20623','E.Cl. 20624','E.Cl. 20385 a','E.Cl. 20385 b','E.Cl. 20610'],645:['CL 218','E.Cl. 218','CL 218 C']}
for n in [635,646,647,648]:RELATED[n]=['DS 1445','CL 127']
def inventory_forms(row):
 out=set(inventory_parts(row['facts']['inventory']));ctx=bycontext.get(row['number'])
 if ctx:
  out.add(ctx['native_inventory'])
  # Only inventory-like inscriptions, not arbitrary measurements or dates.
  text=ctx['literal_detail_text']
  if '\nMarques, inscriptions, poinçons\n:\n' in text:
   marks=text.split('\nMarques, inscriptions, poinçons\n:\n',1)[1]
   for end in ['\nDescription iconographique','\nCommentaire historique','\nThèmes /','\nInstitution','\nMode d’acquisition','\nMode d\'acquisition']:
    marks=marks.split(end,1)[0]
   out.update(x.group(0).strip() for x in re.finditer(r'(?<![\w])(?:J|D|E|F|S|INV)[ .-]*\d{1,}(?:[./-]\d+)*\b',marks,flags=re.I))
 for v in list(out):out.update([re.sub(r'\s+','',v),m.norm(v).replace(' ','').upper()])
 return sorted(out)
def related_forms(row):
 out=set(RELATED.get(row['number'],[]))
 if row['number']==208:
  out.update(re.findall(r'\(([^)]+)\)',row['facts']['source_fields']['Historique']))
 for v in list(out):out.update([re.sub(r'\s+','',v),m.norm(v).replace(' ','').upper()])
 return sorted(out)
def augmented_rows(rows):
 out=copy.deepcopy(rows)
 for r in out:
  v=r['facts'];n=r['number'];ctx=bycontext.get(n)
  if ctx:v['native_page_urls']=sorted(set(v['native_page_urls'])|{ctx['source_url'],ctx['final_url']})
  v['titles']=sorted(set(v['titles'])|set(notes['TITLE_ADDITIONS'].get(n,[])))
  v['comparison_creator_terms']=['batoni','camuccini','doyen'] if n==214 else []
  r['comparison_only']=dict(original_inventory=v['inventory'],object_inventory_forms=inventory_forms(r),related_inventory_forms=related_forms(r),extra_titles=notes['TITLE_ADDITIONS'].get(n,[]),policy='Object aliases and related-object inventories remain separate. Search leads alone neither merge objects nor prove different physical units.')
 return out
def params_for(rows):
 p=base.params_for(rows)
 p['inventories']=sorted(set(p['inventories'])|{v for r in rows for v in inventory_forms(r)+related_forms(r)})
 return p
STOP=set('de du des d le la les l un une et en au aux a the of and in portrait study etude dessin illustration pour dans monsieur madame m mme'.split())
@functools.lru_cache(maxsize=150000)
def significant(title):return frozenset(v for v in m.norm(title).split() if len(v)>2 and v not in STOP)
def lexical(f,a):
 aa=[significant(t) for raw in f['titles'] for t in title_forms(raw)];bb=[significant(t) for k in ['title','alternate_title'] for t in title_forms(a.get(k))]
 return max((len(x&y)/min(len(x),len(y)) for x in aa for y in bb if x and y and len(x&y)>=min(2,len(x),len(y))),default=0)
def citation_inventories(v):
 if isinstance(v,dict):
  for k,value in v.items():
   if isinstance(value,str) and (k in ['inventory','accession','accession_number','Numero_inventaire','inventory_number'] or k.lower().endswith('inventory')):yield value
   elif isinstance(value,(dict,list)):yield from citation_inventories(value)
 elif isinstance(v,list):
  for value in v:
   if isinstance(value,(dict,list)):yield from citation_inventories(value)
def comparisons(rows,state,citations):
 out=base.comparisons(rows,state);by={a['id']:a for a in state['artworks']};links={};invindex={};citationindex={}
 for l in state['links']:links.setdefault(l['artwork_id'],[]).append(l)
 for a in state['artworks']:
  for token in accession_tokens(a['accession_number']):invindex.setdefault(token,set()).add(a['id'])
 wanted={t for r in rows for v in inventory_forms(r)+related_forms(r) for t in accession_tokens(v)}
 for c in citations:
  try:e=json.loads(c['evidence_note'])
  except (ValueError,TypeError):continue
  for raw in citation_inventories(e):
   for token in accession_tokens(raw)&wanted:
    citationindex.setdefault(token,{}).setdefault(c['entity_id'],dict(citation_id=c['id'],source_url=c['source_url'],inventory_literal=raw))
 def detail(aid,**kw):
  a=by[aid];return dict(a,creators=[l['display_name'] for l in links.get(aid,[])],artist_links=links.get(aid,[]),**kw)
 for r,c in zip(rows,out):
  existing={a['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for a in c[k]}
  c['lexical_hits']=[detail(aid,lexical_overlap=round(lexical(r['facts'],by[aid]),4)) for aid in c['creator_pool_ids'] if aid not in existing and lexical(r['facts'],by[aid])>=.60]
  for kind,forms in [('object_alias',inventory_forms(r)),('related_inventory',related_forms(r))]:
   matched={}
   for raw in forms:
    for token in accession_tokens(raw):
     for aid in invindex.get(token,set()):matched.setdefault(aid,[]).append(dict(kind='database_accession',search_alias=raw))
     for aid,e in citationindex.get(token,{}).items():matched.setdefault(aid,[]).append(dict(kind='citation_inventory',search_alias=raw,**e))
   c[kind+'_hits']=[detail(aid,evidence=ev) for aid,ev in sorted(matched.items())]
  c['comparison_only_inputs']=r['comparison_only']
 return out
def within_batch(rows):
 inv={};titles={}
 for r in rows:
  for t in accession_tokens(r['facts']['inventory']):inv.setdefault((r['institution_id'],t),set()).add(r['number'])
  for raw in r['facts']['titles']:
   for t in title_forms(raw):titles.setdefault((r['institution_id'],m.norm(t)),set()).add(r['number'])
 return dict(inventory_groups=[dict(institution_id=i,inventory_key=k,numbers=sorted(ns)) for (i,k),ns in sorted(inv.items()) if len(ns)>1],title_groups=[dict(institution_id=i,title_key=k,numbers=sorted(ns)) for (i,k),ns in sorted(titles.items()) if len(ns)>1])
def main():
 dest=RUN/'native-identity-002.json.gz';cdest=RUN/'identity-citations-002.json.gz';bdest=RUN/'within-batch-identity-002.json.gz';assert not any(p.exists() for p in [dest,cdest,bdest])
 checkpoint=RUN/'review-progress-checkpoint-003.json';cp=m.load(checkpoint);assert ref(checkpoint)['sha256']=='46ab50784308bc81329c5b5a643f70332e58eaac04f6a4dfe628b734b0e39582'
 for dep in cp['references']:checked(dep)
 candidate=RUN/'native-candidates-001.json.gz';rows=augmented_rows(m.load(candidate)['rows']);p=params_for(rows)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  initial=m.load(RUN/'initial-scope-001.json.gz');assert base.snapshot(db,initial['scoped_ids'])==initial['snapshot']
  state=base.queries(db,p)
  citations=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(citations))),flush=True)
 comps=comparisons(rows,state,citations)
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(base.__file__).resolve()),notes_reference=ref(NOTES),context_reference=ref(CONTEXT),checkpoint_reference=ref(checkpoint),params=p,state=state,comparisons=comps,read_only=True,policy='Titles and inventory variants are comparison-only. Literal original records unchanged. Historical and related inventory hits require physical identity review. Citation lookup is restricted to artworks returned by creator/title/inventory/source and selected museum scopes.'))
 m.save(cdest,dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=citations,read_only=True))
 m.save(bdest,dict(at=m.now(),candidate_reference=ref(candidate),identity_reference=ref(dest),**within_batch(rows)))
 print(json.dumps(dict(identity=ref(dest),comparisons=len(comps),hits={k:sum(len(c[k]) for c in comps) for k in ['native_url_hits','lexical_hits','object_alias_hits','related_inventory_hits']},database_writes=0)),flush=True)
if __name__=='__main__':main()
