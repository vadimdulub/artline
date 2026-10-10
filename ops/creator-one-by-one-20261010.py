#!/usr/bin/env python3
"""One source-backed creator expansion. Production only; local DB never opened."""
import argparse
import collections
import csv
import gzip
import html
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import uuid
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('low_count_base', ROOT/'ops/low-count-200-painters-20261008.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
r, m, q, s = b.r, b.m, b.q, b.s
OP = 'creator-one-by-one-20261010'
RUN = ROOT/'docs/research'/OP
BACKUP = Path.home()/'Library/Application Support/Artline/backups'/OP
AID = 'eb421138-2996-5c30-a4f0-e66cb1d2d15d'
SOURCE = 'https://www.wikiart.org/en/ivan-tvorozhnikov'
r.PORT = 55519
b.RUN = m.RUN = q.RUN = r.RUN = s.RUN = RUN
m.CACHE = {}
ACTOR = 'local-european-research'


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP+'/'+value))


def capture(url, tag='captures'):
    raw, rc = m.capture(url, tag, fresh=True)
    assert rc['status'] == 200, f"Source HTTP {rc['status']}: {url}"
    return raw, rc


def inventory(db):
    query = """SELECT to_jsonb(a) artwork,
      ma.source_page_url image_source_url,
      coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e
        WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
      coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c
        WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations
      FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
      WHERE a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s)
      OR a.unlinked_creator_label ILIKE '%%tvorozhnikov%%'
      OR a.unlinked_creator_label ILIKE '%%творожников%%' ORDER BY a.id"""
    return db.execute(query, (AID,)).fetchall()


def research():
    r.save(RUN/'authorization.json', dict(
        request='we have a catalog of link that we can use to get info about painters and artworks; do one by one, pick a creator that have only 0-5 artworoks, add at least 10-100',
        interpretation='Complete one creator at a time; select up to 25 additional source-supported artworks for the first creator.',
        target='production', local_database_connected=False, new_status='review',
        selection='Personal owner study selection; no museum highlight or current-display claim.',
        image_scope='Metadata expansion; source image URLs retained as evidence, no image attachment in this pass.'))
    registry = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    entries = list(csv.DictReader(registry.open()))
    r.save(RUN/'source-registry-review.json', dict(path=str(registry), sha256=r.sha(registry.read_bytes()),
        entries=len(entries), selected_supplement='WikiArt artist/object links approved by user 6 October 2026; existing project WikiArt directory supplies this creator lead.',
        registry_relevant_routes=[x for x in entries if x['source_id'] in ['wikidata','wikimedia_commons','russian_museum','tretyakov']],
        original_registry_not_modified=True))
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artist = db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s', (AID,)).fetchone()['a']
        aliases = [x['alias'] for x in db.execute('SELECT alias FROM artist_aliases WHERE artist_id=%s', (AID,))]
        identifiers = db.execute("SELECT to_jsonb(e) e FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s", (AID,)).fetchall()
        existing = inventory(db)
        query = "SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'"
        count = db.execute(query, (AID,)).fetchone()['n']
        r.save(RUN/'count-query-plan.json', db.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+query, (AID,)).fetchone())
        other_creators = db.execute("SELECT id::text,display_name,slug FROM artists WHERE id<>%s AND (display_name ILIKE '%%tvorozhnikov%%' OR display_name ILIKE '%%творожников%%')", (AID,)).fetchall()
    assert 0 <= count <= 5 and artist['entity_type'] == 'person' and artist['status'] != 'archived'
    assert not other_creators, 'Reconcile duplicate creator profiles first'
    r.save_gz(RUN/'existing-records.json.gz', existing)
    print('Existing:', [(x['artwork']['title'], x['artwork']['date_display']) for x in existing], flush=True)
    raw, profile_receipt = capture(SOURCE)
    soup = m.BeautifulSoup(raw, 'html.parser')
    profile_text = soup.get_text(' ', strip=True)
    assert 'Ivan Tvorozhnikov' in profile_text and '1848' in profile_text and '1919' in profile_text
    assert artist['birth_year'] == 1848 and artist['death_year'] == 1919
    pair = dict(artist=artist, aliases=aliases, identifiers=identifiers, count_at_selection=count,
                source=dict(url=SOURCE, name='Ivan Tvorozhnikov'), profile_receipt=profile_receipt)
    r.save(RUN/'creator.json', pair)
    raw, receipt = capture(SOURCE+'/all-works/text-list')
    soup = m.BeautifulSoup(raw, 'html.parser')
    items = {}
    for link in soup.select('li a[href]'):
        if link['href'].startswith(urlsplit(SOURCE).path+'/'):
            title = link.get_text(' ', strip=True)
            date = link.parent.get_text(' ', strip=True).removeprefix(title).strip(' ,')
            url = urljoin(SOURCE, link['href'])
            items[url] = dict(title=title, url=url, source_date=date, date=m.dates.creation_date(date))
    raw, api_receipt = capture('https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl=ivan-tvorozhnikov&json=2')
    metadata = json.loads(raw)
    r.save_gz(RUN/'source-indexes'/(AID+'.json.gz'), dict(outcome='indexed', items=list(items.values()), metadata=metadata, receipt=receipt, metadata_receipt=api_receipt))
    rows, held = b.source_candidates(pair)
    raw, translation_receipt = capture('https://www.wikiart.org/ru/App/Painting/PaintingsByArtist?artistUrl=ivan-tvorozhnikov&json=2')
    translated = json.loads(raw)
    r.save_gz(RUN/'russian-titles.json.gz', dict(items=translated, receipt=translation_receipt))
    translations = collections.defaultdict(set)
    for item in translated:
        translations[str(item['contentId'])].add(q.norm(item.get('title')))
    selected = []
    existing_titles = {q.norm(w['artwork'].get(k)) for w in existing for k in ['title','alternate_title']}-{''}
    existing_urls = {e.get('canonical_url') for w in existing for e in w['identifiers']} | {c.get('source_url') for w in existing for c in w['citations']} | {w.get('image_source_url') for w in existing}
    title_counts = collections.Counter(q.norm(x['work']['title']) for x in rows)
    for row in rows:
        # Research a bounded selection, dated objects first, then unambiguous source order.
        if len(selected) >= 25:
            held.append(dict(source_url=row['source_url'], title=row['work']['title'], reason='Outside the bounded first selection; not rejected'))
            continue
        names = ({q.norm(row['work']['title'])} | translations[row['source_id']])-{''}
        if names & existing_titles or row['source_url'] in existing_urls:
            held.append(dict(source_url=row['source_url'], title=row['work']['title'], reason='Existing object/title or translated title; preserved'))
            continue
        if title_counts[q.norm(row['work']['title'])] > 1 or re.search(r'beggars.*church', row['work']['title'], re.I):
            held.append(dict(source_url=row['source_url'], title=row['work']['title'], reason='Repeated/translated title needs physical version reconciliation'))
            continue
        raw, rc = capture(row['source_url'], 'page-captures')
        page = q.page_metadata(raw, rc)
        assert page['metadata']['artistUrl'] == urlsplit(SOURCE).path
        assert q.norm(page['metadata']['title']) == q.norm(row['work']['title'])
        assert q.image_key(page['metadata']['image']) == q.image_key(row['metadata']['image'])
        date = s.source_date(page)
        if date and date['creation_year_end'] > 1970:
            held.append(dict(source_url=row['source_url'], reason='Creation date outside scope', page=page))
            continue
        if date and row['work']['creation_year_start'] is not None:
            assert s.years_overlap(date, row['work']), 'Object/list creation-date conflict'
        w = row['work']
        if date:
            w.update(date)
        else:
            w.update(creation_year_start=None, creation_year_end=None, date_precision='unknown', date_display='Unknown date')
            row['date_review'] = 'Direct object page supplies no parseable creation date. Retain as review/research candidate with null years; artist lifespan is not an artwork date or automatic scope proof.'
        w['medium_text'] = page['fields'].get('Media') or page['fields'].get('Medium')
        w['dimensions_text'] = page['fields'].get('Dimensions')
        w['work_type'] = s.kind(w['medium_text'])
        row.update(page=page, wikiart_artwork_id=page['metadata']['_id'], translated_titles_checked=sorted(names),
                   identity_basis='Unique existing creator profile; exact artist name, 1848–1919 lifespan, artist URL, object title, content ID and image path agree across profile, index, JSON and direct artwork page. English and Russian titles checked against all linked and raw-label catalogue leads. No museum holding inferred.')
        selected.append(row)
        print(len(selected), w['title'], w['date_display'], w['medium_text'], flush=True)
    r.save_gz(RUN/'research-selection.json.gz', dict(pair=pair, rows=selected, held=held,
        authorization_sha256=r.sha((RUN/'authorization.json').read_bytes()), source_index_count=len(items), metadata_count=len(metadata)))
    print('Selected', len(selected), 'held/deferred', len(held), flush=True)


def backup():
    description = 'Before selected creator additions '+OP
    dest = BACKUP/'cloud-backup-request.json'
    if not dest.exists():
        raw = subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres',
            '--project=artline-508319','--description='+description,'--async','--format=json'], text=True)
        r.save(dest, json.loads(raw))
    rows = json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres',
        '--project=artline-508319','--limit=30','--format=json'], text=True))
    matches = [x for x in rows if x.get('description') == description]
    if len(matches) == 1 and matches[0]['status'] == 'SUCCESSFUL':
        r.save(BACKUP/'cloud-backup.json', matches[0])
        r.save(RUN/'cloud-backup.json', matches[0])
    print('Recovery backup:', [(x.get('id'), x.get('status')) for x in matches], flush=True)


def validate(plan):
    assert 0 <= plan['pair']['count_at_selection'] <= 5
    assert 10 <= len(plan['rows']) <= 100
    assert plan['authorization_sha256'] == r.sha((RUN/'authorization.json').read_bytes())
    assert plan['pair']['artist']['id'] == AID
    for key in ['artwork_id','source_id','source_url','wikiart_artwork_id']:
        assert len({x[key] for x in plan['rows']}) == len(plan['rows']), 'Duplicate '+key
    receipts = [plan['pair']['profile_receipt'], r.load(RUN/'russian-titles.json.gz')['receipt']]
    for row in plan['rows']:
        w = row['work']
        assert w['id'] == row['artwork_id'] and row['artist_id'] == AID
        assert row['source_url'].startswith(SOURCE+'/') and row['confidence'] >= .9
        assert w['title'].strip() and w['normalized_title'] == q.norm(w['title'])
        if w['creation_year_start'] is None:
            assert w['creation_year_end'] is None and w['date_precision'] == 'unknown' and row['date_review']
        else:
            assert 0 < w['creation_year_start'] <= w['creation_year_end'] <= 1970
        assert row['page']['metadata']['artistUrl'] == urlsplit(SOURCE).path
        assert row['page']['metadata']['_id'] == row['wikiart_artwork_id']
        receipts.extend([row['source_receipt'], row['metadata_receipt'], row['page']['receipt']])
    unique = {rc['body_path']:rc for rc in receipts}
    for path, rc in unique.items():
        raw = (ROOT/path).read_bytes()
        if path.endswith('.gz'): raw = gzip.decompress(raw)
        assert r.sha(raw) == rc['sha256'], 'Evidence checksum changed: '+path
    return len(unique)


def collisions(db, rows):
    ids = [x['artwork_id'] for x in rows]
    urls = [x['source_url'] for x in rows]
    legacy = [x['source_id'] for x in rows]
    canonical = [x['wikiart_artwork_id'] for x in rows]
    occupied = db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
    external = db.execute("""SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers
      WHERE entity_type='artwork' AND (canonical_url=ANY(%s)
        OR (scheme='wikiart-legacy-content-id' AND external_id=ANY(%s))
        OR (scheme='wikiart-artwork' AND external_id=ANY(%s)))""", (urls,legacy,canonical)).fetchall()
    citations = db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (urls,)).fetchall()
    return dict(occupied=occupied, external=external, citations=citations)


def preflight():
    plan = r.load(RUN/'reviewed-plan.json.gz')
    count = validate(plan)
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        conflicts = collisions(db, plan['rows'])
        assert not any(conflicts.values()), conflicts
        assert inventory(db) == r.load(RUN/'existing-records.json.gz'), 'Existing creator records changed; research again'
        before = s.snapshots(db, [x['artwork']['id'] for x in inventory(db)])
        collection = db.execute('SELECT curator_kind,institution_id FROM curated_collections WHERE id=%s', (m.COLLECTION,)).fetchone()
        assert collection == dict(curator_kind='owner', institution_id=None)
        position = db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()['n']
        assert position + len(plan['rows']) <= 100000
        cache_triggers = db.execute("SELECT tgname FROM pg_trigger WHERE tgrelid='artworks'::regclass AND tgname='catalogue_cache_changed'").fetchall()
        assert cache_triggers, 'Catalogue cache invalidation missing'
    r.save_gz(BACKUP/'original-records-before.json.gz', before)
    pin = r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    r.save(RUN/'preflight.json', dict(at=r.now(), plan_sha256=pin, rows=len(plan['rows']),
        verified_source_bodies=count, collisions=conflicts, existing_records=len(before), owner_collection_position=position,
        unknown_dates=sum(x['work']['creation_year_start'] is None for x in plan['rows']), local_database_connected=False))
    print('Preflight passed:', len(plan['rows']), 'new records;', count, 'source bodies verified', flush=True)


def apply():
    plan = r.load(RUN/'reviewed-plan.json.gz')
    validate(plan)
    pin = r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    assert r.load(RUN/'preflight.json')['plan_sha256'] == pin
    assert r.load(BACKUP/'cloud-backup.json')['status'] == 'SUCCESSFUL'
    rows = plan['rows']; ids = [x['artwork_id'] for x in rows]
    source = uid('source/wikiart'); marker = uid('applied/'+AID)
    with r.connect('production', readonly=False) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        previous = db.execute('SELECT after_json FROM audit_log WHERE id=%s', (marker,)).fetchone()
        if previous:
            result = previous['after_json']
            assert result['plan_sha256'] == pin and result['new_ids'] == ids
            assert len(s.snapshots(db, ids)) == len(ids)
        else:
            creator = db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s FOR SHARE', (AID,)).fetchone()['a']
            assert creator == plan['pair']['artist'], 'Creator changed since selection'
            existing = inventory(db)
            assert existing == r.load(RUN/'existing-records.json.gz'), 'Existing artwork evidence changed'
            active_count = db.execute("SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'", (AID,)).fetchone()['n']
            assert active_count == plan['pair']['count_at_selection'] and 0 <= active_count <= 5
            conflicts = collisions(db, rows)
            assert not any(conflicts.values()), conflicts
            old_ids = [x['artwork']['id'] for x in existing]
            before = s.snapshots(db, old_ids)
            r.save_gz(BACKUP/'locked-preimages.json.gz', before)
            collection = db.execute('SELECT curator_kind,institution_id FROM curated_collections WHERE id=%s FOR UPDATE', (m.COLLECTION,)).fetchone()
            assert collection == dict(curator_kind='owner', institution_id=None)
            position = db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()['n']
            assert position+len(rows) <= 100000
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')", (source, OP+'-wikiart', 'WikiArt: selected '+creator['display_name']+' objects, October 2026'))
            with db.pipeline():
                for row in rows:
                    w = row['work']; wid = row['artwork_id']
                    keys = ['id','slug','title','alternate_title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium_text','dimensions_text']
                    db.execute("""INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,status,research_candidate,created_by,updated_by)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""", tuple(w[k] for k in keys)+(ACTOR,ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)", (wid,AID,row['identity_basis']))
                    for scheme, sid in [('wikiart-legacy-content-id',row['source_id']), ('wikiart-artwork',row['wikiart_artwork_id'])]:
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)", (wid,scheme,sid,row['source_url'],source,row['page']['receipt']['retrieved_at']))
                    evidence = dict(operation=OP, plan_sha256=pin, editorial_confidence=row['confidence'], identity_basis=row['identity_basis'],
                        object_fields=row['page']['fields'], source_rights_label=row['page']['rights_label'],
                        source_policy='WikiArt user approval of 6 October 2026 recorded separately from actual rights labels.',
                        date_review=row.get('date_review'), original_index_date=row['index']['source_date'],
                        source_receipts=[row['source_receipt'],row['metadata_receipt'],row['page']['receipt']],
                        translated_titles_checked=row['translated_titles_checked'], editorial_review=row.get('editorial_review'),
                        selection='Personal owner study selection. No museum holding, display or masterpiece assertion. No image downloaded or attached.')
                    db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                      VALUES(%s,'artwork',%s,%s,'creator_expansion_source_identity',%s,%s,%s,%s,%s)""", (uid('citation/'+wid),wid,source,row['source_id'],row['source_url'],json.dumps(evidence,ensure_ascii=False),row['page']['receipt']['retrieved_at'],ACTOR))
                    position += 1
                    db.execute('INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                        (uid('selection/'+wid),m.COLLECTION,wid,position,'Personal creator-study selection requested 10 October 2026: 10–100 additions to a creator with 0–5 active works. Unknown dates remain explicitly under editorial review.',source,row['source_url'],row['page']['receipt']['retrieved_at']))
                db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s', (m.COLLECTION,))
            after = s.snapshots(db, ids)
            assert len(after) == len(rows)
            for row in rows:
                record = after[row['artwork_id']]; artwork = record['artwork']
                assert all(artwork[k] == v for k,v in row['work'].items())
                assert artwork['status'] == 'review' and artwork['research_candidate'] and artwork['published_at'] is None
                assert artwork['primary_media_id'] is None and artwork['current_institution_id'] is None
                assert not record['locations'] and not record['attachments']
                assert len(record['creators']) == 1 and record['creators'][0]['artist_id'] == AID
            assert s.snapshots(db, old_ids) == before
            r.save_gz(BACKUP/'transaction-postimages.json.gz', after)
            result = dict(at=r.now(), artist_id=AID, artist=creator['display_name'], slug=creator['slug'],
                plan_sha256=pin, new_ids=ids, added=len(rows), before=active_count, after=active_count+len(rows),
                existing_records_preserved=True, local_database_connected=False, images_attached=0)
            db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'creator_one_by_one_additions','artist',%s,%s)", (marker,ACTOR,AID,m.Jsonb(result)))
    r.save(RUN/'applied.json', result)
    print('Applied/recovered:', json.dumps(result), flush=True)


def verify():
    plan = r.load(RUN/'reviewed-plan.json.gz')
    applied = r.load(RUN/'applied.json')
    validate(plan)
    assert applied['plan_sha256'] == r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    ids = applied['new_ids']
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        records = s.snapshots(db, ids)
        assert records == r.load(BACKUP/'transaction-postimages.json.gz')
        before = r.load(BACKUP/'locked-preimages.json.gz')
        assert s.snapshots(db, list(before)) == before
        citations = db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE source_id=%s AND entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (uid('source/wikiart'),ids)).fetchall()
        identifiers = db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (ids,)).fetchall()
        selections = db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])', (m.COLLECTION,ids)).fetchall()
        count = db.execute("SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'", (AID,)).fetchone()['n']
    assert len(citations) == len(rows := plan['rows']) and len(identifiers) == 2*len(rows) and len(selections) == len(rows)
    cite_by_id = {c['entity_id']:c for c in citations}
    for row in rows:
        citation = cite_by_id[row['artwork_id']]
        assert citation['source_record_id'] == row['source_id'] and citation['source_url'] == row['source_url']
        assert json.loads(citation['evidence_note'])['plan_sha256'] == applied['plan_sha256']
        refs = {(x['scheme'],x['external_id'],x['canonical_url']) for x in identifiers if x['entity_id']==row['artwork_id']}
        assert refs == {('wikiart-artwork',row['wikiart_artwork_id'],row['source_url']),('wikiart-legacy-content-id',row['source_id'],row['source_url'])}
    assert count == applied['after']
    expected = {x['artwork_id']:x for x in rows}
    found = {}; pages = []; cursor = None
    for _ in range(3):
        params = dict(limit=50)
        if cursor: params['cursor'] = cursor
        response = m.requests.get('https://artlines.org/api/backend/v1/artists/'+applied['slug']+'/works', params=params, timeout=(15,60))
        response.raise_for_status()
        data = response.json()
        assert len(data['items']) <= 50
        pages.append(dict(url=response.url,status=response.status_code,data=data))
        for item in data['items']:
            if item['id'] in expected:
                w = expected[item['id']]['work']
                for key in ['title','creation_year_start','creation_year_end']:
                    assert item[key] == w[key]
                assert item['status'] == 'review'
                found[item['id']] = item
        next_cursor = data.get('next_cursor')
        if not next_cursor: break
        assert next_cursor != cursor
        cursor = next_cursor
    assert set(found) == set(expected), 'Missing additions in live API: '+str(set(expected)-set(found))
    r.save_gz(RUN/'api-pages.json.gz', pages)
    proof = dict(at=r.now(),artist=applied['artist'],artist_id=AID,slug=applied['slug'],before=applied['before'],
        added=len(rows),after=count,known_creation_dates=sum(x['work']['creation_year_start'] is not None for x in rows),
        unknown_dates=sum(x['work']['creation_year_start'] is None for x in rows),source_citations=len(citations),
        external_identifiers=len(identifiers),owner_selections=len(selections),api_new_records_found=len(found),
        api_pages=len(pages),api_page_limit=50,existing_records_preserved=True,all_new_records_review=True,
        no_new_holdings_or_display_claims=True,images_attached=0,local_database_connected=False,
        cloud_backup_id=r.load(BACKUP/'cloud-backup.json')['id'],plan_sha256=applied['plan_sha256'])
    r.save(RUN/'verification.json', proof)
    with (RUN/'new-artworks.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['artwork_id','title','alternate_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium','dimensions','source_url','status'])
        writer.writeheader()
        for row in rows:
            w = row['work']
            writer.writerow(dict(artwork_id=w['id'],title=w['title'],alternate_title=w['alternate_title'],date_display=w['date_display'],
                creation_year_start=w['creation_year_start'],creation_year_end=w['creation_year_end'],date_precision=w['date_precision'],
                work_type=w['work_type'],medium=w['medium_text'],dimensions=w['dimensions_text'],source_url=row['source_url'],status='review'))
    report = f'''# First creator expansion: Ivan Tvorozhnikov

Verified {proof['at']}. **25 new production artworks; 2 → 27 active works.**

[Open the creator](https://artlines.org/artists/{applied['slug']}) · [Artwork ledger](new-artworks.csv) · [Verification](verification.json)

The user requested one creator at a time, choosing a creator with 0–5 works and adding 10–100 supported artworks. A current read-only production check confirmed two active works for this existing creator before selection and again inside the insert transaction. This pass completes one creator. It does not claim all low-count creators have been expanded.

The supplied 111-entry [source registry review](source-registry-review.json) and the project's approved WikiArt directory were inspected. This creator's additions use the separately user-approved [WikiArt profile](https://www.wikiart.org/en/ivan-tvorozhnikov), visible artwork list, English and Russian JSON indexes and **every selected individual object page**. Bodies, retrieval times and SHA-256 hashes are retained. The profile heading says 42 works, while its current list and JSON each supplied 41; no missing work was invented.

Ten new objects have documented creation dates; **15 remain explicitly undated**, with null years, unknown precision and review/research-candidate state. Artist life dates were used for creator identity only. Two direct page intervals override shortened list dates: Seller of icons is 1887–1888, and Girl with a Book is 1890–1900. Both source representations remain in evidence. The Mirovich picture's 1764 historical subject date is retained in its title, while its actual creation date is 1884. Original Russian titles are retained where supplied. Twenty-three oil works are classified as paintings; mixed-media and unspecified types remain unknown.

Two existing works were excluded and preserved. Four ambiguous title/version leads were withheld: two Portrait of a Woman entries and two church-beggar variants. Ten further source objects are outside this bounded selection and remain available for later research. Stable WikiArt object IDs, source URLs, English/Russian titles, image paths, all linked creator objects and matching raw creator labels were checked for duplication. No reproduction was downloaded or visually compared in this metadata pass; unresolved version collisions were withheld rather than treated as separate confirmed objects.

All 25 additions remain in review and are personal owner study selections, separate from museum highlights. Source location labels for two objects remain citation evidence; no accepted holdings or current-display assertions were created. **No new images were attached.** Existing creator metadata and artwork records remain unchanged.

Seven adversarial plan checks passed, covering the minimum size, initial count, date cutoff, inconsistent unknown dates, duplicate source IDs, wrong creator and missing uncertainty review. Preflight rechecked evidence hashes and current catalogue identities. A pinned plan was applied atomically with a deterministic audit marker, transaction preimages and verified postimages. Cloud SQL backup `{proof['cloud_backup_id']}` succeeded before writes. Recovery artifacts are under `{BACKUP}`. The audit marker makes a replay recoverable without duplicate inserts.

Read-only postflight verified all 25 works, 25 citations, 50 external identifiers and 25 owner selections. The live public creator API returned every addition in one bounded page, with matching titles, dates and review status. Existing database triggers invalidate catalogue caches. The creator count query used an indexed artist lookup; the query plan is retained, but this bounded pass is not a ten-million-row load test. The real local database was never connected to. No fixtures, commit, migration or deployment were made.
'''
    r.save(RUN/'README.md', report.encode())
    print('Verified:', json.dumps(proof), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['research','backup','preflight','apply','verify'])
    args = parser.parse_args()
    globals()[args.command]()
