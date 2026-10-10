#!/usr/bin/env python3
"""Individual physical-object decisions for five underfilled French museums."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-france-thirteenth-identity-v2-20261008.py'));identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)
f=identity.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
CANDIDATES=RUN/'native-candidates-001.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz'
ns=importlib.util.spec_from_file_location("notes",Path(__file__).with_name("museum-expansion-france-thirteenth-notes-20261008.py"));notes=importlib.util.module_from_spec(ns);ns.loader.exec_module(notes)
NOTES=notes.NOTES;HOLDS=notes.HOLDS
def derive_date(v,n):
    override=notes.DATE_OVERRIDES.get(n)
    if not override:return None
    keys=['date_display','first','last','date_precision'];old={k:v[k] for k in keys};d=v['source_fields']
    if n==266:
        assert d['Reference']=='06340036172' and d['Millesime_de_creation']=='1936'
        assert '27 avril 1937' in d['Commentaires'] and 'Bronze fondu pour le Salon de 1937' in d['Commentaires']
        assert (override['first'],override['last'],override['date_precision'])==(1937,1937,'exact')
        source_keys=['Millesime_de_creation','Commentaires']
    elif n==426:
        assert d['Reference']=='07840001747' and 'supposition' in d['Historique']
        assert d['Millesime_de_creation']=='1837'
        bounds=f.n.explicit_period_union(d['Periode_de_creation'])
        assert bounds==(override['first'],override['last'])==(1826,1850)
        assert override['date_display']=='1837 (supposé)' and override['date_precision']=='range'
        source_keys=['Millesime_de_creation','Periode_de_creation','Historique']
    else:raise AssertionError('Unreviewed date derivation')
    assert override['first']<=override['last']<=1970
    for key in keys:v[key]=override[key]
    return dict(original=old,derived={k:v[k] for k in keys},source_fields={key:d[key] for key in source_keys},basis=override['basis'])

def build():
    for context_name in ['physical-comparison-context-001.json.gz','physical-comparison-context-002.json.gz','manual-comparison-supplement-001.json.gz','final-object-context-001.json.gz']:
        context=m.load(RUN/context_name)
        for dep in context['dependencies']:checked(dep)
    x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS)
    for dep in x['dependencies']+[x['parser_reference'],ix['query_reference'],ix['base_query_reference']]:checked(dep)
    assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
    validation=m.load(RUN/'identity-recomputed-002.json');checked(validation['validator_reference'])
    assert validation['comparisons_recomputed_equal'] and validation['identity_reference']==ref(IDENTITY) and validation['candidate_reference']==ref(CANDIDATES)
    assert ix['params']==identity.params_for(x['rows'])
    assert set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)==set(range(1,621));out=[]
    for row,cmp in zip(x['rows'],ix['comparisons']):
        assert row==f.parse(row['index'],checked(row['source_reference']));assert row['source_id']==cmp['source_id'];n=row['number'];v=copy.deepcopy(row['facts'])
        if n in HOLDS:out.append(dict(row,state='editorial_hold',basis=HOLDS[n],comparison=cmp));continue
        assert v['date_issue'] is None and v['date_precision']!='after'
        assert (v['first'] is None and v['date_precision']=='before' and v['last']<=1971) or (v['first'] is not None and v['first']<=v['last']<=1970)
        assert v['inventory'] and v['credit_line'];assert v['creator_label']==(v['source_fields']['Auteur'].strip() if v['source_fields']['Auteur'] is not None else None)
        assert {a['id'] for a in cmp['untitled_creator_hits']}==notes.UNTITLED_EXCEPTIONS.get(n,set()) and not any(cmp[k] for k in ['native_scheme_hits','native_url_hits','source_record_hits']) and {a['id'] for a in cmp['inventory_hits'] if a['relevant']}==notes.INVENTORY_EXCEPTIONS.get(n,set())
        if v['holding_context_reference']:
            checked(v['holding_context_reference']);assert v['credit_line']==v['source_fields']['Statut_juridique']
        derivations=dict(object_form=None,type_derivations=v['type_derivations'])
        date=derive_date(v,n)
        if date:derivations['physical_creation_date']=date
        if n in notes.QUALIFIED:
            label,key=notes.QUALIFIED[n];assert v['source_fields'].get(key)
            derivations['qualified_creator_label']=dict(original=v['creator_label'],derived=label,source_field=key,literal_evidence=v['source_fields'][key],basis='Explicit source attribution, role, copy or impression qualification is preserved in the object-level maker label; original label and supporting source text retained without a new biography or artist authority.')
            if n in notes.FRANCOIS_NUMBERS:
                assert v['creator_label']=='François André (1931-2019)'
                derivations['qualified_creator_label'].update(basis='Literal source name retained with an explicit biography conflict instead of repeating source dates 1931–2019. Captured Centre Pompidou authority gives 1915–2005. No replacement biography or artist authority is created.',authority_reference=ref(RUN/'final-object-context-001.json.gz'))
            v['creator_label']=label
        if n in notes.TYPE_OVERRIDES:
            typ,key=notes.TYPE_OVERRIDES[n];assert v['source_fields'].get(key)
            derivations['physical_work_type']=dict(original=v['work_type'],derived=typ,source_field=key,literal_evidence=v['source_fields'][key],basis='Explicit physical reproduction technique determines new object type; literal source domain remains evidence.')
            v['work_type']=typ
        basis='Official Joconde object '+v['source_id']+', inventory '+v['inventory']+'. '+NOTES[n]+' Literal physical description: '+str(v['medium'])+'; '+str(v['dimensions_text'])+'. Literal current source acquisition/ownership label (no legal-title claim): '+v['credit_line']+'.'
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=derivations,limitation='Editorial confidence in physical object identity and documented museum connection, not a calibrated probability. Literal source creator roles, dates, unknowns and source labels retained. New record remains review. No artist authority, image, publication or current-display assertion.'))
    return out
def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();rows=build()
    paths=[RUN/'physical-comparison-context-001.json.gz',RUN/'physical-comparison-context-002.json.gz',CANDIDATES,IDENTITY,CITATIONS,RUN/'identity-recomputed-002.json',Path(notes.__file__).resolve()]
    paths += [RUN/'manual-comparison-supplement-001.json.gz',RUN/'final-object-context-001.json.gz']
    paths += sorted(p for p in RUN.glob('object-context-*/*') if p.is_file())
    paths += sorted(RUN.glob('object-context-capture-complete-*.json'))
    m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=rows,supplement_references=[ref(p) for p in paths],policy='Individual source-backed physical-object decisions. No quota overrides of dates or identity; unresolved cases remain research holds. Selected new local records remain review.'))
    print(json.dumps(dict(approved=len(NOTES),held=len(HOLDS),by_museum={v['museum']['name']:sum(a['institution_id']==v['institution_id'] and a['state']=='approved_review_only_addition' for a in rows) for v in rows})),flush=True)
if __name__=='__main__':main()
