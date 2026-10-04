#!/usr/bin/env python3
"""Bounded, sourced decolonization additions to the local review catalogue.

Seven new records, two existing records reconciled, and an explicit period
selection. Download only the one pinned public-domain reproduction. Never
publish or deploy; existing provenance, unknown fields and statuses survive.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.CAMPAIGN = 'decolonization-20260927'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
PRESETS = core.ROOT / 'apps/server/internal/atlas/presets.json'
NGMA = 'https://www.ngmaindia.gov.in/virtual-tour-of-amrita-sher-gil.asp'
SHORT_CENTURY = 'https://www.moma.org/calendar/exhibitions/4749'
COMMONS = 'https://commons.wikimedia.org/wiki/File:Bharat_Mata_by_Abanindranath_Tagore.jpg'
PDM = 'https://creativecommons.org/publicdomain/mark/1.0/'
PROVIDERS = {
    'moma': ('wikimedia-museum-q188740', 'Museum of Modern Art', 'https://www.moma.org/'),
    'smithsonian': ('national-museum-of-african-art', 'National Museum of African Art', 'https://africa.si.edu/'),
    'singapore': ('national-gallery-singapore', 'National Gallery Singapore', 'https://www.nationalgallery.sg/'),
    'victoria': ('victoria-memorial-hall-kolkata', 'Victoria Memorial Hall, Kolkata', 'https://vmhkolkata.com/'),
}
# This is an editorial selection, never a museum highlight designation.
EXISTING = [
    ('e703177f-aa07-56d1-9499-dda109a4bfee', 'related', None, 'Retained from the previous Lam selection; cultural context rather than a claim that this portrait depicts independence.'),
    ('11539053-c7ed-5f25-b874-6c282de66523', 'related', None, 'Retained Lam selection: Afro-Caribbean cultural expression.'),
    ('1aa58a35-7134-5874-a0d3-7d902a590605', 'related', 'https://www.moma.org/collection/works/34666', 'Lam’s response to the legacies of colonialism and Afro-Cuban cultural life.'),
    ('760e1db3-dae8-4e11-a6e7-ec9f2c2722ea', 'related', None, 'Retained Lam selection: Afro-Caribbean cultural expression.'),
    ('0b95593a-88ca-59ac-9046-b4d895daa13b', 'related', 'https://www.ngmaindia.gov.in/virtual-tour-of-bapu.asp', 'Bose’s Gandhi linocut connects printmaking to the Salt March and Indian independence.'),
    ('34b53477-a0e2-5149-a1c1-fa58789cb321', 'related', NGMA, 'Indian rural life in Sher-Gil’s development of an Indian modern painting; cultural self-representation, not a depicted political protest.'),
    ('d059bcc8-bfa2-59bb-b5d1-05d071bc32e2', 'related', NGMA, 'Women’s lives in pre-independence India and Sher-Gil’s artistic return to India.'),
    ('f6ade8f0-2975-52b7-a33a-656fbd0351ec', 'related', NGMA, 'Part of the 1937 South Indian group shaped by Indian visual traditions.'),
    ('0061ae26-7e3d-5447-be6a-c550c5efae90', 'related', NGMA, 'Part of the 1937 South Indian group; local subjects and Indian visual traditions.'),
    ('596a993f-f961-5150-a25b-0565b8c9a9ac', 'related', NGMA, 'Part of the 1937 South Indian group; rural subjects and Indian visual traditions.'),
    ('6ff2f71c-4b89-56ef-bdc5-6d9a9bae4adc', 'related', NGMA, 'Rural India as a subject of an Indian modern painting before independence.'),
    ('8122bc94-c58e-5ee1-9192-a4c29d571026', 'related', NGMA, 'Local storytelling and everyday life, selected as cultural context.'),
    ('e3ecdb87-4455-5cfb-994c-d7c21ac74bbe', 'context', 'https://artsandculture.google.com/story/HgXx4Bz_4BcpLg', 'Earlier Bengal School roots: a Mughal historical subject in Tagore’s renewal of Indian painting.'),
    ('06d5f22a-89b7-5d72-81ff-3a100edbc562', 'context', 'https://artsandculture.google.com/story/HgXx4Bz_4BcpLg', 'Earlier Bengal School roots: historical Indian subject matter, not an independence event.'),
    ('53669dde-5c3b-4eae-828c-57a223d4d722', 'related', SHORT_CENTURY, 'Okeke’s Nigerian modernism and Natural Synthesis; existing museum record retained without downloading a restricted image.'),
    ('0f49b50b-bc07-4611-ae5e-580f421f870d', 'related', SHORT_CENTURY, 'Okeke’s Nigerian modernism; a selected existing museum record, without a new image claim.'),
    ('3ea61a1f-1d3c-4cda-9abc-e9fdefd193e8', 'related', SHORT_CENTURY, 'Boghossian’s African modernism; cultural context grounded in the museum’s independence and liberation exhibition.'),
]


def candidates():
    out = []
    def add(key, provider, oid, title, maker, year, kind, medium, dimensions, accession, url, reason, **extra):
        out.append(dict(key=key, provider=provider, object_id=oid, title=title, maker=maker,
            lo=year, hi=year, date_display=str(year), precision='exact', type=kind,
            medium=medium, dimensions=dimensions, accession=accession, url=url,
            reason=reason, country=None, **extra))
    add('bharat-mata', 'victoria', 'vmh_kol-RBS27ANT-16706', 'Bharat Mata [Mother India]', 'Abanindranath Tagore', 1905,
        'painting', 'Watercolour; wash', '10 1/2 × 6 in.', 'RBS27ANT',
        'https://museumsofindia.gov.in/repository/record/vmh_kol-RBS27ANT-16706',
        'An image of the motherland associated with the Swadeshi movement and the Indian freedom struggle.',
        artist_id='fd002e0b-8d5b-53ec-bf2d-d97b447abbc9', relation='context',
        provenance='Rabindra Bharati Society, Jorasanko, Kolkata. The national museum portal names Victoria Memorial Hall as the museum; this is a holding connection, not a transfer-of-ownership claim.',
        image_url='https://upload.wikimedia.org/wikipedia/commons/3/3a/Bharat_Mata_by_Abanindranath_Tagore.jpg',
        image_page_url=COMMONS)
    add('ana-mmuo', 'smithsonian', 'nmafa_97-3-1', 'Ana Mmuo (Land of the Dead)', 'Uche Okeke', 1961,
        'painting', 'Oil on board', '91.6 × 121.9 cm (unframed)', '97-3-1',
        'https://africa.si.edu/collection/object/nmafa_97-3-1',
        'Igbo masked spirit dancers expressed through Natural Synthesis; the museum documents this work in The Short Century: Independence and Liberation Movements in Africa.',
        artist_id='47eb7f8b-345f-472d-9c89-dad1a9a21a96')
    add('war-and-peace', 'singapore', '1997-02155', 'War and Peace', 'Hendra Gunawan', 1950,
        'painting', 'Oil on canvas', '93.7 × 140.3 cm (image)', '1997-02155',
        'https://www.nationalgallery.sg/sg/en/visit/tours/audio-guide.stop.html/between-declarations-and-dreams-audio-tour/3.html',
        'Indonesian independence fighters against Dutch colonial rule; the museum connects the painting to the artist’s experience with the Frontline Painters.')
    out[-1].update(hi=1959, date_display='c. 1950s', precision='circa_range',
        date_note='The museum gives an approximate decade. 1950–1959 are decade bounds, not an invented single creation year.')
    for oid, title, year, kind, medium, dims, accession, existing in [
        ('78385', 'The Mosque', 1964, 'painting', 'Oil on canvas', '30.7 × 46 cm', '7.1965', '9e50ae95-4c68-4be1-98ae-b6acddd2176d'),
        ('450851', 'No Shade but His Shade', 1968, 'painting', 'Oil and enamel on canvas', '95 × 95 × 7 cm', '81.2024', '04640603-53ff-4ed4-9a47-3cc0586a2af3'),
        ('280148', 'By His Will, We Teach Birds How to Fly No.13', 1969, 'drawing', 'Pen, ink, and wash on paper', '38.1 × 55.6 cm', '192.2018', None),
    ]:
        add('moma-'+oid, 'moma', oid, title, 'Ibrahim El-Salahi', year, kind, medium, dims, accession,
            'https://www.moma.org/collection/works/'+oid,
            'Sudanese modernism and calligraphic abstraction in the era of independence; cultural context, not a claim that this work depicts an independence event.', existing_id=existing)
    for oid, title, dims, accession in [
        ('420295', 'Madness of Maria Chissano III (Loucura de Maria Chissano III)', '18.5 × 23.8 cm', '71.2021'),
        ('420294', "PIDE's Punishment Room (Sala de castigo da PIDE)", '43.5 × 32.5 cm', '72.2021'),
        ('420293', 'Untitled', '20.7 × 17.5 cm', '73.2021'),
    ]:
        add('moma-'+oid, 'moma', oid, title, 'Malangatana Valente Ngwenya', 1965, 'drawing', 'Ink and pencil on paper', dims, accession,
            'https://www.moma.org/collection/works/'+oid,
            'A drawing from Malangatana’s period of imprisonment under Portuguese colonial rule; museum research connects this body of work to colonial repression.')
    return out


def duplicate(db, c):
    return db.execute('''SELECT id::text FROM artworks WHERE (current_institution_id=%s AND accession_number=%s)
      OR (normalized_title=%s AND unlinked_creator_label=%s)
      UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s
      UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s''',
      (c['institution_id'], c['accession'], core.norm(c['title']), c['maker'], c['url'], c['url'])).fetchall()


def plan():
    institutions, create, records, existing = {}, [], candidates(), []
    with core.connect() as db:
        for key, (slug, name, website) in PROVIDERS.items():
            found = db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s OR normalized_name=%s', (slug, core.norm(name))).fetchall()
            assert len(found) <= 1
            institution = found[0]['record'] if found else dict(id=core.uid('institution/'+key), slug=slug, name=name,
                normalized_name=core.norm(name), kind='museum', status='review', website_url=website)
            institutions[key] = institution
            if not found:
                create.append(institution)
        for c in records:
            c.update(institution_id=institutions[c['provider']]['id'], artwork_id=c.get('existing_id') or core.uid(c['key']),
                slug='decolonization-'+c['key'])
            matches = duplicate(db, c)
            assert all(r['id'] == c.get('existing_id') for r in matches), (c['key'], matches)
            if c.get('existing_id'):
                old = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (c['existing_id'],)).fetchone()['record']
                assert old['title'] == c['title'] and old['unlinked_creator_label'] == c['maker']
                assert (old['creation_year_start'], old['creation_year_end']) == (c['lo'], c['hi'])
                assert old['status'] == 'review' and old['primary_media_id'] is None
                assert old['current_institution_id'] is None and old['accession_number'] is None and old['work_type'] == 'unknown'
                c['preimage'] = old
                c['slug'] = old['slug']
        for aid, relation, url, reason in EXISTING:
            row = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (aid,)).fetchone()['record']
            assert row['creation_year_end'] <= 1970 and row['status'] in ('review', 'published')
            existing.append(dict(id=aid, slug=row['slug'], title=row['title'], relation=relation, source_url=url, reason=reason, preimage=row))
    captures = {p.name:core.sha(p.read_bytes()) for p in (core.RUN/'captures').glob('*.json')}
    assert all(name in captures for name in ['decol-details-1.json','museum-final-1.json','object-final.json','malangatana-objects.json','hendra-object.json'])
    core.save(core.RUN/'plan.json', dict(records=records, institutions=institutions, institutions_to_create=create,
        existing_selection=existing, captures=captures, image_policy='Only Bharat Mata: explicit Commons PD-Art/PDM; author died 1951, 1905 work. No download of modern copyrighted works.',
        selection_bound='Nine exact museum objects, including two existing records reconciled without duplication. Seventeen additional existing artworks explicitly selected.'))
    core.save(core.RUN/'plan-pin.json', dict(sha256=core.sha((core.RUN/'plan.json').read_bytes())))
    print('Pinned 7 new records, 2 reconciliations, 17 existing selections, 1 public-domain image.')


def prepare():
    p = core.pinned()
    # Reuse image preparation with only the explicitly cleared object.
    core.pinned = lambda: {**p, 'records':[c for c in p['records'] if c.get('image_url')]}
    core.prepare()


def apply():
    p = core.pinned()
    if (core.RUN/'applied.json').exists():
        return verify()
    for name, digest in p['captures'].items():
        assert core.sha((core.RUN/'captures'/name).read_bytes()) == digest
    backup, qa = core.load('backup.json'), core.load('visual-review.json')
    assert core.sha(Path(backup['path']).read_bytes()) == backup['sha256']
    assert qa['approved'] and qa['plan_sha256'] == core.load('plan-pin.json')['sha256']
    assert qa['images_sha256'] == core.sha((core.RUN/'images.json').read_bytes())
    images = {i['key']:i for i in core.load('images.json')}
    assert set(images) == {'bharat-mata'}
    with core.connect(False) as db, db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('LOCK TABLE artworks,external_identifiers IN SHARE ROW EXCLUSIVE MODE')
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active', (core.ACTOR,)).fetchone()
        for c in p['records']:
            assert all(r['id'] == c.get('existing_id') for r in duplicate(db,c))
            if c.get('preimage'):
                assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (c['artwork_id'],)).fetchone()['record'] == c['preimage']
        for c in p['existing_selection']:
            assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (c['id'],)).fetchone()['record'] == c['preimage']
        for i in p['institutions_to_create']:
            assert not db.execute('SELECT 1 FROM institutions WHERE slug=%s OR normalized_name=%s', (i['slug'],i['normalized_name'])).fetchone()
            core.insert(db,'institutions',i)
        for key, (_, name, base) in PROVIDERS.items():
            core.insert(db,'sources',dict(id=core.uid('source/'+key),slug=core.CAMPAIGN+'-'+key,
                name='Decolonization selection — '+name,source_type='collection_page',base_url=base))
        core.insert(db,'sources',dict(id=core.uid('source/themes'),slug=core.CAMPAIGN+'-themes',
            name='Decolonization — thematic museum research',source_type='collection_page',base_url=SHORT_CENTURY))
        for c in p['records']:
            sid = core.uid('source/'+c['provider'])
            values = dict(work_type=c['type'],medium_text=c['medium'],dimensions_text=c['dimensions'],
                current_institution_id=c['institution_id'],accession_number=c['accession'],description_md=c['reason'],updated_by=core.ACTOR)
            if c.get('existing_id'):
                db.execute(core.sql.SQL('UPDATE artworks SET {} WHERE id=%s').format(core.sql.SQL(',').join(
                    core.sql.SQL('{}=%s').format(core.sql.Identifier(k)) for k in values)), [*values.values(),c['artwork_id']])
            else:
                core.insert(db,'artworks',dict(id=c['artwork_id'],slug=c['slug'],title=c['title'],normalized_title=core.norm(c['title']),
                    creation_year_start=c['lo'],creation_year_end=c['hi'],date_display=c['date_display'],date_precision=c['precision'],
                    unlinked_creator_label=c['maker'],status='review',research_candidate=True,created_by=core.ACTOR,**values))
            if c.get('artist_id'):
                core.insert(db,'artwork_artists',dict(artwork_id=c['artwork_id'],artist_id=c['artist_id'],attribution_role='primary',attribution_note='Named maker in official museum record: '+c['url']))
            if c['key'] in images:
                im = images[c['key']]
                raw = (core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
                assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
                core.insert(db,'media_assets',dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=COMMONS,
                    provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],
                    alt_text='Bharat Mata [Mother India] — Abanindranath Tagore, 1905',rights_status='public_domain',license_label='Public Domain Mark 1.0 (PD-Art)',license_url=PDM,
                    creator_credit='Abanindranath Tagore; reproduction via Wikimedia Commons',attribution_text='Bharat Mata, 1905. Abanindranath Tagore. Public domain. Full-frame resize and JPEG compression.',
                    retrieved_at=im['download']['at'],verified_at=qa['at'],verified_by=core.ACTOR))
                core.insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=sid,source_record_id=c['object_id'],
                    source_checksum=core.sha(core.encode(c)),source_image_url=c['image_url'],policy_url=COMMONS,
                    rights_basis='Exact Commons file explicitly marked PD-Art/PDM; 1905 painting, creator died 1951. Museum metadata and Rabindra Bharati Society provenance preserved separately.',
                    adapter_version=core.CAMPAIGN,checked_at=qa['at'],evidence_json=core.Jsonb(dict(captures=p['captures'],download=im['download'],record=c))))
                core.insert(db,'artwork_media',dict(artwork_id=c['artwork_id'],media_id=im['media_id'],sort_order=0,view_label='Public-domain reproduction'))
                db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['media_id'],c['artwork_id']))
            core.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=c['artwork_id'],scheme=c['provider']+'-object',external_id=c['object_id'],canonical_url=c['url'],source_id=sid,retrieved_at=core.now()))
            core.insert(db,'artwork_location_assertions',dict(artwork_id=c['artwork_id'],claim_type='holding',institution_id=c['institution_id'],context='collection',
                source_id=sid,source_url=c['url'],evidence_note='Official museum record, accession '+c['accession']+'. '+c.get('provenance','')+' No current display claim.',checked_at=qa['at'],review_state='accepted'))
            core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['artwork_id'],field_name='official_object_identity',source_id=sid,source_record_id=c['object_id'],source_url=c['url'],
                evidence_note=json.dumps(dict(record={k:v for k,v in c.items() if k!='preimage'},captures=p['captures'],plan_sha256=core.load('plan-pin.json')['sha256'],
                    image_decision='Public-domain Commons reproduction' if c.get('image_url') else 'Metadata only; no rights-cleared reproduction downloaded.'),ensure_ascii=False),retrieved_at=core.now(),created_by=core.ACTOR))
        for c in p['existing_selection']:
            if c['source_url']:
                core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['id'],source_id=core.uid('source/themes'),field_name='decolonization_editorial_selection',source_url=c['source_url'],
                    evidence_note=json.dumps(dict(reason=c['reason'],relation=c['relation'],captures=p['captures'],museum_highlight_claim=False),ensure_ascii=False),retrieved_at=core.now(),created_by=core.ACTOR))
        verify_rows(db,p)
    core.save(core.RUN/'applied.json',dict(at=core.now(),target='local',new_records=7,enriched_existing=2,new_images=1,review_only=True,plan_sha256=core.load('plan-pin.json')['sha256']))
    verify()


def preset():
    p = core.pinned()
    presets = json.loads(PRESETS.read_text())
    previous = next(x for x in core.load('presets-before.json') if x['id']=='decolonization')
    item = next(x for x in presets if x['id']=='decolonization')
    assert item == previous, 'Preset changed since planning; review before replacing it.'
    item['context']['start'] = 1900
    item['description'] = 'Art and writing trace struggles for independence and cultural self-representation in India, Africa, Indonesia and the Caribbean. Earlier Bengal School works provide roots; later writing and South African democracy extend the story.'
    item['startingCountries'], item['startingCreators'] = [], []
    item['startingScope'] = 'India, Africa, Indonesia & the Caribbean'
    f = item['focus']
    f['global'] = False
    f['label'] = 'Selected works explore independence, colonial repression and cultural self-representation. Three earlier Bengal School works provide context; not every picture depicts a political event.'
    selected = [(c['id'],c['relation']) for c in p['existing_selection']] + [(c['artwork_id'],c.get('relation','related')) for c in p['records']]
    for relation in ['related','context']:
        f[relation]['artwork'] = [aid for aid,rel in selected if rel==relation]
    f['artworkIdentities'] = {'760e1db3-dae8-4e11-a6e7-ec9f2c2722ea':'europe-tate-1c9046d1586d-ibaye'}
    for name,url in [
        ('National museums portal — Bharat Mata','https://museumsofindia.gov.in/repository/record/vmh_kol-RBS27ANT-16706'),
        ('NGMA — Amrita Sher-Gil',NGMA),
        ('Smithsonian — Ana Mmuo','https://africa.si.edu/collection/object/nmafa_97-3-1'),
        ('MoMA — Independence and Liberation Movements in Africa',SHORT_CENTURY),
        ('MoMA — Malangatana as Anti-Colonial Subject','https://post.moma.org/malangatana-as-anti-colonial-subject-1959-74/'),
        ('National Gallery Singapore — War and Peace',next(c['url'] for c in p['records'] if c['key']=='war-and-peace')),
    ]:
        item['sources'].append(dict(name=name,url=url))
    PRESETS.write_text(json.dumps(presets,ensure_ascii=False,indent=2)+'\n')
    core.save(core.RUN/'preset-after.json',item)
    print('Selected 26 artworks, including 15 with existing or newly cleared images; 9 books and 9 events retained.')


def verify_rows(db,p):
    rows = db.execute('''SELECT a.id::text,a.title,a.status,a.published_at,a.work_type,a.creation_year_start,a.creation_year_end,
        a.unlinked_creator_label,a.primary_media_id::text,a.current_institution_id::text,a.accession_number,
        artline_has_selection_evidence(a.id) selected,
        (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display') displays,
        (SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists
        FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',([c['artwork_id'] for c in p['records']],)).fetchall()
    assert len(rows)==9
    for c in p['records']:
        r=next(x for x in rows if x['id']==c['artwork_id'])
        assert r['status']=='review' and r['published_at'] is None and r['selected'] and r['displays']==0, r
        assert r['work_type']==c['type'] and r['unlinked_creator_label']==c['maker']
        assert (r['creation_year_start'],r['creation_year_end'])==(c['lo'],c['hi']) and c['hi']<=1970
        assert r['current_institution_id']==c['institution_id'] and r['accession_number']==c['accession']
        assert r['artists']==int(bool(c.get('artist_id'))) and bool(r['primary_media_id'])==bool(c.get('image_url'))
        if c.get('existing_id'):
            assert db.execute("SELECT 1 FROM citations WHERE entity_id=%s AND source_url LIKE '%%210a729ead48d12b%%'",(c['artwork_id'],)).fetchone()
    return rows


def verify():
    p=core.pinned()
    with core.connect() as db:
        rows=verify_rows(db,p)
    for im in core.load('images.json'):
        raw=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
    if not (core.RUN/'verification.json').exists():
        core.save(core.RUN/'verification.json',dict(at=core.now(),records=rows,new_records=7,enriched_existing=2,new_images=1,new_artist_profiles=0,new_display_claims=0))
    print('Verified 7 new and 2 enriched local review records; source provenance retained; 1 cleared image.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','prepare','backup','apply','preset','verify'])
    phase=parser.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
