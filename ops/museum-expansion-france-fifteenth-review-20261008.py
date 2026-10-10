"""Release resolved Estève, Avelines and Dobrée objects; retain all other research."""
import copy, hashlib, importlib.util, json, runpy
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
identity=module('identity','museum-expansion-france-fifteenth-identity-v2-20261008.py')
f=identity.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NOTEFILE=RUN/'working-notes-release-three-museums-001.py';notes=runpy.run_path(str(NOTEFILE))
NOTES={n:b for n,b in notes['SOURCE_NOTES'].items() if n<=360 and n not in notes['PENDING']}
HOLDS=notes['HOLDS'];PENDING=notes['PENDING'];GENERIC=notes['GENERIC_REVIEW']
CANDIDATES=RUN/'native-candidates-001.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz'
def initial_omissions(c):
    printed={a['id'] for a in c['leads'] if a['title_similarity']>=.70}
    printed|={a['id'] for a in c['exact_title_hits'] if a['id'] not in c['creator_pool_ids'] and not(len(c['exact_title_hits'])>8 and (a['creators'] or a['unlinked_creator_label']) and 'anonyme' not in (a['unlinked_creator_label'] or '').lower())}
    printed|={a['id'] for a in c['untitled_creator_hits']}|{a['id'] for a in c['inventory_hits'] if a['relevant']}
    return sorted({a['id'] for k in ['leads','exact_title_hits'] for a in c[k]}-printed)
def coverage(rows,old,new):
    out=[]
    for row,a,b in zip(rows,old,new):
        n=row['number'];seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in a[k]}
        delta=sorted({v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits'] for v in b[k]}-seen)
        needed=bool(delta or b['object_alias_hits'] or b['related_inventory_hits']);omitted=initial_omissions(a)
        if n in NOTES:
            assert not needed or n in notes['SUPPLEMENTAL_REVIEW'],(n,'unreviewed supplemental comparisons')
            assert not omitted or n in GENERIC,(n,'unreviewed initial generic comparisons')
            assert n not in PENDING and n not in HOLDS
        out.append(dict(number=n,selected=n in NOTES,new_comparison_ids=delta,supplemental_review_needed=needed,supplemental_basis=notes['SUPPLEMENTAL_REVIEW'].get(n),initial_omitted_comparison_ids=omitted,generic_basis=GENERIC.get(n),specific_pending=PENDING.get(n)))
    return out
def batch_review(rows):
    batch=m.load(RUN/'within-batch-identity-002.json.gz')
    assert identity.within_batch(identity.augmented_rows(rows))=={k:batch[k] for k in ['inventory_groups','title_groups']}
    groups=[]
    for kind in ['inventory_groups','title_groups']:
        for g in batch[kind]:
            selected=[n for n in g['numbers'] if n in NOTES]
            if kind=='inventory_groups' and len(selected)>1:assert selected==[158,159] and g['inventory_key']=='303'
            groups.append(dict(g,kind=kind,selected=selected,individual_physical_bases={str(n):notes['SOURCE_NOTES'].get(n,HOLDS.get(n)) for n in g['numbers']},basis='Selected same-title pairs were individually distinguished by material, composition, size, physical treatment and museum marks. Avelines158/159 share old303 but have different current accessions and differently sized/color-treated sheets. Held or deferred records are not counted.'))
    selected=[v for v in rows if v['number'] in NOTES];cross=[]
    forms={v['number']:{m.norm(t) for raw in v['facts']['titles'] for t in identity.title_forms(raw)} for v in selected}
    terms={v['number']:set(identity.terms(v['facts'])) for v in selected}
    for pos,a in enumerate(selected):
        for b in selected[pos+1:]:
            if a['institution_id']!=b['institution_id'] and forms[a['number']]&forms[b['number']] and terms[a['number']]&terms[b['number']]:cross.append([a['number'],b['number']])
    assert not cross,('unresolved cross-museum pair',cross)
    return dict(groups=groups,cross_museum_same_title_and_maker_pairs=cross)
def derive_creator(v,n):
    old=v['creator_label'];d=v['source_fields']
    if n in [220,221]:
        assert 'copie de barthelemy beham' in m.norm(d['Description']) and 'beham hans sebald' in m.norm(old)
        v['creator_label']='BEHAM Hans Sebald (graveur, copie d’après BEHAM Barthel)'
        field='Description'
    elif n in [276,277,278]:
        assert 'attribuee a philippe galle' in m.norm(d['Historique'])
        v['creator_label']=old.replace('Galle Philippe (1537-1612) (graveur)','Galle Philippe (1537-1612) (attribué à, graveur)').replace('Galle Philippe (1537-1612) (exécutant)','Galle Philippe (1537-1612) (attribué à, exécutant)')
        assert v['creator_label']!=old;field='Historique'
    else:
        assert n not in notes['QUALIFIED'] and n not in notes['NATIVE_QUALIFIED'];return None
    return dict(original=old,derived=v['creator_label'],basis=notes['QUALIFIED'][n],source_field=field,literal_source_evidence=d[field],policy='Object-level qualification from the same national object record. Literal export creator label remains in source_fields. No artist authority or biography mutation.')
def build():
    cp=RUN/'review-progress-checkpoint-004.json';assert ref(cp)['sha256']=='8fb625b25663321fb1df4600e57362e292122c894286bb769b48ec7260a2811e'
    for dep in m.load(cp)['references']:checked(dep)
    for dep in m.load(cp)['external_references']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
    assert set(notes['SOURCE_NOTES']).isdisjoint(HOLDS) and set(notes['SOURCE_NOTES'])|set(HOLDS)==set(range(1,651))
    assert len(NOTES)==291 and {n for n in NOTES if n in notes['QUALIFIED']}=={220,221,276,277,278}
    x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS);old=m.load(RUN/'native-identity-001.json.gz')
    for dep in x['dependencies']+[x['parser_reference'],ix['query_reference'],ix['base_query_reference'],ix['notes_reference'],ix['context_reference']]:checked(dep)
    assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
    assert ix['params']==identity.params_for(identity.augmented_rows(x['rows']))
    vcheck=m.load(RUN/'identity-recomputed-002.json');assert vcheck['comparisons_recomputed_equal'] and vcheck['candidates_reparsed_equal']==650
    coverage(x['rows'],old['comparisons'],ix['comparisons']);batch_review(x['rows']);out=[]
    for row,cmp in zip(x['rows'],ix['comparisons']):
        n=row['number'];assert row['source_id']==cmp['source_id']
        if n not in NOTES:
            state='editorial_hold' if n in HOLDS else 'deferred_identity_review'
            reason=HOLDS.get(n,PENDING.get(n,'Further generic-title, native-version and historical inventory review remains open; retained in the selected research queue for subsequent release.'))
            out.append(dict(row,state=state,basis=reason,comparison=cmp));continue
        assert row==f.parse(row['index'],checked(row['source_reference']));v=copy.deepcopy(row['facts'])
        assert not v['date_issue'] and v['date_precision']!='after'
        assert (v['first'] is None and v['date_precision']=='before' and v['last']<=1971) or (v['first'] is not None and v['first']<=v['last']<=1970)
        assert v['inventory'] and v['creator_label']==(v['source_fields']['Auteur'].strip() if v['source_fields']['Auteur'] is not None else None)
        assert not any(cmp[k] for k in ['untitled_creator_hits','native_scheme_hits','native_url_hits','source_record_hits'])
        assert not [a for a in cmp['inventory_hits'] if a['relevant']]
        checked(v['holding_context_reference']);assert v['credit_line']==v['source_fields']['Statut_juridique']
        derived=dict(object_form=None,type_derivations=v['type_derivations']);creator=derive_creator(v,n)
        if creator:derived['qualified_creator_label']=creator
        basis='Official Joconde object '+v['source_id']+', inventory '+v['inventory']+'. '+NOTES[n]+' '+notes['SUPPLEMENTAL_REVIEW'].get(n,'')+' '+GENERIC.get(n,'')+' Final release: initial source/version assessment, supplemental object aliases and full relevant comparison coverage checked; no outstanding specific question for this selected object. Literal physical description: '+str(v['medium'])+'; '+str(v['dimensions_text'])+'. Literal ownership/credit label: '+str(v['credit_line'])+'.'
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=derived,limitation='Editorial confidence, not a calibrated probability. Original national facts, rights labels and unknowns retained. New record remains review. No artist authority, image, publication or current-display assertion. Other650-candidate research decisions remain independently held or deferred.'))
    return out
def main():
    dest=RUN/'editorial-reviewed-001.json.gz';scope=RUN/'supplemental-review-001.json.gz';assert not dest.exists() and not scope.exists();ds=build();rows=m.load(CANDIDATES)['rows']
    m.save(scope,dict(at=m.now(),coverage=coverage(rows,m.load(RUN/'native-identity-001.json.gz')['comparisons'],m.load(IDENTITY)['comparisons']),within_batch=batch_review(rows),notes_reference=ref(NOTEFILE),identity_reference=ref(IDENTITY),database_writes=0))
    paths=[NOTEFILE,CANDIDATES,IDENTITY,CITATIONS,scope,RUN/'review-progress-checkpoint-004.json',RUN/'identity-recomputed-002.json',RUN/'physical-comparison-context-002.json.gz',RUN/'sparse-comparison-context-001.json.gz']
    m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=ds,supplement_references=[ref(p) for p in paths],policy='291 resolved objects released for three museums.58 editorial holds and301 deferred candidates remain in research; no missing review is silently approved. The all-museum goal and outstanding five-museum research continue.'))
    print(json.dumps(dict(review=ref(dest),approved=len(NOTES),held=sum(d['state']=='editorial_hold' for d in ds),deferred=sum(d['state']=='deferred_identity_review' for d in ds),by_museum={v['museum']['name']:sum(a['institution_id']==v['institution_id'] and a['state']=='approved_review_only_addition' for a in ds) for v in ds})),flush=True)
if __name__=='__main__':main()
