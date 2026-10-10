#!/usr/bin/env python3
"""Read-only Auckland target verification against complete preserved preimages."""
import collections
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('u',Path(__file__).with_name('museum-expansion-auckland-20261006.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
m=u.m


def main():
    plan,digest=m.validate_plan('auckland-001')
    applied=m.load(m.RUN/'auckland-001-applied.json')
    assert applied['plan_sha256']==digest and applied['created']==148
    iid=plan['records'][0]['museum']['id']
    backup=m.BACKUP/'auckland-001-existing-artwork-rows.json.gz'
    prior=m.load(backup)['artworks'];ids=[r['row']['id'] for r in prior]
    citation_backup=m.BACKUP/'auckland-001-existing-citations.json.gz'
    citations=m.load(citation_backup)
    with m.connect() as db:
        rows=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        assert rows==prior,'Existing artwork rows changed'
        now_citations=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
        assert now_citations==citations['citations'],'Existing citations changed'
        current=db.execute("""SELECT id::text,accession_number,
          artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope
          FROM artworks WHERE current_institution_id=%s AND status<>'archived' ORDER BY id""",(iid,)).fetchall()
        new_ids=[r['artwork_id'] for r in plan['records']]
        links=db.execute('SELECT count(*) n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(new_ids,)).fetchone()['n']
        assert links==0,'Unreviewed artist links'
    inventories=collections.Counter(k for r in current for k in u.inventory_keys(r['accession_number']))
    missing=sum(not u.inventory_keys(r['accession_number']) for r in current)
    after=dict(linked=len(current),eligible=sum(r['scope']=='eligible' for r in current),
        distinct_normalized_inventories=len(inventories),legacy_missing_inventory=missing)
    assert after['linked']==242 and after['eligible']==200
    new_keys=[next(iter(u.inventory_keys(r['facts']['accession']))) for r in plan['records']]
    assert len(set(new_keys))==148 and all(inventories[k]==1 for k in new_keys)
    result=dict(at=m.now(),museum_id=iid,plan_sha256=digest,before=plan['before'],after=after,
        added_this_campaign=148,distinct_new_native_inventories=148,
        prior_full_artwork_rows_unchanged=len(prior),prior_full_citations_unchanged=len(now_citations),
        previous_full_rows_backup=str(backup),previous_full_citations_backup=str(citation_backup),
        duplicate_normalized_inventories={k:n for k,n in inventories.items() if n>1},
        limitations='SQL date eligibility includes older entries and does not newly validate each legacy physical-object identity. Prior full artwork and citation rows are unchanged. Trust collection ownership and permanent-loan holdings remain qualified; no image, artist link or display claim was added.')
    m.save(u.RUN/'target-200-verification.json',result)
    print(result,flush=True)


if __name__=='__main__':main()
