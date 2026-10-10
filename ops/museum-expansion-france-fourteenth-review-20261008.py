"""Final individual decisions for 605 notices, with pinned native qualifications."""
import copy,importlib.util,json,runpy
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
identity=module('identity','museum-expansion-france-fourteenth-identity-v2-20261008.py');f=identity.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
notes=module('notes','museum-expansion-france-fourteenth-notes-20261008.py');NOTES=notes.NOTES;HOLDS=notes.HOLDS
CANDIDATES=RUN/'native-candidates-001.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz';CONTEXT=RUN/'paris-object-context-checked-003.json.gz'
def coverage(rows,old,new):
    out=[]
    for row,a,b in zip(rows,old,new):
        seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in a[k]}
        delta=sorted({v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits'] for v in b[k]}-seen)
        n=row['number']
        if delta and n in NOTES:assert n in notes.SUPPLEMENTAL_REVIEW,(n,'Unreviewed supplemental leads')
        out.append(dict(number=n,new_comparison_ids=delta,state='supported' if n in NOTES else 'held',basis=notes.SUPPLEMENTAL_REVIEW.get(n,HOLDS.get(n,'No additional comparator beyond the individually reviewed initial scope.'))))
    return out
def batch_review(rows):
    batch=m.load(RUN/'within-batch-identity-002.json.gz');assert identity.within_batch(rows)=={k:batch[k] for k in ['inventory_groups','title_groups','policy']}
    groups=[]
    for kind in ['inventory_groups','title_groups']:
        for g in batch[kind]:
            selected=[n for n in g['numbers'] if n in NOTES]
            if kind=='inventory_groups':assert len(selected)<=1,(g,'Unresolved shared physical inventory')
            groups.append(dict(g,kind=kind,selected=selected,individual_physical_bases={str(n):NOTES.get(n,HOLDS.get(n)) for n in g['numbers']},basis='Original individual native-page reviews distinguish plate captions/numbers, materials, dimensions, composition, stamps and separate physical sheets. Shared bound inventories and unresolved duplicate notices are held. A series title, edition size or count of figures does not create extra artworks.'))
    # Detect same-title/same-maker objects newly selected at different museums.
    cross=[];selected=[v for v in rows if v['number'] in NOTES]
    forms={v['number']:{m.norm(t) for t in identity.title_forms(v['facts']['title'])} for v in selected};terms={v['number']:set(identity.terms(v['facts'])) for v in selected}
    for i,a in enumerate(selected):
        for b in selected[i+1:]:
            if a['institution_id']!=b['institution_id'] and forms[a['number']]&forms[b['number']] and terms[a['number']]&terms[b['number']]:cross.append([a['number'],b['number']])
    assert not cross,'Unreviewed cross-museum selected-object pair'
    return dict(groups=groups,cross_museum_same_title_and_maker_pairs=cross)
def derive_creator(v,n,ctx):
    if n not in notes.NATIVE_QUALIFIED:return None
    label,basis=notes.NATIVE_QUALIFIED[n];assert ctx and ctx['number']==n and ctx['source_id']==v['source_id']
    detail=ctx['literal_detail_text'];assert 'Auteur(s)\n:\n' in detail
    if 'attribué à' in label:assert 'attribue a' in m.norm(detail)
    if n in [173,259,294]:assert '1808' in detail and '1892' in detail and '1848-1923' in v['creator_label']
    if n in [456,537,555]:assert not v['creator_label'] and 'Hugo, Victor' in detail
    old=v['creator_label'];v['creator_label']=label
    return dict(original=old,derived=label,basis=basis,native_context_reference=ref(CONTEXT),number=n,source_id=v['source_id'],source_url=ctx['source_url'],final_url=ctx['final_url'],body_reference=ctx['body_reference'],literal_native_detail=detail,policy='Object-level maker label only. Original national fields remain literal. No artist authority or biography database changes.')
def build():
    cp=RUN/'review-progress-checkpoint-003.json';assert ref(cp)['sha256']=='6dae01993cdf04732637aa0680daab72316d8bc057cc9d79b49c50c553b8c549'
    for dep in m.load(cp)['references']:checked(dep)
    native=m.load(CONTEXT);contexts={v['number']:v for v in native['rows']};assert len(contexts)==599 and 583 not in contexts
    frozen=runpy.run_path(str(RUN/'working-notes-through-605-003.py'));assert notes.NATIVE_QUALIFIED==frozen['NATIVE_QUALIFIED']
    for name in ['physical-comparison-context-001.json.gz','physical-comparison-context-002.json.gz','supplemental-context-001.json.gz']:
        for dep in m.load(RUN/name)['dependencies']:checked(dep)
    supplement=m.load(RUN/'supplemental-context-001.json.gz');assert not supplement['citation_hits'] and not supplement['external_hits'] and len(supplement['resolved_primary_records'])==1
    x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS);old=m.load(RUN/'native-identity-001.json.gz')
    for dep in x['dependencies']+[x['parser_reference'],ix['query_reference'],ix['base_query_reference'],ix['underlying_query_reference'],ix['notes_reference'],ix['context_reference']]:checked(dep)
    assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
    validation=m.load(RUN/'identity-recomputed-002.json');checked(validation['validator_reference']);assert validation['comparisons_recomputed_equal'] and validation['identity_reference']==ref(IDENTITY)
    assert ix['params']==identity.params_for(x['rows']);assert not notes.DATE_OVERRIDES and not notes.TYPE_OVERRIDES and not notes.QUALIFIED
    assert set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)==set(range(1,606))
    coverage(x['rows'],old['comparisons'],ix['comparisons']);batch_review(x['rows']);out=[]
    for row,cmp in zip(x['rows'],ix['comparisons']):
        assert row==f.parse(row['index'],checked(row['source_reference']));assert row['source_id']==cmp['source_id'];n=row['number'];v=copy.deepcopy(row['facts'])
        if n in HOLDS:out.append(dict(row,state='editorial_hold',basis=HOLDS[n],comparison=cmp));continue
        assert not v['date_issue'] and v['date_precision']!='after'
        assert (v['first'] is None and v['date_precision']=='before' and v['last']<=1971) or (v['first'] is not None and v['first']<=v['last']<=1970)
        assert v['inventory'] and v['creator_label']==(v['source_fields']['Auteur'].strip() if v['source_fields']['Auteur'] is not None else None)
        assert {a['id'] for a in cmp['untitled_creator_hits']}==notes.UNTITLED_EXCEPTIONS.get(n,set()) and not any(cmp[k] for k in ['native_scheme_hits','native_url_hits','source_record_hits']) and {a['id'] for a in cmp['inventory_hits'] if a['relevant']}==notes.INVENTORY_EXCEPTIONS.get(n,set())
        checked(v['holding_context_reference']);assert v['credit_line']==v['source_fields']['Statut_juridique']
        if n>=6:assert n in contexts
        derivations=dict(object_form=None,type_derivations=v['type_derivations']);creator=derive_creator(v,n,contexts.get(n))
        if creator:derivations['qualified_creator_label']=creator
        basis='Official Joconde object '+v['source_id']+', inventory '+v['inventory']+'. '+NOTES[n]+' '+notes.SUPPLEMENTAL_REVIEW.get(n,'')+' Literal physical description: '+str(v['medium'])+'; '+str(v['dimensions_text'])+'. Literal acquisition/ownership label (no legal-title claim): '+str(v['credit_line'])+'.'
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=derivations,limitation='Editorial confidence in physical object identity and documented museum connection, not a calibrated probability. Native and national source roles, dates, unknowns and labels retained. New record remains review. No artist authority, image, publication, site-specific location or current-display assertion.'))
    return out
def main():
    dest=RUN/'editorial-reviewed-001.json.gz';scope=RUN/'supplemental-review-001.json.gz';assert not dest.exists() and not scope.exists();ds=build();rows=m.load(CANDIDATES)['rows'];old=m.load(RUN/'native-identity-001.json.gz')['comparisons'];new=m.load(IDENTITY)['comparisons']
    m.save(scope,dict(at=m.now(),coverage=coverage(rows,old,new),within_batch=batch_review(rows),notes_reference=ref(Path(notes.__file__).resolve()),identity_reference=ref(IDENTITY),database_writes=0))
    names=['physical-comparison-context-001.json.gz','physical-comparison-context-002.json.gz','supplemental-context-001.json.gz','supplemental-review-001.json.gz','identity-recomputed-002.json','within-batch-identity-002.json.gz','review-progress-checkpoint-003.json']
    paths=[RUN/n for n in names]+[CANDIDATES,IDENTITY,CITATIONS,CONTEXT,Path(notes.__file__).resolve()]
    m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=ds,supplement_references=[ref(p) for p in paths],policy='605 individual source-backed physical-object decisions. Supplemental leads explicitly covered. Bound pages and unresolved identities remain held. Selected new local records remain review.'))
    print(json.dumps(dict(review=ref(dest),approved=len(NOTES),held=len(HOLDS),by_museum={v['museum']['name']:sum(a['institution_id']==v['institution_id'] and a['state']=='approved_review_only_addition' for a in ds) for v in ds})),flush=True)
if __name__=='__main__':main()
