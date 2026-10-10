#!/usr/bin/env python3
"""Read-only target verification against preserved full AGSA preimages."""
import collections
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m


def main():
    plan,digest=m.validate_plan('agsa-001')
    applied=m.load(m.RUN/'agsa-001-applied.json')
    assert applied['plan_sha256']==digest and applied['created']==131
    iid=plan['records'][0]['museum']['id']
    backup=m.BACKUP/'agsa-001-existing-artwork-rows.json.gz'
    prior=m.load(backup)['artworks'];ids=[r['row']['id'] for r in prior]
    citation_backup=m.BACKUP/'agsa-001-existing-citations.json.gz'
    citations=m.load(citation_backup)
    with m.connect() as db:
        rows=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        assert rows==prior,'Existing artwork rows changed'
        now_citations=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
        assert now_citations==citations['citations'],'Existing citations changed'
        current=db.execute("""SELECT id::text,accession_number,
          artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope
          FROM artworks WHERE current_institution_id=%s AND status<>'archived' ORDER BY id""",(iid,)).fetchall()
    inventories=collections.Counter(k for r in current for k in a.inventory_keys(r['accession_number']))
    missing=sum(not a.inventory_keys(r['accession_number']) for r in current)
    after=dict(linked=len(current),eligible=sum(r['scope']=='eligible' for r in current),
        distinct_normalized_inventories=len(inventories),legacy_missing_inventory=missing)
    assert after['linked']==201 and after['eligible']==200
    new_keys=[next(iter(a.inventory_keys(r['facts']['accession']))) for r in plan['records']]
    assert len(set(new_keys))==131 and all(inventories[k]==1 for k in new_keys)
    result=dict(at=m.now(),museum_id=iid,plan_sha256=digest,before=plan['before'],after=after,
        added_this_campaign=131,distinct_new_native_inventories=131,
        prior_full_artwork_rows_unchanged=len(prior),prior_full_citations_unchanged=len(now_citations),
        previous_full_rows_backup=str(backup),previous_full_citations_backup=str(citation_backup),
        duplicate_normalized_inventories={k:n for k,n in inventories.items() if n>1},
        limitations='SQL eligible-date counts include older entries and do not newly validate every legacy object identity. Existing artwork rows and complete citation rows remain unchanged; no images or display claims were added.')
    m.save(a.RUN/'target-200-verification.json',result)
    print(result,flush=True)


if __name__=='__main__':main()
