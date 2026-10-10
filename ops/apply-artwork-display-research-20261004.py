#!/usr/bin/env python3
"""Deliver three explicit dated display/location observations, separately from holdings."""
import argparse
import importlib.util
from pathlib import Path
import json
from psycopg.types.json import Jsonb

s = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-artwork-locations-20261004.py'))
a = importlib.util.module_from_spec(s)
s.loader.exec_module(a)
r = a.r
WAVE = 'dated-display-02'
FOLDER = r.RUN / 'delivery' / WAVE
LAVRA_URL = 'https://lavra.ru/lavra-news/kommentariy-namestnika-troitse-sergievoy-lavry-o-sostoyanii-ikony-svyatoy-troitsy-napisannoy-prepodo/'


def plan():
    assert not (FOLDER / 'plan.json.gz').exists()
    prior = r.RUN / 'delivery/dated-display-01/plan.json.gz'
    if prior.exists():
        assert r.sha(prior.read_bytes()) == r.load(prior.with_name('pin.json'))['sha256']
        data = r.load(prior)
        for target, records in data['targets'].items():
            for v in records:
                if v['display_state'] == 'not_on_view':
                    v['venue'] = None
                else:
                    v['venue']['visit_url'] = v['institution']['website_url']
            r.save_gz(r.BACKUP / WAVE / (target + '-preimages.json.gz'), {v['artwork_id']: v['before'] for v in records})
        data['schema_adjustment'] = 'Preserved original pinned read-only preimages; required public museum visit link added, and inaccessible workshop kept without a visiting venue. First local transaction rolled back in full.'
        r.save_gz(FOLDER / 'plan.json.gz', data)
        r.save(FOLDER / 'pin.json', {'sha256': r.sha((FOLDER / 'plan.json.gz').read_bytes()), 'records_per_target': 3, 'on_view': 2, 'not_on_view': 1})
        print('Pinned schema-compatible dated observations; exact preimages checked again on apply')
        return
    curated, _ = a.pinned('curated-01')
    claims = {c['artwork_id']: c for c in curated['claims']}
    specs = [('03d32934-c867-5df7-a95e-3446c2f92ee4', 'on_view'), ('02b0f1cc-ae7f-5ba3-b889-df8e37940139', 'on_view'), ('1bc60885-3b30-50ff-b94d-38eeac4e98fd', 'not_on_view')]
    targets = {}
    for target in ['local', 'production']:
        records = []
        with r.connect(target) as db:
            for aid, state in specs:
                c = claims[aid]
                tid = c['target_ids'][target]
                old = a.snapshots(db, [tid])[tid]
                assert not any(h['claim_type'] == 'display' and h['review_state'] == 'accepted' and not h['superseded_by'] for h in old['assertions'])
                if state == 'on_view':
                    inst = c['target_institutions'][target]
                    venue = {'id': a.uid('venue/greek-national-gallery-main-building'), 'institution_id': inst['id'], 'slug': 'national-gallery-greece-main-building', 'name': 'National Gallery – Main Building', 'place_id': inst.get('place_id'), 'source_url': c['source_url'], 'visit_url': inst['website_url']}
                    receipt = c['source_receipt']
                    note = 'The current official object page explicitly states “On view Main Building”. This is a dated observation for this exact inventory, not inferred from museum membership.'
                    context, updated = 'collection', None
                else:
                    inst = {'id': a.uid('institution/trinity-lavra-of-st-sergius'), 'slug': 'trinity-lavra-of-st-sergius', 'name': 'Trinity Lavra of St Sergius', 'normalized_name': 'trinity lavra of st sergius', 'kind': 'historic_site', 'website_url': 'https://lavra.ru/', 'wikidata_id': None, 'description': 'Historic monastery and documented loan destination of Rublev’s Trinity. Its September 2026 statement locates the original in its conservation workshop; it does not establish public access to that workshop.'}
                    existing = db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=%s', (inst['slug'],)).fetchone()
                    if existing:
                        inst = existing['row']
                    venue = None  # No public visiting venue is asserted for a workshop.
                    receipt = c['object_evidence']['dated_physical_location_source']
                    note = 'The Lavra’s official statement dated 19 September 2026 says the original Rublev Trinity is in its conservation workshop, removed from the cathedral iconostasis for work on the climate-controlled case. This records the latest located statement, not a claim of a new observation on 4 October. Museum collection association is preserved separately.'
                    context, updated = 'loan', '2026-09-19T00:00:00Z'
                records.append({'artwork_id': tid, 'local_artwork_id': aid, 'institution': inst, 'venue': venue, 'display_state': state, 'context': context, 'source_receipt': receipt, 'source_url': receipt['url'], 'source_updated_at': updated, 'note': note, 'before': old})
        targets[target] = records
        r.save_gz(r.BACKUP / WAVE / (target + '-preimages.json.gz'), {v['artwork_id']: v['before'] for v in records})
    r.save_gz(FOLDER / 'plan.json.gz', {'at': r.now(), 'targets': targets})
    r.save(FOLDER / 'pin.json', {'sha256': r.sha((FOLDER / 'plan.json.gz').read_bytes()), 'records_per_target': 3, 'on_view': 2, 'not_on_view': 1})
    print('Pinned three dated observations for both catalogues', flush=True)


def pinned():
    path = FOLDER / 'plan.json.gz'
    digest = r.load(FOLDER / 'pin.json')['sha256']
    assert r.sha(path.read_bytes()) == digest
    return r.load(path), digest


def apply(target):
    data, digest = pinned()
    records = data['targets'][target]
    sid = a.uid('source/' + WAVE)
    with r.connect(target, readonly=False) as db:
        with db.transaction():
            db.execute("SET LOCAL lock_timeout='30s'")
            db.execute('SELECT pg_advisory_xact_lock(202610041)')
            ids = sorted(v['artwork_id'] for v in records)
            db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (ids,)).fetchall()
            existing = db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE id=ANY(%s::uuid[])', ([a.uid(WAVE + '/' + tid) for tid in ids],)).fetchone()['n']
            if existing:
                assert existing == len(records)
                print('Dated observations already present', target)
                return
            assert a.snapshots(db, ids) == {v['artwork_id']: v['before'] for v in records}, 'Artwork changed since display preflight'
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,is_active) VALUES(%s,%s,%s,'collection_page',%s,true)", (sid, a.ACTOR + '-' + WAVE, 'Dated primary-source artwork display observations', records[0]['institution']['website_url']))
            for v in records:
                inst, venue = v['institution'], v['venue']
                db.execute("INSERT INTO institutions(id,slug,name,normalized_name,website_url,kind,status,description) VALUES(%s,%s,%s,%s,%s,%s,'review',%s) ON CONFLICT(id) DO NOTHING", (inst['id'], inst['slug'], inst['name'], inst['normalized_name'], inst.get('website_url'), inst['kind'], inst.get('description', '')))
                if venue:
                    db.execute("INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'review') ON CONFLICT(id) DO NOTHING", (venue['id'], inst['id'], venue['slug'], venue['name'], venue['place_id'], venue['visit_url'], venue['source_url'], v['source_receipt']['retrieved_at']))
                evidence = json.dumps({'operation': a.ACTOR, 'wave': WAVE, 'plan_sha256': digest, 'observation': v['note'], 'source_receipt': v['source_receipt']}, ensure_ascii=False)
                db.execute("""INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,venue_id,display_state,context,source_id,source_url,evidence_note,checked_at,source_updated_at,review_state)
                  VALUES(%s,%s,'display',%s,%s,%s,%s,%s,%s,%s,%s,%s,'accepted')""", (a.uid(WAVE + '/' + v['artwork_id']), v['artwork_id'], inst['id'], venue['id'] if venue else None, v['display_state'], v['context'], sid, v['source_url'], evidence, v['source_receipt']['retrieved_at'], v['source_updated_at']))
                db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,'dated_display_location',%s,%s,%s,%s,%s)", (a.uid(WAVE + '/citation/' + v['artwork_id']), v['artwork_id'], sid, v['source_url'], evidence, v['source_receipt']['retrieved_at'], a.EDITOR))
    r.save(FOLDER / (target + '-receipt.json'), {'at': r.now(), 'plan_sha256': digest, 'records': len(records)})
    print('Applied dated observations', target, len(records), flush=True)


def verify(targets=None):
    data, digest = pinned()
    totals = {}
    for target, records in data['targets'].items():
        if targets and target not in targets:
            continue
        with r.connect(target) as db:
            after = a.snapshots(db, [v['artwork_id'] for v in records])
            for v in records:
                old, new = v['before'], after[v['artwork_id']]
                for key in ['artwork', 'identifiers', 'creators', 'creator_keys', 'media']:
                    assert new[key] == old[key], (target, key)
                assertions = {x['id']: x for x in new['assertions']}
                assert len(new['assertions']) == len(old['assertions']) + 1
                assert all(assertions[h['id']] == h for h in old['assertions'])
                h = assertions[a.uid(WAVE + '/' + v['artwork_id'])]
                assert h['claim_type'] == 'display' and h['display_state'] == v['display_state'] and h['venue_id'] == (v['venue']['id'] if v['venue'] else None) and h['review_state'] == 'accepted'
            assert db.execute('SELECT count(*) n FROM citations WHERE source_id=%s', (a.uid('source/' + WAVE),)).fetchone()['n'] == len(records)
        totals[target] = len(records)
    reference = next(iter(data['targets'].values()))
    r.save(FOLDER / ('verification.json' if len(totals) == 2 else 'verification-' + '-'.join(totals) + '.json'), {'at': r.now(), 'plan_sha256': digest, 'targets': totals, 'all_prior_data_preserved': True, 'on_view': sum(v['display_state'] == 'on_view' for v in reference), 'not_on_view': sum(v['display_state'] == 'not_on_view' for v in reference)})
    print('Verified dated observations', totals, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--target', choices=['local', 'production'], default='local')
    parser.add_argument('--targets', nargs='+', choices=['local', 'production'])
    args = parser.parse_args()
    apply(args.target) if args.command == 'apply' else verify(args.targets) if args.command == 'verify' else plan()
