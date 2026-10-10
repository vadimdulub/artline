"""Source-preserving release of119 Écouen and two Cognacq-Jay objects."""
import copy,hashlib,importlib.util,json,runpy
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
i=module('i','museum-expansion-france-sixteenth-identity-20261008.py');n=module('n','museum-expansion-france-sixteenth-review-notes-20261008.py')
m=i.m;f=i.f;RUN=i.RUN;identity=i.identity;ref=i.ref;checked=i.checked
CANDIDATES=RUN/'remaining-candidates-001.json.gz';IDENTITY=RUN/'native-identity-001.json.gz';CITATIONS=RUN/'identity-citations-001.json.gz'
OLDNOTES=i.OLD/'working-notes-release-three-museums-001.py';old=runpy.run_path(str(OLDNOTES));NOTES={k:old['SOURCE_NOTES'][k] for k in n.SELECTED}
HOLDS=dict(old['HOLDS']);HOLDS.update({k:n.DEFERRED_ECOUEN[k] for k in [584,586]})
def coverage(rows,triage):
    out=[]
    for row,t in zip(rows,triage['rows']):
        assert row['number']==t['number'] and row['source_id']==t['source_id'];num=row['number'];manual=[e['existing_artwork_id'] for e in t['entries'] if e['needs_individual_review']]
        if num in NOTES:
            assert num not in HOLDS and num not in n.DEFERRED_ECOUEN
            assert not manual or num in n.FOLLOWUP, (num,'missing individual comparison basis')
        out.append(dict(number=num,selected=num in NOTES,physical_triage_pairs=[e for e in t['entries'] if not e['needs_individual_review']],individual_comparison_ids=manual,individual_basis=n.FOLLOWUP.get(num),general_basis=n.GENERAL if num in NOTES else None,remaining_question=n.DEFERRED_ECOUEN.get(num,old['PENDING'].get(num))))
    return out
def batch_review(rows):
    batch=m.load(RUN/'within-batch-identity-001.json.gz');groups=[]
    for key in ['inventory_groups','title_groups']:
        for g in batch[key]:
            selected=[v for v in g['numbers'] if v in NOTES]
            if key=='inventory_groups':assert len(selected)<=1,('shared inventory',g)
            groups.append(dict(g,kind=key,selected=selected,bases={str(k):old['SOURCE_NOTES'].get(k,HOLDS.get(k))+' '+n.FOLLOWUP.get(k,'') for k in g['numbers']},policy='Individual source notes describe material, size, composition and physical treatment. Historical furniture ensembles are not counted in addition to detached panels. Same-work uncertainties remain deferred.'))
    assert not {584,586}&set(NOTES)
    return groups
def derive_creator(v,num,native):
    if num!=488:
        assert num not in old['NATIVE_QUALIFIED'];return None
    detail=native['literal_detail_text'];assert native['native_inventory']=='J 15' and native['inventory_equal']
    assert all(s in detail for s in ['Ecole française','auteur du modèle','Anciennement attribué à','Boucher, François (atelier de)','copie'])
    before=v['creator_label'];v['creator_label']='Ecole française (peintre, copie d’après Boucher François, auteur du modèle ; anciennement attribué à l’atelier de Boucher)'
    return dict(original=before,derived=v['creator_label'],basis=n.FOLLOWUP[488],source_url=native['source_url'],native_reference=ref(i.OLD/'paris-object-context-checked-001.json.gz'),literal_native_evidence=detail,policy='Executing school, model author and former workshop attribution separated at object-label level. National creator export remains literal in source_fields; no artist-authority mutation.')
def build():
    rows=m.load(CANDIDATES)['rows'];ix=m.load(IDENTITY);triage=m.load(RUN/'comparison-triage-001.json.gz')
    assert len(rows)==359 and len(NOTES)==121 and sum(k>=511 for k in NOTES)==119
    assert set(NOTES).isdisjoint({d['number'] for d in m.load(i.prior.REVIEW)['decisions'] if d['state']=='approved_review_only_addition'})
    assert ix['candidate_reference']==ref(CANDIDATES);assert triage['identity_reference']==ref(IDENTITY);assert triage['candidate_reference']==ref(CANDIDATES)
    proof=m.load(RUN/'identity-recomputed-001.json');assert proof['candidates_reparsed_equal']==359 and proof['comparisons_recomputed_equal'] and proof['identity_reference']==ref(IDENTITY)
    coverage(rows,triage);batch_review(rows);native={v['number']:v for v in m.load(i.OLD/'paris-object-context-checked-001.json.gz')['rows']};out=[]
    for row,cmp in zip(rows,ix['comparisons']):
        num=row['number'];assert row['source_id']==cmp['source_id'];v=copy.deepcopy(row['facts'])
        if num not in NOTES:
            out.append(dict(row,state='editorial_hold' if num in HOLDS else 'deferred_identity_review',basis=HOLDS.get(num,n.DEFERRED_ECOUEN.get(num,old['PENDING'].get(num,'Further object/version and generic-comparison review remains open.'))),comparison=cmp));continue
        assert row==f.parse(row['index'],checked(row['source_reference']))
        assert not v['date_issue'] and v['date_precision']!='after' and v['first'] is not None and v['first']<=v['last']<=1970
        assert not any(cmp[k] for k in ['untitled_creator_hits','native_scheme_hits','native_url_hits','source_record_hits','object_alias_hits','related_inventory_hits'])
        assert not [a for a in cmp['inventory_hits'] if a['relevant']]
        checked(v['holding_context_reference']);assert v['credit_line']==v['source_fields']['Statut_juridique']
        derivation=dict(object_form=None,type_derivations=v['type_derivations']);creator=derive_creator(v,num,native.get(num))
        if creator:derivation['qualified_creator_label']=creator
        if num in [439,488]:
            for key in ['receipt_reference','body_reference','text_reference']:checked(native[num][key])
            derivation['native_object_context']=native[num]
        basis='Official Joconde '+v['source_id']+', inventory '+v['inventory']+'. Earlier source/version assessment: '+NOTES[num]+' Follow-up resolution: '+n.FOLLOWUP.get(num,'Initial and supplemental physical comparisons and within-batch units remain distinct; no exact identity returned in the fresh search.')+' '+n.GENERAL+' Preserve literal medium '+str(v['medium'])+', dimensions '+str(v['dimensions_text'])+' and custody/credit '+str(v['credit_line'])+'.'
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=derivation,limitation='Editorial confidence, not a calibrated probability. Source fields, unknowns, chronology and attributed/anonymous makers retained. Source-sparse unrelated title matches have limited metadata, as recorded in the comparison bundle. Holdings do not imply display. All new records remain review; no images or artist links attached.'))
    return out
def main():
    target=RUN/'editorial-reviewed-001.json.gz';assert not target.exists();ds=build();scope=RUN/'supplemental-review-001.json.gz'
    m.save(scope,dict(at=m.now(),coverage=coverage(m.load(CANDIDATES)['rows'],m.load(RUN/'comparison-triage-001.json.gz')),within_batch=batch_review(m.load(CANDIDATES)['rows']),notes_reference=ref(Path(n.__file__).resolve()),identity_reference=ref(IDENTITY),database_writes=0))
    paths=[CANDIDATES,IDENTITY,CITATIONS,OLDNOTES,Path(n.__file__).resolve(),scope,RUN/'identity-recomputed-001.json',RUN/'comparison-triage-001.json.gz',RUN/'targeted-context-001.json.gz',RUN/'existing-targeted-context-001.json.gz',RUN/'selected-evidence-001.json',i.OLD/'paris-object-context-checked-001.json.gz']
    m.save(target,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),supplement_references=[ref(p) for p in paths],policy='121 resolved review-only additions:119Écouen,2Cognacq-Jay. Other candidates retained as held or deferred; all-museum objective remains active.'))
    from collections import Counter
    print(json.dumps(dict(states=Counter(d['state'] for d in ds),review=ref(target))),flush=True)
if __name__=='__main__':main()
