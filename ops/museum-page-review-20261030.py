"""Museum profile audit and source-reviewed corrections; production only.

No artwork, holding, display, image, status or real-local catalogue writes.
All source checks in this pass used the web research tool, not native captures.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

sys.path.insert(0, str(Path(__file__).parent))
import exhibitions_common as c

OP = 'museum-page-review-20261030'
ROOT = c.ROOT
H = Path.home() / 'Library/Application Support/Artline'
E = ROOT / 'docs/research' / OP
D = H / 'source-metadata' / OP
B = H / 'backups' / OP
CONTENT = E / 'profiles-reviewed.json'
ACTOR = 'local-european-research'


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + key))


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def setup():
    for path in [E, D, B]:
        path.mkdir(parents=True, exist_ok=True)
    B.chmod(0o700)
    assert shutil.disk_usage(H).free > 30 * 1024**3


def audit():
    setup()
    baseline = c.load(D / 'baseline.json.gz')
    links = c.load(ROOT / 'apps/web/content/articles/museum-guides/institution-links.json')
    guides = collections.defaultdict(list)
    for guide, slugs in links.items():
        for slug in slugs:
            guides[slug].append('/guides/' + guide)
    boilerplate = re.compile(r'authority candidate|identity documented|selected (?:museum|official)|source[- ]backed|object-level|source identity|source label|not asserted|current display|holding link|institution record|collecting museum function|institution page confirms', re.I)
    rows = []
    for row in baseline['rows']:
        item = row['record']
        places = [dict(city=row['city'], country=row['country'])] + row['venues']
        countries = sorted({p['country'] for p in places if p.get('country')})
        cities = sorted({p['city'] for p in places if p.get('city')})
        description = item['description'].strip()
        rows.append(dict(id=item['id'], slug=item['slug'], name=item['name'], kind=item['kind'],
            page='/museums/' + item['slug'], primary_city=row['city'] or '', primary_country=row['country'] or '',
            recorded_countries=' | '.join(countries), recorded_cities=' | '.join(cities),
            location_review='missing_country' if not countries else 'missing_city' if not cities else 'recorded_requires_source_review',
            description_review='missing' if not description else 'import_note_requires_rewrite' if boilerplate.search(description) else 'existing_copy_requires_source_review',
            guide_links=' | '.join(guides[item['slug']]), has_holdings=row['has_holdings'],
            website=item['website_url'] or '', citation_urls=' | '.join(sorted({x['source_url'] for x in row['citations'] if x.get('source_url')}))))
    dest = E / 'all-institutions-audit.csv'
    assert not dest.exists()
    with dest.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    c.save(E / 'audit-summary.json', dict(at=c.now(), baseline=pin(D / 'baseline.json.gz'),
        institutions=len(rows), location_dispositions=dict(collections.Counter(r['location_review'] for r in rows)),
        description_dispositions=dict(collections.Counter(r['description_review'] for r in rows)),
        institutions_with_editorial_guides=sum(bool(r['guide_links']) for r in rows),
        limitation='Complete structural review of the frozen active canonical institution inventory, including empty and historic-site records. Recorded location/copy is not independent source verification. Holdings existence is not directory membership for historic sites or incoming loans.',
        audit=pin(dest)))
    print('AUDITED', len(rows), 'institution records', flush=True)


def plan():
    setup()
    assert not (B / 'plan.json.gz').exists()
    profiles = c.load(CONTENT)
    assert len({p['slug'] for p in profiles}) == len(profiles)
    assert all(len(p['description'].split('\n\n')) == 2 and p['sources'] for p in profiles)
    initial = {r['record']['slug']: r['record'] for r in c.load(D / 'baseline.json.gz')['rows']}
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows = {r['v']['slug']: r['v'] for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE slug=ANY(%s)', ([p['slug'] for p in profiles],))}
        places = [r['v'] for r in db.execute('SELECT to_jsonb(p)v FROM places p')]
        countries = {r['code'].strip() for r in db.execute('SELECT code FROM countries')}
    changes, new_places = [], {}
    for profile in profiles:
        before = rows[profile['slug']]
        assert before == initial[profile['slug']], 'Institution changed since baseline; reconcile before planning'
        assert profile['country'] in countries
        assert before['canonical_institution_id'] is None and before['status'] != 'archived'
        target_place = before['place_id']
        if not target_place:
            matches = [p for p in places if c.norm(p['name']) == c.norm(profile['city']) and (p['country_code'] or '').strip() == profile['country']]
            assert len(matches) <= 1, 'Ambiguous existing city: ' + profile['city']
            if matches:
                target_place = matches[0]['id']
            else:
                key = profile['city'] + '/' + profile['country']
                target_place = uid('place/' + key)
                new_places[key] = dict(id=target_place, name=profile['city'], normalized_name=c.norm(profile['city']), country_code=profile['country'])
        else:
            existing = next(p for p in places if p['id'] == target_place)
            assert (existing['country_code'] or '').strip() == profile['country'], 'Existing country conflict requires separate review'
        changes.append(dict(before=before, place_id=target_place, description=profile['description'],
            sources=profile['sources'], reviewed_city=profile['city'], reviewed_country=profile['country']))
    B.joinpath('AGENTS-before-write.md').write_bytes((ROOT / 'AGENTS.md').read_bytes())
    value = dict(at=c.now(), content=pin(CONTENT), instructions=pin(ROOT / 'AGENTS.md'), changes=changes,
        new_places=list(new_places.values()), source=dict(id=uid('source'), slug=OP + '-references',
            name='Museum profile references reviewed 30 October 2026', source_type='collection_page', priority=80, is_active=True),
        source_method='Web research tool; no native response bodies, HTTP status receipts or full-page reading claims',
        location_policy='Only fill a missing institution place. Reuse an unambiguous existing city/country; new city rows have no invented coordinates. Preserve existing locations and every venue.')
    c.save(B / 'plan.json.gz', value)
    c.save(E / 'plan-pin.json', pin(B / 'plan.json.gz'))
    print('PLANNED', len(changes), 'descriptions,', sum(p['before']['place_id'] != p['place_id'] for p in changes), 'location links,', len(new_places), 'new cities', flush=True)


def locks_held(db):
    proof = db.execute("""SELECT pg_backend_pid()pid,txid_current()::text tx,
    (SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND locktype='advisory' AND granted
    AND classid=0 AND objsubid=1 AND objid IN((hashtext('artline-curated-ingestion')::bigint&4294967295)::oid,202610053::oid,2026101201::oid)) held""").fetchone()
    assert proof['held'] == 3
    return dict(proof)


def insert(db, table, row):
    columns = list(row)
    statement = sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING to_jsonb({})v').format(
        sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, columns)),
        sql.SQL(',').join(sql.Placeholder() for _ in columns), sql.Identifier(table))
    return db.execute(statement, list(row.values())).fetchone()['v']


def apply():
    assert not (E / 'applied.json').exists() and not (B / 'transaction-staged.json.gz').exists(), 'Reconcile any dispatched transaction; never replay'
    assert pin(B / 'plan.json.gz') == c.load(E / 'plan-pin.json')
    value = c.load(B / 'plan.json.gz')
    assert pin(CONTENT) == value['content'] and pin(ROOT / 'AGENTS.md') == value['instructions']
    digest = pin(B / 'plan.json.gz')['sha256']
    changes = []
    with c.connect(write=True) as db:
        assert db.execute("SELECT current_database()db,current_setting('transaction_read_only')ro").fetchone() == dict(db='artline', ro='off')
        db.execute("SET LOCAL application_name='artline-museum-profile-review'")
        db.execute("SET LOCAL statement_timeout='60s'")
        db.execute("SET LOCAL lock_timeout='45s'")
        for query in ["SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))", 'SELECT pg_advisory_xact_lock(2026101201)', 'SELECT pg_advisory_xact_lock(202610053)']:
            db.execute(query)
        proof = locks_held(db)
        assert pin(ROOT / 'AGENTS.md') == value['instructions']
        assert not db.execute('SELECT id FROM audit_log WHERE request_id=%s LIMIT 1', (OP,)).fetchone()
        for change in value['changes']:
            current = db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=%s FOR UPDATE', (change['before']['id'],)).fetchone()['v']
            assert current == change['before']
        db.execute("SELECT set_config('artline.actor_user_id',%s,true),set_config('artline.request_id',%s,true)", (ACTOR, OP))
        for row in value['new_places']:
            after = insert(db, 'places', row)
            changes.append(dict(table='places', before=None, after=after))
        changes.append(dict(table='sources', before=None, after=insert(db, 'sources', value['source'])))
        for change in value['changes']:
            after = db.execute('UPDATE institutions SET place_id=%s,description=%s,updated_at=now() WHERE id=%s RETURNING to_jsonb(institutions)v',
                (change['place_id'], change['description'], change['before']['id'])).fetchone()['v']
            changes.append(dict(table='institutions', before=change['before'], after=after))
            citation = dict(id=uid('citation/' + after['id']), entity_type='institution', entity_id=after['id'],
                field_name='description_and_location', source_id=value['source']['id'], source_record_id=after['slug'],
                source_url=change['sources'][0], evidence_note=json.dumps(dict(sources=change['sources'],
                    city=change['reviewed_city'], country=change['reviewed_country'], method=value['source_method'],
                    original_English_summary=True, holdings_or_display_not_changed=True, plan_sha256=digest)),
                retrieved_at=value['at'], created_by=ACTOR)
            changes.append(dict(table='citations', before=None, after=insert(db, 'citations', citation)))
        for index, change in enumerate(changes):
            audit = dict(id=uid('audit/' + str(index)), actor_user_id=ACTOR, action='review_museum_description_and_location',
                entity_type=change['table'], entity_id=change['after']['id'], request_id=OP,
                before_json=Jsonb(change['before']), after_json=Jsonb(dict(record=change['after'], transaction=proof, plan_sha256=digest)))
            insert(db, 'audit_log', audit)
            change['audit_id'] = audit['id']
        assert locks_held(db) == proof
        assert pin(ROOT / 'AGENTS.md') == value['instructions'], 'Instructions changed: rollback'
        c.save(B / 'transaction-staged.json.gz', dict(at=c.now(), transaction=proof, changes=changes, plan_sha256=digest))
    c.save(E / 'applied.json', dict(at=c.now(), transaction=proof, explicit_audits=len(changes),
        tables=dict(collections.Counter(ch['table'] for ch in changes)), descriptions=len(value['changes']),
        new_location_links=sum(ch['before']['place_id'] != ch['place_id'] for ch in value['changes']),
        three_shared_locks_retained_before_writes_and_after_audits=True, plan_sha256=digest))
    print('COMMITTED', len(changes), 'atomic changes', proof, flush=True)


def verify():
    staged = c.load(B / 'transaction-staged.json.gz')
    checked = []
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for change in staged['changes']:
            statement = sql.SQL('SELECT to_jsonb(t)v FROM {} t WHERE id=%s').format(sql.Identifier(change['table']))
            assert db.execute(statement, (change['after']['id'],)).fetchone()['v'] == change['after']
            audit = db.execute('SELECT before_json,after_json FROM audit_log WHERE id=%s AND request_id=%s', (change['audit_id'], OP)).fetchone()
            assert audit['before_json'] == change['before'] and audit['after_json']['record'] == change['after']
            if change['before']:
                old, new = change['before'], change['after']
                assert {k:v for k,v in old.items() if k not in ['place_id','description','updated_at']} == {k:v for k,v in new.items() if k not in ['place_id','description','updated_at']}
            checked.append(dict(table=change['table'], id=change['after']['id'], audit_id=change['audit_id']))
        assert db.execute('SELECT count(*)n FROM audit_log WHERE request_id=%s', (OP,)).fetchone()['n'] == len(checked)
        armenia = db.execute("SELECT i.slug,p.name city,trim(p.country_code) country FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.slug='national-gallery-armenia'").fetchone()
        assert armenia == dict(slug='national-gallery-armenia', city='Yerevan', country='AM')
    c.save(E / 'database-verification.json', dict(at=c.now(), read_only=True, checked=checked, Armenia=armenia,
        exact_rows_and_audits=True, institution_identity_status_and_other_fields_preserved=True))
    print('VERIFIED', len(checked), 'rows and atomic audits', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['audit','plan','apply','verify'])
    globals()[parser.parse_args().action]()
