"""Imperial War Museums creator/title/source/inventory comparison; similarity is discovery only."""
import collections,difflib,functools,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-iwm-facts-20261009.py');q=module('q','museum-expansion-royal-identity-base-20261009.py');m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;IIDS=f.s.IIDS;terms=q.search_terms
STOP=set('di del della delle degli dell da de du le la les the of a an and con with il lo i gli un una e et in sul nel su saint san santa santo st portrait ritratto studio study head testa figure figura male female man woman uomo donna painting dipinto attributed attribuito bottega scuola ambito maniera esecutore copia autore notizie secolo pittore italiano'.split())
TRANSLATIONS={'madonna':'virgin','vergine':'virgin','bambino':'child','bambini':'children','ritratto':'portrait','autoritratto':'selfportrait','paesaggio':'landscape','natura':'nature','morta':'dead','fiori':'flowers','frutta':'fruit','cristo':'christ','gesu':'jesus','giuseppe':'joseph','giovanni':'john','giovannino':'john','battista':'baptist','francesco':'francis','maria':'mary','maddalena':'magdalene','antonio':'anthony','girolamo':'jerome','pietro':'peter','paolo':'paul','caterina':'catherine','famiglia':'family','sacra':'holy','sacro':'holy','annunciazione':'annunciation','adorazione':'adoration','magi':'magi','pastori':'shepherds','crocifissione':'crucifixion','deposizione':'deposition','compianto':'lamentation','fuga':'flight','egitto':'egypt','riposo':'rest','uccelli':'birds','architetture':'architecture','rovine':'ruins','santo':'saint','santa':'saint','san':'saint','st':'saint','sant':'saint','battesimo':'baptism','venere':'venus','amore':'cupid','ercole':'hercules','diana':'diana','satiro':'satyr','ninfa':'nymph','putti':'cherubs','putto':'cherub','angelo':'angel','angeli':'angels','donna':'woman','uomo':'man','cavallo':'horse','cavalli':'horses','battaglia':'battle','pastore':'shepherd','notturno':'nocturne','teste':'heads','testa':'head','fanciullo':'boy','fanciulla':'girl','vecchio':'old','vecchia':'old','giovane':'young','monaco':'monk','frate':'friar','andrea':'andrew','martirio':'martyrdom','sebastiano':'sebastian','sposalizio':'marriage','natale':'nativity','nativita':'nativity','resurrezione':'resurrection','resurrezione':'resurrection','morte':'death','incoronazione':'coronation','assunzione':'assumption','musica':'music','concerto':'concert','de':'of','con':'with','et':'and','e':'and'}
def legacy_terms(v):
 label=v['source_fields'].get('ATTRIBUZIONI') or '';out=set()
 for chunk in re.split(r'\([^)]*\)|;|:\s*esecutore|:\s*autore',label,flags=re.I):
  ts=m.norm(chunk).split()
  while ts and ts[0] in {'da','di','de','del','della','dell','degli','van','von','il','lo'}:ts=ts[1:]
  if ts and len(ts[0])>=3 and ts[0] not in STOP:out.add(ts[0])
  if 'detto' in ts:out.update(t for t in ts[ts.index('detto')+1:] if len(t)>=4 and t not in STOP)
 aliases={'schidone':['schedoni'],'fiori':['barocci'],'barbieri':['guercino'],'santi':['raphael','raffaello'],'vecellio':['titian','tiziano'],'botticelli':['filipepi'],'rigaud':['hyacinthe'],'lorrain':['gellee'],'caravaggio':['merisi'],'mulier':['tempesta'],'ponte':['bassano'],'sustermans':['suttermans'],'ricke':['ricci'],'veronese':['caliari'],'wouwerman':['wouwermans'],'brueghel':['bruegel'],'tiziano':['titian'],'raphael':['raffaello'],'salvatore':['salvator']}
 for t in list(out):out.update(aliases.get(t,[]))
 return sorted(out)
@functools.lru_cache(maxsize=150000)
def forms(title):
 out={m.norm(title)} if title else set()
 if title:out.update(m.norm(t) for t in re.split(r'[.;]|\([^)]*\)',title) if len(m.norm(t))>2)
 return frozenset(out)
@functools.lru_cache(maxsize=150000)
def words(title):return frozenset(TRANSLATIONS.get(t,t) for t in m.norm(title).split() if len(t)>2 and t not in STOP)
def invparts(value):return {m.norm(re.sub(r'^Art\.','',v,flags=re.I)).replace(' ','') for v in (value or '').split(';') if m.norm(v)}
def urls(v):
 out=set()
 for raw in [v['source_url'],v['artuk_url']]+v['native_page_urls']+v['native_metadata_urls']:
  variants={raw}
  for u in variants:
   for protocol in ['http:','https:']:
    for tail in ['','/']:out.add(re.sub(r'^https?:',protocol,u).rstrip('/')+tail)
 return sorted(out)
def params_for(rows):
 ts=sorted({t for r in rows for t in terms(r['facts'])});raw={'%'+t+'%' for t in ts}
 for r in rows:
  tsr=set(terms(r['facts']))
  raw.update('%'+t.lower()+'%' for t in re.findall(r'[^\W\d_]+',r['facts']['creator_label'] or '',re.UNICODE) if m.norm(t) in tsr)
 return dict(patterns=['%'+t+'%' for t in ts],raw_patterns=sorted(raw),title_keys=sorted({t for r in rows for rawtitle in r['facts']['titles'] for t in forms(rawtitle)}),inventories=sorted({v.strip() for r in rows for v in (r['facts']['inventory'] or '').split(';') if v.strip()}),source_urls=sorted({u for r in rows for u in urls(r['facts'])}),qids=[],native_object_ids=[],source_ids=sorted({v for r in rows for v in [r['source_id'],r['source_id'].split('/')[-1]]}))
def queries(db,p):
 state=q.queries(db,p)
 ei=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(p['source_ids'],)).fetchall()
 ci=db.execute("SELECT entity_id::text,source_record_id,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) ORDER BY entity_id,source_record_id,source_url,field_name",(p['source_ids'],)).fetchall()
 # Refresh institution scope: catch records added since the initial snapshot.
 scoped=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(IIDS,IIDS))]
 extra=sorted(({v['entity_id'] for v in ei+ci}|set(scoped))-set(state['artwork_ids']))
 state['artworks']+=db.execute('SELECT '+q.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
 state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
 state['artworks'].sort(key=lambda v:v['id']);state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state.update(native_id_hits=ei,source_record_hits=ci,scoped_ids=scoped)
 state['museum_assertions']=db.execute('SELECT artwork_id::text,institution_id::text,review_state,superseded_by::text FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND institution_id=ANY(%s::uuid[]) ORDER BY artwork_id,institution_id,id',(scoped,IIDS)).fetchall()
 return state
def comparisons(rows,state):
 by={v['id']:v for v in state['artworks']};links=collections.defaultdict(list);aw=collections.defaultdict(set);uw=collections.defaultdict(set);tw=collections.defaultdict(set);iw=collections.defaultdict(set);mw=collections.defaultdict(set)
 for v in state['links']:links[v['artwork_id']].append(v);aw[v['artist_id']].add(v['artwork_id'])
 for v in state['museum_assertions']:mw[v['institution_id']].add(v['artwork_id'])
 for v in by.values():
  mw[v['current_institution_id']].add(v['id'])
  for t in q.tokens(v['unlinked_creator_label']):uw[t].add(v['id'])
  for t in forms(v['title'])|forms(v['alternate_title']):tw[t].add(v['id'])
  for t in invparts(v['accession_number']):iw[t].add(v['id'])
 out=[]
 for row in rows:
  v=row['facts'];ts=set(terms(v));ars={x['id'] for x in state['artists'] if q.tokens(x['display_name'])&ts}|{x['artist_id'] for x in state['aliases'] if q.tokens(x['alias'])&ts};pool=set(mw[row['institution_id']])
  for ar in ars:pool|=aw[ar]
  for t in ts:pool|=uw[t]
  tt={t for raw in v['titles'] for t in forms(raw)};exact=set().union(*(tw[t] for t in tt));inv=set().union(*(iw[t] for t in invparts(v['inventory']))) if v['inventory'] else set();hits=[]
  for aid in sorted(pool|exact|inv):
   art=by[aid];ats=forms(art['title'])|forms(art['alternate_title']);score=max((difflib.SequenceMatcher(None,t,u).ratio() for t in tt for u in ats),default=0)
   lexical=max((len(words(t)&words(u))/min(len(words(t)),len(words(u))) for t in tt for u in ats if words(t) and words(u) and len(words(t)&words(u))>=min(2,len(words(t)),len(words(u)))),default=0)
   kinds=[]
   if aid in exact:kinds.append('exact_title')
   if aid in inv:kinds.append('inventory')
   if aid in pool and score>=.62:kinds.append('similar_title')
   if aid in pool and lexical>=.5:kinds.append('translated_lexical')
   if aid in pool and not ats:kinds.append('untitled')
   if kinds:hits.append(dict(art,creators=[l['display_name'] for l in links[aid]],artist_links=links[aid],hit_types=kinds,title_similarity=round(score,4),lexical_overlap=round(lexical,4),same_museum=aid in mw[row['institution_id']],same_creator=any(l['artist_id'] in ars for l in links[aid]) or bool(q.tokens(art['unlinked_creator_label'])&ts)))
  u=set(urls(v));rids={row['source_id'],row['source_id'].split('/')[-1]}
  source=[x for x in state['source_hits'] if x['source_url'] in u]+[x for x in state['external_hits'] if x['canonical_url'] in u]+[x for x in state['native_id_hits'] if x['external_id'] in rids]+[x for x in state['source_record_hits'] if x['source_record_id'] in rids]
  out.append(dict(number=row['number'],source_id=row['source_id'],creator_terms=sorted(ts),artist_ids=sorted(ars),creator_pool_ids=sorted(pool),source_hits=source,hits=hits))
 return out
def within_batch(rows):
 groups=collections.defaultdict(set)
 for row in rows:
  for value in invparts(row['facts']['inventory']):groups[('inventory',row['institution_id'],value)].add(row['number'])
  for value in {t for raw in row['facts']['titles'] for t in forms(raw)}:groups[('title',row['institution_id'],value)].add(row['number'])
 return [dict(kind=k,institution_id=i,value=v,numbers=sorted(ns)) for (k,i,v),ns in sorted(groups.items()) if len(ns)>1]
def rows():return f.rows()[0]
def params(rs):
 p=params_for(rs);p['qids']=sorted(r['source_id'] for r in rs);p['inventories']=sorted(set(p['inventories'])|{v for r in rs for v in [r['facts']['normalized_inventory'],'Art.'+r['facts']['normalized_inventory']] if v});return p
def main():
 dest=RUN/'identity-001.json.gz';assert not dest.exists();rs=rows();p=params(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');initial=m.load(RUN/'initial-scope-001.json.gz');assert f.s.snapshot(db,initial['scoped_ids'])==initial['snapshot'];state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(artworks=len(state['artwork_ids']),citations=len(cs))),flush=True);comps=comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=p,state=state,comparisons=comps,within_batch=within_batch(rs),source_reference=ref(RUN/'candidate-facts-001.json.gz'),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='Full collection scope plus bounded creator/title/inventory/source queries. Art. inventory prefix normalization is comparison-only. Network and London scopes both queried; no branch inferred from institution name. No creator/title similarity constitutes physical identity.'))
 m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=cs,read_only=True));print(json.dumps(dict(comparisons=len(comps),hits=sum(len(v['hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
