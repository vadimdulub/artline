"""Read-only former-maker, translated-title and historical collection comparisons."""
import copy,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-italy-fourth-identity-v2-20261008.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i)
m=i.m;RUN=i.RUN;ref=i.ref;checked=i.checked
WORKING=RUN/'source-editorial-working-001.json';EXTRA={int(k):v for k,v in m.load(WORKING)['extra_creator_terms'].items()}
EXTRA.update({450:['aleni','campi'],451:['melone','meloni'],453:['sesto','bernazzano'],454:['campi'],455:['parmigianino','mazzola'],459:['romanino','romani'],460:['romanino','romani'],461:['romanino','romani'],462:['romanino','romani'],463:['greco','theotokopoulos','theotokopulos'],464:['pitati','bonifacio','vecellio'],467:['cantarini','creti'],470:['gimignani','trevisani','romanelli','brandi','cortona','berrettini'],471:['machiavelli','macchiavelli'],472:['lippi','baldassarre','biagio','boccati'],473:['parenzano','parentino','mantegna'],474:['parenzano','parentino','mantegna'],475:['giorgio','pacchiarotto','neroccio','botticini','botticelli','filipepi','martini','ciampanti','montalcino'],476:['botticelli','filipepi','lippi','botticini','parenzano','parentino','bartolomeo','giovanni','garbo','raffaellino'],477:['lippi','rosselli','cosimo','membrini','lathrop'],478:['perugino','francia','brea','membrini','lathrop'],479:['frediani','buonvisi','lippi','garbo'],480:['ciampanti','stratonice'],481:['zacchia','ezechia'],483:['passignano','cresti'],485:['zacchia','ezechia','marti','malatesta'],486:['brandimarte','sarto'],487:['paolino','bartolomeo','fiorentini'],489:['agostino']})
FLORENCE=[v['id'] for v in m.load(RUN/'florence-inventory-scope-search-001.json')['rows'] if v['id']!='930bdb5d-cfb7-5748-8110-e30826726357']+['3f6055b6-e076-5162-a7f1-3bcd5ec7593d','2b1cab09-ca5e-59b2-88f7-ff8103593cee']
CENACOLO='68c4a112-471f-538b-ba93-e45f76fcda8b';GUINIGI='9f564ccc-072e-59fd-8aa8-eb1d96eda269';MANSI='5765387c-17a1-51f2-a015-7f1f8eab6a72';RELATEDMAP={CENACOLO:FLORENCE,GUINIGI:FLORENCE+[MANSI]};RELATED=sorted(set().union(*map(set,RELATEDMAP.values())))
original_terms=i.terms;original_queries=i.queries;original_comparisons=i.comparisons;original_invparts=i.invparts

def invparts(value):
 out=set(original_invparts(value))
 for raw in (value or '').split(';'):
  match=re.fullmatch(r'\s*(?:inv(?:entario)?\.?\s*)?1890\s*(?:[,/:.-]\s*|\s+(?:n\.?\s*)?)(\d{1,6})\s*',raw,re.I)
  if match:out.add('florence1890:'+str(int(match[1])))
 return out

def rows():
 out=[]
 for original in m.load(RUN/'native-candidates-002.json.gz')['rows']:
  if original['state']!='candidate':continue
  r=copy.deepcopy(original);v=r['facts'];v['comparison_extra_terms']=EXTRA.get(r['number'],[])
  # Comparison-only mechanical title aliases, never catalogue replacements.
  aliases=[]
  for title in v['titles']:
   words=[i.TRANSLATIONS.get(t,t) for t in m.norm(title).split()];alias=' '.join(words);aliases+=[alias,alias.replace(' with ',' and '),alias.replace('virgin','madonna'),alias.replace('virgin','madonna').replace(' with ',' and ')]
  v['titles']=sorted(set(v['titles'])|set(aliases));out.append(r)
 return out

def terms(v):return sorted(set(original_terms(v))|set(v.get('comparison_extra_terms',[])))

def queries(db,p):
 state=original_queries(db,p);related=db.execute('SELECT DISTINCT id::text,institution_id::text FROM (SELECT id,current_institution_id institution_id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id,institution_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[])) x ORDER BY id,institution_id',(RELATED,RELATED)).fetchall();ids=sorted({v['id'] for v in related});extra=sorted(set(ids)-set(state['artwork_ids']))
 state['artworks']+=db.execute('SELECT '+i.q.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall();state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
 state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['artworks'].sort(key=lambda v:v['id']);state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']))
 state['related_collection_scope']=dict(institution_ids=RELATED,artwork_ids=ids,membership=related,comparison_map=RELATEDMAP,institutions=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(RELATED,))],policy='Comparison only: documented transfers among historic Florence collections/SanSalvi and Pitti/Lucca. Mansi and Guinigi share historical museum inventories. Institutions are not merged; no additional holdings asserted.')
 return state

def comparisons(rs,state):
 scoped=dict(state);scoped['museum_assertions']=state['museum_assertions']+[dict(artwork_id=x['id'],institution_id=parent,comparison_only=True) for parent,children in RELATEDMAP.items() for x in state['related_collection_scope']['membership'] if x['institution_id'] in children]
 return original_comparisons(rs,scoped)
i.terms=terms;i.queries=queries;i.comparisons=comparisons;i.invparts=invparts

def main():
 dest=RUN/'selected-identity-003.json.gz';assert not dest.exists();rs=rows();params=i.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';state=queries(db,params)
  citations=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comps=comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=params,state=state,comparisons=comps,within_batch=i.within_batch(rs),script_reference=ref(Path(__file__).resolve()),dependencies=[ref(WORKING),ref(RUN/'native-identity-002.json.gz'),ref(RUN/'florence-inventory-scope-search-001.json'),ref(RUN/'related-institution-search-001.json'),ref(RUN/'lucca-inventory-scope-search-001.json')],read_only=True,policy='Comparison-only historical maker terms, mechanical translated title aliases and inventory canonicalization. Neither similar names nor shared historical collections establish same-object identity. Full actual source context and support/date/version checks still required.'))
 m.save(RUN/'selected-citations-003.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=citations,read_only=True));print(json.dumps(dict(selected=len(rs),scope=len(state['artwork_ids']),related_scope=len(state['related_collection_scope']['artwork_ids']),hits=sum(len(v['hits']) for v in comps),source_hits=sum(len(v['source_hits']) for v in comps))))
if __name__=='__main__':main()
