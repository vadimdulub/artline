#!/usr/bin/env python3
"""A bounded, local-only Chagall selection. Default is a read-only preflight.

The pinned source captures, catalogue preimages and recovery dump must exist
before --apply. Never publishes records or downloads images.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/chagall-paintings-20260919'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/chagall-paintings-20260919'
ACTOR = 'local-european-research'
SOURCE = 'chagall-paintings-selected-20260919'
DSN = 'postgres://localhost/artline'


def norm(value):
    text = unicodedata.normalize('NFKD', value or '').casefold()
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in text if not unicodedata.combining(c))))


def save(path, value):
    with path.open('x') as output:
        json.dump(value, output, default=str, ensure_ascii=False, indent=2)
        output.write('\n')


def check_plan():
    raw = (RUN / 'selected.json').read_bytes()
    plan = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == json.loads((RUN / 'selection-manifest.json').read_text())['sha256']
    assert len(plan['records']) == 10
    for work in plan['records']:
        assert work['work_type'] == 'painting'
        assert 1887 <= work['creation_year_start'] <= work['creation_year_end'] <= 1970
        assert work['date_precision'] == ('exact' if work['creation_year_start'] == work['creation_year_end'] else 'range')
        assert work['source_receipts'] and work['evidence_note'] and work['selection_reason']
        for receipt in work['source_receipts']:
            body = (RUN / receipt['path']).read_bytes()
            assert len(body) == receipt['bytes'] and body
            assert hashlib.sha256(body).hexdigest() == receipt['sha256']
    return plan


def preflight(db, plan):
    artist = db.execute('SELECT id::text,slug,display_name,birth_year,death_year,status FROM artists WHERE id=%s', (plan['artist_id'],)).fetchone()
    assert artist and artist['slug'] == plan['artist_slug'] and artist['display_name'] == 'Marc Chagall'
    assert (artist['birth_year'], artist['death_year'], artist['status']) == (1887, 1985, 'review')
    institutions = db.execute('SELECT * FROM institutions WHERE slug=ANY(%s)', (list({w['institution_slug'] for w in plan['records']}),)).fetchall()
    by_slug = {i['slug']: i for i in institutions}
    assert len(institutions) == 5 and all(i['status'] != 'archived' for i in institutions)
    works = db.execute('SELECT w.* FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=%s ORDER BY w.id', (plan['artist_id'],)).fetchall()
    for work in plan['records']:
        assert not db.execute('SELECT id FROM artworks WHERE id=%s OR slug=%s', (work['id'], work['slug'])).fetchone(), 'Selection already exists; use verification receipt, do not import twice'
        names = {norm(work['title']), norm(work['alternate_title'])}
        for old in works:
            overlap = (old['creation_year_start'] or 0) <= work['creation_year_end'] and (old['creation_year_end'] or 9999) >= work['creation_year_start']
            assert not (overlap and names.intersection({norm(old['title']), norm(old['alternate_title'])})), 'Title/date collision requires review'
            assert not (work['accession_number'] and norm(old['accession_number']) == norm(work['accession_number'])), 'Existing painter accession requires reconciliation'
        if work['accession_number']:
            assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s', (by_slug[work['institution_slug']]['id'], work['accession_number'])).fetchone(), 'Institution accession collision'
        assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s", (SOURCE, work['source_record_id'])).fetchone()
    ids = [i['id'] for i in institutions]
    collections = db.execute("SELECT * FROM curated_collections WHERE institution_id=ANY(%s) AND curator_kind='owner'", (ids,)).fetchall()
    assert all(c['status'] == 'review' for c in collections)
    items = db.execute('SELECT * FROM curated_collection_items WHERE collection_id=ANY(%s)', ([c['id'] for c in collections],)).fetchall()
    return dict(artist=artist, institutions=institutions, artworks=works, collections=collections, collection_items=items)


def apply(plan):
    recovery = json.loads((RUN / 'backup.json').read_text())
    dump = Path(recovery['path'])
    assert dump.is_relative_to(BACKUP) and dump.stat().st_size == recovery['bytes']
    assert hashlib.file_digest(dump.open('rb'), 'sha256').hexdigest() == recovery['sha256']
    assert (BACKUP / 'local-before.contents.txt').stat().st_size > 0
    with psycopg.connect(DSN, row_factory=dict_row) as db:
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE', (plan['artist_id'],))
        before = preflight(db, plan)
        save(BACKUP / 'selected-preimages.json', before)
        institutions = {i['slug']: i for i in before['institutions']}
        sid = db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,'Marc Chagall: selected official museum records','collection_page','https://www.guggenheim.org/') RETURNING id", (SOURCE,)).fetchone()['id']
        collection_ids = {}
        for slug, institution in institutions.items():
            db.execute("INSERT INTO curated_collections(institution_id,curator_kind,title,status) VALUES(%s,'owner','Selected research works','review') ON CONFLICT(institution_id,curator_kind) DO NOTHING", (institution['id'],))
            collection_ids[slug] = db.execute("SELECT id FROM curated_collections WHERE institution_id=%s AND curator_kind='owner' FOR UPDATE", (institution['id'],)).fetchone()['id']
        for work in plan['records']:
            iid = institutions[work['institution_slug']]['id']
            receipt = work['source_receipts'][0]
            url, checked = receipt['url'], receipt['retrieved_at']
            description = work['description_md']
            if work['slug'] == 'chagall-promenade':
                description += '\n\nMuseum sources date this work to 1917 or 1917–1918; the timeline retains the full documented interval.'
            db.execute("""INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,description_md,accession_number,status,research_candidate,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,%s,%s,'review',true,%s,%s)""", (work['id'],work['slug'],work['title'],work['alternate_title'],norm(work['title']),work['date_display'],work['creation_year_start'],work['creation_year_end'],work['date_precision'],work['medium_text'],work['dimensions_text'],description,work['accession_number'],ACTOR,ACTOR))
            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Official museum record explicitly names Marc Chagall; linked to existing 1887–1985 artist authority.')", (work['id'], plan['artist_id']))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)", (work['id'],SOURCE,work['source_record_id'],url,sid,checked))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,%s,%s,%s,%s,%s,'accepted')", (work['id'],iid,work['holding_context'],sid,url,work['evidence_note']+' Collection credit only; no current-display or on-view claim.',checked))
            evidence = json.dumps(dict(note=work['evidence_note'],sources=work['source_receipts'],image_status=work['image_status']), ensure_ascii=False)
            db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)", (work['id'],sid,work['source_record_id'],url,evidence,checked,ACTOR))
            cid = collection_ids[work['institution_slug']]
            position = db.execute('SELECT coalesce(max(position),0)+1 AS n FROM curated_collection_items WHERE collection_id=%s', (cid,)).fetchone()['n']
            db.execute('INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s)', (cid,work['id'],position,work['selection_reason'],sid,url,checked))
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=ANY(%s)', (list(collection_ids.values()),))
        ids = [w['id'] for w in plan['records']]
        verified = db.execute("SELECT id::text,title,status,published_at,primary_media_id,artline_has_selection_evidence(id) AS selected,artline_creation_scope(creation_year_start,creation_year_end,date_precision) AS scope FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY title", (ids,)).fetchall()
        assert len(verified) == 10 and all(w['status']=='review' and w['published_at'] is None and w['primary_media_id'] is None and w['selected'] and w['scope']=='eligible' for w in verified)
        assert not db.execute("SELECT id FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='display'", (ids,)).fetchone()
        preserved = db.execute('SELECT w.* FROM artworks w WHERE id=ANY(%s) ORDER BY id', ([w['id'] for w in before['artworks']],)).fetchall()
        assert preserved == before['artworks'], 'Existing Chagall artworks changed'
    save(RUN / 'local-applied.json', dict(at=datetime.now(timezone.utc), records=verified, existing_artworks_preserved=len(preserved), backup=recovery, local_only=True))
    print('Added and verified 10 review paintings; existing artworks preserved:', len(preserved))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    plan = check_plan()
    if args.apply:
        apply(plan)
    else:
        with psycopg.connect(DSN, options='-c default_transaction_read_only=on', row_factory=dict_row) as db:
            state = preflight(db, plan)
        save(RUN / 'preflight.json', dict(at=datetime.now(timezone.utc), artist=state['artist'], existing_artworks=len(state['artworks']), new_paintings=len(plan['records']), collisions=0))
        print('Read-only preflight passed: 10 new paintings, no collisions')
