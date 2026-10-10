#!/usr/bin/env python3
"""Read-only national-catalogue identity scope with surname-first creator labels."""
import difflib,importlib.util,json,re
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('f','museum-expansion-france-tenth-facts-20261008.py');i=module('i','museum-expansion-yale-identity-20261007.py');prior=module('prior','museum-expansion-princeton-followup-apply-20261008.py')
m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;TARGETS=m.load(f.n.DISCOVERY)['targets'];IIDS=sorted(r['id'] for r in TARGETS);i.RUN=RUN;i.IID=IIDS[0]
SUPPLEMENTAL_TERMS={'00130004257': ['aldegrever', 'solis'], '00000067140': ['orschwiller'], '00130025146': ['buonarroti', 'michelangelo'], '00130130828': ['pippi'], '00130130823': ['titian', 'tiziano'], '00000065670': ['kanda'], '00000065689': ['kubin'], '00130068060': ['delaune'], '03610002858': ['gericault', 'géricault'], '04220060050': ['delacroix'], '04220060019': ['bertrand', 'delatre', 'letourneau', 'martin'], '06610000039': ['hondecooter'], '04220059995': ['delatre', 'eaton', 'eatton', 'jacque', 'trimolet'], '04220059994': ['charlet', 'delatre', 'remongin', 'remougin'], '04220059996': ['campagnola', 'delatre', 'dorival', 'gemier', 'mercadier'], '04220059997': ['delatre', 'henriques', 'rodrigues'], '04220059999': ['delatre', 'legrand'], '04220060003': ['bertrand', 'delatre'], '04220060004': ['delatre', 'peske', 'peské'], '04220060005': ['delatre', 'morin'], '04220060006': ['delatre', 'tuyll'], '04220060012': ['delatre', 'janniot', 'jeanniot'], '04220060013': ['delatre', 'robida'], '04220060014': ['delatre', 'luigini'], '04220060015': ['carre', 'delatre'], '04220060016': ['delatre', 'maufra'], '04220060018': ['delatre', 'rudinoff'], '04220060021': ['delatre', 'forton'], '04220060024': ['bucci', 'delatre'], '04220060025': ['delatre', 'egusquiza'], '04220060026': ['delatre', 'paillard'], '04220060028': ['delatre', 'viala'], '04220060029': ['berton', 'delatre'], '04220060030': ['colin', 'delatre']}
SUPPLEMENTAL_TERMS.update({'00000065698': ['arapov'], '00130004756': ['durer', 'pollaiuolo'], '00130101352': ['altdorfer'], '00130021003': ['callot'], '00130041715': ['merian', 'tempesta', 'stimmer'], '00130066766': ['schongauer'], '00130101381': ['vico', 'raimondi', 'raphael'], 'M0094000505': ['sickert', 'sikert']})
# Additional source-note maker variants are comparison terms only.
def terms(facts):
    out=set()
    for label in facts['identity_creator_labels']:
        raw=re.sub(r'\([^)]*\)','',label);ts=m.norm(raw).split()
        if not ts or ts[0] in ['anonyme','inconnu','manufacture','maison','faiencerie','atelier','ecole']:continue
        if ts[0]=='imprimerie':ts=ts[1:]
        if not ts:continue
        while len(ts)>1 and ts[0] in ['le','la','van','de','d','des','der','du','von']:ts=ts[1:]
        first=ts[0]
        if len(first)>=3:out.add(first)
        if first=='abbeville':out.add('sanson')
        if first=='nilouss':out.update(['nilus','nilous','nilouss'])
        if first=='caruelle':out.add('aligny')
        if first=='berthelemy':out.add('barthelemy')
        if first=='nevelson':out.add('berliawsky')
        if first=='schidone':out.add('schedoni')
        if first=='janssens':out.add('dietrich')
        if first=='hondecoeter':out.add('hondecooter')
        if first=='del' and m.norm(raw).startswith('del marle '):out.update(['marle','delmarle'])
    if facts['source_fields']['Code_Museofile']=='M0889':
        for label in facts['identity_creator_labels']:
            out.update(t for t in m.norm(re.sub(r'\([^)]*\)','',label)).split() if len(t)>=4 and t not in ['actif','anonyme'])
    out.update(SUPPLEMENTAL_TERMS.get(facts['source_id'],[]))
    return sorted(out)
i.search_terms=terms

def title_forms(title):
    forms={title} if title else set()
    if title and re.search(r'\((?:titre|translitt)',title,re.I):
        forms.update(v.strip(' ;,') for v in re.split(r'\([^)]*\)|\s{2,}',title) if len(m.norm(v))>=3)
    return sorted(forms)
def compare_score(facts,art):
    aa={v for t in facts['titles'] for v in title_forms(t)}
    bb={v for k in ['title','alternate_title'] for v in title_forms(art.get(k))}
    return max((difflib.SequenceMatcher(None,m.norm(t),m.norm(u)).ratio() for t in aa for u in bb),default=0)

def params_for(rows):
    p=i.params_for(rows);p['native_object_ids']=[];p['joconde_ids']=sorted(r['source_id'] for r in rows)
    # Legacy normalized names sometimes retain accents. Include literal accented
    # source spellings as search patterns, then compare normalized tokens.
    raw=set(p['raw_patterns'])
    for row in rows:
        ts=set(terms(row['facts']))
        for token in re.findall(r"[^\W\d_]+",row['facts']['creator_label'] or '',re.UNICODE):
            if m.norm(token) in ts:raw.add('%'+token.lower()+'%')
    p['raw_patterns']=sorted(raw)
    variants={v for r in rows for v in [r['facts']['inventory']]+[s.split('(')[0].strip() for s in r['facts']['inventory'].split(';')] if v};p['inventories']=sorted(set(p['inventories'])|variants);p['title_keys']=sorted(set(p['title_keys'])|{m.norm(t) for r in rows for raw in r['facts']['titles'] for t in title_forms(raw)});return p
def queries(db,p):
    state=i.queries(db,p)
    native=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%joconde%%' ORDER BY entity_id,scheme,external_id",(p['joconde_ids'],)).fetchall()
    cites=db.execute("SELECT entity_id::text,source_record_id,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) ORDER BY entity_id,source_record_id,source_url,field_name",(p['joconde_ids'],)).fetchall()
    extra=sorted(({v['entity_id'] for v in native+cites}|set(m.load(RUN/'initial-scope-001.json.gz')['scoped_ids']))-set(state['artwork_ids']))
    state['artworks']+=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
    state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
    state['artworks'].sort(key=lambda v:v['id']);state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state.update(native_scheme_hits=native,source_record_hits=cites);return state
def snapshot(db,ids):
    out=prior.prior.base.snapshot(db,ids,IIDS[0]);out.pop('museum');out['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE id=ANY(%s::uuid[]) ORDER BY id',(IIDS,))]
    mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return {iid:prior.prior.base.counts(db,iid) for iid in IIDS}
def initial():
    dest=RUN/'initial-scope-001.json.gz';assert not dest.exists()
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(IIDS,IIDS))];state=snapshot(db,ids);cs=counts(db)
    m.save(dest,dict(at=m.now(),scoped_ids=ids,snapshot=state,counts=cs,read_only=True));print(json.dumps(dict(initial_records=len(ids),counts=cs)),flush=True)
def comparisons(rows,state):
    # Same evidence dimensions as the earlier comparator; index the bounded
    # scope once to avoid repeatedly scanning it for each selected source row.
    by={a['id']:a for a in state['artworks']};links={};artist_works={};word_works={};title_works={};inv_works={}
    for link in state['links']:links.setdefault(link['artwork_id'],[]).append(link);artist_works.setdefault(link['artist_id'],set()).add(link['artwork_id'])
    for a in state['artworks']:
        for word in i.tokens(a['unlinked_creator_label']):word_works.setdefault(word,set()).add(a['id'])

        for t in title_forms(a['title']):title_works.setdefault(m.norm(t),set()).add(a['id'])
        for token in m.acc(a['accession_number']):inv_works.setdefault(token,set()).add(a['id'])
    initial=m.load(RUN/'initial-scope-001.json.gz');oldscope=set(initial['scoped_ids']);museum_works={iid:set() for iid in IIDS};out=[]
    for a in initial['snapshot']['artworks']:
        if a['current_institution_id'] in museum_works:museum_works[a['current_institution_id']].add(a['id'])
    for h in initial['snapshot']['assertions']:
        if h['institution_id'] in museum_works:museum_works[h['institution_id']].add(h['artwork_id'])
    for row in rows:
        v=row['facts'];ts=set(terms(v));ids={a['id'] for a in state['artists'] if i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in state['aliases'] if i.tokens(a['alias'])&ts};pool=set()
        for aid in ids:pool|=artist_works.get(aid,set())
        for word in ts:pool|=word_works.get(word,set())
        pool|=museum_works[row['institution_id']]
        exact=set();invs=set()
        for title in {t for raw in v['titles'] for t in title_forms(raw)}:exact|=title_works.get(m.norm(title),set())
        for inv in m.acc(v['inventory']):invs|=inv_works.get(inv,set())
        context={}
        for aid in sorted(pool|exact|invs):
            a=by[aid];score=compare_score(v,a);context[aid]=dict(a,creators=[x['display_name'] for x in links.get(aid,[])],artist_links=links.get(aid,[]),title_similarity=round(score,4))
        urls={u.replace('http:','https:').rstrip('/') for u in [v['source_url']]+v['native_page_urls']+v['native_metadata_urls']}
        native=[a for a in state['source_hits'] if a['source_url'].replace('http:','https:').rstrip('/') in urls]+[a for a in state['external_hits'] if a['canonical_url'] and a['canonical_url'].replace('http:','https:').rstrip('/') in urls]
        out.append(dict(source_id=row['source_id'],creator_terms=sorted(ts),artist_ids=sorted(ids),creator_pool_ids=sorted(pool),untitled_creator_hits=[context[a] for a in sorted(pool) if not by[a]['title'] and not by[a]['alternate_title']],leads=sorted([context[a] for a in sorted(pool)],key=lambda a:a['title_similarity'],reverse=True)[:12],exact_title_hits=[context[a] for a in sorted(exact)],inventory_hits=[dict(context[a],relevant=(a in pool or a in oldscope or by[a]['current_institution_id']==row['institution_id'])) for a in sorted(invs)],native_url_hits=native,native_scheme_hits=[a for a in state['native_scheme_hits'] if a['external_id']==row['source_id']],source_record_hits=[a for a in state['source_record_hits'] if a['source_record_id']==row['source_id']]))
    return out
def main():
    if not (RUN/'initial-scope-001.json.gz').exists():initial()
    candidate=RUN/'native-candidates-001.json.gz';dest=RUN/'native-identity-002.json.gz';assert not dest.exists();x=m.load(candidate)
    for dep in [x['parser_reference']]+x['dependencies']:checked(dep)
    rows=x['rows'];params=params_for(rows)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');state=queries(db,params);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True)
    cmp=comparisons(rows,state);m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(i.__file__).resolve()),params=params,state=state,comparisons=cmp,read_only=True))
    m.save(RUN/'identity-citations-002.json.gz',dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=cs,read_only=True));print('Identity comparisons complete',flush=True)
if __name__=='__main__':main()
