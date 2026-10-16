#!/usr/bin/env python3
"""Hold contradictory exhibition relationships without rewriting artist/work dates."""
import json
from psycopg.types.json import Jsonb
import exhibitions_common as c

run=c.RUN/'chronology'
if (run/'delivery.json').exists():
    print('Chronology already reviewed');raise SystemExit
with c.connect() as db:
    people=db.execute("SELECT e.id::text,e.title,e.end_year,e.event_state,e.state_basis,p.id::text participant_id,p.evidence,a.id::text artist_id,a.display_name,a.birth_year FROM exhibitions e JOIN exhibition_participants p ON p.exhibition_id=e.id JOIN artists a ON a.id=p.artist_id WHERE p.role='artist' AND e.status<>'archived' AND e.event_state='held' AND e.end_year<a.birth_year").fetchall()
    entries=db.execute("SELECT x.id::text,x.exhibition_id::text,e.title exhibition,e.end_year,x.participation,x.evidence,a.id::text artwork_id,a.title artwork,a.creation_year_start,a.creation_year_end,a.date_precision FROM exhibition_entries x JOIN exhibitions e ON e.id=x.exhibition_id JOIN artworks a ON a.id=x.artwork_id WHERE e.status<>'archived' AND e.end_year<a.creation_year_start AND a.date_precision<>'unknown' AND x.participation='exhibited'").fetchall()
c.save(run/'reviewed-preimages.json.gz',dict(at=c.now(),participants=people,entries=entries))
with c.connect(write=True) as db:
    db.execute('SELECT pg_advisory_xact_lock(20261011047)')
    for p in people:
        issue=dict(reason='Recorded exhibition ends before the linked artist was born; event dates or source participation need review',artist_id=p['artist_id'],artist_name=p['display_name'],birth_year=p['birth_year'],exhibition_end_year=p['end_year'])
        db.execute("UPDATE exhibitions SET event_state='uncertain',state_basis=%s,updated_at=now() WHERE id=%s::uuid",(issue['reason'],p['id']))
        db.execute('UPDATE exhibition_participants SET evidence=evidence||jsonb_build_object(\'chronology_review\',%s::jsonb) WHERE id=%s::uuid',(Jsonb(issue),p['participant_id']))
    for x in entries:
        issue=dict(reason='Linked artwork creation range starts after the recorded exhibition ended; the source association is retained as uncertain',artwork_id=x['artwork_id'],creation_year_start=x['creation_year_start'],creation_year_end=x['creation_year_end'],exhibition_end_year=x['end_year'],previous_participation=x['participation'])
        db.execute("UPDATE exhibition_entries SET participation='uncertain',evidence=evidence||jsonb_build_object('chronology_review',%s::jsonb) WHERE id=%s::uuid",(Jsonb(issue),x['id']))
receipt=dict(at=c.now(),artist_chronology_conflicts=len(people),events_held_for_review=len({p['id'] for p in people}),artwork_participation_conflicts=len(entries),artist_and_artwork_dates_unchanged=True)
c.save(run/'delivery.json',receipt);print(json.dumps(receipt))
