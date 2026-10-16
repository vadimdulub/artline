#!/usr/bin/env python3
"""Audited source-format correction and future-participation review.

Original normalized captures and delivery plans stay immutable. Only this new
exhibition campaign's rows are amended; the local catalogue remains read-only.
"""
import collections
import re
from psycopg.types.json import Jsonb
import exhibitions_common as c
from exhibitions_apj import parse_period

RUN=c.RUN/'date-review-v1'


def main():
    if (RUN/'delivery.json').exists():
        print('Date review already delivered');return
    groups=collections.defaultdict(list);venues=[];source_updates=[]
    for path in sorted((c.RUN/'plans/apj_full').glob('*.json.gz')):
        for r in c.load(path)['rows']:
            period=r.get('date_display') or '';start,end=parse_period(period)
            conflict=bool(start and end and start>end)
            if conflict:start=end=None
            year_match=re.fullmatch(r'(\d{4})(?:-\d{2})?/(\d{4})(?:-\d{2})?',period)
            sy=int(start[:4]) if start else int(year_match[1]) if year_match else None
            ey=int(end[:4]) if end else int(year_match[2]) if year_match else None
            if sy and ey and sy>ey:sy=ey=None
            groups[r['canonical_id']].append(dict(native_id=r['native_id'],start=start,end=end,sy=sy,ey=ey,conflict=conflict,period=period))
            interpretation=dict(date_review=dict(parser='apj-explicit-period-v1',original_period=period,start_date=start,end_date=end,conflict=conflict),date_conflict=conflict)
            source_updates.append((Jsonb(interpretation),c.uid('source/apj_full/'+r['native_id'])))
            for i,v in enumerate(r['occurrences']):
                venues.append((start,end,Jsonb({'date_review':interpretation['date_review']}),c.uid(f'occurrence/apj_full/{r["native_id"]}/{i}')))
    events=[]
    for eid,rows in groups.items():
        dated=[x for x in rows if x['start'] and x['end'] and not x['conflict']]
        starts=[x['start'] for x in rows if x['start']];ends=[x['end'] for x in rows if x['end']]
        years=[x['sy'] for x in rows if x['sy']];endyears=[x['ey'] for x in rows if x['ey']]
        start=min(starts) if starts else None;end=max(ends) if ends else None
        sy=min(years) if years else None;ey=max(endyears) if endyears else None
        # A dated venue is sufficient evidence that this tour occurred. Unknown
        # stops remain unknown and do not receive invented occurrence dates.
        state='held' if any(x['end']<=c.TODAY.isoformat() for x in dated) else 'announced' if start and start>c.TODAY.isoformat() else 'uncertain'
        precision='day' if start and end and all(x['start'] and x['end'] for x in rows) else 'mixed' if start or end else 'year' if sy or ey else 'unknown'
        basis='Publisher exhibition-history record; explicit date ranges normalized from ISO or dotted notation. Touring identity follows tourStartExhibitionID.'
        if len(rows)>1:basis+=' Event dates span documented stops; other stops may have incomplete dates.'
        if state=='uncertain':basis+=' The available period is incomplete or ambiguous.'
        display=rows[0]['period'] if len(rows)==1 else ' / '.join([start or str(sy or '?'),end or str(ey or '?')])+' (documented tour span)'
        events.append((start,end,sy,ey,precision,state,basis,display,eid))
    with c.connect() as db:
        before=dict(at=c.now(),events=db.execute("SELECT to_jsonb(e) row FROM exhibitions e WHERE EXISTS(SELECT 1 FROM exhibition_source_records s WHERE s.exhibition_id=e.id AND s.source_key='apj_full')").fetchall(),
          occurrences=db.execute("SELECT to_jsonb(v) row FROM exhibition_occurrences v JOIN exhibition_source_records s ON s.id=v.source_record_id WHERE s.source_key='apj_full'").fetchall(),
          source_interpretations=db.execute("SELECT id,interpretation FROM exhibition_source_records WHERE source_key='apj_full'").fetchall(),
          participation=db.execute("SELECT x.id,x.participation,e.event_state FROM exhibition_entries x JOIN exhibitions e ON e.id=x.exhibition_id JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE s.source_key='cleveland' AND e.event_state<>'held'").fetchall())
    c.save(RUN/'before.json.gz',before)
    c.save(RUN/'plan.json.gz',dict(events=events,occurrences=[[*x[:2],x[2].obj,x[3]] for x in venues],source_updates=[[x[0].obj,x[1]] for x in source_updates]))
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(20261011047)')
        cur=db.cursor()
        cur.executemany('UPDATE exhibitions SET start_date=%s,end_date=%s,start_year=%s,end_year=%s,date_precision=%s,event_state=%s,state_basis=%s,date_display=%s,updated_at=now() WHERE id=%s::uuid AND import_batch=\'exhibitions-100k-20261011\'',events)
        cur.executemany('UPDATE exhibition_occurrences SET start_date=%s,end_date=%s,evidence=evidence||%s WHERE id=%s::uuid',venues)
        cur.executemany('UPDATE exhibition_source_records SET interpretation=interpretation||%s WHERE id=%s::uuid',source_updates)
        changed=db.execute("UPDATE exhibition_entries x SET participation=CASE WHEN e.event_state='announced' THEN 'proposed' ELSE 'catalogued' END,evidence=x.evidence||jsonb_build_object('participation_review','Future or uncertain exhibition; source association is not proof of completed physical display','previous_participation',x.participation) FROM exhibitions e,exhibition_source_records s WHERE e.id=x.exhibition_id AND s.id=x.source_record_id AND s.source_key='cleveland' AND e.event_state<>'held' AND x.participation='exhibited' RETURNING x.id").fetchall()
    with c.connect() as db:
        after=db.execute("SELECT event_state,count(*) FROM exhibitions e WHERE EXISTS(SELECT 1 FROM exhibition_source_records s WHERE s.exhibition_id=e.id AND s.source_key='apj_full') GROUP BY 1").fetchall()
    receipt=dict(at=c.now(),apj_events=len(events),apj_occurrences=len(venues),states_after=after,participation_corrections=len(changed),verified_after_commit=True)
    c.save(RUN/'delivery.json',receipt);print(receipt)


if __name__=='__main__':main()
