#!/usr/bin/env python3
"""Continue the preserved Irish index; selected metadata only, no database writes."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('ireland',Path(__file__).with_name('museum-expansion-ireland-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
m=i.m


def main():
    destination=i.RUN/'ireland-002-research.json.gz'
    if destination.exists():
        print('Retained research',destination,flush=True);return
    previous=m.load(i.RUN/'ireland-001-research.json.gz')
    continuation=m.load(i.RUN/'continuation-001.json')
    museum=next(r for r in m.load(m.RUN/'after-wave-16.json')['institutions'] if r['slug']==i.SLUG)
    seen={r['source_record_id'] for r in previous['records']}
    seen.update(r['index']['source_id'] for r in previous['held'] if 'index' in r)
    with m.connect() as db:
        known,titles,inventories=i.existing_keys(db,museum['id'])
        counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        legacy=db.execute('''WITH selected AS MATERIALIZED (
          SELECT id FROM artworks WHERE current_institution_id=%s
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,
          a.date_display,a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.primary_media_id::text,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM selected s JOIN artworks a ON a.id=s.id ORDER BY a.id''',(museum['id'],museum['id'])).fetchall()
    m.save(i.RUN/'identity-before-002.json',dict(at=m.now(),museum=museum,counts=counts,records=legacy))
    goal=max(0,200-counts['eligible']);target=min(goal+20,100)
    assert goal>0
    records=[];held=[];indexes=[];failures=0;processed=0;url=continuation['resume_index'];remaining=[]
    # Up to 180 newly examined index entries and 60 candidate records for this
    # 40-work shortfall; a separate narrative review selects the final plan.
    for page in range(23,39):
        if not url or len(records)>=target or failures>=3 or processed>=180:break
        try:
            raw,cap=i.n.capture('ireland',url);rows,next_url=i.index_rows(raw,url)
        except (i.requests.RequestException,AssertionError) as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        indexes.append(dict(capture=cap,rows=rows,next_url=next_url))
        with m.connect() as db:
            matches=i.title_collisions(db,[dict(facts=dict(title=r['title'])) for r in rows])
        collision_keys={m.norm(r[k]) for r in matches for k in ['title','alternate_title'] if r[k]}
        remaining=[]
        for pos,index in enumerate(rows):
            if len(records)>=target or failures>=3 or processed>=180:
                remaining=rows[pos:];break
            oid=index['source_id']
            if oid in seen:continue
            seen.add(oid);processed+=1
            if oid in known:held.append(dict(index=index,reason='existing_source_identity'));continue
            key=m.norm(index['title'])
            if key in titles:held.append(dict(index=index,reason='existing_or_selected_title'));continue
            if key in collision_keys:
                held.append(dict(index=index,reason='catalogue_title_identity_requires_review',existing=[r for r in matches if any(r[k] and m.norm(r[k])==key for k in ['title','alternate_title'])]));continue
            if not i.creation_date(index['date']):held.append(dict(index=index,reason='index_creation_date_requires_review'));continue
            try:
                body,obj=i.n.capture('ireland',index['url']);parsed=i.fields(body);facts,reason=i.facts(parsed,index)
            except (i.requests.RequestException,AssertionError) as exc:
                failures+=1;held.append(dict(index=index,reason='native_source_failure',error=str(exc)[:250]));continue
            if not reason and i.inventory_keys(facts['accession'])&inventories:reason='existing_or_selected_inventory'
            if reason:held.append(dict(index=index,reason=reason,native_fields=parsed,capture=obj));continue
            records.append(dict(source_record_id=oid,museum=museum,facts=facts,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed)))
            titles.add(key);inventories.update(i.inventory_keys(facts['accession']))
        print('Ireland continuation page',page,'candidates',len(records),'held',len(held),'examined',processed,flush=True)
        m.save(i.RUN/'progress'/f'ireland-002-{page:03d}.json.gz',dict(records=records,held=held,indexes=indexes,before=counts))
        if remaining:break
        url=next_url
    result=dict(at=m.now(),museum=museum,before=counts,goal_remaining=goal,records=records,held=held,indexes=indexes,
        source_failures=failures,new_index_rows_examined=processed,resume_index=url,unprocessed_captured_rows=remaining,
        next_index=indexes[-1]['next_url'] if indexes else url,
        policy='Resume the saved index, exclude all previously evaluated identities, recheck current native IDs, inventories and catalogue titles. At most 180 new index rows; candidate pages only. Narrative and creator-scoped identity review still required.')
    m.save(destination,result);print('Saved candidates',len(records),'held',len(held),flush=True)


if __name__=='__main__':main()
