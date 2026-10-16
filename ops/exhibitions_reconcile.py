#!/usr/bin/env python3
"""Final source-preserving exhibition identity and event-type reconciliation."""
import argparse
import collections
import datetime as dt
import itertools
import json
import re
from psycopg.types.json import Jsonb
import exhibitions_common as c


def main(run_name,apply=False):
    run=c.RUN/'identity-review'/run_name
    if (run/'delivery.json').exists():print('Reconciliation already delivered');return
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        events=db.execute("SELECT id::text,title,normalized_title,alternate_titles,start_date,end_date,event_state,format,status FROM exhibitions WHERE status<>'archived' AND import_batch=%s",(c.OP,)).fetchall()
        venues=db.execute('SELECT exhibition_id::text,institution_id::text,venue_label,city_label,country_code,start_date,end_date FROM exhibition_occurrences').fetchall()
        people=db.execute("SELECT exhibition_id::text,name_label FROM exhibition_participants WHERE role='artist'").fetchall()
        sources=db.execute('SELECT exhibition_id::text,source_key,source_record_id,source_url FROM exhibition_source_records').fetchall()
    c.save(run/'snapshot.json.gz',dict(at=c.now(),events=events,venues=venues,people=people,sources=sources))
    byid={e['id']:e for e in events};byvenue=collections.defaultdict(list);byartist=collections.defaultdict(set);bysource=collections.defaultdict(list)
    for v in venues:byvenue[v['exhibition_id']].append(v)
    for p in people:byartist[p['exhibition_id']].add(c.norm(p['name_label']))
    for s in sources:bysource[s['exhibition_id']].append(s)
    parent={x:x for x in byid}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def join(a,b):
        a,b=root(a),root(b)
        if a==b:return
        # Retain the ID with a held source first, then stable lexical UUID.
        a,b=sorted([a,b],key=lambda x:(byid[x]['event_state']!='held',x));parent[b]=a
    keys=collections.defaultdict(set)
    for e in events:
        titles={e['normalized_title'],*(c.norm(t) for t in e['alternate_titles'])}
        for v in byvenue[e['id']]:
            start=v['start_date'] or e['start_date'];end=v['end_date'] or e['end_date']
            if not start or not end or start>end:continue
            venue=v['institution_id'] or '|'.join([c.norm(v['venue_label']).removeprefix('the '),c.norm(v['city_label']),v['country_code'] or ''])
            if not v['institution_id'] and not c.norm(v['venue_label']):continue
            for title in titles:
                if title:keys[(title,venue,str(start),str(end))].add(e['id'])
    evidence=[];held={}
    for key,ids in keys.items():
        if len(ids)<2:continue
        for a,b in itertools.combinations(sorted(ids),2):
            if byartist[a] and byartist[b] and not byartist[a]&byartist[b]:
                held[b]=dict(reason='Same title/venue/dates but disjoint recorded artist identities; event identity needs review',related_ids=[a,b])
                continue
            join(a,b);evidence.append(dict(key=key,event_ids=[a,b],basis='Exact normalized title or source alternate title, same venue identity and explicit occurrence date range; no disjoint recorded artist sets'))
    groups=collections.defaultdict(list)
    for eid in byid:groups[root(eid)].append(eid)
    merges=[dict(canonical_id=k,merged_ids=[x for x in ids if x!=k]) for k,ids in groups.items() if len(ids)>1]
    overlapping=collections.defaultdict(set)
    for e in events:
        if root(e['id'])!=e['id'] or e['event_state']!='held' or not e['start_date'] or not e['end_date']:continue
        for v in byvenue[e['id']]:
            venue=v['institution_id'] or '|'.join([c.norm(v['venue_label']),c.norm(v['city_label']),v['country_code'] or ''])
            if v['institution_id'] or c.norm(v['venue_label']):overlapping[(e['normalized_title'],venue)].add(e['id'])
    for key,ids in overlapping.items():
        if len(ids)>150:continue
        ordered=sorted(ids,key=lambda x:(byid[x]['start_date'],x))
        for i,b in enumerate(ordered):
            for a in ordered[:i]:
                aa,bb=byid[a],byid[b]
                overlap=(min(aa['end_date'],bb['end_date'])-max(aa['start_date'],bb['start_date'])).days+1
                shortest=min((aa['end_date']-aa['start_date']).days+1,(bb['end_date']-bb['start_date']).days+1)
                if shortest<=0 or overlap/shortest<.8:continue
                if byartist[a] and byartist[b] and not byartist[a]&byartist[b]:continue
                held[b]=dict(reason='Possible duplicate or extended date range: same title and venue with at least 80% overlap of the shorter documented period; no disjoint source artist sets',related_ids=[a,b])
                break
    # A long, distinctive repeated title and nearly identical artist lists at
    # different venues may be a tour absent an explicit source relationship.
    # Keep those records; exclude additional uncertain identities from the goal.
    title_groups=collections.defaultdict(list)
    for e in events:
        if root(e['id'])!=e['id'] or e['event_state']!='held' or not e['start_date'] or not e['end_date']:continue
        t=e['normalized_title']
        if len(t)>=35 and len(t.split())>=5 and byartist[e['id']]:title_groups[t].append(e['id'])
    for title,ids in title_groups.items():
        ids.sort(key=lambda x:(byid[x]['start_date'],x))
        if len(ids)>50:continue # Generic recurring labels require separate review.
        for i,b in enumerate(ids):
            for a in ids[:i]:
                days=(byid[b]['start_date']-byid[a]['end_date']).days
                if days < -60 or days>730:continue
                aa,bb=byartist[a],byartist[b]
                if len(aa&bb)/len(aa|bb)<.8:continue
                va={v['institution_id'] or c.norm(v['venue_label']) for v in byvenue[a]};vb={v['institution_id'] or c.norm(v['venue_label']) for v in byvenue[b]}
                if va==vb:continue
                held[b]=dict(reason='Possible touring or overlapping exhibition identity: same distinctive title and at least 80% overlapping source artist sets at different venues within two years; no tour relationship asserted',related_ids=[a,b],title=title)
                break
    # Institution APIs include administrative loans/conservation records too.
    # Named loan exhibitions and collection exhibitions are retained.
    for e in events:
        if re.search(r'\bfilm festival\b|映画祭|^(?:conference|symposium|lecture|film series|film screening)\s*[:\-]',e['title'],re.I):
            held[e['id']]=dict(reason='Possible festival, screening or discussion programme; a distinct visual-art exhibition requires confirmation',related_ids=[])
        if not any(s['source_key']=='cleveland' for s in bysource[e['id']]):continue
        if re.search(r'\b(long[ -]term loan|loan request|reciprocal loan)$|\bconservation treatment\b|^long[ -]term loan\b|^reciprocal loan\b',e['title'],re.I) and not re.search(r'\bexhibition\b',e['title'],re.I):
            held[e['id']]=dict(reason='Possible administrative loan/conservation record; independent exhibition identity requires confirmation',related_ids=[])
    holds=[dict(id=root(eid),**v) for eid,v in held.items() if root(eid) in byid and byid[root(eid)]['event_state']=='held']
    # Conflicts do not propagate from a discarded duplicate onto its securely
    # identified canonical event unless that canonical ID was itself flagged.
    holds=[x for x in holds if x['id'] in held]
    unique={x['id']:x for x in holds};holds=list(unique.values())
    plan=dict(at=c.now(),merges=merges,merge_evidence=evidence,identity_holds=holds,before_counts=dict(collections.Counter(e['event_state'] for e in events)))
    c.save(run/'plan.json.gz',plan)
    print(json.dumps(dict(events=len(events),merge_groups=len(merges),duplicate_records=sum(len(x['merged_ids']) for x in merges),identity_holds=len(holds))),flush=True)
    if not apply:return
    assert plan['before_counts'].get('held',0)>=100000,'Finish source collection and delivery before final identity consolidation'
    mapping=[dict(old_id=old,new_id=m['canonical_id']) for m in merges for old in m['merged_ids']]
    with c.connect() as db:
        c.save(run/'before-merge-events.json.gz',db.execute('SELECT to_jsonb(e) row FROM exhibitions e WHERE id=ANY(%s::uuid[])',([x for m in merges for x in [m['canonical_id'],*m['merged_ids']]]+[x['id'] for x in holds],)).fetchall())
        c.save(run/'before-held-entries.json.gz',db.execute('SELECT id,exhibition_id,participation,evidence FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[])',([x['id'] for x in holds],)).fetchall())
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(20261011047)')
        for table in ['exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']:
            db.execute(f'WITH mapping AS(SELECT * FROM jsonb_to_recordset(%s) AS m(old_id uuid,new_id uuid)) UPDATE {table} child SET exhibition_id=m.new_id FROM mapping m WHERE child.exhibition_id=m.old_id',(Jsonb(mapping),))
        db.execute("WITH mapping AS(SELECT * FROM jsonb_to_recordset(%s) AS m(old_id uuid,new_id uuid)) UPDATE exhibition_source_records s SET exhibition_id=m.new_id,interpretation=interpretation||jsonb_build_object('identity_consolidation',jsonb_build_object('previous_exhibition_id',m.old_id,'canonical_exhibition_id',m.new_id,'review',%s::text)) FROM mapping m WHERE s.exhibition_id=m.old_id",(Jsonb(mapping),run_name))
        db.execute("WITH mapping AS(SELECT * FROM jsonb_to_recordset(%s) AS m(old_id uuid,new_id uuid)) UPDATE exhibitions e SET status='archived',updated_at=now(),state_basis=state_basis||' Duplicate identity consolidated into '||m.new_id::text||'; original record retained for audit.' FROM mapping m WHERE e.id=m.old_id",(Jsonb(mapping),))
        for hold in holds:
            db.execute("UPDATE exhibitions SET event_state='uncertain',state_basis=%s,updated_at=now() WHERE id=%s::uuid AND status<>'archived'",(hold['reason'],hold['id']))
            db.execute("UPDATE exhibition_source_records SET interpretation=interpretation||jsonb_build_object('identity_review',%s::jsonb) WHERE exhibition_id=%s::uuid",(Jsonb(hold),hold['id']))
            if hold['reason'].startswith(('Possible administrative','Possible festival')):
                db.execute("UPDATE exhibition_entries SET participation='catalogued',evidence=evidence||jsonb_build_object('event_type_review',%s::text,'previous_participation',participation) WHERE exhibition_id=%s::uuid AND participation='exhibited'",(hold['reason'],hold['id']))
        # Merged events keep all original occurrence dates and source texts.
        for m in merges:
            db.execute("UPDATE exhibitions e SET checklist_state=CASE WHEN EXISTS(SELECT 1 FROM exhibition_entries x WHERE x.exhibition_id=e.id) THEN 'partial' ELSE e.checklist_state END WHERE e.id=%s::uuid",(m['canonical_id'],))
            canonical=byid[m['canonical_id']]
            alternatives=set(canonical['alternate_titles'])
            for old in m['merged_ids']:alternatives.update([byid[old]['title'],*byid[old]['alternate_titles']])
            alternatives.discard(canonical['title'])
            db.execute('UPDATE exhibitions SET alternate_titles=%s WHERE id=%s::uuid',(Jsonb(sorted(alternatives)),m['canonical_id']))
    with c.connect() as db:
        counts=db.execute("SELECT event_state,count(*) n FROM exhibitions WHERE status<>'archived' GROUP BY 1").fetchall()
        mismatches={table:db.execute(f'SELECT count(*) n FROM {table} x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE x.exhibition_id<>s.exhibition_id').fetchone()['n'] for table in ['exhibition_occurrences','exhibition_participants','exhibition_entries','exhibition_publications']}
        assert not any(mismatches.values()),mismatches
    receipt=dict(at=c.now(),counts=counts,archived_duplicate_records=len(mapping),identity_holds=len(holds),source_relationship_mismatches=mismatches,verified_after_commit=True)
    c.save(run/'delivery.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args();main(a.run,a.apply)
