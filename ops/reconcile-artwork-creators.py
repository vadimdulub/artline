#!/usr/bin/env python3
"""Reconcile retained artworks to already established museum creator identities.

Uses PG* environment variables. Planning and verification are read-only. Apply
requires a reviewed, checksum-pinned plan and never creates/publishes artists.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

QUALIFIED = re.compile(r"unknown|anonym|an[oó]nim|inconnu|not recorded|unident|ubekendt|ukendt|tiedossa|ignoto|workshop|atelier|bottega|school|scuola|d'après|attribu|tilskrevet|circle of|follower|master of|ma[iî]tre|\b(skole|skola|schule|école|ecole|mesteren fra|mesteren af|mester af|meister von|maestro di)\b|;", re.I)
ACTOR = "local-european-research"
FIELD = "reconciled_museum_creator"


def query(sql, write=False):
    env = os.environ.copy()
    env.setdefault('PGCONNECT_TIMEOUT', '20')
    env['PGOPTIONS'] = '-c timezone=UTC -c statement_timeout=120000 -c lock_timeout=10000 -c jit=off'
    if not write:
        env['PGOPTIONS'] += ' -c default_transaction_read_only=on'
    p = subprocess.run(['psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, capture_output=True, env=env)
    if p.returncode:
        # SQL contains only public catalogue metadata; credentials never enter SQL.
        raise RuntimeError(p.stderr)
    return [json.loads(line) for line in p.stdout.splitlines() if line.strip()]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(source, painter):
    if source in ('smk', 'tate') and painter.get('source_id'):
        return (source, painter['source_id'])
    if source == 'joconde' and painter.get('birth') is not None and painter.get('death') is not None:
        # Literal museum creator name plus BOTH documented lifespan boundaries.
        return (source, painter['name'], painter['birth'], painter['death'])
    return None


def blocked(row):
    p, c = row['painter'], row['context'] or {}
    if row['state'] != 'needs_review' or row['review'].get('blocks_promotion'):
        return 'attribution_or_state_hold'
    if QUALIFIED.search(p['name']) or c.get('creator_qualifier') or 'kopi efter' in c.get('creator_notes', '').lower():
        return 'qualified_creator'
    if p.get('role', '').lower() not in ('artist', 'painter', 'kunstner', 'maler', ''):
        return 'creator_role'
    if 'conflict' in row['note'] or row['note'] == 'source biography requires review':
        return 'existing_conflict'
    if p.get('birth') is not None and p.get('death') is not None:
        if not 0 <= p['death'] - p['birth'] <= 125:
            return 'biography_conflict'
    if row['precision'] != 'unknown':
        if p.get('birth') is not None and row['last'] is not None and row['last'] < p['birth']:
            return 'date_conflict'
        if row['type'] == 'painting' and p.get('death') is not None and row['first'] is not None and row['first'] > p['death']:
            return 'date_conflict'
    return None


def plan(directory):
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'manifest.json').exists():
        raise ValueError('Use a new plan directory; evidence is immutable')
    anchors = query("""SELECT jsonb_build_object('rid',r.research_record_id,'sha',r.facts_sha256,
      'source',r.source_kind,'painter',r.facts_json->'painter','slug',a.slug,'birth',a.birth_year,
      'death',a.death_year,'status',a.status,'entity_type',a.entity_type)
      FROM research_resolutions r JOIN artists a ON a.id=r.artist_id
      WHERE r.state='catalogued' AND a.status<>'archived' ORDER BY r.research_record_id""")
    candidates = query("""SELECT jsonb_build_object('rid',r.research_record_id,'sha',r.facts_sha256,
      'source',r.source_kind,'painter',r.facts_json->'painter','url',r.object_url,
      'context',r.facts_json->'object_context','state',r.state,'note',r.note,
      'review',r.review_evidence,'review_md5',md5(r.review_evidence::text),
      'slug',w.slug,'label',w.unlinked_creator_label,'type',w.work_type,
      'first',w.creation_year_start,'last',w.creation_year_end,'precision',w.date_precision,
      'entry_sha',l.entry_sha256)
      FROM research_artwork_links l JOIN research_resolutions r ON r.research_record_id=l.research_record_id
      JOIN artworks w ON w.id=l.artwork_id WHERE l.disposition='created'
      AND w.research_candidate AND w.status='review'
      AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)
      ORDER BY r.research_record_id""")
    save(directory / 'artist-anchors.json', anchors)
    save(directory / 'unlinked-source-artworks.json', candidates)
    identities = collections.defaultdict(dict)
    for a in anchors:
        key = identity(a['source'], a['painter'])
        if key and a['entity_type'] == 'person':
            identities[key].setdefault(a['slug'], a)
    entries, decisions = [], collections.Counter()
    for row in candidates:
        reason = blocked(row)
        key = identity(row['source'], row['painter'])
        matches = identities.get(key, {})
        if not reason and len(matches) != 1:
            reason = 'ambiguous_identity' if matches else 'no_established_identity'
        if not reason:
            anchor = next(iter(matches.values()))
            for field in ('birth', 'death'):
                supplied, existing = row['painter'].get(field), anchor[field]
                if supplied is not None and existing is not None and supplied != existing:
                    reason = 'biography_conflict'
            if row['precision'] != 'unknown':
                if anchor['birth'] is not None and row['last'] is not None and row['last'] < anchor['birth']:
                    reason = 'existing_biography_date_conflict'
                if row['type'] == 'painting' and anchor['death'] is not None and row['first'] is not None and row['first'] > anchor['death']:
                    reason = 'existing_biography_date_conflict'
        if reason:
            decisions[reason] += 1
            continue
        row['anchor'] = anchor
        row['identity_basis'] = 'museum_person_id' if len(key) == 2 else 'literal_museum_name_and_closed_biography'
        entries.append(row)
        decisions['link_' + row['source']] += 1
    if len({r['slug'] for r in entries}) != len(entries):
        raise ValueError('Multiple planned records for one artwork require review')
    save(directory / 'plan.json', entries)
    manifest = {'version': 1, 'sha256': digest((directory / 'plan.json').read_bytes()),
                'candidate_records': len(candidates), 'links': len(entries),
                'artists': len({r['anchor']['slug'] for r in entries}), 'decisions': dict(decisions)}
    save(directory / 'manifest.json', manifest)
    print(json.dumps(manifest), flush=True)


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def batch_sql(entries, sha):
    # Input travels through stdin, never shell interpolation or command arguments.
    payload = literal(json.dumps(entries, ensure_ascii=False))
    return """BEGIN;
SET LOCAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;
DO $$ BEGIN
 IF current_database()<>'artline' THEN RAISE EXCEPTION 'Expected artline database'; END IF;
 PERFORM pg_advisory_xact_lock(2026090959);
END $$;
CREATE TEMP TABLE creator_plan ON COMMIT DROP AS
 SELECT value AS p FROM jsonb_array_elements(""" + payload + """::jsonb);
ANALYZE creator_plan;
CREATE TEMP TABLE creator_checked ON COMMIT DROP AS
 SELECT p.p,w.id AS work_id,a.id AS artist_id,l.research_record_id
 FROM creator_plan p
 JOIN research_artwork_links l ON l.research_record_id=p.p->>'rid' AND l.disposition='created'
 JOIN artworks w ON w.id=l.artwork_id AND w.slug=p.p->>'slug'
 JOIN research_resolutions r ON r.research_record_id=l.research_record_id
 JOIN research_resolutions anchor ON anchor.research_record_id=p.p#>>'{anchor,rid}'
 JOIN artists a ON a.id=anchor.artist_id AND a.slug=p.p#>>'{anchor,slug}'
 WHERE r.facts_sha256=p.p->>'sha' AND md5(r.review_evidence::text)=p.p->>'review_md5'
 AND r.state='needs_review' AND r.note=p.p->>'note'
 AND r.facts_json->'painter'=p.p->'painter'
 AND anchor.state='catalogued' AND anchor.facts_sha256=p.p#>>'{anchor,sha}'
 AND anchor.facts_json->'painter'=p.p#>'{anchor,painter}'
 AND a.status<>'archived' AND a.entity_type='person'
 AND a.birth_year IS NOT DISTINCT FROM (p.p#>>'{anchor,birth}')::int
 AND a.death_year IS NOT DISTINCT FROM (p.p#>>'{anchor,death}')::int
 AND l.entry_sha256=p.p->>'entry_sha' AND w.status='review' AND w.research_candidate
 AND w.work_type=p.p->>'type' AND w.date_precision=p.p->>'precision'
 AND w.creation_year_start IS NOT DISTINCT FROM (p.p->>'first')::int
 AND w.creation_year_end IS NOT DISTINCT FROM (p.p->>'last')::int
 AND (w.unlinked_creator_label=p.p->>'label' OR (w.unlinked_creator_label IS NULL
   AND EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=w.id
     AND c.field_name='reconciled_museum_creator' AND c.source_record_id=l.research_record_id)))
 AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id
   AND (aa.artist_id<>a.id OR aa.attribution_role<>'primary'));
ANALYZE creator_checked;
DO $$ BEGIN
 IF (SELECT count(*) FROM creator_checked)<>(SELECT count(*) FROM creator_plan)
 OR (SELECT count(DISTINCT work_id) FROM creator_checked)<>(SELECT count(*) FROM creator_plan)
 THEN RAISE EXCEPTION 'Creator evidence or target changed; batch not applied'; END IF;
END $$;
-- The parent-row lock also serializes concurrent FK-backed attribution inserts.
DO $$ BEGIN PERFORM 1 FROM artworks WHERE id IN (SELECT work_id FROM creator_checked) FOR UPDATE; END $$;
WITH added AS (
 INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)
 SELECT work_id,artist_id,'primary',
 'Museum creator reconciliation ('||(p->>'identity_basis')||'). Source: '||(p->>'url')||
 '. Artwork remains in review; unresolved date, type and holding issues are unchanged. Plan SHA256: '||""" + literal(sha) + """
 FROM creator_checked ON CONFLICT DO NOTHING RETURNING artwork_id
) SELECT json_build_object('added_links',count(*)) FROM added;
INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artwork',v.work_id,'reconciled_museum_creator',s.id,v.research_record_id,v.p->>'url',
 'Creator identity only; anchored to previously reconciled museum record '||(v.p#>>'{anchor,rid}')||
 '; method: '||(v.p->>'identity_basis')||'; plan SHA256: '||""" + literal(sha) + """,now(),'local-european-research'
 FROM creator_checked v CROSS JOIN sources s WHERE s.slug='expanded-csv-review-artworks'
 AND NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=v.work_id
   AND c.field_name='reconciled_museum_creator' AND c.source_record_id=v.research_record_id);
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM creator_checked v WHERE NOT EXISTS(SELECT 1 FROM citations c
   WHERE c.entity_type='artwork' AND c.entity_id=v.work_id AND c.field_name='reconciled_museum_creator'
   AND c.source_record_id=v.research_record_id)) THEN RAISE EXCEPTION 'Missing creator citation'; END IF;
END $$;
WITH updated AS (
 UPDATE artworks w SET unlinked_creator_label=NULL,revision=revision+1,
 updated_at=now(),updated_by='local-european-research' FROM creator_checked v
 WHERE w.id=v.work_id AND w.unlinked_creator_label IS NOT NULL RETURNING w.id
) SELECT json_build_object('updated_labels',count(*)) FROM updated;
COMMIT;
"""


def apply(directory, label):
    manifest = json.loads((directory / 'manifest.json').read_text())
    raw = (directory / 'plan.json').read_bytes()
    if digest(raw) != manifest['sha256']:
        raise ValueError('Plan checksum changed')
    entries = json.loads(raw)
    if len(entries) != manifest['links'] or not entries:
        raise ValueError('Invalid plan size')
    path = directory / (label + '-apply.jsonl')
    with path.open('a') as log:
        for start in range(0, len(entries), 250):
            result = query(batch_sql(entries[start:start+250], manifest['sha256']), write=True)
            receipt = {'start': start, 'records': len(entries[start:start+250]), 'result': result}
            log.write(json.dumps(receipt) + '\n'); log.flush()
            print(json.dumps(receipt), flush=True)


def audit(directory, label, before=False):
    raw = (directory / 'plan.json').read_bytes()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if digest(raw) != manifest['sha256']:
        raise ValueError('Plan checksum changed')
    entries = json.loads(raw)
    checked = []
    for start in range(0, len(entries), 250):
        # Only identity keys enter this bounded audit query. Keep full source
        # facts in the guarded writer; avoid expanding megabytes of JSON here.
        keys = [{'rid': r['rid'], 'work': r['slug'], 'artist': r['anchor']['slug']}
                for r in entries[start:start+250]]
        sql = """WITH p AS MATERIALIZED (SELECT value AS p FROM jsonb_array_elements(""" + literal(json.dumps(keys)) + """::jsonb))
        SELECT jsonb_build_object(
         'rid',p.p->>'rid','artist',a.slug,
         'links',(SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=w.id),
         'correct_links',(SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=w.id AND aa.artist_id=a.id AND aa.attribution_role='primary'),
         'citations',(SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=w.id AND c.field_name='reconciled_museum_creator' AND c.source_record_id=p.p->>'rid'),
         'remaining_labels',(w.unlinked_creator_label IS NOT NULL)::int,
         'non_review',(w.status<>'review' OR NOT w.research_candidate)::int,
         'unknown_dates',(w.date_precision='unknown')::int,
         'unknown_types',(w.work_type='unknown')::int,
         'post_cutoff',(artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='excluded')::int,
         'work_hash',md5((to_jsonb(w)-ARRAY['id','created_at','updated_at','revision','unlinked_creator_label','updated_by','primary_media_id'])::text),
         'artist_hash',md5((to_jsonb(a)-ARRAY['id','created_at','updated_at','revision','portrait_media_id'])::text))
        FROM p JOIN artworks w ON w.slug=p.p->>'work' JOIN artists a ON a.slug=p.p->>'artist'
        ORDER BY p.p->>'rid';"""
        part = query(sql)
        assert len(part) == len(keys), 'Missing or duplicate audit targets'
        checked.extend(part)
    checked.sort(key=lambda row: row['rid'])
    assert len({r['rid'] for r in checked}) == len(entries), 'Duplicate audit target'
    result = {key: sum(r[key] for r in checked) for key in
              ['links', 'correct_links', 'citations', 'remaining_labels', 'non_review',
               'unknown_dates', 'unknown_types', 'post_cutoff']}
    result.update(works=len(checked), artists=len({r['artist'] for r in checked}),
                  source_counts=dict(collections.Counter(r['source'] for r in entries)),
                  work_metadata_digest=hashlib.md5(''.join(r['work_hash'] for r in checked).encode()).hexdigest(),
                  artist_metadata_digest=hashlib.md5(''.join(r['artist_hash'] for r in checked).encode()).hexdigest())
    save(directory / (label + ('-before.json' if before else '-verification.json')), result)
    assert result['works'] == manifest['links'] and result['artists'] == manifest['artists'], result
    assert result['non_review'] == result['post_cutoff'] == 0, result
    if before:
        assert result['links'] == result['citations'] == 0 and result['remaining_labels'] == manifest['links'], result
    else:
        assert result['links'] == result['correct_links'] == result['citations'] == manifest['links'], result
        assert result['remaining_labels'] == 0, result
        baseline = json.loads((directory / (label + '-before.json')).read_text())
        for key in ['work_metadata_digest', 'artist_metadata_digest', 'unknown_dates', 'unknown_types']:
            assert result[key] == baseline[key], (key, result[key], baseline[key])
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'apply', 'before', 'verify'])
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--label', default='local')
    args = parser.parse_args()
    if args.action == 'plan':
        plan(args.dir)
    elif args.action == 'apply':
        apply(args.dir, args.label)
    else:
        audit(args.dir, args.label, args.action == 'before')
