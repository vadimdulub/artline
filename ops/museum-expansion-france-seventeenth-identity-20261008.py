"""Fresh identity scope after the121 wave71 additions; only238 unresolved notices."""
import copy,importlib.util,json,re
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
prior=module('prior','museum-expansion-france-sixteenth-apply-20261008.py');identity=prior.r.identity;f=identity.f;m=f.m;OLD=prior.r.i.OLD
RUN=m.RUN/'native/france-seventeenth-minimum-20261008';ref=f.ref;checked=f.checked;identity.base.RUN=RUN
ORIGINAL=OLD/'native-candidates-001.json.gz';DECISIONS=prior.REVIEW
def rows():
    remaining={d['source_id'] for d in m.load(DECISIONS)['decisions'] if d['state']!='approved_review_only_addition'}
    selected=[copy.deepcopy(r) for r in m.load(ORIGINAL)['rows'] if r['source_id'] in remaining];assert len(selected)==238
    for row in selected:
        if row['number'] in [531]+list(range(584,594)):
            nums=re.findall(r'\bINV\s+(\d+)',row['facts']['inventory']);identity.RELATED[row['number']]=list(set(identity.RELATED.get(row['number'],[]))|{'OA '+n for n in nums})
    # Literal historical alias on the captured Louvre OA428 page is a research
    # conflict, not an asserted additional identity for the pending wax portraits.
    identity.RELATED[586]=sorted(set(identity.RELATED.get(586,[]))|{'CL 22278','ECL 22278','OA 428'})
    augmented=identity.augmented_rows(selected)
    for row in augmented:
        urls={531:'https://collections.louvre.fr/ark:/53355/cl010109869',585:'https://collections.louvre.fr/ark:/53355/cl010097192',586:'https://collections.louvre.fr/ark:/53355/cl010097193'}
        if row['number'] in urls:row['facts']['native_page_urls']=sorted(set(row['facts']['native_page_urls'])|{urls[row['number']]})
    return selected,augmented
def main():
    paths=[RUN/n for n in ['initial-scope-001.json.gz','remaining-candidates-001.json.gz','native-identity-001.json.gz','identity-citations-001.json.gz']];assert not any(p.exists() for p in paths)
    continuation=m.load(RUN/'continuation-001.json');assert continuation['verified']==121 and continuation['previous_goal_turn']=='progress';checked(continuation['previous_checkpoint']);selected,augmented=rows();params=identity.params_for(augmented)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        ids=[r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(identity.base.IIDS,identity.base.IIDS))];assert len(ids)==691
        counts=identity.base.counts(db);assert counts==continuation['counts'];m.save(paths[0],dict(at=m.now(),scoped_ids=ids,snapshot=identity.base.snapshot(db,ids),counts=counts,read_only=True,baseline_checkpoint=continuation['previous_checkpoint']))
        state=identity.base.queries(db,params);citations=[r['row'] for r in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    m.save(paths[1],dict(at=m.now(),rows=selected,original_reference=ref(ORIGINAL),prior_decisions_reference=ref(DECISIONS),policy='238 remaining notices:178 deferred,60 held. Delivered291+121 objects excluded.'))
    comparisons=identity.comparisons(augmented,state,citations);m.save(paths[2],dict(at=m.now(),candidate_reference=ref(paths[1]),original_reference=ref(ORIGINAL),prior_decisions_reference=ref(DECISIONS),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(identity.__file__).resolve()),params=params,state=state,comparisons=comparisons,read_only=True,policy='Fresh post-wave71 identity search. Discovery aliases remain hypotheses; literal object/date/custody facts unchanged.'))
    m.save(paths[3],dict(at=m.now(),identity_reference=ref(paths[2]),selected_ids=state['artwork_ids'],citations=citations,read_only=True))
    m.save(RUN/'within-batch-identity-001.json.gz',dict(at=m.now(),candidate_reference=ref(paths[1]),identity_reference=ref(paths[2]),**identity.within_batch(augmented)))
    print(json.dumps(dict(remaining=len(selected),state_counts={k:len(v) for k,v in state.items()},citations=len(citations),identity=ref(paths[2]),hits={k:sum(len(c[k]) for c in comparisons) for k in ['native_url_hits','native_scheme_hits','source_record_hits','object_alias_hits','related_inventory_hits']})),flush=True)
if __name__=='__main__':main()
