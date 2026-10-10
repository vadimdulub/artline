#!/usr/bin/env python3
"""Deliver individually reviewed fourth-round influences to production only.

Preserves every existing claim, citation, painter status and factual field.
Uses an immutable plan, scoped backup, exact preimages and atomic insertion.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import uuid
from urllib.parse import urlparse

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('previous_delivery', Path(__file__).with_name('apply-painter-influences-20261008.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
r = d.research
ROOT = d.ROOT
OP = 'painter-influences-round4-20261009'
RUN = ROOT / 'docs/research' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
PLAN = RUN / 'production-plan-v1.json.gz'
PREVIOUS = [ROOT / 'docs/research' / name for name in ('painter-influences-round2-20261008', 'painter-influences-round3-20261009')]
CACHE = Path.home() / 'Library/Application Support/Artline/research' / OP
_extra_bindings = None


def qids_for(artist):
    global _extra_bindings
    if _extra_bindings is None:
        values = r.load(RUN / 'supplemental-identity-bindings.json') + r.load(RUN / 'research-identity-bindings.json')
        _extra_bindings = {}
        for value in values:
            if value['decision'] != 'supported_research_identity':
                continue
            aid, qid = value['artist_id'], value['qid']
            assert aid not in _extra_bindings or _extra_bindings[aid] == qid
            _extra_bindings[aid] = qid
    result = r.qids_for(artist)
    if artist['id'] in _extra_bindings:
        qid = _extra_bindings[artist['id']]
        assert not result or result == {qid}, 'Supplemental identity conflicts'
        result.add(qid)
    return result


def authority_index():
    original = r.authority_index()
    previous_run = r.RUN
    try:
        r.RUN = RUN
        original.update(r.authority_index())
    finally:
        r.RUN = previous_run
    return original


def research_roster():
    result = r.roster()
    known = {v['id'] for a in result for v in a['catalogue_bindings'] if v['catalogue'] == 'production'}
    for a in r.load(RUN / 'production-artists.json.gz'):
        if a['id'] not in known:
            a['catalogue_bindings'] = [dict(catalogue='production', id=a['id'])]
            result.append(a)
    return result


def sha(value):
    return hashlib.sha256(d.encoded(value)).hexdigest()


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artlines.org/research/' + OP + '/' + key))


def assertions():
    leads = r.load(RUN / 'candidate-passages.json.gz')
    reviews = [json.loads(line) for line in (RUN / 'reviews.jsonl').read_text().splitlines()]
    assert len({v['i'] for v in reviews}) == len(reviews)
    previous_ids = {v['lead_id'] for v in r.load(r.RUN / 'reviewed-biography-decisions.json')}
    for directory in PREVIOUS:
        previous_leads = r.load(directory / 'candidate-passages.json.gz')
        previous_ids.update(previous_leads[json.loads(line)['i']]['id'] for line in (directory / 'reviews.jsonl').read_text().splitlines())
    assert not previous_ids & {leads[v['i']]['id'] for v in reviews}, 'Previously reviewed passage reused as new research'
    result = []
    for review in reviews:
        lead = leads[review['i']]
        context = r.load((CACHE if lead.get('newcomer_discovery') else r.CACHE) / 'lead-context' / (lead['id'] + '.json.gz'))
        assert context['text'] == lead['text']
        assert hashlib.sha256(context['wikitext'].encode()).hexdigest() == lead['paragraph_sha256']
        for source, target, kind, note in review['links']:
            result.append(dict(source_qid=source, target_qid=target, relationship_type=kind, evidence=dict(
                provider='Wikipedia', language=lead['language'], source_url=lead['revision_url'], article_url=lead['source_url'],
                source_title=lead['subject_title'], retrieved_at=lead['retrieved_at'],
                paragraph_sha256=lead['paragraph_sha256'], paragraph_hash_format='original wikitext', paragraph_number=lead['paragraph_number'],
                reviewed_at=review['reviewed_at'], review_index=review['i'], lead_id=lead['id'],
                evidence_level='editorial_inference', note=note)))
    receipts = {v['key']: v for v in r.load(RUN / 'primary-source-receipts.json') + r.load(RUN / 'primary-source-receipts-extra.json')}
    import gzip
    primary = r.load(RUN / 'primary-decisions.json')
    for item in primary:
        evidence = item['evidence']
        receipt = receipts[evidence['source_receipt_key']]
        assert receipt['http_status'] == 200
        source_path = Path(receipt['cache_path'])
        raw = source_path.read_bytes()
        if source_path.suffix == '.gz':
            raw = gzip.decompress(raw)
        assert hashlib.sha256(raw).hexdigest() == receipt['sha256'] == evidence['source_sha256']
    result.extend(primary)
    for item in result:
        assert item['relationship_type'] in {'influenced', 'teacher_of', 'documented_admiration'}
        assert item['source_qid'] != item['target_qid']
        item['evidence'].update(source_wikidata_id=item['source_qid'], target_wikidata_id=item['target_qid'])
    return result, reviews


def definition(ev):
    host = urlparse(ev['source_url']).hostname.removeprefix('www.')
    if host == 'metmuseum.org':
        return dict(slug='met-the-met')
    if host == 'rmgallery.rusmuseumvrm.ru':
        return dict(slug='popular-repin-russian-museum')
    if host == 'thf.gr':
        return dict(id=uid('source/theocharakis'), slug=OP + '-theocharakis', name='B. & M. Theocharakis Foundation',
                    source_type='article', base_url='https://thf.gr', priority=40, is_active=True)
    return d.source_definition(ev)


def painter_role(authority):
    return any(re.search(r'painter|miniaturist|iconographer|watercolorist|watercolourist|ukiyo-e artist', value, re.I)
               for value in authority.get('occupations', []))


def chronology_issue(source, target, kind):
    if source.get('birth_year') is not None and target.get('death_year') is not None and source['birth_year'] > target['death_year']:
        return 'source born after target died'
    if kind == 'teacher_of' and source.get('death_year') is not None and target.get('birth_year') is not None and source['death_year'] < target['birth_year']:
        return 'teacher died before pupil was born'
    return None


def prepare(path):
    assert not path.exists(), 'Choose a new plan version; immutable plans are never overwritten.'
    items, reviews = assertions()
    auth = authority_index()
    roster = research_roster()
    byq = defaultdict(list)
    binding = {}
    original = {}
    identity = defaultdict(set)
    aliases = defaultdict(set)
    for a in roster:
        qs = qids_for(a)
        for b in a['catalogue_bindings']:
            if b['catalogue'] == 'production':
                binding[a['id']] = b['id']; original[b['id']] = a
                identity[b['id']].update(qs)
        for q in qs:
            byq[q].append(a)
            aliases[q].update(r.norm(n) for n in [a['display_name']] + a['aliases'])
    chosen = {}
    for q, values in byq.items():
        valid = [a for a in values if a['id'] in binding and qids_for(a) == {q}]
        native = [a for a in valid if any(v['scheme'] == 'wikidata' and v['external_id'] == q for v in a['identifiers'])]
        if valid:
            chosen[q] = binding[sorted(native or valid, key=lambda a: a['id'])[0]['id']]
    qs = sorted({v[k] for v in items for k in ('source_qid', 'target_qid')})
    definitions = {v['slug']: v for item in items for v in [definition(item['evidence'])]}
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        target = d.inspect_target(db)
        existing = d.rows(db, 'influence_claims')
        prior_citations = d.rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([v['id'] for v in existing],))
        native_ids = defaultdict(list)
        for v in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s)", (qs,)):
            native_ids[v['external_id']].append(v['entity_id'])
        for q, ids in native_ids.items():
            if q not in chosen and len(ids) == 1:
                chosen[q] = ids[0]
        needed = {chosen[q] for q in qs if q in chosen}
        old_endpoints = {v[k] for v in existing for k in ('source_artist_id', 'target_artist_id') if v[k]}
        all_ids = sorted(needed | old_endpoints)
        artists = d.rows(db, 'artists', 'id=ANY(%s::uuid[])', (all_ids,))
        identifiers = d.rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (all_ids,))
        sources = d.rows(db, 'sources', 'slug=ANY(%s)', (sorted(definitions),))
    current = {v['id']: v for v in artists}
    native = defaultdict(set)
    for v in identifiers:
        if v['scheme'] == 'wikidata':
            native[v['entity_id']].add(v['external_id'])
            identity[v['entity_id']].add(v['external_id'])
    for q in qs:
        aliases[q].update(r.norm(n) for n in auth.get(q, {}).get('names', []))
    old_source_qs = defaultdict(set)
    for v in prior_citations:
        try:
            note = json.loads(v['evidence_note'])
        except (ValueError, TypeError):
            continue
        if isinstance(note, dict):
            context = note.get('production_identity_context', {})
            old_source_qs[v['entity_id']].update(context.get('source_qids', []))
            for ev in note.get('evidence', []):
                if isinstance(ev, dict) and ev.get('source_wikidata_id'):
                    old_source_qs[v['entity_id']].add(ev['source_wikidata_id'])
    groups = {}; held = []
    for item in items:
        sq, tq, kind = item['source_qid'], item['target_qid'], item['relationship_type']
        sid, tid = chosen.get(sq), chosen.get(tq)
        issue = None
        if not painter_role(auth.get(sq, {})):
            issue = 'source painting practice not established by checked authority occupations'
        elif not tid:
            issue = 'target has no unambiguous identity in the research roster or fresh production Wikidata identifiers'
        for q, aid in ((sq, sid), (tq, tid)):
            if not aid:
                continue
            a = current.get(aid)
            old = original.get(aid)
            if not a or a['status'] == 'archived':
                issue = 'endpoint missing or archived'
            elif identity[aid] != {q}:
                issue = 'endpoint has conflicting or ambiguous authority IDs'
            elif old and (a['slug'] != old['slug'] or a['display_name'] != old['display_name']):
                issue = 'production identity changed since research snapshot'
            elif old and any(a.get(field) != old.get(field) for field in ('birth_year', 'death_year')):
                issue = 'production life dates changed since research snapshot; identity requires fresh review'
        if sid and sid == tid:
            issue = 'self relationship after production mapping'
        if not issue:
            source = current.get(sid, {})
            issue = chronology_issue(source, current[tid], kind)
            # Check authority chronology as well; use only uniquely reported years.
            dates = []
            for q in (sq, tq):
                value = {}
                for field in ('birth', 'death'):
                    years = {int(x.split('-')[0]) for x in auth.get(q, {}).get(field, []) if re.match(r'^\d{4}-', x)}
                    value[field + '_year'] = next(iter(years)) if len(years) == 1 else None
                dates.append(value)
            issue = issue or chronology_issue(*dates, kind)
        if issue:
            held.append(dict(reason=issue, assertion=item)); continue
        key = (sid or sq, tid, kind)
        group = groups.setdefault(key, dict(source_artist_id=sid, target_artist_id=tid, source_qid=sq, target_qid=tq,
            source_label=current[sid]['display_name'] if sid else auth[sq]['names'][0], relationship_type=kind, evidence=[]))
        if item['evidence'] not in group['evidence']:
            group['evidence'].append(item['evidence'])
    source_map = {v['slug']: v for v in sources}
    new_sources = []
    for slug, value in definitions.items():
        if slug not in source_map:
            assert value.get('id'), ('missing canonical source', slug)
            source_map[slug] = value; new_sources.append(value)
        assert source_map[slug]['is_active']
    claims = []; citations = []; skipped = []; accepted = []
    for key, g in sorted(groups.items()):
        matches = [old for old in existing if old['relationship_type'] == g['relationship_type']
            and (old['target_artist_id'] == g['target_artist_id'] or g['target_qid'] in identity[old['target_artist_id']])
            and ((g['source_artist_id'] and old['source_artist_id'] == g['source_artist_id'])
                 or g['source_qid'] in identity[old['source_artist_id']]
                 or g['source_qid'] in old_source_qs[old['id']]
                 or (not old['source_artist_id'] and r.norm(old['source_label']) in aliases[g['source_qid']]))]
        if matches:
            skipped.append(dict(existing_claim_ids=[v['id'] for v in matches], relationship=g)); continue
        level, confidence, qualification = d.grade(g['evidence'])
        preferred = [e['note'] for e in g['evidence'] if e['provider'] == 'Museum'] or [e['note'] for e in g['evidence']]
        note = ' '.join(dict.fromkeys(preferred)) + ' ' + qualification
        if g['relationship_type'] == 'teacher_of':
            note += ' Teaching does not by itself establish artistic influence.'
        claim = dict(id=uid('claim/' + json.dumps(key)), source_artist_id=g['source_artist_id'], source_label=g['source_label'],
            target_artist_id=g['target_artist_id'], relationship_type=g['relationship_type'], evidence_level=level,
            confidence=confidence, evidence_note=note, status='published', created_by=d.ACTOR, updated_by=d.ACTOR)
        claims.append(claim); accepted.append(dict(claim_id=claim['id'], **g))
        evidence_groups = defaultdict(list)
        for ev in g['evidence']:
            evidence_groups[(definition(ev)['slug'], ev['source_url'])].append(ev)
        for (slug, url), values in sorted(evidence_groups.items()):
            provenance = dict(operation=OP, evidence=values, source_qid=g['source_qid'], target_qid=g['target_qid'],
                qualification=qualification, production_identity_context=dict(source_artist_id=g['source_artist_id'],
                    target_artist_id=g['target_artist_id'], source_qids=[g['source_qid']], target_qids=[g['target_qid']]))
            if any(v['provider'] == 'Wikipedia' for v in values):
                provenance.update(attribution='Wikipedia contributors', license_url='https://creativecommons.org/licenses/by-sa/4.0/')
            citations.append(dict(id=uid('citation/' + claim['id'] + '/' + url), entity_type='influence', entity_id=claim['id'],
                field_name=claim['relationship_type'], source_id=source_map[slug]['id'], source_record_id=OP + '/' + sha(url), source_url=url,
                page_or_locator='; '.join(sorted({('paragraph ' + v['paragraph_sha256']) if v.get('paragraph_sha256') else v.get('page_or_locator', v['source_title']) for v in values})),
                evidence_note=d.encoded(provenance).decode(), retrieved_at=min(v['retrieved_at'] for v in values), created_by=d.ACTOR))
    used = {v['source_id'] for v in citations}
    new_sources = [v for v in new_sources if v['id'] in used]
    before = dict(artists=artists, identifiers=identifiers, influence_claims=existing, citations=prior_citations, sources=sources)
    backup = BACKUP / (path.name.removesuffix('.json.gz') + '-before.json.gz')
    d.save_new(backup, dict(at=d.now(), target=target, before=before))
    dependencies = [Path(__file__), Path(d.__file__), Path(r.__file__), ROOT / 'ops/align-catalogues-20261008.py']
    dependencies += [RUN / n for n in ('candidate-passages.json.gz', 'reviews.jsonl', 'primary-decisions.json', 'primary-holds.json',
        'primary-source-receipts.json', 'primary-source-receipts-extra.json', 'supplemental-identity-bindings.json',
        'supplementary-review-resolutions.json', 'initial-production-influence-coverage.json.gz',
        'research-identity-bindings.json', 'production-artists.json.gz', 'production-snapshot.json',
        'named-source-titles.json', 'named-source-resolution-receipts.json.gz')]
    dependencies += [r.RUN / n for n in ('research-identity-bindings.json', 'local-artists.json.gz', 'production-artists.json.gz')]
    dependencies += sorted((r.RUN / 'wikidata-authorities').glob('*.json.gz'))
    dependencies += [directory / name for directory in PREVIOUS for name in ('candidate-passages.json.gz', 'reviews.jsonl')]
    dependencies += [r.RUN / 'reviewed-biography-decisions.json']
    dependencies += sorted((RUN / 'wikidata-authorities').glob('*.json.gz'))
    dependencies += sorted((RUN / 'identity-search').glob('*.json'))
    plan = dict(operation=OP, at=d.now(), production_only=True,
        authorization='User: ok, this is most imporaatnt, let us do one more research and update the prod data. Prior approval covers publication of supported influence relationships; unified catalogue preserves existing statuses.',
        policy='Insert supported relationships and citations. Preserve existing records, all painter statuses, artworks and factual review flags. Unified catalogue visibility applies.',
        dependencies=[dict(path=str(p.relative_to(ROOT)), sha256=d.checksum(p)) for p in dependencies],
        backup_path=str(backup), backup_sha256=d.checksum(backup), before_sha256=sha(before),
        artist_ids=all_ids, source_slugs=sorted(definitions), inserts=dict(sources=new_sources, influence_claims=claims, citations=citations),
        accepted=accepted, skipped=skipped, held=held,
        summary=dict(reviewed_passages=len(reviews), reviewed_primary_assertions=len(r.load(RUN / 'primary-decisions.json')),
            interpreted_assertions=len(items), canonical_pairs=len(groups), new_claims=len(claims), new_citations=len(citations),
            new_sources=len(new_sources), existing_pairs_skipped=len(skipped), held_assertions=len(held),
            new_target_painters=len({v['target_artist_id'] for v in claims}),
            claim_types=dict(Counter(v['relationship_type'] for v in claims)), confidence=dict(Counter(v['confidence'] for v in claims)),
            evidence_levels=dict(Counter(v['evidence_level'] for v in claims))))
    d.save_new(path, plan)
    d.save_new(path.with_name(path.name.replace('.json.gz', '-summary.json')), dict(plan_sha256=d.checksum(path), **plan['summary']))
    print(json.dumps(dict(plan=str(path), sha256=d.checksum(path), **plan['summary']), indent=2), flush=True)


def checked(path, expected_sha=None):
    digest = d.checksum(path)
    assert not expected_sha or digest == expected_sha
    plan = r.load(path)
    assert plan['operation'] == OP and plan['production_only']
    for v in plan['dependencies']:
        assert d.checksum(ROOT / v['path']) == v['sha256'], ('changed dependency', v['path'])
    assert d.checksum(Path(plan['backup_path'])) == plan['backup_sha256']
    plan['before'] = r.load(Path(plan['backup_path']))['before']
    assert sha(plan['before']) == plan['before_sha256']
    assert all(v['status'] == 'published' for v in plan['inserts']['influence_claims'])
    return plan, digest


def verify(db, plan):
    actual_new = {}
    for table, values in plan['inserts'].items():
        actual = d.rows(db, table, 'id=ANY(%s::uuid[])', ([v['id'] for v in values],))
        found = {v['id']: v for v in actual}
        assert len(found) == len(values), ('row count', table)
        for value in values:
            fields = value.copy()
            if table == 'citations':
                assert datetime.fromisoformat(found[value['id']]['retrieved_at']) == datetime.fromisoformat(fields.pop('retrieved_at'))
            assert d.same_fields(found[value['id']], fields), ('row contents', table, value['id'])
        actual_new[table] = actual
    for table in ('artists', 'influence_claims', 'sources'):
        old = plan['before'][table]
        assert d.rows(db, table, 'id=ANY(%s::uuid[])', ([v['id'] for v in old],)) == old, ('protected records changed', table)
    assert d.rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (plan['artist_ids'],)) == plan['before']['identifiers']
    assert d.rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([v['id'] for v in plan['before']['influence_claims']],)) == plan['before']['citations']
    ids = [v['id'] for v in plan['inserts']['influence_claims']]
    checks = db.execute("""SELECT count(*) AS total,
        count(*) FILTER (WHERE i.status='published') AS published,
        count(*) FILTER (WHERE t.status<>'archived' AND (s.id IS NULL OR s.status<>'archived')
          AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)) AS publicly_eligible,
        count(*) FILTER (WHERE EXISTS(SELECT 1 FROM audit_log a WHERE a.entity_type='influence' AND a.entity_id=i.id AND a.action='insert')) AS audited
        FROM influence_claims i JOIN artists t ON t.id=i.target_artist_id LEFT JOIN artists s ON s.id=i.source_artist_id
        WHERE i.id=ANY(%s::uuid[])""", (ids,)).fetchone()
    assert all(v == len(ids) for v in checks.values()), checks
    targets = sorted({v['target_artist_id'] for v in plan['inserts']['influence_claims']})
    incoming = db.execute("""SELECT max(n) AS maximum FROM (SELECT count(*) AS n FROM influence_claims i
        JOIN artists t ON t.id=i.target_artist_id LEFT JOIN artists s ON s.id=i.source_artist_id
        WHERE i.target_artist_id=ANY(%s::uuid[]) AND i.status<>'archived' AND t.status<>'archived'
        AND (s.id IS NULL OR s.status<>'archived') AND EXISTS(SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id
        WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active) GROUP BY i.target_artist_id) counts""", (targets,)).fetchone()['maximum']
    assert incoming <= 40, ('incoming links exceed API page limit', incoming)
    total = db.execute('SELECT count(*) AS n FROM influence_claims').fetchone()['n']
    assert total == len(plan['before']['influence_claims']) + len(ids)
    return dict(checks=checks, total_claims=total, new_rows={k: len(v) for k, v in actual_new.items()},
        existing_claims_preserved=len(plan['before']['influence_claims']), existing_citations_preserved=len(plan['before']['citations']),
        painter_rows_and_statuses_preserved=len(plan['before']['artists']), max_target_incoming_links=incoming,
        data_sha256={k: sha(v) for k, v in actual_new.items()})


def apply(path, expected_sha):
    plan, digest = checked(path, expected_sha)
    receipt = path.with_name(path.name.replace('.json.gz', '-applied.json'))
    ids = [v['id'] for v in plan['inserts']['influence_claims']]
    with d.connections.connect('production', readonly=True) as db:
        count = db.execute('SELECT count(*) AS n FROM influence_claims WHERE id=ANY(%s::uuid[])', (ids,)).fetchone()['n']
        if count:
            assert count == len(ids), 'Unexpected partial prior application'
            result = verify(db, plan)
            if not receipt.exists():
                d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, recovered_committed_operation=True, verification=result))
            print('Verified completed operation; no replay writes.'); return
    assert not receipt.exists()
    with d.connections.connect('production', readonly=False) as db:
        db.execute("SET LOCAL application_name='artline-influences-round4-20261009'")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (d.OP,))
        db.execute('LOCK TABLE influence_claims IN SHARE ROW EXCLUSIVE MODE')
        db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', (plan['artist_ids'],)).fetchall()
        db.execute('SELECT id FROM sources WHERE slug=ANY(%s) ORDER BY id FOR SHARE', (plan['source_slugs'],)).fetchall()
        d.preflight(db, plan)
        before_revision = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        for table in ('sources', 'influence_claims', 'citations'):
            values = plan['inserts'][table]
            if not values:
                continue
            fields = list(values[0]); assert all(set(v) == set(fields) for v in values)
            names = sql.SQL(',').join(map(sql.Identifier, fields))
            query = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(sql.Identifier(table), names, names, sql.Identifier(table))
            for offset in range(0, len(values), 200):
                batch = values[offset:offset + 200]
                assert db.execute(query, (Jsonb(batch),)).rowcount == len(batch)
            print('Inserted', table, len(values), flush=True)
        result = verify(db, plan)
        after_revision = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        assert after_revision > before_revision
        result.update(cache_revision_before=before_revision, cache_revision_after=after_revision)
        print('Insertions, citations, audit records, visibility and protected preimages verified before commit.', flush=True)
    d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, backup_path=plan['backup_path'], backup_sha256=plan['backup_sha256'], verification=result))
    print('Production committed.', flush=True)


def verify_only(path):
    plan, digest = checked(path)
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        result = verify(db, plan)
    receipt = path.with_name(path.name.replace('.json.gz', '-verified.json'))
    if not receipt.exists():
        d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, read_only=True, verification=result))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'apply', 'verify'])
    parser.add_argument('--plan', type=Path, default=PLAN)
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.plan)
    elif args.command == 'apply':
        assert args.plan_sha256, 'Pinned --plan-sha256 is required'
        apply(args.plan, args.plan_sha256)
    else:
        verify_only(args.plan)
