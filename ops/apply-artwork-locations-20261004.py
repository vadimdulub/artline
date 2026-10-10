#!/usr/bin/env python3
"""Pinned, backed-up delivery of sourced holdings to the two real catalogues.

The plan stage is read-only. It excludes conflicting source identities and
records changed since research. Apply locks and compares exact preimages,
inserts location evidence, and preserves publication, dates, creators and media.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import uuid

from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('research', Path(__file__).with_name('research-artwork-locations-20261004.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
ACTOR = 'artwork-location-research-20261004'
EDITOR = 'local-european-research'


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/' + ACTOR + '/' + key))


def snapshots(db, ids):
    if not ids:
        return {}
    rows = db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('slug',ar.slug,'name',ar.display_name,'role',aa.attribution_role) ORDER BY ar.slug) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creator_keys,
      COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY am.media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') media,
      COALESCE((SELECT jsonb_agg(to_jsonb(h) ORDER BY h.id) FROM artwork_location_assertions h WHERE h.artwork_id=a.id),'[]') assertions
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''', (ids,)).fetchall()
    return {v['artwork']['id']: v for v in rows}


def scheme_family(scheme):
    for provider in ['joconde', 'smk', 'rijks', 'moma', 'fng', 'mia', 'walters', 'saam', 'ng', 'whitney', 'tate', 'vam', 'ycba', 'aberdeen', 'met', 'iwm', 'louvre', 'prado', 'hunterian', 'bristol', 'glasgow', 'mds', 'rmg', 'auckland']:
        if provider in scheme.split('-'):
            return provider
    return scheme


def canonical_urls(url):
    """Known official catalogue URL migrations, for conservative duplicate holds."""
    values = {url, url.replace('https://pop.culture.gouv.fr/', 'https://www.pop.culture.gouv.fr/')}
    if match := re.fullmatch(r'https://collections\.louvre\.fr/(?:en/)?ark(?::|%3[Aa])/53355/(cl\d{9})(?:\.json)?', url):
        for language in ['', 'en/']:
            for colon in [':', '%3A', '%3a']:
                values.add('https://collections.louvre.fr/' + language + 'ark' + colon + '/53355/' + match[1])
    if url.startswith('https://catalogo.cultura.gov.it/'):
        values.add(url.replace('https://catalogo.cultura.gov.it/', 'https://catalogo.beniculturali.it/'))
        values.add(url.replace('https://catalogo.cultura.gov.it/', 'http://catalogo.beniculturali.it/'))
        match = re.fullmatch(r'https://catalogo.cultura.gov.it/detail/Lombardia/HistoricOrArtisticProperty/([A-Za-z0-9-]+)_R03', url)
        if match:
            # Regional ArCo source IDs retain the exact Lombardia notice code.
            # These aliases only prevent assigning duplicate physical objects.
            for code in {match[1], match[1].lower()}:
                for prefix in ['https://', 'http://']:
                    base = prefix + 'www.lombardiabeniculturali.it/opere-arte/schede/' + code
                    values.update([base, base + '/'])
    return values


def claim_urls(claim):
    return set().union(*(canonical_urls(url) for url in [claim['source_url'], *claim.get('duplicate_source_urls', [])]))


def plan(wave, providers, targets=None):
    targets = targets or ['local', 'production']
    dest = r.RUN / 'delivery' / wave / 'plan.json.gz'
    assert not dest.exists(), 'Preserve pinned plan; use a new wave name'
    researched = {v['artwork']['id']: v for v in r.load(r.RUN / 'missing-locations.json.gz')}
    proposed = collections.defaultdict(list)
    for name in providers:
        for c in r.load(r.RUN / 'primary-plans' / (name + '.json.gz'))['claims']:
            proposed[c['artwork_id']].append({**c, 'provider': name})
    candidates, held = [], []
    for aid, group in proposed.items():
        accepted = [c for c in group if c.get('review_state', 'accepted') == 'accepted']
        pool = accepted or group
        museums = {c['institution']['id'] for c in pool}
        if len(museums) != 1:
            held.append({'artwork_id': aid, 'reason': 'conflicting_researched_museums', 'providers': [c['provider'] for c in pool]})
            continue
        candidates.append(pool[0])
    candidates.sort(key=lambda c: c['artwork_id'])
    target_snapshots, target_institutions, source_owners, target_ids = {}, {}, {}, {}
    for target in targets:
        with r.connect(target) as db:
            snap, ownership, mappings = {}, collections.defaultdict(set), {}
            available_schemes = [v['scheme'] for v in db.execute("SELECT DISTINCT scheme FROM external_identifiers WHERE entity_type='artwork'").fetchall()]
            for offset in range(0, len(candidates), 500):
                part = candidates[offset:offset+500]
                slugs = [researched[c['artwork_id']]['artwork']['slug'] for c in part]
                found = {v['slug']: str(v['id']) for v in db.execute('SELECT id,slug FROM artworks WHERE slug=ANY(%s)', (slugs,)).fetchall()}
                for c in part:
                    slug = researched[c['artwork_id']]['artwork']['slug']
                    if slug in found:
                        mappings[c['artwork_id']] = found[slug]
                snap.update(snapshots(db, list(found.values())))
                native = sorted({oid for c in part for oid in [c['external_id'], *c.get('duplicate_native_ids', [])]})
                urls = sorted(set().union(*(claim_urls(c) for c in part)))
                families = {scheme_family(c['scheme']) for c in part}
                schemes = [s for s in available_schemes if scheme_family(s) in families]
                # Separate indexed lookups avoid a global OR scan of all identifiers.
                rows = db.execute("""WITH selected AS MATERIALIZED (
                    SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers
                    WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)
                    UNION
                    SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers
                    WHERE entity_type='artwork' AND canonical_url=ANY(%s)
                  ) SELECT e.entity_id::text,e.scheme,e.external_id,e.canonical_url,a.status
                  FROM selected e JOIN artworks a ON a.id=e.entity_id WHERE a.status<>'archived'""", (schemes, native, urls)).fetchall()
                for row in rows:
                    ownership[(scheme_family(row['scheme']), row['external_id'])].add(row['entity_id'])
                    ownership[('url', row['canonical_url'])].add(row['entity_id'])
                if offset % 5000 == 0:
                    print('Preflight', target, min(offset+500, len(candidates)), '/', len(candidates), flush=True)
            target_snapshots[target] = snap
            target_ids[target] = mappings
            target_institutions[target] = [x['row'] for x in db.execute('SELECT to_jsonb(i) row FROM institutions i').fetchall()]
            source_owners[target] = ownership
    ready = []
    for c in candidates:
        aid = c['artwork_id']
        reason = None
        expected = researched[aid]
        c['target_ids'] = {}
        c['target_institutions'] = {}
        for target in targets:
            target_id = target_ids[target].get(aid)
            old = target_snapshots[target].get(target_id)
            if not old:
                reason = target + '_artwork_identity_missing'
                break
            a = old['artwork']
            if a['status'] == 'archived' or a['current_institution_id'] or any(h['claim_type'] == 'holding' and h['review_state'] == 'accepted' and not h['superseded_by'] for h in old['assertions']):
                reason = target + '_already_has_holding_or_archived'
                break
            keys = ['title', 'alternate_title', 'date_display', 'creation_year_start', 'creation_year_end', 'date_precision', 'work_type', 'accession_number', 'unlinked_creator_label']
            if any(a[k] != expected['artwork'][k] for k in keys):
                reason = target + '_identity_metadata_differs_from_research'
                break
            old_creators = sorted((v['slug'], v['name'], v['role']) for v in old['creator_keys'])
            research_creators = sorted((v['slug'], v['name'], v['role']) for v in expected['artists'])
            if old_creators != research_creators:
                reason = target + '_creator_relationship_differs'
                break
            owners = set().union(*(source_owners[target][(scheme_family(c['scheme']), oid)] for oid in [c['external_id'], *c.get('duplicate_native_ids', [])])) | set().union(*(source_owners[target][('url', url)] for url in claim_urls(c)))
            if owners - {target_id}:
                reason = target + '_source_object_already_represents_another_artwork'
                break
            same_scheme = [e for e in old['identifiers'] if e['scheme'] == c['scheme']]
            known_ids = {c['external_id'], *c.get('duplicate_native_ids', [])}
            if same_scheme and any(e['external_id'] not in known_ids for e in same_scheme):
                reason = target + '_native_identifier_conflict'
                break
            inst = c['institution']
            matches = [i for i in target_institutions[target] if i['id'] == inst['id'] or i['slug'] == inst['slug'] or (inst.get('wikidata_id') and i.get('wikidata_id') == inst['wikidata_id'])]
            if len(matches) > 1 or (matches and (matches[0]['slug'] != inst['slug'] or matches[0]['name'] != inst['name'] or matches[0]['status'] == 'archived')):
                reason = target + '_institution_identity_conflict'
                break
            c['target_ids'][target] = target_id
            c['target_institutions'][target] = matches[0] if matches else inst
        if reason:
            held.append({'artwork_id': aid, 'reason': reason, 'provider': c['provider'], 'source_url': c['source_url']})
        else:
            ready.append(c)
    # New claims must not assign a single exact physical source object to two rows.
    groups = collections.defaultdict(list)
    for c in ready:
        groups[(scheme_family(c['scheme']), c['external_id'])].append(c)
    duplicate_ids = {c['artwork_id'] for group in groups.values() if len(group) > 1 for c in group}
    for aid in sorted(duplicate_ids):
        held.append({'artwork_id': aid, 'reason': 'multiple_catalogue_rows_match_one_source_object'})
    ready = [c for c in ready if c['artwork_id'] not in duplicate_ids]
    ready_ids = {c['artwork_id'] for c in ready}
    preimages = {}
    for target in targets:
        included = {c['target_ids'][target] for c in ready}
        assert len(included) == len(ready), 'Two local records map to one target'
        before = {aid: old for aid, old in target_snapshots[target].items() if aid in included}
        path = r.BACKUP / wave / (target + '-preimages.json.gz')
        r.save_gz(path, before)
        preimages[target] = {'path': str(path), 'sha256': r.sha(path.read_bytes())}
    payload = {'at': r.now(), 'wave': wave, 'providers': providers, 'targets': targets, 'claims': ready, 'held': held, 'preimages': preimages,
               'policy': 'Apply supported holding evidence only; preserve every existing artwork, attribution, creation date, publication state and image. Review claims do not set a current institution. No current-display inference.'}
    r.save_gz(dest, payload)
    r.save(dest.with_name('plan-pin.json'), {'sha256': r.sha(dest.read_bytes()), 'records': len(ready), 'held': len(held), 'by_provider': dict(collections.Counter(c['provider'] for c in ready)), 'new_institutions': [i for i in {c['institution']['id']: c['institution'] for c in ready}.values() if not any(x['id'] == i['id'] for x in target_institutions[targets[0]])]})
    summary = r.load(dest.with_name('plan-pin.json'))
    summary['new_institution_count'] = len(summary.pop('new_institutions'))
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    print('Preflight holds', collections.Counter(h['reason'] for h in held), flush=True)


def pinned(wave):
    folder = r.RUN / 'delivery' / wave
    path = folder / 'plan.json.gz'
    pin = r.load(folder / 'plan-pin.json')
    assert r.sha(path.read_bytes()) == pin['sha256']
    data = r.load(path)
    for v in data['preimages'].values():
        assert r.sha(Path(v['path']).read_bytes()) == v['sha256']
    return data, pin['sha256']


def backup():
    r.BACKUP.mkdir(parents=True, exist_ok=True)
    path = r.BACKUP / 'local-before.dump'
    if not path.exists():
        temp = path.with_suffix('.incomplete')
        subprocess.run(['pg_dump', '-h', 'localhost', '-d', 'artline', '-Fc', '-f', str(temp)], check=True)
        subprocess.run(['pg_restore', '--list', str(temp)], check=True, stdout=subprocess.DEVNULL)
        temp.rename(path)
    subprocess.run(['pg_restore', '--list', str(path)], check=True, stdout=subprocess.DEVNULL)
    with path.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    description = 'Before artwork museum location research 20261004'
    receipt = r.BACKUP / 'production-backup-create.json'
    if not receipt.exists():
        raw = subprocess.check_output(['gcloud', 'sql', 'backups', 'create', '--instance=artline-postgres', '--project=artline-508319', '--description=' + description, '--format=json'])
        r.save(receipt, raw)
    backups = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'list', '--instance=artline-postgres', '--project=artline-508319', '--limit=20', '--format=json']))
    item = next(v for v in backups if v.get('description') == description)
    assert item['status'] == 'SUCCESSFUL'
    r.save(r.RUN / 'backups.json', {'at': r.now(), 'local': {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}, 'production': item})
    print('Verified recovery backups', path.stat().st_size, 'bytes, Cloud SQL backup', item['id'], flush=True)


def apply(wave, target, batch_limit=0):
    data, digest = pinned(wave)
    backups = r.load(r.RUN / 'backups.json')
    assert backups['production']['status'] == 'SUCCESSFUL'
    before = r.load(data['preimages'][target]['path'])
    folder = r.RUN / 'delivery' / wave / target
    with r.connect(target, readonly=False) as db:
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active', (EDITOR,)).fetchone(), 'Established catalogue research actor required'
        # Related authority rows are inserted in the same transaction as each batch.
        for offset in range(0, len(data['claims']), 100):
            if batch_limit and offset >= batch_limit * 100:
                break
            group = [{**c, 'artwork_id': c['target_ids'][target], 'institution': c['target_institutions'][target]} for c in data['claims'][offset:offset+100]]
            dest = folder / f'{offset//100:04d}.json'
            if dest.exists():
                continue
            ids = [c['artwork_id'] for c in group]
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='10s'")
                db.execute("SET LOCAL statement_timeout='120s'")
                db.execute('SELECT pg_advisory_xact_lock(202610041)')
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (ids,)).fetchall()
                current = snapshots(db, ids)
                assertion_ids = [uid(wave + '/holding/' + aid) for aid in ids]
                existing = {str(v['id']) for v in db.execute('SELECT id FROM artwork_location_assertions WHERE id=ANY(%s::uuid[])', (assertion_ids,)).fetchall()}
                if existing:
                    assert len(existing) == len(group), 'Partial batch unexpectedly present'
                    # A committed batch whose receipt was interrupted is verified below.
                else:
                    assert current == {aid: before[aid] for aid in ids}, 'Live catalogue changed after pinned preflight'
                    for inst in {c['institution']['id']: c['institution'] for c in group}.values():
                        db.execute('''INSERT INTO institutions(id,slug,name,normalized_name,website_url,wikidata_id,kind,status,description)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,'review',%s) ON CONFLICT(id) DO NOTHING''', (inst['id'], inst['slug'], inst['name'], inst['normalized_name'], inst.get('website_url'), inst.get('wikidata_id'), inst['kind'], inst.get('description', '')))
                    for provider in sorted({c['provider'] for c in group}):
                        c = next(c for c in group if c['provider'] == provider)
                        db.execute('''INSERT INTO sources(id,slug,name,source_type,base_url,is_active) VALUES(%s,%s,%s,'collection_page',%s,true) ON CONFLICT(id) DO NOTHING''', (uid('source/' + provider), ACTOR + '-' + provider, 'Artwork museum location research: ' + provider, c['source_url']))
                    records = []
                    for c in group:
                        aid = c['artwork_id']
                        sid = uid('source/' + c['provider'])
                        evidence = {'operation': ACTOR, 'wave': wave, 'plan_sha256': digest, 'identity_basis': c['identity_basis'], 'source_class': c['source_class'], 'scheme': c['scheme'], 'object_id': c['external_id'], 'institution': c['institution']['name'], 'source_response_sha256': c['source_receipt']['sha256'], 'source_response_url': c['source_receipt']['url'], 'evidence_path': c['source_receipt']['body_path'], 'limitation': c['limitation']}
                        records.append({'id': uid(wave + '/holding/' + aid), 'artwork_id': aid, 'institution_id': c['institution']['id'], 'source_id': sid, 'source_url': c['source_url'], 'evidence_note': json.dumps(evidence, ensure_ascii=False), 'checked_at': c['checked_at'], 'review_state': c.get('review_state', 'accepted'), 'citation_id': uid(wave + '/citation/' + aid), 'external_record_id': c['external_id'], 'location_text': c['location_text']})
                    db.execute('''INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                      SELECT id,artwork_id,'holding',institution_id,'collection',source_id,source_url,evidence_note,checked_at,review_state
                      FROM jsonb_to_recordset(%s) x(id uuid,artwork_id uuid,institution_id uuid,source_id uuid,source_url text,evidence_note text,checked_at timestamptz,review_state text)''', (Jsonb(records),))
                    db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                      SELECT citation_id,'artwork',artwork_id,'museum_holding_research',source_id,external_record_id,source_url,evidence_note,checked_at,%s
                      FROM jsonb_to_recordset(%s) x(citation_id uuid,artwork_id uuid,source_id uuid,external_record_id text,source_url text,evidence_note text,checked_at timestamptz)''', (EDITOR, Jsonb(records)))
                    db.execute('''UPDATE artworks a SET current_location_text=x.location_text,current_location_unknown_reason=NULL,location_checked_at=x.checked_at,revision=a.revision+1,updated_at=now(),updated_by=%s
                      FROM jsonb_to_recordset(%s) x(artwork_id uuid,location_text text,checked_at timestamptz,review_state text)
                      WHERE a.id=x.artwork_id AND x.review_state='accepted' ''', (EDITOR, Jsonb(records)))
                check = db.execute('SELECT id,artwork_id,institution_id,review_state FROM artwork_location_assertions WHERE id=ANY(%s::uuid[])', (assertion_ids,)).fetchall()
                assert len(check) == len(group)
                expected = {uid(wave + '/holding/' + c['artwork_id']): (c['artwork_id'], c['institution']['id'], c.get('review_state', 'accepted')) for c in group}
                assert all((str(v['artwork_id']), str(v['institution_id']), v['review_state']) == expected[str(v['id'])] for v in check)
            r.save(dest, {'at': r.now(), 'plan_sha256': digest, 'target': target, 'artwork_ids': ids, 'assertion_ids': assertion_ids})
            print('Applied', target, wave, min(offset+100, len(data['claims'])), '/', len(data['claims']), flush=True)


def verify(wave, targets=None):
    data, digest = pinned(wave)
    targets = targets or data.get('targets', ['local', 'production'])
    totals = {}
    for target in targets:
        before = r.load(data['preimages'][target]['path'])
        count = 0
        with r.connect(target) as db:
            for offset in range(0, len(data['claims']), 500):
                group = [{**c, 'artwork_id': c['target_ids'][target], 'institution': c['target_institutions'][target]} for c in data['claims'][offset:offset+500]]
                after = snapshots(db, [c['artwork_id'] for c in group])
                for c in group:
                    aid = c['artwork_id']
                    old, new = before[aid], after[aid]
                    accepted = c.get('review_state', 'accepted') == 'accepted'
                    allowed = {'current_institution_id', 'current_location_text', 'current_location_unknown_reason', 'location_checked_at', 'revision', 'updated_at', 'updated_by'} if accepted else set()
                    assert {k: v for k, v in old['artwork'].items() if k not in allowed} == {k: v for k, v in new['artwork'].items() if k not in allowed}, ('Unexpected artwork change', target, aid)
                    for key in ['identifiers', 'creators', 'creator_keys', 'media']:
                        assert old[key] == new[key], ('Relationship changed', target, aid, key)
                    by_id = {v['id']: v for v in new['assertions']}
                    assert len(new['assertions']) == len(old['assertions']) + 1
                    assert all(by_id[v['id']] == v for v in old['assertions'])
                    assertion = by_id[uid(wave + '/holding/' + aid)]
                    assert assertion['review_state'] == c.get('review_state', 'accepted') and assertion['institution_id'] == c['institution']['id'] and assertion['source_url'] == c['source_url']
                    assert assertion['claim_type'] == 'holding' and assertion['display_state'] is None
                    if accepted:
                        assert new['artwork']['current_institution_id'] == c['institution']['id'] and new['artwork']['current_location_text'] == c['location_text'] and new['artwork']['current_location_unknown_reason'] is None
                        assert new['artwork']['revision'] == old['artwork']['revision'] + 1
                    count += 1
            citations = db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])', ([uid(wave + '/citation/' + c['target_ids'][target]) for c in data['claims']],)).fetchone()['n']
            assert citations == count
        totals[target] = count
    assert all(n == len(data['claims']) for n in totals.values())
    filename = 'verification.json' if set(targets) == set(data.get('targets', ['local', 'production'])) else 'verification-' + '-'.join(targets) + '.json'
    r.save(r.RUN / 'delivery' / wave / filename, {'at': r.now(), 'plan_sha256': digest, 'targets': totals, 'accepted_holdings': sum(c.get('review_state', 'accepted') == 'accepted' for c in data['claims']), 'review_assertions': sum(c.get('review_state') == 'review' for c in data['claims']), 'prior_records_and_relationships_preserved': True, 'publication_and_date_fields_preserved': True, 'new_display_claims': 0, 'errors': []})
    print('Verified', wave, totals, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'backup', 'apply', 'verify'])
    parser.add_argument('--wave', default='primary-01')
    parser.add_argument('--providers', nargs='+', default=['moma', 'fng', 'mia', 'lombardia'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    parser.add_argument('--batch-limit', type=int, default=0)
    parser.add_argument('--targets', nargs='+', choices=['local', 'production'])
    args = parser.parse_args()
    if args.command == 'plan':
        plan(args.wave, args.providers, args.targets)
    elif args.command == 'backup':
        backup()
    elif args.command == 'apply':
        apply(args.wave, args.target, args.batch_limit)
    else:
        verify(args.wave, args.targets)
