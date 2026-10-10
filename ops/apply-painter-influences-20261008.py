#!/usr/bin/env python3
"""Insert the authorized painter-influence research into production, in review.

No local writes, publication, artist changes, schema changes or conflict-upserts.
Immutable plan, scoped backup, exact preimages, atomic inserts and readback checks.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import uuid
from urllib.parse import urlparse

from psycopg import sql
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/painter-influences-20261008'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/painter-influences-20261008'
OP = 'painter-influences-20261008'
ACTOR = 'local-european-research'
DEFAULT_PLAN = RUN / 'production-plan-v1.json.gz'
spec = importlib.util.spec_from_file_location('influence_research', ROOT / 'ops/research-painter-influences-20261008.py')
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)
spec = importlib.util.spec_from_file_location('catalogue_connections', ROOT / 'ops/align-catalogues-20261008.py')
connections = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connections)


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = encoded(value)
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    with path.open('xb') as out:
        out.write(raw)


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artlines.org/research/' + OP + '/' + key))


def rows(db, table, where='true', parameters=()):
    query = sql.SQL('SELECT to_jsonb(t) AS row FROM {} t WHERE ' + where + ' ORDER BY id').format(sql.Identifier(table))
    return [r['row'] for r in db.execute(query, parameters)]


def same_fields(actual, expected):
    return all(actual.get(k) == v for k, v in expected.items())


def source_qids(edge):
    found = {v['source_wikidata_id'] for v in edge['evidence'] if v.get('source_wikidata_id')}
    for url in [edge['source_authority_url']] + [v.get('source_authority_url', '') for v in edge['evidence']]:
        match = re.fullmatch(r'https://www\.wikidata\.org/wiki/(Q\d+)', url)
        if match:
            found.add(match[1])
    return found


def grade(evidence):
    primary = [e for e in evidence if e['provider'] in ('Museum', 'Scholarly publication')]
    if any(e.get('evidence_level') == 'documented' for e in primary):
        return 'documented', 'high', 'The cited museum text was read and supports this relationship.'
    if primary:
        return 'editorial_inference', 'medium', 'The cited scholarly interpretation was read; it is not labelled a scholarly consensus.'
    if any(e['provider'] in ('Wikipedia', 'WikiArt') for e in evidence):
        return 'editorial_inference', 'medium', 'Explicit secondary-source assertion; independent historical verification remains pending.'
    return 'editorial_inference', 'low', 'Wikidata assertion retained for review; its references, if supplied, have not been independently verified.'


def source_definition(evidence):
    provider = evidence['provider']
    host = urlparse(evidence['source_url']).hostname.removeprefix('www.')
    if provider == 'Wikidata':
        return dict(slug='wikidata', name='Wikidata (CC0)', source_type='authority_data', base_url='https://www.wikidata.org', priority=100)
    if provider == 'WikiArt':
        key, name, kind, base, priority = 'wikiart', 'WikiArt — painter influence fields', 'collection_page', 'https://www.wikiart.org', 100
    elif provider == 'Wikipedia':
        key, name, kind, base, priority = 'wikipedia', 'Wikipedia contributors — artist biographies (CC BY-SA 4.0)', 'article', 'https://en.wikipedia.org', 150
    else:
        key = re.sub('[^a-z0-9]+', '-', host)
        names = {
            'nationalgallery.org.uk': 'National Gallery, London',
            'nationalgallery.gr': 'National Gallery, Athens',
            'nga.gov': 'National Gallery of Art, Washington',
            'museodelprado.es': 'Museo Nacional del Prado',
            'whitney.org': 'Whitney Museum of American Art',
            'okeeffemuseum.org': 'Georgia O’Keeffe Museum',
            'icon-art.info': 'M. V. Alpatov, Andrei Rublev — text hosted by Icon-Art',
        }
        name = names.get(host, evidence.get('publisher', host))
        kind, base, priority = ('book' if provider == 'Scholarly publication' else 'article'), 'https://' + host, 40
    slug = OP + '-' + key
    return dict(id=uid('source/' + slug), slug=slug, name=name, source_type=kind, base_url=base, priority=priority, is_active=True)


def citations_for(claim, evidence, plan_input_sha, at, source_ids, context):
    grouped = defaultdict(list)
    for e in evidence:
        grouped[(source_definition(e)['slug'], e['source_url'])].append(e)
    result = []
    for (source_slug, url), values in sorted(grouped.items()):
        dates = [e.get('retrieved_at') or e.get('reviewed_at') for e in values]
        assert all(dates), ('missing retrieval/review date', url)
        dates.sort()
        stamp = dates[0]
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp):
            stamp += 'T00:00:00+00:00'
        locators = sorted({e.get('statement_url') or ('paragraph ' + e['paragraph_sha256'] if e.get('paragraph_sha256') else None)
            or e.get('source_field') or 'reviewed source text' for e in values})
        provenance = dict(operation=OP, research_input_sha256=plan_input_sha, imported_at=at,
            evidence=values, production_identity_context=context,
            qualification='Review record only. References and source assertions are retained without asserting independent verification.')
        if any(e['provider'] == 'Wikipedia' for e in values):
            provenance.update(attribution='Wikipedia contributors', license_url='https://creativecommons.org/licenses/by-sa/4.0/')
        result.append(dict(id=uid('citation/' + claim['id'] + '/' + source_slug + '/' + url),
            entity_type='influence', entity_id=claim['id'], field_name=claim['relationship_type'],
            source_id=source_ids[source_slug], source_record_id=OP + '/' + hashlib.sha256((source_slug + url).encode()).hexdigest(),
            source_url=url, page_or_locator='; '.join(locators), evidence_note=encoded(provenance).decode(),
            retrieved_at=datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone(timezone.utc).isoformat(), created_by=ACTOR))
    return result


def inspect_target(db):
    target = db.execute('SELECT current_database() AS name,inet_server_addr()::text AS address,inet_server_port() AS port').fetchone()
    assert target['name'] == 'artline', target
    assert db.execute('SELECT is_active FROM editor_accounts WHERE user_id=%s', (ACTOR,)).fetchone() == {'is_active': True}
    triggers = {(r['table_name'], r['tgname']) for r in db.execute("SELECT c.relname AS table_name,t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE t.tgenabled='O' AND NOT t.tgisinternal AND c.relname IN ('influence_claims','citations','sources')")}
    assert {('influence_claims', 'influences_audit'), ('influence_claims', 'catalogue_cache_changed'), ('citations', 'catalogue_cache_changed'), ('sources', 'catalogue_cache_changed')} <= triggers
    return target


def prepare(path):
    assert not path.exists(), 'Preserve the existing immutable plan; choose a new version for replanning.'
    research.validate()
    input_path = RUN / 'source-reported-relationships.json.gz'
    input_sha = checksum(input_path)
    edges = research.load(input_path)
    roster = research.roster()
    original = {a['id']: a for a in roster}
    bindings = {a['id']: next(b['id'] for b in a['catalogue_bindings'] if b['catalogue'] == 'production') for a in roster}
    needed_ids = {bindings[e['target_artist_id']] for e in edges} | {bindings[e['source_artist_id']] for e in edges if e['source_artist_id']}
    wanted_qids = sorted({q for e in edges for q in source_qids(e)})
    definitions = {d['slug']: d for e in edges for v in e['evidence'] for d in [source_definition(v)]}
    with connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        target = inspect_target(db)
        qmap = {r['external_id']: str(r['entity_id']) for r in db.execute("SELECT external_id,entity_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s)", (wanted_qids,))}
        needed_ids |= set(qmap.values())
        artists = rows(db, 'artists', 'id=ANY(%s::uuid[])', (sorted(needed_ids),))
        identifiers = rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (sorted(needed_ids),))
        existing = rows(db, 'influence_claims')
        old_citations = rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([r['id'] for r in existing],))
        existing_sources = rows(db, 'sources', 'slug=ANY(%s)', (sorted(definitions),))
    by_id = {a['id']: a for a in artists}
    by_q = defaultdict(set)
    for v in identifiers:
        if v['scheme'] == 'wikidata':
            by_q[v['entity_id']].add(v['external_id'])
    identity_issues = {}
    for local_id in {e['target_artist_id'] for e in edges} | {e['source_artist_id'] for e in edges if e['source_artist_id']}:
        a = by_id.get(bindings[local_id]); old = original[local_id]
        if not a or a['status'] == 'archived':
            identity_issues[local_id] = 'production record missing or archived'
        elif a['slug'] != old['slug'] or (a['display_name'] != old['display_name'] and not by_q[a['id']] & research.qids_for(old)):
            identity_issues[local_id] = 'production identity changed since the pinned roster'
        elif by_q[a['id']] and research.qids_for(old) and not by_q[a['id']] & research.qids_for(old):
            identity_issues[local_id] = 'production authority conflicts with research identity'
    groups = {}; held = []
    for index, edge in enumerate(edges):
        issue = identity_issues.get(edge['target_artist_id']) or identity_issues.get(edge['source_artist_id'])
        if issue:
            held.append(dict(research_row=index, reason=issue, edge=edge)); continue
        source_id = bindings.get(edge['source_artist_id']); target_id = bindings[edge['target_artist_id']]
        qs = source_qids(edge)
        if len(qs) > 1:
            held.append(dict(research_row=index, reason='conflicting source authority IDs', edge=edge)); continue
        if not source_id and len(qs) == 1:
            candidate = qmap.get(next(iter(qs)))
            if candidate and by_id[candidate]['status'] != 'archived':
                source_id = candidate
        if source_id and qs and by_q[source_id] and not qs & by_q[source_id]:
            held.append(dict(research_row=index, reason='source evidence disagrees with production identity', edge=edge)); continue
        source = by_id.get(source_id); target_artist = by_id[target_id]
        if source_id == target_id or (source_id and by_q[source_id] & by_q[target_id]):
            held.append(dict(research_row=index, reason='self relation after production mapping', edge=edge)); continue
        if source and source['birth_year'] is not None and target_artist['death_year'] is not None and source['birth_year'] > target_artist['death_year']:
            held.append(dict(research_row=index, reason='current production chronology conflicts', edge=edge)); continue
        if source and edge['relationship_type'] == 'teacher_of' and source['death_year'] is not None and target_artist['birth_year'] is not None and source['death_year'] < target_artist['birth_year']:
            held.append(dict(research_row=index, reason='current production teaching chronology conflicts', edge=edge)); continue
        source_key = 'artist:' + source_id if source_id else 'authority:' + next(iter(qs)) if qs else 'external:' + edge['source_authority_url'] + '#' + research.norm(edge['source_label'])
        key = (target_id, edge['relationship_type'], source_key)
        g = groups.setdefault(key, dict(source_artist_id=source_id, source_label=source['display_name'] if source else edge['source_label'],
            target_artist_id=target_id, relationship_type=edge['relationship_type'], evidence=[], research_rows=[], source_qids=sorted(qs)))
        g['research_rows'].append(index)
        for ev in edge['evidence']:
            if ev not in g['evidence']:
                g['evidence'].append(ev)
    source_ids = {}; new_sources = []
    existing_source_map = {s['slug']: s for s in existing_sources}
    for slug, definition in sorted(definitions.items()):
        if slug in existing_source_map:
            assert existing_source_map[slug]['is_active'], ('inactive source', slug)
            source_ids[slug] = existing_source_map[slug]['id']
        else:
            assert definition.get('id'), ('canonical source absent', slug)
            source_ids[slug] = definition['id']; new_sources.append(definition)
    claims = []; citations = []; skipped = []; at = now()
    for key, g in sorted(groups.items()):
        matches = [r for r in existing if r['target_artist_id'] == g['target_artist_id'] and r['relationship_type'] == g['relationship_type']
            and ((g['source_artist_id'] and r['source_artist_id'] == g['source_artist_id'])
                or (r['source_artist_id'] is None and research.norm(r['source_label']) == research.norm(g['source_label'])))]
        if matches:
            skipped.append(dict(research_rows=g['research_rows'], existing_claim_ids=[r['id'] for r in matches], reason='existing claim preserved, including its publication state and citations')); continue
        level, confidence, qualification = grade(g['evidence'])
        primary_notes = [v['note'] for v in g['evidence'] if v['provider'] in ('Museum', 'Scholarly publication')]
        notes = primary_notes or list(dict.fromkeys(v['note'] for v in g['evidence'] if v['provider'] == 'Wikipedia'))
        # Keep contextual qualifications visible; full statements remain in citations.
        evidence_note = ' '.join(dict.fromkeys(notes)) + (' ' if notes else '') + qualification
        if g['relationship_type'] == 'teacher_of':
            evidence_note += ' Teaching is recorded separately and does not itself establish artistic influence.'
        claim = dict(id=uid('claim/' + json.dumps(key)), source_artist_id=g['source_artist_id'], source_label=g['source_label'],
            target_artist_id=g['target_artist_id'], relationship_type=g['relationship_type'], evidence_level=level,
            confidence=confidence, evidence_note=evidence_note, status='review', created_by=ACTOR, updated_by=ACTOR)
        claims.append(claim)
        citations.extend(citations_for(claim, g['evidence'], input_sha, at, source_ids,
            dict(research_rows=g['research_rows'], source_artist_id=g['source_artist_id'], target_artist_id=g['target_artist_id'], source_qids=g['source_qids'])))
    used_sources = {c['source_id'] for c in citations}
    new_sources = [s for s in new_sources if s['id'] in used_sources]
    preimage = dict(artists=artists, identifiers=identifiers, influence_claims=existing, citations=old_citations, sources=existing_sources)
    backup_path = BACKUP / (path.name.removesuffix('.json.gz') + '-before.json.gz')
    save_new(backup_path, dict(at=at, production_target=target, before=preimage))
    dependencies = [input_path, RUN / 'painter-research-register.json.gz', RUN / 'research-identity-bindings.json',
        RUN / 'local-artists.json.gz', RUN / 'production-artists.json.gz', Path(__file__), ROOT / 'ops/research-painter-influences-20261008.py']
    plan = dict(operation=OP, at=at, production_only=True, authorization='User: go ahead! update the prod db',
        policy='Insert eligible research assertions in review; preserve existing claims and citations. No artist, artwork, identity, schema or publication changes.',
        dependencies=[dict(path=str(p.relative_to(ROOT)), sha256=checksum(p)) for p in dependencies],
        input_sha256=input_sha, backup_path=str(backup_path), backup_sha256=checksum(backup_path),
        artist_ids=sorted(needed_ids), source_slugs=sorted(definitions), before_sha256=hashlib.sha256(encoded(preimage)).hexdigest(),
        inserts=dict(sources=new_sources, influence_claims=claims, citations=citations), skipped=skipped, held=held,
        summary=dict(research_rows=len(edges), canonical_mapped_pairs=len(groups), duplicate_research_rows_merged=sum(len(g['research_rows']) - 1 for g in groups.values()),
            new_claims=len(claims), new_citations=len(citations), new_sources=len(new_sources), existing_claims_preserved=len(existing),
            existing_pairs_skipped=len(skipped), held=len(held), claim_types=dict(Counter(r['relationship_type'] for r in claims)),
            confidence=dict(Counter(r['confidence'] for r in claims)), evidence_levels=dict(Counter(r['evidence_level'] for r in claims))))
    save_new(path, plan)
    save_new(path.with_name(path.name.replace('.json.gz', '-summary.json')), dict(plan_sha256=checksum(path), **plan['summary']))
    print(json.dumps(dict(plan=str(path), sha256=checksum(path), **plan['summary']), indent=2), flush=True)


def checked_plan(path, expected_sha=None):
    digest = checksum(path)
    assert not expected_sha or expected_sha == digest, 'Plan digest mismatch'
    p = research.load(path)
    assert p['operation'] == OP and p['production_only']
    for dependency in p['dependencies']:
        assert checksum(ROOT / dependency['path']) == dependency['sha256'], ('research dependency changed', dependency['path'])
    assert checksum(Path(p['backup_path'])) == p['backup_sha256'], 'Backup changed'
    p['before'] = research.load(Path(p['backup_path']))['before']
    assert hashlib.sha256(encoded(p['before'])).hexdigest() == p['before_sha256'], 'Preimage content changed'
    for r in p['inserts']['influence_claims']:
        assert r['status'] == 'review'
    return p, digest


def preflight(db, plan):
    inspect_target(db)
    assert rows(db, 'artists', 'id=ANY(%s::uuid[])', (plan['artist_ids'],)) == plan['before']['artists'], 'Artist preimages changed'
    assert rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (plan['artist_ids'],)) == plan['before']['identifiers'], 'Artist identifiers changed'
    assert rows(db, 'influence_claims') == plan['before']['influence_claims'], 'Influence claims changed'
    assert rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([r['id'] for r in plan['before']['influence_claims']],)) == plan['before']['citations'], 'Existing citations changed'
    assert rows(db, 'sources', 'slug=ANY(%s)', (plan['source_slugs'],)) == plan['before']['sources'], 'Source registry changed'
    for table, new_rows in plan['inserts'].items():
        assert not rows(db, table, 'id=ANY(%s::uuid[])', ([r['id'] for r in new_rows],)), ('planned ID already exists', table)


def verify(db, plan):
    actual_new = {}
    for table, expected in plan['inserts'].items():
        actual = rows(db, table, 'id=ANY(%s::uuid[])', ([r['id'] for r in expected],))
        found = {r['id']: r for r in actual}
        assert len(found) == len(expected), ('new-row count', table)
        for r in expected:
            if table == 'citations':
                assert datetime.fromisoformat(found[r['id']]['retrieved_at']) == datetime.fromisoformat(r['retrieved_at'])
                fields = {k: v for k, v in r.items() if k != 'retrieved_at'}
            else:
                fields = r
            assert same_fields(found[r['id']], fields), ('new-row contents', table, r['id'])
        actual_new[table] = actual
    for table in ('artists', 'influence_claims', 'sources'):
        expected = plan['before'][table]
        assert rows(db, table, 'id=ANY(%s::uuid[])', ([r['id'] for r in expected],)) == expected, ('protected preimages changed', table)
    assert rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (plan['artist_ids'],)) == plan['before']['identifiers']
    assert rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([r['id'] for r in plan['before']['influence_claims']],)) == plan['before']['citations']
    ids = [r['id'] for r in plan['inserts']['influence_claims']]
    checks = db.execute("""SELECT count(*) AS total,
        count(*) FILTER (WHERE status='review') AS review,
        count(*) FILTER (WHERE EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='influence' AND c.entity_id=i.id AND s.is_active)) AS cited,
        count(*) FILTER (WHERE EXISTS(SELECT 1 FROM audit_log a WHERE a.entity_type='influence' AND a.entity_id=i.id AND a.action='insert')) AS audited
        FROM influence_claims i WHERE id=ANY(%s::uuid[])""", (ids,)).fetchone()
    assert all(v == len(ids) for v in checks.values()), checks
    assert db.execute('SELECT count(*) AS n FROM influence_claims').fetchone()['n'] == len(ids) + len(plan['before']['influence_claims'])
    return dict(new_rows={t: len(v) for t, v in actual_new.items()}, checks=checks,
        before_claims_preserved=len(plan['before']['influence_claims']), artist_rows_preserved=len(plan['before']['artists']),
        published_added=0, claim_types=dict(Counter(r['relationship_type'] for r in plan['inserts']['influence_claims'])),
        data_sha256={t: hashlib.sha256(encoded(v)).hexdigest() for t, v in actual_new.items()})


def apply(path, expected_sha):
    plan, digest = checked_plan(path, expected_sha)
    receipt = path.with_name(path.name.replace('.json.gz', '-applied.json'))
    # Deterministic IDs and exact readback make a completed replay a read-only no-op.
    with connections.connect('production', readonly=True) as db:
        count = db.execute('SELECT count(*) AS n FROM influence_claims WHERE id=ANY(%s::uuid[])', ([r['id'] for r in plan['inserts']['influence_claims']],)).fetchone()['n']
        if count:
            assert count == len(plan['inserts']['influence_claims']), 'Unexpected partial prior operation'
            result = verify(db, plan)
            if not receipt.exists():
                save_new(receipt, dict(at=now(), plan_sha256=digest, recovered_committed_operation=True, verification=result))
            print('Verified completed import; zero replay writes.', flush=True); return
    assert not receipt.exists()
    with connections.connect('production', readonly=False) as db:
        db.execute("SET LOCAL application_name='artline-painter-influence-import-20261008'")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (OP,))
        db.execute('LOCK TABLE influence_claims IN SHARE ROW EXCLUSIVE MODE')
        db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', (plan['artist_ids'],)).fetchall()
        db.execute('SELECT id FROM sources WHERE slug=ANY(%s) ORDER BY id FOR SHARE', (plan['source_slugs'],)).fetchall()
        preflight(db, plan)
        before_revision = db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n']
        for table in ('sources', 'influence_claims', 'citations'):
            expected = plan['inserts'][table]
            if not expected:
                continue
            fields = list(expected[0])
            assert all(set(r) == set(fields) for r in expected)
            names = sql.SQL(',').join(map(sql.Identifier, fields))
            statement = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(
                sql.Identifier(table), names, names, sql.Identifier(table))
            for offset in range(0, len(expected), 250):
                batch = expected[offset:offset + 250]
                assert db.execute(statement, (Jsonb(batch),)).rowcount == len(batch)
            print('Inserted', table, len(expected), flush=True)
        result = verify(db, plan)
        after_revision = db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n']
        assert after_revision > before_revision, 'Catalogue cache invalidation did not occur'
        result['cache_revision_before'] = int(before_revision)
        result['cache_revision_after'] = int(after_revision)
        print('All planned rows, citations, audit records and protected preimages verified before commit.', flush=True)
    save_new(receipt, dict(at=now(), plan_sha256=digest, backup_path=plan['backup_path'], backup_sha256=plan['backup_sha256'], verification=result))
    print('Production transaction committed.', flush=True)


def verify_only(path):
    plan, digest = checked_plan(path)
    with connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        result = verify(db, plan)
    receipt = path.with_name(path.name.replace('.json.gz', '-verified.json'))
    if not receipt.exists():
        save_new(receipt, dict(at=now(), plan_sha256=digest, read_only=True, verification=result))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'apply', 'verify'])
    parser.add_argument('--plan', type=Path, default=DEFAULT_PLAN)
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.plan)
    elif args.command == 'apply':
        assert args.plan_sha256, '--plan-sha256 is required'
        apply(args.plan, args.plan_sha256)
    else:
        verify_only(args.plan)
