#!/usr/bin/env python3
"""Individual physical-object decisions for five underfilled French museums."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-france-fifth-identity-v2-20261008.py'));identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)
f=identity.f;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
CANDIDATES=RUN/'native-candidates-001.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CITATIONS=RUN/'identity-citations-002.json.gz'
ns=importlib.util.spec_from_file_location("notes",Path(__file__).with_name("museum-expansion-france-fifth-notes-20261008.py"));notes=importlib.util.module_from_spec(ns);ns.loader.exec_module(notes)
NOTES=notes.NOTES;HOLDS=notes.HOLDS
def build():
    x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS)
    for dep in x['dependencies']+[x['parser_reference'],ix['query_reference'],ix['base_query_reference']]:checked(dep)
    assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
    validation=m.load(RUN/'identity-recomputed-002.json');checked(validation['validator_reference'])
    assert validation['comparisons_recomputed_equal'] and validation['identity_reference']==ref(IDENTITY) and validation['candidate_reference']==ref(CANDIDATES)
    assert ix['params']==identity.params_for(x['rows'])
    assert set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)==set(range(1,203));out=[]
    for row,cmp in zip(x['rows'],ix['comparisons']):
        assert row==f.parse(row['index'],checked(row['source_reference']));assert row['source_id']==cmp['source_id'];n=row['number'];v=copy.deepcopy(row['facts'])
        if n in HOLDS:out.append(dict(row,state='editorial_hold',basis=HOLDS[n],comparison=cmp));continue
        assert v['date_issue'] is None and v['date_precision']!='after'
        assert (v['first'] is None and v['date_precision']=='before' and v['last']<=1971) or (v['first'] is not None and v['first']<=v['last']<=1970)
        assert v['inventory'] and v['credit_line'];assert v['creator_label']==(v['source_fields']['Auteur'].strip() if v['source_fields']['Auteur'] is not None else None)
        assert not cmp['untitled_creator_hits'] and not any(cmp[k] for k in ['native_scheme_hits','native_url_hits','source_record_hits']) and {a['id'] for a in cmp['inventory_hits'] if a['relevant']}==notes.INVENTORY_EXCEPTIONS.get(n,set())
        if v['holding_context_reference']:
            checked(v['holding_context_reference']);assert v['credit_line']==v['source_fields']['Statut_juridique']
        derivations=dict(object_form=None,type_derivations=v['type_derivations'])
        if n in notes.QUALIFIED:
            label,key=notes.QUALIFIED[n];assert v['source_fields'].get(key)
            derivations['qualified_creator_label']=dict(original=v['creator_label'],derived=label,source_field=key,literal_evidence=v['source_fields'][key],basis='Qualification in current source notes is part of attribution, not a new identification.')
            v['creator_label']=label
        basis='Official Joconde object '+v['source_id']+', inventory '+v['inventory']+'. '+NOTES[n]+(' Musée de l’Armée exact source museum name and Paris match the existing city-qualified institution name; its empty database city remains unchanged.' if v['source_fields']['Code_Museofile']=='M5025' else '')+' Literal physical description: '+str(v['medium'])+'; '+str(v['dimensions_text'])+'. Literal current source acquisition/ownership label (no legal-title claim): '+v['credit_line']+'.'
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=derivations,limitation='Editorial confidence in physical object identity and documented museum connection, not a calibrated probability. Literal source creator roles, dates, unknowns and source labels retained. New record remains review. No artist authority, image, publication or current-display assertion.'))
    return out
def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();rows=build()
    paths=[CANDIDATES,IDENTITY,CITATIONS,RUN/'identity-recomputed-002.json',Path(notes.__file__).resolve()]
    m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=rows,supplement_references=[ref(p) for p in paths],policy='Individual source-backed physical-object decisions. No quota overrides of dates or identity; unresolved cases remain research holds. Selected new local records remain review.'))
    print(json.dumps(dict(approved=len(NOTES),held=len(HOLDS),by_museum={v['museum']['name']:sum(a['institution_id']==v['institution_id'] and a['state']=='approved_review_only_addition' for a in rows) for v in rows})),flush=True)
if __name__=='__main__':main()
