#!/usr/bin/env python3
"""Independent read-only final counts plus a production research coverage ledger."""
import argparse
import json
from psycopg.types.json import Jsonb
import exhibitions_common as c


def coverage():
    path=c.RUN/'coverage-delivery.json'
    if path.exists():print('Coverage ledger exists');return
    with c.connect() as db:
        institutions=db.execute("SELECT id::text,name,website_url FROM institutions WHERE status<>'archived' AND canonical_institution_id IS NULL").fetchall()
        observed=db.execute("""SELECT v.institution_id::text,count(DISTINCT e.id) exhibitions,
          count(DISTINCT e.id) FILTER(WHERE e.event_state='held') held,min(e.start_year) first_year,max(e.end_year) last_year,
          array_agg(DISTINCT s.source_key) sources
          FROM exhibition_occurrences v JOIN exhibitions e ON e.id=v.exhibition_id AND e.status<>'archived'
          JOIN exhibition_source_records s ON s.id=v.source_record_id WHERE v.institution_id IS NOT NULL GROUP BY 1""").fetchall()
    index={r['institution_id']:r for r in observed};rows=[]
    for i in institutions:
        found=index.get(i['id']);state='partial' if found else 'not_started'
        rows.append((c.uid('coverage/institution/'+i['id']),i['id'],i['website_url'],found['first_year'] if found else None,found['last_year'] if found else None,state,Jsonb(dict(institution_name=i['name'],observed=found,scope='Research ledger, not a claim of all-year institutional coverage; recorded venue occurrences do not establish current holdings/display',campaign=c.OP))))
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(20261011047)')
        db.cursor().executemany('INSERT INTO exhibition_source_coverage(id,institution_id,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',rows)
    c.save(path,dict(at=c.now(),institutions=len(rows),with_records=len(index),not_complete=True))


def verify(name):
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        states=db.execute("SELECT event_state,count(*) n FROM exhibitions WHERE status<>'archived' GROUP BY 1 ORDER BY 1").fetchall()
        held=next(r['n'] for r in states if r['event_state']=='held')
        sources=db.execute("""SELECT s.source_key,count(*) source_records,count(DISTINCT e.id) active_exhibitions,
          count(DISTINCT e.id) FILTER(WHERE e.event_state='held') held_exhibitions
          FROM exhibition_source_records s JOIN exhibitions e ON e.id=s.exhibition_id AND e.status<>'archived' GROUP BY 1 ORDER BY 1""").fetchall()
        entries=db.execute("""SELECT count(*) entries,count(DISTINCT exhibition_id) exhibitions_with_entries,count(artwork_id) artwork_links,count(DISTINCT artwork_id) linked_artworks FROM exhibition_entries""").fetchone()
        participants=db.execute("SELECT count(*) records,count(artist_id) artist_links,count(DISTINCT artist_id) linked_artists FROM exhibition_participants").fetchone()
        venues=db.execute("SELECT count(*) occurrences,count(institution_id) museum_links,count(DISTINCT institution_id) linked_institutions FROM exhibition_occurrences").fetchone()
        pub=db.execute('SELECT publication_type,count(*) n FROM exhibition_publications GROUP BY 1 ORDER BY 1').fetchall()
        formats=db.execute("SELECT format,count(*) n,count(*) FILTER(WHERE event_state='held') held FROM exhibitions WHERE status<>'archived' GROUP BY 1 ORDER BY 1").fetchall()
        chronology=db.execute("SELECT min(start_year) first_year,max(end_year) last_year,count(*) FILTER(WHERE start_year IS NULL) missing_start_year FROM exhibitions WHERE status<>'archived' AND event_state='held'").fetchone()
        anomaly_queries={
          'active_without_source':"SELECT count(*) n FROM exhibitions e WHERE status<>'archived' AND NOT EXISTS(SELECT 1 FROM exhibition_source_records s WHERE s.exhibition_id=e.id)",
          'reversed_event_dates':"SELECT count(*) n FROM exhibitions WHERE start_date>end_date OR start_year>end_year",
          'reversed_occurrence_dates':"SELECT count(*) n FROM exhibition_occurrences WHERE start_date>end_date",
          'held_with_future_start':"SELECT count(*) n FROM exhibitions WHERE status<>'archived' AND event_state='held' AND start_date>date '2026-10-11'",
          'held_artsy_flagged':"SELECT count(*) n FROM exhibition_source_records s JOIN exhibitions e ON e.id=s.exhibition_id AND e.status<>'archived' AND e.event_state='held' WHERE s.source_key='artsy' AND (coalesce((s.source_payload->>'isFairBooth')::boolean,false) OR coalesce((s.source_payload->>'isStubShow')::boolean,false))",
          'future_exhibition_claims_exhibited':"SELECT count(*) n FROM exhibition_entries x JOIN exhibitions e ON e.id=x.exhibition_id WHERE e.event_state='announced' AND x.participation='exhibited'",
          'held_exhibition_before_linked_artist_birth':"SELECT count(*) n FROM exhibitions e JOIN exhibition_participants p ON p.exhibition_id=e.id JOIN artists a ON a.id=p.artist_id WHERE e.status<>'archived' AND e.event_state='held' AND p.role='artist' AND e.end_year<a.birth_year",
          'later_work_claimed_exhibited':"SELECT count(*) n FROM exhibition_entries x JOIN exhibitions e ON e.id=x.exhibition_id JOIN artworks a ON a.id=x.artwork_id WHERE e.status<>'archived' AND x.participation='exhibited' AND e.end_year<a.creation_year_start AND a.date_precision<>'unknown'",
          'blank_active_titles':"SELECT count(*) n FROM exhibitions WHERE status<>'archived' AND btrim(title)=''",
          'artsy_entries_absent_from_captured_list':"SELECT count(*) n FROM exhibition_entries x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE s.source_key='artsy' AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(s.source_payload->'artworksConnection'->'edges','[]'::jsonb)) a WHERE a->'node'->>'internalID'=x.source_artwork_id)",
          'cleveland_entries_absent_from_captured_list':"SELECT count(*) n FROM exhibition_entries x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE s.source_key='cleveland' AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(s.source_payload->'artworks','[]'::jsonb)) a WHERE a->>'id'=x.source_artwork_id)",
        }
        anomalies={k:db.execute(sql).fetchone()['n'] for k,sql in anomaly_queries.items()}
        for table in ['exhibition_occurrences','exhibition_entries','exhibition_participants','exhibition_publications']:
            anomalies[table+'_source_mismatch']=db.execute(f'SELECT count(*) n FROM {table} x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE x.exhibition_id<>s.exhibition_id').fetchone()['n']
        archived=db.execute("SELECT count(*) n FROM exhibitions WHERE status='archived'").fetchone()['n']
        catalogue={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','institutions']}
    with c.connect(local=True) as db:
        assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','institutions']}
        local_exh=db.execute("SELECT to_regclass('public.exhibitions') present").fetchone()['present']
    baseline=c.load(c.RUN/'baseline.json.gz')
    result=dict(at=c.now(),goal=100000,held=held,active=sum(r['n'] for r in states),states=states,sources=sources,entries=entries,participants=participants,venues=venues,publications=pub,formats=formats,chronology=chronology,archived_duplicates=archived,anomalies=anomalies,production_catalogue=catalogue,local_readonly_counts=local,local_counts_unchanged=local==baseline['local_readonly_counts'],local_exhibition_table=local_exh,assertions_passed=held>=100000 and not any(anomalies.values()))
    c.save(c.RUN/(name+'.json'),result);print(json.dumps(result,default=str,indent=2),flush=True)
    assert result['assertions_passed'],'Final corpus checks have outstanding failures'
    assert result['local_counts_unchanged'] and local_exh is None,'Investigate local database changes before reporting'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--coverage',action='store_true');p.add_argument('--report',default='final-verification');a=p.parse_args()
    if a.coverage:coverage()
    else:verify(a.report)
