#!/usr/bin/env python3
"""Preserve unresolved location evidence as review citations in existing records.

No institutions, holding assertions, display assertions, or artworks are changed.
Ambiguous source-object duplicates remain evidence requiring identity review.
"""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
from psycopg.types.json import Jsonb

s = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-artwork-locations-20261004.py'))
d = importlib.util.module_from_spec(s)
s.loader.exec_module(d)
r = d.r
WAVE = 'location-leads-review-01'
FOLDER = r.RUN / 'delivery' / WAVE
FIELD = 'museum_location_lead_review'


def snapshots(db, ids):
    result = d.snapshots(db, ids)
    for v in result.values():
        v['citations'] = []
    for v in db.execute("SELECT entity_id::text,to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id", (ids,)).fetchall():
        result[v['entity_id']]['citations'].append(v['row'])
    return result


def candidates(original):
    leads = {}
    latest = {p.name: p for p in (r.RUN / 'wikiart-leads').glob('*.json')}
    latest.update({p.name: p for p in (r.RUN / 'wikiart-leads-retry-20261005').glob('*.json')})
    for path in sorted(latest.values()):
        v = r.load(path)
        if v['outcome'] not in ['museum_lead_requires_corroboration', 'non_museum_or_unknown_location']:
            continue
        aid = v['artwork_id']
        row = original[aid]
        assert any(e['scheme'] == 'wikiart-artwork' and e['external_id'] == v['external_id'] and e['canonical_url'] == v['source_url'] for e in row['identifiers'])
        assert v['source_receipt']['status'] == 200 and v['fields'].get('Location')
        creators = [a['name'] for a in row['artists']]
        if row['artwork'].get('unlinked_creator_label'):
            creators.append(row['artwork']['unlinked_creator_label'])
        lead = {'artwork_id': aid, 'provider': 'wikiart-location-review-20261005', 'external_id': v['external_id'], 'source_url': v['source_url'], 'source_receipt': v['source_receipt'], 'review_state': 'review', 'reported_location': v['fields']['Location'], 'source_title': v['source_title'], 'source_artist': v.get('source_artist'), 'source_fields': v['fields'], 'source_outcome': v['outcome'], 'creator_name_agrees': r.namekey(v.get('source_artist')) in {r.namekey(x) for x in creators}, 'limitation': 'Uncorroborated secondary-source location text, retained as a review citation only. It may describe an old location, a private collection, or an unresolved institution. Does not establish museum identity, legal ownership, present physical location, public display, or an accepted artwork attribution.'}
        leads[(aid, lead['source_url'])] = lead
    # Preserve the exact supported-source candidate when delivery was held for
    # a duplicate identity. A citation cannot assign the object to another row.
    for path in sorted((r.RUN / 'delivery').glob('*/plan.json.gz')):
        data = r.load(path)
        if 'claims' not in data or path.parent.name == 'primary-01':
            continue
        held = {v['artwork_id']: v for v in data.get('held', []) if v['reason'].endswith('source_object_already_represents_another_artwork') or v['reason'] == 'multiple_catalogue_rows_match_one_source_object'}
        if not held:
            continue
        for provider in data['providers']:
            for c in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
                aid = c['artwork_id']
                if aid not in held:
                    continue
                key = (aid, c['source_url'])
                lead = {'artwork_id': aid, 'provider': 'duplicate-object-review-20261005', 'external_id': c['external_id'], 'source_url': c['source_url'], 'source_receipt': c['source_receipt'], 'review_state': 'review', 'reported_location': c['institution']['name'], 'candidate_institution': c['institution'], 'scheme': c['scheme'], 'identity_basis': c['identity_basis'], 'source_class': c['source_class'], 'preflight_hold': held[aid], 'candidate_evidence_path': str(path.relative_to(r.ROOT)), 'requires_duplicate_reconciliation': True, 'limitation': 'Candidate source object also represents another catalogue row, or several catalogue rows match the same source object. Identity must be reconciled before accepting any holding. This citation preserves the lead without assigning a current institution, merging records, or changing attribution. ' + c['limitation']}
                if key in leads:
                    previous = leads[key]
                    # One object URL can be supported by different scoped
                    # searches or later source captures. Preserve both proofs.
                    if previous['source_receipt'] != lead['source_receipt']:
                        if previous['source_receipt']['body_path'] == lead['source_receipt']['body_path']:
                            assert previous['source_receipt']['sha256'] == lead['source_receipt']['sha256']
                        lead['previous_research_captures'] = [*previous.get('previous_research_captures', []),
                            {'source_receipt': previous['source_receipt'], 'candidate_evidence_path': previous.get('candidate_evidence_path'), 'preflight_hold': previous.get('preflight_hold')}]
                leads[key] = lead
    return sorted(leads.values(), key=lambda v: (v['artwork_id'], v['source_url']))


def plan():
    assert not (FOLDER / 'plan.json.gz').exists()
    original = {v['artwork']['id']: v for v in r.load(r.RUN / 'missing-locations.json.gz')}
    leads = candidates(original)
    ids = sorted({v['artwork_id'] for v in leads})
    before, mappings, held = {}, {}, {}
    keys = ['title', 'alternate_title', 'date_display', 'creation_year_start', 'creation_year_end', 'date_precision', 'work_type', 'accession_number', 'unlinked_creator_label']
    for target in ['local', 'production']:
        before[target], mappings[target] = {}, {}
        with r.connect(target) as db:
            for start in range(0, len(ids), 500):
                part = ids[start:start+500]
                slugs = [original[aid]['artwork']['slug'] for aid in part]
                found = {v['slug']: str(v['id']) for v in db.execute('SELECT id,slug FROM artworks WHERE slug=ANY(%s)', (slugs,)).fetchall()}
                snap = snapshots(db, list(found.values()))
                for aid in part:
                    tid = found.get(original[aid]['artwork']['slug'])
                    old = snap.get(tid)
                    if not old or old['artwork']['status'] == 'archived':
                        held[aid] = target + '_identity_missing_or_archived'
                    elif any(old['artwork'][k] != original[aid]['artwork'][k] for k in keys):
                        held[aid] = target + '_identity_changed_since_research'
                    elif sorted((v['slug'], v['name'], v['role']) for v in old['creator_keys']) != sorted((v['slug'], v['name'], v['role']) for v in original[aid]['artists']):
                        held[aid] = target + '_creators_changed_since_research'
                    else:
                        before[target][tid] = old
                        mappings[target][aid] = tid
                print('Review citation preflight', target, min(start+500, len(ids)), '/', len(ids), flush=True)
    ready = []
    for lead in leads:
        aid = lead['artwork_id']
        if aid not in held:
            lead['target_ids'] = {t: mappings[t][aid] for t in mappings}
            ready.append(lead)
    preimages = {}
    for target in before:
        tids = {v['target_ids'][target] for v in ready}
        path = r.BACKUP / WAVE / (target + '-preimages.json.gz')
        r.save_gz(path, {tid: before[target][tid] for tid in tids})
        preimages[target] = {'path': str(path), 'sha256': r.sha(path.read_bytes())}
    payload = {'at': r.now(), 'wave': WAVE, 'leads': ready, 'held': held, 'preimages': preimages}
    r.save_gz(FOLDER / 'plan.json.gz', payload)
    summary = {'sha256': r.sha((FOLDER / 'plan.json.gz').read_bytes()), 'citations': len(ready), 'artworks': len({v['artwork_id'] for v in ready}), 'by_provider': dict(collections.Counter(v['provider'] for v in ready)), 'held': len(held)}
    r.save(FOLDER / 'plan-pin.json', summary)
    print(json.dumps(summary), flush=True)


def pinned():
    path = FOLDER / 'plan.json.gz'
    digest = r.load(FOLDER / 'plan-pin.json')['sha256']
    assert r.sha(path.read_bytes()) == digest
    data = r.load(path)
    for v in data['preimages'].values():
        assert r.sha(Path(v['path']).read_bytes()) == v['sha256']
    return data, digest


def record(v, target, digest):
    assert v['review_state'] == 'review', 'This writer only accepts explicitly marked review evidence'
    aid = v['target_ids'][target]
    evidence = {k: val for k, val in v.items() if k not in ['target_ids', 'artwork_id']}
    evidence.update(operation=d.ACTOR, wave=WAVE, plan_sha256=digest)
    return {'id': d.uid(WAVE + '/citation/' + aid + '/' + v['source_url']), 'entity_id': aid, 'source_id': d.uid('source/' + v['provider']), 'source_record_id': v['external_id'], 'source_url': v['source_url'], 'evidence_note': json.dumps(evidence, ensure_ascii=False), 'retrieved_at': v['source_receipt']['retrieved_at']}


def apply(target):
    data, digest = pinned()
    assert r.load(r.RUN / 'backups.json')['production']['status'] == 'SUCCESSFUL'
    before = r.load(data['preimages'][target]['path'])
    groups = collections.defaultdict(list)
    for v in data['leads']:
        groups[v['target_ids'][target]].append(v)
    ids = sorted(groups)
    with r.connect(target, readonly=False) as db:
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active', (d.EDITOR,)).fetchone()
        for offset in range(0, len(ids), 100):
            path = FOLDER / target / f'{offset//100:04d}.json'
            if path.exists():
                continue
            part = ids[offset:offset+100]
            leads = [v for aid in part for v in groups[aid]]
            records = [record(v, target, digest) for v in leads]
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='10s'")
                db.execute('SELECT pg_advisory_xact_lock(202610041)')
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (part,)).fetchall()
                existing = db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])', ([v['id'] for v in records],)).fetchone()['n']
                if existing:
                    assert existing == len(records), 'Unexpected partial citation batch'
                else:
                    assert snapshots(db, part) == {aid: before[aid] for aid in part}, 'Catalogue changed since citation preflight'
                    for provider in sorted({v['provider'] for v in leads}):
                        source = next(v for v in leads if v['provider'] == provider)
                        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,is_active) VALUES(%s,%s,%s,'collection_page',%s,true) ON CONFLICT(id) DO NOTHING", (d.uid('source/' + provider), d.ACTOR + '-' + provider, 'Unresolved artwork location evidence for review: ' + provider, source['source_url']))
                    db.execute("""INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                      SELECT id,'artwork',entity_id,%s,source_id,source_record_id,source_url,evidence_note,retrieved_at,%s
                      FROM jsonb_to_recordset(%s) x(id uuid,entity_id uuid,source_id uuid,source_record_id text,source_url text,evidence_note text,retrieved_at timestamptz)""", (FIELD, d.EDITOR, Jsonb(records)))
            r.save(path, {'at': r.now(), 'plan_sha256': digest, 'artwork_ids': part, 'citation_ids': [v['id'] for v in records]})
            print('Applied review citations', target, min(offset+100, len(ids)), '/', len(ids), flush=True)


def verify():
    data, digest = pinned()
    totals = {}
    for target in data['preimages']:
        before = r.load(data['preimages'][target]['path'])
        groups = collections.defaultdict(list)
        for v in data['leads']:
            groups[v['target_ids'][target]].append(record(v, target, digest))
        ids = sorted(groups)
        with r.connect(target) as db:
            for offset in range(0, len(ids), 500):
                after = snapshots(db, ids[offset:offset+500])
                assert len(after) == len(ids[offset:offset+500])
                for aid, new in after.items():
                    old = before[aid]
                    assert {k:v for k,v in new.items() if k != 'citations'} == {k:v for k,v in old.items() if k != 'citations'}
                    citations = {v['id']:v for v in new['citations']}
                    assert len(citations) == len(old['citations']) + len(groups[aid])
                    assert all(citations[v['id']] == v for v in old['citations'])
                    for expected in groups[aid]:
                        actual = citations[expected['id']]
                        assert actual['entity_type'] == 'artwork' and actual['field_name'] == FIELD and actual['created_by'] == d.EDITOR
                        for key in ['id', 'entity_id', 'source_id', 'source_record_id', 'source_url']:
                            assert actual[key] == expected[key], (target, aid, key)
                        assert json.loads(actual['evidence_note']) == json.loads(expected['evidence_note'])
        totals[target] = len(data['leads'])
    r.save(FOLDER / 'verification.json', {'at': r.now(), 'plan_sha256': digest, 'targets': totals, 'all_prior_artwork_data_assertions_and_citations_preserved': True, 'review_only': True, 'new_holdings': 0, 'new_display_claims': 0})
    print('Verified review citations', totals, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    args = parser.parse_args()
    apply(args.target) if args.command == 'apply' else verify() if args.command == 'verify' else plan()
