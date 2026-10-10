"""Supplemental read-only identity: pinned native URLs, labels, titles and old inventories."""
import copy,functools,importlib.util,json,re,runpy
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=module('identity_base','museum-expansion-france-fourteenth-identity-20261008.py')
f=base.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NOTES_PATH=RUN/'working-notes-through-605-003.py';notes=runpy.run_path(str(NOTES_PATH))
CONTEXT=RUN/'paris-object-context-checked-003.json.gz';contexts=m.load(CONTEXT);bycontext={v['number']:v for v in contexts['rows']}
for sid,ts in notes['SUPPLEMENTAL_TERMS'].items():base.SUPPLEMENTAL_TERMS[sid]=sorted(set(base.SUPPLEMENTAL_TERMS.get(sid,[]))|set(ts))
base.TITLE_ALIASES.update({m.norm(k):v for k,v in notes['TITLE_ALIASES'].items()})
base.TITLE_ALIASES.update({m.norm(k):v for k,v in {
    'Victor Hugo':['Portrait of Victor Hugo','Portrait de Victor Hugo'],
    'Portrait du général Hugo':['Le Général Hugo','General Hugo'],
    'Boppart':['Boppard'],
    'La Mort de Messaline de Louis Boulanger':['La Mort de Messaline'],
    'La bénédiction':['The Blessing'],
    'Le Sylphe':['The Sylph'],
    'Lénore ou le retour de l’armée':['Lenore','The Return of the Army'],
    'Saint Brandan':['Saint Brendan','St Brendan'],
}.items()})
old_terms=base.terms
def terms(v):
    out=set(old_terms(v))
    if v.get('comparison_qualified_label'):
        z=dict(v,creator_label=v['comparison_qualified_label']);out.update(old_terms(z))
    for t in list(out):
        out.update({'leclerc':['clerc'],'poittevin':['poitevin','poidevin'],'poitevin':['poittevin','poidevin'],'connell':['miethe'],'willaumez':['bouet'],'regereau':['regereaux'],'david':['david']}.get(t,[]))
    return sorted(out)
base.terms=terms;base.i.search_terms=terms
old_title_forms=base.title_forms
@functools.lru_cache(maxsize=150000)
def title_forms(title):
    forms=set(old_title_forms(title))
    for raw in list(forms):
        stripped=re.sub(r'\[[^]]*\]',' ',raw)
        stripped=re.sub(r'\([^)]*\)',' ',stripped)
        stripped=re.sub(r'\s+',' ',stripped).strip(' \"\'“”.,:;')
        if len(m.norm(stripped))>=3:forms.add(stripped)
        core=re.sub(r"^portrait(?: présumé)?(?: en buste)?\s+(?:de |du |d[’'])",'',stripped,flags=re.I)
        if len(m.norm(core))>=3:forms.add(core)
        if '. ' in stripped:
            first=stripped.split('. ',1)[0]
            if len(m.norm(first))>=5:forms.add(first)
        for key in [m.norm(raw),m.norm(stripped),m.norm(core)]:forms.update(base.TITLE_ALIASES.get(key,[]))
    return tuple(sorted(forms))
base.title_forms=title_forms
# Comparison-only variants, never corrections to stored inventory strings.
MANUAL_INVENTORIES={249:['1909.18'],288:['1909.19'],317:['S 3331','S3331','E 19601','E19601'],390:['S 3332','S3332'],395:['CSR AG 28','CSR AG28','CSR AG028'],499:['441.1'],511:['423','INV. 423','652','Cat. 652']}
def inventory_forms(row):
    out={s.split('(')[0].strip() for s in row['facts']['inventory'].split(';') if s.strip()}
    n=row['number'];ctx=bycontext.get(n)
    if ctx:
        out.add(ctx['native_inventory'])
        # Delimited accession-like inscriptions only; measurements and dates
        # are not mined from arbitrary narrative text as inventory evidence.
        d=ctx['literal_detail_text']
        if '\nMarques, inscriptions, poinçons\n:\n' in d:
            marks=d.split('\nMarques, inscriptions, poinçons\n:\n',1)[1]
            for end in ['\nDescription iconographique','\nCommentaire historique','\nThèmes /','\nInstitution']:
                marks=marks.split(end,1)[0]
            for match in re.finditer(r'(?<![\w])(?:MVHP[A-Z]*[. -]*[A-Z]?[-. ]*)?\b(?:D|E|S|INV)[ .-]*\d{2,}(?:[./-]\d+)*\b|\bMVHP[A-Z]+\d+\b|\bCSR[ .]*[A-Z]+[ .]*\d+\b',marks,flags=re.I):out.add(match.group(0).strip())
    out.update(MANUAL_INVENTORIES.get(n,[]))
    for value in list(out):out.update([re.sub(r'\s+','',value),base.i.compact(value).upper()])
    return sorted(v for v in out if v)
def augmented_rows(rows):
    out=copy.deepcopy(rows)
    for row in out:
        v=row['facts'];n=row['number'];urls=set(v['native_page_urls'])
        literal=v['source_fields'].get('Lien_site_associe')
        if literal:urls.add(literal.strip())
        if n in bycontext:urls.update([bycontext[n]['source_url'],bycontext[n]['final_url']])
        v['native_page_urls']=sorted(urls)
        v['inventory']=' ; '.join(inventory_forms(row))
        v['comparison_qualified_label']=notes['NATIVE_QUALIFIED'].get(n,[None])[0]
        row['comparison_only']=dict(native_context_reference=ref(CONTEXT) if n in bycontext else None,original_inventory=rows[n-1]['facts']['inventory'],historical_inventory_forms=inventory_forms(rows[n-1]),policy='Search variants only; literal frozen candidate facts are unchanged.')
    return out
def params_for(rows):return base.params_for(augmented_rows(rows))
def queries(db,p):
    state=base.queries(db,p)
    extra=sorted(set(notes['EXTRA_COMPARATOR_IDS'])-set(state['artwork_ids']))
    if extra:
        state['artworks']+=db.execute('SELECT '+base.i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
        state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
    state['artworks'].sort(key=lambda a:a['id']);state['links'].sort(key=lambda a:(a['artwork_id'],a['artist_id']));state['artwork_ids']=sorted(a['id'] for a in state['artworks'])
    assert set(extra)<=set(state['artwork_ids'])
    return state
STOP=set('de du des d le la les l un une et en au aux a the of and in portrait study etude dessin illustration pour dans edition livre monsieur madame m mme'.split())
@functools.lru_cache(maxsize=150000)
def significant(title):return frozenset(t for t in m.norm(title or '').split() if t not in STOP and len(t)>2)
def lexical_overlap(facts,art):
    aa=[significant(t) for raw in facts['titles'] for t in title_forms(raw)]
    bb=[significant(t) for k in ['title','alternate_title'] for t in title_forms(art.get(k))]
    return max((len(a&b)/min(len(a),len(b)) for a in aa for b in bb if a and b and len(a&b)>=min(2,len(a),len(b))),default=0)
def comparisons(rows,state):
    augmented=augmented_rows(rows);out=base.comparisons(augmented,state);by={a['id']:a for a in state['artworks']};links={}
    for a in state['links']:links.setdefault(a['artwork_id'],[]).append(a)
    for row,c in zip(augmented,out):
        existing={a['id'] for a in c['leads']+c['exact_title_hits']+c['inventory_hits']+c['untitled_creator_hits']};hits=[]
        for aid in c['creator_pool_ids']:
            if aid in existing:continue
            art=by[aid];score=lexical_overlap(row['facts'],art)
            if score>=.60:hits.append(dict(art,creators=[a['display_name'] for a in links.get(aid,[])],artist_links=links.get(aid,[]),lexical_overlap=round(score,4)))
        c['lexical_hits']=hits
        c['comparison_only_inputs']=row['comparison_only']
    return out
def within_batch(rows):
    groups={};titlegroups={}
    for row in rows:
        v=row['facts'];n=row['number']
        for inv in m.acc(' ; '.join(inventory_forms(row))):groups.setdefault((row['institution_id'],inv),set()).add(n)
        for title in title_forms(v['title']):titlegroups.setdefault((row['institution_id'],m.norm(title)),set()).add(n)
    inv=[dict(institution_id=k[0],inventory_key=k[1],numbers=sorted(ns)) for k,ns in sorted(groups.items()) if len(ns)>1]
    titles=[dict(institution_id=k[0],title_key=k[1],numbers=sorted(ns)) for k,ns in sorted(titlegroups.items()) if len(ns)>1]
    return dict(inventory_groups=inv,title_groups=titles,policy='Discovery groups, not merge decisions. Same-title editions may be different works; accession-only separation does not prove independent physical units.')
def main():
    candidate=RUN/'native-candidates-001.json.gz';dest=RUN/'native-identity-002.json.gz';citesdest=RUN/'identity-citations-002.json.gz';batchdest=RUN/'within-batch-identity-002.json.gz'
    assert not any(p.exists() for p in [dest,citesdest,batchdest])
    checkpoint=RUN/'review-progress-checkpoint-003.json';cp=m.load(checkpoint)
    assert ref(checkpoint)['sha256']=='6dae01993cdf04732637aa0680daab72316d8bc057cc9d79b49c50c553b8c549'
    for dep in cp['references']:checked(dep)
    for dep in contexts['dependencies']:checked(dep)
    x=m.load(candidate)
    for dep in [x['parser_reference']]+x['dependencies']:checked(dep)
    rows=x['rows'];p=params_for(rows)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        initial=m.load(RUN/'initial-scope-001.json.gz');assert base.snapshot(db,initial['scoped_ids'])==initial['snapshot']
        state=queries(db,p)
        cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True)
    cmp=comparisons(rows,state)
    m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(base.__file__).resolve()),underlying_query_reference=ref(Path(base.i.__file__).resolve()),notes_reference=ref(NOTES_PATH),context_reference=ref(CONTEXT),checkpoint_reference=ref(checkpoint),params=p,state=state,comparisons=cmp,comparison_only_inputs=[r['comparison_only'] for r in augmented_rows(rows)],read_only=True,policy='Search-only augmentation preserves all frozen literal source facts. Scores are discovery leads, not physical identity approvals.'))
    m.save(citesdest,dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=cs,read_only=True))
    m.save(batchdest,dict(at=m.now(),candidate_reference=ref(candidate),identity_reference=ref(dest),**within_batch(rows)))
    print(json.dumps(dict(identity=ref(dest),comparisons=len(cmp),lexical_hits=sum(len(v['lexical_hits']) for v in cmp),native_hits=sum(len(v['native_url_hits']) for v in cmp),database_writes=0)),flush=True)
if __name__=='__main__':main()
