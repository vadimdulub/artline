"""Fresh post-wave70 identity scope for the359 remaining source notices."""
import copy,importlib.util,json,re
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
prior=module('prior','museum-expansion-france-fifteenth-apply-20261008.py');identity=prior.r.identity;f=identity.f;m=f.m;OLD=prior.RUN
RUN=m.RUN/'native/france-sixteenth-minimum-20261008';ref=f.ref;checked=f.checked
identity.base.RUN=RUN
ORIGINAL=OLD/'native-candidates-001.json.gz';DECISIONS=OLD/'editorial-reviewed-001.json.gz'
def rows():
    decisions=m.load(DECISIONS)['decisions'];remaining={d['source_id'] for d in decisions if d['state']!='approved_review_only_addition'}
    selected=[copy.deepcopy(r) for r in m.load(ORIGINAL)['rows'] if r['source_id'] in remaining];assert len(selected)==359
    # OA is a search hypothesis for historical Louvre INV labels, supported only
    # for OA427/431 so far. Returned objects still require individual review.
    for row in selected:
        if row['number'] in [531]+list(range(584,594)):
            nums=re.findall(r'\bINV\s+(\d+)',row['facts']['inventory'])
            identity.RELATED[row['number']]=list(set(identity.RELATED.get(row['number'],[]))|{'OA '+n for n in nums})
    augmented=identity.augmented_rows(selected)
    for row in augmented:
        if row['number'] in [531,585]:
            url={531:'https://collections.louvre.fr/ark:/53355/cl010109869',585:'https://collections.louvre.fr/ark:/53355/cl010097192'}[row['number']]
            row['facts']['native_page_urls']=sorted(set(row['facts']['native_page_urls'])|{url})
    return selected,augmented
def main():
    dest=RUN/'native-identity-001.json.gz';cites=RUN/'identity-citations-001.json.gz';initial=RUN/'initial-scope-001.json.gz';candidate=RUN/'remaining-candidates-001.json.gz'
    assert not any(p.exists() for p in [dest,cites,initial,candidate]);continuation=m.load(RUN/'continuation-001.json');assert continuation['verified']==291 and continuation['previous_goal_turn']=='progress'
    checked(continuation['previous_checkpoint']);selected,augmented=rows();params=identity.params_for(augmented)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(identity.base.IIDS,identity.base.IIDS))]
        snap=identity.base.snapshot(db,ids);counts=identity.base.counts(db);assert counts==continuation['counts'] and len(ids)==570
        m.save(initial,dict(at=m.now(),scoped_ids=ids,snapshot=snap,counts=counts,read_only=True,baseline_checkpoint=continuation['previous_checkpoint']))
        state=identity.base.queries(db,params)
        citations=[r['row'] for r in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    print(json.dumps(dict(state_counts={k:len(v) for k,v in state.items()},citations=len(citations),remaining=len(selected))),flush=True)
    comparisons=identity.comparisons(augmented,state,citations)
    m.save(candidate,dict(at=m.now(),rows=selected,original_reference=ref(ORIGINAL),prior_decisions_reference=ref(DECISIONS),policy='Preserved source notices not delivered in wave70.301 deferred and58 editorial holds remain separate; no reselection of the291 delivered records.'))
    m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),original_reference=ref(ORIGINAL),prior_decisions_reference=ref(DECISIONS),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(identity.__file__).resolve()),params=params,state=state,comparisons=comparisons,read_only=True,policy='Fresh post-release scope. OA variants are discovery-only related inventories, not asserted historical aliases. Captured Louvre OA427/431 pages are search identities with unresolved source contradictions. Original catalogue source fields remain unchanged.'))
    m.save(cites,dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=citations,read_only=True))
    m.save(RUN/'within-batch-identity-001.json.gz',dict(at=m.now(),candidate_reference=ref(candidate),identity_reference=ref(dest),**identity.within_batch(augmented)))
    print(json.dumps(dict(identity=ref(dest),comparisons=len(comparisons),hits={k:sum(len(c[k]) for c in comparisons) for k in ['native_url_hits','native_scheme_hits','source_record_hits','object_alias_hits','related_inventory_hits']},database_writes=0)),flush=True)
if __name__=='__main__':main()
