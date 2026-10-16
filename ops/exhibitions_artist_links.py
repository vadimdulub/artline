#!/usr/bin/env python3
"""Reconcile exhibition participants by unique full name and source life dates.

No artist biography/date changes and no name-only or artwork-title matching.
"""
import argparse
import collections
import json
import re
import time
from psycopg.types.json import Jsonb
import exhibitions_common as c


def main(run_name,apply=False):
    run=c.RUN/'artist-links'/run_name
    if (run/'delivery.json').exists():print('Already delivered');return
    with c.connect() as db:
        artists=db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists WHERE status<>'archived' AND entity_type='person'").fetchall()
    index=collections.defaultdict(list)
    for a in artists:index[c.norm(a['name'])].append(a)
    candidates={}
    for path in sorted((c.DATA/'normalized/artsy').glob('*.json.gz')):
        for r in c.load(path):
            for p in r['participants']:
                if p['role']!='artist' or not p.get('source_person_id'):continue
                ids=index[c.norm(p['name_label'])]
                if len(ids)==1 and ids[0]['birth_year'] and len(c.norm(p['name_label']).split())>=2:
                    candidates[p['source_person_id']]=dict(source_id=p['source_person_id'],name=p['name_label'],candidate=ids[0])
    c.save(run/'candidates.json.gz',candidates)
    accepted=[];held=[];ids=sorted(candidates)
    def year(raw):return int(raw) if raw and re.fullmatch(r'\d{4}',raw) else None
    for offset in range(0,len(ids),50):
        batch=ids[offset:offset+50]
        query='query ArtlineArtistIdentity { artists(ids: '+json.dumps(batch)+', size: 50) { internalID slug name birthday deathday nationality } }'
        raw,rc=c.capture('https://metaphysics-cdn.artsy.net/v2',{'query':query});doc=json.loads(raw)
        if doc.get('errors'):raise ValueError(str(doc['errors']))
        sources={a['internalID']:a for a in doc['data']['artists']}
        for sid in batch:
            candidate=candidates[sid];a=candidate['candidate'];s=sources.get(sid);reason=None
            if not s:reason='Provider did not return the requested public identity'
            elif c.norm(s['name'])!=c.norm(a['name']):reason='Public profile name differs'
            elif year(s['birthday'])!=a['birth_year']:reason='Birth year absent, qualified or conflicting'
            elif year(s.get('deathday')) and a['death_year'] and year(s['deathday'])!=a['death_year']:reason='Death year conflict'
            record=dict(source_id=sid,artist_id=a['id'],name=candidate['name'],candidate=a,source=s,source_url='https://www.artsy.net/artist/'+s['slug'] if s else None,receipt=rc)
            if reason:record['reason']=reason;held.append(record)
            else:
                record['basis']='Unique exact normalized full name plus exact birth year; no conflicting known death year; stable Artsy artist ID. Editorial identity confidence 95%, not calibrated probability.'
                accepted.append(record)
        print(json.dumps(dict(reviewed=min(offset+50,len(ids)),candidates=len(ids),accepted=len(accepted),held=len(held))),flush=True)
        time.sleep(.4)
    c.save(run/'review.json.gz',dict(accepted=accepted,held=held))
    if not apply:return
    rows=[dict(source_id=x['source_id'],artist_id=x['artist_id'],evidence=dict(artist_identity_review=dict({k:x[k] for k in ['source_url','candidate','source','basis']},capture_sha256=x['receipt']['sha256'],capture_receipt_id=c.sha(x['receipt']['url'].encode()),retrieved_at=x['receipt']['retrieved_at']))) for x in accepted]
    with c.connect() as db:
        before=db.execute("SELECT p.id,p.artist_id FROM exhibition_participants p JOIN exhibition_source_records s ON s.id=p.source_record_id WHERE s.source_key='artsy' AND p.role='artist' AND p.artist_id IS NULL AND p.source_person_id=ANY(%s)",([x['source_id'] for x in rows],)).fetchall()
    c.save(run/'before.json.gz',before)
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(20261011047)')
        changed=db.execute("""WITH matches AS(SELECT * FROM jsonb_to_recordset(%s) AS m(source_id text,artist_id uuid,evidence jsonb))
          UPDATE exhibition_participants p SET artist_id=m.artist_id,evidence=p.evidence||m.evidence
          FROM matches m,exhibition_source_records s,artists a
          WHERE p.source_person_id=m.source_id AND p.source_record_id=s.id AND s.source_key='artsy'
            AND p.role='artist' AND p.artist_id IS NULL AND a.id=m.artist_id AND a.status<>'archived'
          RETURNING p.id""",(Jsonb(rows),)).fetchall()
    with c.connect() as db:
        count=db.execute("SELECT count(*) links,count(DISTINCT artist_id) artists FROM exhibition_participants p JOIN exhibition_source_records s ON s.id=p.source_record_id WHERE s.source_key='artsy' AND artist_id IS NOT NULL").fetchone()
    receipt=dict(at=c.now(),matched_source_artists=len(accepted),held_identities=len(held),new_links=len(changed),verified_totals=count)
    c.save(run/'delivery.json',receipt);print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args();main(a.run,a.apply)
