#!/usr/bin/env python3
"""Two selected Byzantine painted leaves; exact native exhibition links only."""
import base64
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import requests
from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage
from psycopg.types.json import Jsonb

import exhibitions_common as c

OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/byzantine-historical'
DEST = OUT / 'leaves'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/byzantine-leaves'
OP = 'historical-exhibition-byzantine-leaves-20261012'
ACTOR = 'local-european-research'
IID = '729385eb-92b0-4cc8-9229-1ac3a46aee1f'
SID = 'd63cee47-716a-45ba-9e88-b552ff5b59c0'
NATIVES = ['121697', '121698']
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
API = 'https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1'


def plain(value):
    return json.loads(json.dumps(value, default=str))


def conflicts(db):
    ids = NATIVES + ['1942.1511', '1942.1512']
    urls = [f'https://{host}/art/{accession}' for host in ['clevelandart.org', 'www.clevelandart.org'] for accession in ids[2:]]
    return plain(dict(
        identifiers=db.execute("SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))", (ids, urls)).fetchall(),
        works=db.execute("SELECT id,title,accession_number FROM artworks WHERE current_institution_id=%s AND (accession_number=ANY(%s) OR normalized_title LIKE '%%lectionary%%')", (IID, ids[2:])).fetchall()))


def plan():
    rows = []
    with c.connect() as db:
        duplicate_check = conflicts(db)
        assert duplicate_check == dict(identifiers=[], works=[]), duplicate_check
        institution = db.execute('SELECT id,name,status FROM institutions WHERE id=%s', (IID,)).fetchone()
        assert institution['status'] != 'archived'
        entries = db.execute('SELECT * FROM exhibition_entries WHERE source_artwork_id=ANY(%s) ORDER BY id', (NATIVES,)).fetchall()
        assert len(entries) == 13 and all(e['artwork_id'] is None and e['participation'] == 'exhibited' for e in entries)
        eids = sorted({str(e['exhibition_id']) for e in entries})
        events = db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id', (eids,)).fetchall()
        sources = db.execute('SELECT * FROM exhibition_source_records WHERE id=ANY(%s::uuid[]) ORDER BY id', (sorted({str(e['source_record_id']) for e in entries}),)).fetchall()
        assert len(events) == 9 and all(1600 <= e['start_year'] <= e['end_year'] <= 1989 for e in events)
        for native in NATIVES:
            f = OUT / ('cma-' + native + '.json')
            receipt = c.load(f.with_suffix('.json.receipt.json'))
            assert c.sha(f.read_bytes()) == receipt['sha256']
            o = c.load(f)['data']
            im = c.load(DEST / 'prepared' / (native + '.json'))
            assert str(o['id']) == native and im['state'] == 'prepared'
            assert o['type'] == 'Manuscript' and 'tempera' in o['technique'] and 'vellum' in o['technique']
            assert o['creation_date_earliest'] == 1057 and o['creation_date_latest'] == 1063 and not o['creators']
            assert o['share_license_status'] == 'CC0' and not o.get('copyright') and not o.get('rights_and_reproductions')
            assert o['legal_status'] == 'accessioned' and o['on_loan'] is False
            assert c.sha(Path(im['path']).read_bytes()) == im['sha256']
            assert c.sha(Path(im['originalPath']).read_bytes()) == im['sourceSHA256']
            selected_entries = [e for e in entries if e['source_artwork_id'] == native]
            native_events = {c.uid('cleveland/' + str(x['id'])): x for x in o['exhibitions']['current']}
            for e in selected_entries:
                assert e['evidence']['accession_number'] == o['accession_number'] and str(e['evidence']['id']) == native
                assert str(e['exhibition_id']) in native_events, 'Existing event must match the museum native event ID'
                assert c.norm(e['title_label']) == c.norm(o['title'])
            visual = dict(decision='accept', originalViewed=True, derivativeViewed=True, confidence=.99,
                basis='Full painted evangelist leaf with gold background and ornamental arch, exact accession-specific primary image. Original irregular vellum edges and paint losses preserved. No cropping, invented restoration or closed-book substitution.',
                figure='Luke: dark-haired evangelist seated at a writing desk.' if native == '121697' else 'Matthew: white-bearded evangelist seated beside a desk.',
                sourceType='Manuscript', selectedType='manuscript_illumination',
                scopeBasis='Pictorial tempera painting on vellum, not a text-only manuscript or decorative binding.')
            rows.append(dict(id=im['id'], nativeID=native, object=o, metadataReceipt=receipt, image=im, visualReview=visual,
                creatorLabel='Unknown artist', culturalContext='; '.join(o['culture']), entryIDs=[str(e['id']) for e in selected_entries],
                dateConflictsPreserved='Existing 1957 Oberlin and 1980 Dumbarton Oaks event day discrepancies are retained for separate catalogue review. This operation does not rewrite exhibition dates.',
                excludedConnection='The 1931 Paris legacy text describes the Phanar Gospel with Mark and John; it does not securely establish that these detached Luke/Matthew leaves were exhibited. No connection is added.'))
    p = dict(at=c.now(), operation=OP, records=rows, pinnedEntries=entries, pinnedEvents=events, pinnedSources=sources,
        pinnedInstitution=institution, duplicateCheck=duplicate_check, newArtworks=2, newImages=2, newlyCanonicalLinkedEntries=13,
        exhibitions=9, newParticipationClaims=0, realLocalDatabaseWrites=False,
        authorization='Selected source-backed historical paintings and authentic images with exact exhibition links; production delivery authorized. Anonymous creators and review status retained.')
    c.save(DEST / 'delivery-plan.json', p)
    c.save(BACKUP / 'preimage.json.gz', p)
    print('Prepared two painted leaves, two images and 13 exact native connections across nine events.', flush=True)


def upload():
    p = c.load(DEST / 'delivery-plan.json')
    spec = importlib.util.spec_from_file_location('byzantine_image_core', Path(__file__).with_name('enrich-artwork-images.py'))
    core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
    credentials = core.GcloudCredentials(); credentials.refresh(None)
    bucket = storage.Client(project='artline-508319', credentials=credentials).bucket('artline-508319-images')
    receipts = []
    for r in p['records']:
        im = r['image']; raw = Path(im['path']).read_bytes()
        assert c.sha(raw) == im['sha256'] and len(raw) <= 100000
        blob = bucket.blob(im['imagePath'].lstrip('/'))
        blob.metadata = {'sha256': im['sha256'], 'operation': OP, 'artwork-id': r['id'], 'native-id': r['nativeID']}
        blob.cache_control = 'public,max-age=31536000,immutable'
        try:
            blob.upload_from_string(raw, content_type='image/jpeg', if_generation_match=0, timeout=45)
        except PreconditionFailed:
            blob.reload(timeout=30)
        assert blob.size == len(raw) and blob.md5_hash == base64.b64encode(hashlib.md5(raw).digest()).decode()
        response = requests.get('https://artlines.org' + im['imagePath'], timeout=30); response.raise_for_status()
        assert c.sha(response.content) == im['sha256']
        receipts.append(dict(artworkID=r['id'], sha256=im['sha256'], generation=blob.generation, publicBytesVerified=True))
    c.save(DEST / 'uploaded.json', dict(at=c.now(), receipts=receipts, planSHA256=c.sha((DEST / 'delivery-plan.json').read_bytes())))
    print('Two selected images uploaded and public bytes verified.', flush=True)


def apply():
    p = c.load(DEST / 'delivery-plan.json'); pin = c.sha((DEST / 'delivery-plan.json').read_bytes())
    assert c.load(DEST / 'uploaded.json')['planSHA256'] == pin
    assert c.load(BACKUP / 'preimage.json.gz') == p
    with c.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)", (ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert conflicts(db) == p['duplicateCheck']
        assert plain(db.execute('SELECT id,name,status FROM institutions WHERE id=%s FOR SHARE', (IID,)).fetchone()) == p['pinnedInstitution']
        for table, key in [('exhibition_entries', 'pinnedEntries'), ('exhibitions', 'pinnedEvents'), ('exhibition_source_records', 'pinnedSources')]:
            for before in p[key]:
                assert plain(db.execute(f'SELECT * FROM {table} WHERE id=%s FOR UPDATE', (before['id'],)).fetchone()) == before
        for r in p['records']:
            o = r['object']; im = r['image']; aid = r['id']; native = r['nativeID']; mid = im['mediaID']
            db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,unlinked_creator_label,cultural_context,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,1057,1063,'range','manuscript_illumination',%s,%s,%s,%s,%s,'review',true,%s,%s)",
                (aid, c.norm(o['title']).replace(' ', '-') + '-' + aid[:8], o['title'], c.norm(o['title']), o['creation_date'], o['technique'], o['measurements'], o['accession_number'], r['creatorLabel'], r['culturalContext'], ACTOR, ACTOR))
            db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,'cleveland',%s,%s,%s)", (c.uid(OP + '/native/' + native), aid, native, o['url'], SID))
            db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'historical_exhibition_object_identity',%s,%s,%s,%s,%s)",
                (c.uid(OP + '/citation/' + native), aid, SID, native, o['url'], json.dumps(dict(record=r, planSHA256=pin), ensure_ascii=False), p['at'], ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",
                (c.uid(OP + '/holding/' + native), aid, IID, SID, o['url'], json.dumps(dict(confidence=.99, basis='Native accession, accessioned legal status and exact museum object record.', currentDisplayClaim=False)), p['at']))
            credit = o.get('creditline') or 'The Cleveland Museum of Art'
            attribution = 'The Cleveland Museum of Art; ' + credit + '; CC0. Full frame proportionally resized and compressed.'
            db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'The Cleveland Museum of Art','image/jpeg',%s,%s,%s,%s,%s,'public_domain','CC0',%s,%s,%s,%s,now(),%s)",
                (mid, im['imagePath'], o['url'], im['width'], im['height'], im['bytes'], im['sha256'], o['title'] + ' — unknown Byzantine artist, 1057–1063', CC0, credit, attribution, im['sourceReceipt']['retrievedAt'], ACTOR))
            db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)",
                (mid, SID, native, r['metadataReceipt']['sha256'], im['sourceReceipt']['url'], CC0, 'Exact native museum object explicitly labels the supplied primary image CC0; copyright and rights-and-reproductions fields are empty.', OP, Jsonb(dict(record=r, planSHA256=pin))))
            db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full painted leaf reproduction')", (aid, mid))
            db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s', (mid, aid))
            for eid in r['entryIDs']:
                db.execute("UPDATE exhibition_entries SET artwork_id=%s,date_label=%s,medium_label=%s,dimensions_label=%s,match_basis=%s,evidence=evidence||%s WHERE id=%s",
                    (aid, o['creation_date'], o['technique'], o['measurements'], 'Exact museum native object and accession; source exhibition ID matches the current museum object history.', Jsonb(dict(canonicalObjectReview=dict(operation=OP, artworkID=aid, sourceURL=o['url'], metadataReceipt=r['metadataReceipt'], visualReview=r['visualReview'], planSHA256=pin))), eid))
            a = db.execute('SELECT status,published_at,current_institution_id,primary_media_id,artline_has_selection_evidence(id) selected FROM artworks WHERE id=%s', (aid,)).fetchone()
            assert a['status'] == 'review' and a['published_at'] is None and str(a['current_institution_id']) == IID and str(a['primary_media_id']) == mid and a['selected']
    c.save(DEST / 'delivered.json', dict(at=c.now(), newArtworks=2, newPrimaryImages=2, newlyCanonicalLinkedEntries=13, exhibitions=9, newParticipationClaims=0, realLocalDatabaseWrites=False, planSHA256=pin))
    print('Committed two illustrated review works and 13 exact existing exhibition-entry links.', flush=True)


def verify():
    p = c.load(DEST / 'delivery-plan.json'); checks = []
    with c.connect() as db:
        for r in p['records']:
            a = db.execute('SELECT id,title,status,published_at,work_type,creation_year_start,creation_year_end,current_institution_id,primary_media_id,unlinked_creator_label FROM artworks WHERE id=%s', (r['id'],)).fetchone()
            assert a['status'] == 'review' and a['published_at'] is None and a['work_type'] == 'manuscript_illumination'
            assert (a['creation_year_start'], a['creation_year_end']) == (1057,1063) and a['unlinked_creator_label'] == 'Unknown artist'
            assert str(a['primary_media_id']) == r['image']['mediaID'] and str(a['current_institution_id']) == IID
            assert db.execute('SELECT count(*) n FROM artwork_artists WHERE artwork_id=%s', (r['id'],)).fetchone()['n'] == 0
            response = requests.get(API + '/exhibitions', params={'artwork': r['id'], 'limit': 50}, timeout=30); response.raise_for_status()
            expected = {e['exhibition_id'] for e in p['pinnedEntries'] if e['id'] in r['entryIDs']}
            assert {e['id'] for e in response.json()['items']} == expected
            image = requests.get('https://artlines.org' + r['image']['imagePath'], timeout=30); image.raise_for_status()
            assert c.sha(image.content) == r['image']['sha256']
            checks.append(dict(artwork=plain(a), reverseExhibitions=len(expected), publicImageBytesVerified=True))
        for before in p['pinnedEntries']:
            after = plain(db.execute('SELECT * FROM exhibition_entries WHERE id=%s', (before['id'],)).fetchone())
            permitted = {'artwork_id','date_label','medium_label','dimensions_label','match_basis','evidence'}
            assert {k:v for k,v in after.items() if k not in permitted} == {k:v for k,v in before.items() if k not in permitted}
        for before in p['pinnedEvents']:
            assert plain(db.execute('SELECT * FROM exhibitions WHERE id=%s', (before['id'],)).fetchone()) == before
    public_entries = []
    for event in p['pinnedEvents']:
        response = requests.get(API + '/exhibitions/' + event['id'] + '/entries', params={'limit':50}, timeout=30); response.raise_for_status()
        wanted = {r['id'] for r in p['records'] if any(e['exhibition_id'] == event['id'] and e['id'] in r['entryIDs'] for e in p['pinnedEntries'])}
        items = [x for x in response.json()['items'] if x.get('artworkId') in wanted]
        assert {x['artworkId'] for x in items} == wanted and all(x.get('image') for x in items)
        public_entries.extend(x['id'] for x in items)
    assert len(public_entries) == 13
    c.save(DEST / 'verified.json', dict(at=c.now(), checks=checks, verifiedIllustratedEntries=13, unchangedEvents=9, newParticipationClaims=0, realLocalDatabaseWrites=False))
    print('Verified two authentic public images, all 13 illustrated entries, reverse links and nine unchanged event records.', flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['plan','upload','apply','verify']:
        raise SystemExit('Use plan, upload, apply or verify')
    globals()[sys.argv[1]]()
