#!/usr/bin/env python3
"""Pinned local decolonisation research: selected records, truthful rights, no publication.

Reuses the approved <=1955 WikiArt delivery workflow. Source rights labels are
not copyright clearance. No new biography, current-display or museum-highlight
claims. New named creators without reconciled profiles remain object labels.
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
core.CAMPAIGN = 'decolonization-deep-20260928'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
PRESETS = core.ROOT / 'apps/server/internal/atlas/presets.json'
COLLECTION = '42c83e94-d1f2-539a-accb-b4e9ded61f06'
HOOD = 'df07612a-32f8-5c99-9973-cb45a2bc8fe5'
SINGAPORE = '580f9edd-03ae-5e05-99c7-b50ee8641f91'
TATE = '87051538-1955-4687-bcea-c7bf623c7ee2'
ABEDIN = 'https://www.documenta14.de/en/notes-and-works/24940/zainul-abedin-1914-1976-'
HYPPOLITE = 'https://www.moma.org/collection/artists/2790'
BAYA = 'https://awarewomenartists.com/en/artiste/baya/'
HOOD_GUIDE = 'https://hoodmuseum.dartmouth.edu/sites/hoodmuseum/files/orozcovisitorguide.pdf'
NGS = 'https://www.nationalgallery.sg/sg/en/learn-about-art/our-publications/digital-catalog/siapa-nama-kamu-exhibition-catalogue/chapters-overview/the-real-against-the-new-social-realism-and-abstraction.html'
POMPIDOU = 'https://www.centrepompidou.fr/en/ressources/oeuvre/cGEEgpG'
MET_LABELS = 'https://libmma.contentdm.oclc.org/digital/api/collection/p16028coll12/id/18919/download'
SOURCES = {
    'wikiart': ('WikiArt — selected decolonisation objects', 'https://www.wikiart.org/'),
    'research': ('Decolonisation — museum and scholarly research', 'https://www.moma.org/'),
}


def candidates():
    out = []
    def add(key, title, maker, year, kind, url, reason, theme, **extra):
        lo, hi = year if isinstance(year, tuple) else (year, year)
        out.append(dict(key=key, title=title, maker=maker, lo=lo, hi=hi,
            date_display=str(lo) if lo == hi else f'{lo}–{hi}', precision='exact' if lo == hi else 'range',
            type=kind, url=url, reason=reason, theme_url=theme, country=None,
            medium=None, dimensions=None, institution_id=None, accession=None, **extra))
        return out[-1]
    def wiki(slug, ending, key, title, year, kind, reason, theme, rights, label, **extra):
        profile = core.ROOT / 'docs/research/wikiart-artist-coverage-20260920/profiles' / (slug+'.json')
        d = json.loads(profile.read_bytes())
        w = next(x for x in d['featured'] if x['paintingUrl'].endswith('/'+ending))
        names = {a['slug'].removeprefix('wikiart-artist-'):a for a in core.load('artists-before.json')}
        ids = {'wifredo-lam':'b3ed3d1c-ddc2-4fbe-8215-3e962f4998c2',
            'joaquin-torres-garcia':'f30dd185-e8fd-4eb5-a87a-83a3f32489b7'}
        artist_id = ids.get(slug) or names[slug]['id']
        c = add(key,title,w['artistName'],year,kind,'https://www.wikiart.org'+w['paintingUrl'],reason,theme,
            artist_id=artist_id, image_url=w['image'], rights_status=rights, rights_label=label,
            source_object_id=w['_id'], profile_evidence=dict(path=str(profile.relative_to(core.ROOT)),
                sha256=core.sha(profile.read_bytes()), original_receipt=d['receipt'], object=w), **extra)
        return c
    c=wiki('gerard-sekoto','the-song-of-the-pick-1947','sekoto-song-pick','The Song of the Pick',(1946,1947),'painting',
        'Black workers under a white overseer: Sekoto gives the labourers collective strength. A work about racialised labour and dignity, not a depiction of a national independence ceremony.',
        'https://www.sil.si.edu/silpublications/modernafricanart/monographs_detail.cfm?artist=Sekoto%2C+Gerard%2C+1913-1993',
        'restricted','Gerard Sekoto Fair Use (WikiArt)')
    c['date_note']='WikiArt gives 1947; Smithsonian Libraries discusses the work as 1946–1947. Preserve the supported range; no holding institution inferred.'
    for ending,key,title,kind in [('famine-sketch-1943','abedin-famine-sketch','Famine Sketch','drawing'),
        ('laborer-couple-1943','abedin-laborer-couple','Laborer couple','unknown')]:
        wiki('zainul-abedin',ending,key,title,1943,kind,
            'Witness to poverty and human vulnerability in colonial Bengal. Selected alongside Abedin’s documented 1943 famine practice; individual WikiArt sheets are not automatically equated with the specific loans shown at documenta.',
            ABEDIN, 'unknown' if key=='abedin-famine-sketch' else 'restricted',
            'Rights not independently verified' if key=='abedin-famine-sketch' else 'Zainul Abedin Fair Use (WikiArt)')
    c=wiki('joaquin-torres-garcia','inverted-america-1943','torres-inverted-america','Inverted America',1943,'drawing',
        'Reverses the map’s north–south hierarchy to assert South American cultural autonomy. An editorial connection to cultural decolonisation, rather than a record of a political independence event.',
        'https://smarthistory.org/torres-garcia-inverted-america/','public_domain','Public domain (WikiArt)')
    c.update(medium='Ink on paper',dimensions='22 × 16 cm',
        holding_note='Sources disagree over foundation ownership and museum loans; no accepted holding created.')
    c=wiki('mahmoud-saiid','girls-from-bahary-banat-bahary','said-girls-bahary','Girls from Bahary (Banat Bahary)',1935,'painting',
        'Alexandrian women and local life in Egyptian modern painting. Included as cultural self-representation, with the artist’s class and gendered viewpoint left open to critical reading.',
        'https://direct.mit.edu/afar/article/54/4/20/107715/The-Negress-of-Alexandria-African-Womanhood-in',
        'unknown','Public domain Egypt (WikiArt; territorial label)')
    c['rights_note']='A territorial public-domain label is preserved without asserting worldwide copyright clearance.'
    for ending,key,title,year in [('zambezia-zambezia-1950','lam-zambezia','Zambezia, Zambezia',1950),
        ('la-fianc-e-de-kiriwina-1949','lam-kiriwina','La Fiancée de Kiriwina',1949)]:
        wiki('wifredo-lam',ending,key,title,year,'painting',
            'Lam’s hybrid figures connect Afro-Caribbean spiritual and cultural worlds with modern painting. Selected for the challenge to colonial cultural hierarchies, not as a literal independence scene.',
            'https://www.moma.org/collection/works/34666','restricted','Wifredo Lam Fair Use (WikiArt)')
    out[-2].update(medium='Oil on canvas',dimensions='125.4 × 110.8 cm')
    out[-1].update(medium='Oil',dimensions='128 × 113.5 cm')
    for key,subject,panel,oid,image,dimensions in [
        ('orozco-cortez','Cortez and the Cross',11,'p.934.13.13','https://uploads1.wikiart.org/00307/images/jose-clemente-orozco/panel-13-cortez-and-the-cross-2.jpg!Large.jpg','304.8 × 188 cm'),
        ('orozco-hispano','Hispano-America',14,'p.934.13.16','https://uploads4.wikiart.org/00307/images/jose-clemente-orozco/panel-16-hispano-america-2.jpg','304.8 × 302.3 cm')]:
        legacy=13 if panel==11 else 16
        ending=f'panel-{legacy}-'+('cortez-and-the-cross' if panel==11 else 'hispano-america')+'-the-epic-of-american-civilization-1934'
        c=add(key,f'The Epic of American Civilization: {subject} (Panel {panel})','José Clemente Orozco',(1932,1934),'painting',
            'https://www.wikiart.org/en/jose-clemente-orozco/'+ending,
            'The Dartmouth mural cycle critiques conquest, colonial power and their modern continuities. This panel is selected individually, with the museum’s title and numbering.',HOOD_GUIDE,
            artist_id='b5bb7d85-7a3b-41cf-9493-432f82f787b1',image_url=image,rights_status='public_domain',rights_label='Public domain (WikiArt)',
            museum_url='https://hoodmuseum.dartmouth.edu/objects/'+oid,
            identity_note=f'WikiArt labels this Panel {legacy}; Hood Museum identifies it as Panel {panel}. These are the same titled panel, not two artworks.')
        c.update(institution_id=HOOD,accession=oid.upper(),medium='Fresco',dimensions=dimensions)
        if key=='orozco-cortez':
            c['image_note']='Installation view: Cortez and the Cross is the central panel; adjoining mural panels and architectural surroundings are visible. Full source frame retained.'
    c=add('hyppolite-fete-morts','Fête du Morts','Hector Hyppolite',1946,'painting',
        'https://www.wikiart.org/en/hector-hyppolite/fete-du-morts-1946',
        'Haitian religious imagery and Vodou cultural authority, read in the context of Hyppolite’s artistic agency and the colonial hierarchies through which European audiences received his work.',HYPPOLITE,
        artist_id='15057d91-cdbc-4d86-9c72-20d60e00159f',image_url='https://uploads3.wikiart.org/00547/images/hector-hyppolite/hyppolite-fete-du-morts-1946-1948.jpg!Large.jpg',
        rights_status='restricted',rights_label='Hector Hyppolite Fair Use (WikiArt)')
    c.update(dimensions='61 × 61 cm',date_note='WikiArt object caption dates the work 1946. The image filename contains 1946–1948; a filename is not treated as an authoritative creation-date field.')
    c=add('chua-national-language','National Language Class','Chua Mia Tee',1959,'painting',NGS,
        'Learning Malay becomes a collective act of Malayanisation and anti-colonial cultural change. The National Gallery interprets the classroom as history painting from below.',NGS)
    c.update(medium='Oil on canvas',dimensions='112 × 153 cm',institution_id=SINGAPORE,accession='P-0145',
        museum_url='https://www.nationalgallery.sg/content/dam/about/annual-reports/reports/FY2021%20Annual%20Report.pdf')
    c=add('chua-epic-poem','Epic Poem of Malaya','Chua Mia Tee',1955,'painting',
        'https://www.roots.gov.sg/Collection-Landing/listing/1116747?taigerlist=collections',
        'A speaker and young listeners embody an emerging Malayan nationalism. Selected for the national heritage record’s explicit interpretation.',NGS)
    c.update(medium='Oil on canvas',dimensions='107 × 125.5 cm (image; Roots record)',institution_id=SINGAPORE,
        metadata_note='Published dimensions vary (105.5 × 125 cm in a Gallery festival booklet); retain the object-level Roots dimensions and do not invent an accession number.')
    for key,title,ending in [('baya-birds','Paysage aux oiseaux','paysage-aux-oiseaux-1966-gouache-sur-papier-1966'),
        ('baya-vase','Vase aux poissons et cithare','vase-aux-poissons-et-cithare-1966')]:
        c=add(key,title,'Baya',1966,'painting','https://www.wikiart.org/en/baya-mahieddine/'+ending,
            'Baya’s renewed painting after Algerian independence builds a visual world of birds, plants and music. Read as cultural agency; neither a literal liberation scene nor proof of a political affiliation.',BAYA)
        c.update(medium='Gouache on paper',dimensions='100 × 150 cm',
            holding_note='AWARE credits Musée du Quai Branly photography and rights holders. Photo credit alone is not an accepted current-holding assertion.',rights_note='© Othmane Mahieddine; metadata only.')
    c=add('melehi-pulsation','Pulsation','Mohamed Melehi',1964,'painting',POMPIDOU,
        'An early wave motif in Melehi’s abstraction, linked by the museum to Arabic calligraphy and his later cultural activity in Morocco. Exhibited in Présences arabes: Art moderne et décolonisation; cultural context, not a depiction of liberation.',POMPIDOU)
    c.update(medium='Acrylic on canvas',dimensions='152 × 131 cm',accession='AM 2011-123',institution_id=core.uid('institution/pompidou'),
        museum_url=POMPIDOU,place_note='Museum inscription and catalogue say made in New York; Moroccan creator identity is not a creation-place claim.')
    add('salahi-reborn','Reborn Sounds of Childhood Dreams I','Ibrahim El-Salahi',(1961,1965),'painting',
        'https://shop.tate.org.uk/ibrahim-el-salahi-reborn-sounds-of-childhood-dreams-i-art-print/26593.html',
        'Sudanese modernism joins memory, spiritual imagery and a reworking of inherited visual languages in the independence era. Tate confirms the title and 1961–65 creation range.',
        'https://www.moma.org/calendar/exhibitions/4749',metadata_note='The accessible Tate print page supports the original title/date; dimensions and medium of the reproduction are not copied onto the original. Direct collection-page retrieval failed.')
    c=add('malangatana-untitled-1967','Untitled','Malangatana Valente Ngwenya',1967,'painting',
        'https://www.tate.org.uk/art/artworks/ngwenya-untitled-t13985',
        'Colonial violence and the struggle in Mozambique form the context for Malangatana’s densely populated imagery. Selected alongside the museum-documented prison drawings already in the period.',
        'https://post.moma.org/malangatana-as-anti-colonial-subject-1959-74/',
        metadata_source_url=MET_LABELS,metadata_note='Tate collection page unavailable; the Met’s Surrealism Beyond Borders labels identify the 1967 work and its Tate loan. No current display claim.')
    c.update(institution_id=TATE,museum_url=MET_LABELS,accession='T13985',medium='Oil on hardboard')
    add('siqueiros-america-tropical','América Tropical','David Alfaro Siqueiros',1932,'painting',
        'https://www.getty.edu/projects/conservation-america-tropical/',
        'The Los Angeles mural confronts imperial domination through a crucified Indigenous figure beneath an eagle. Its whitewashing and later recovery are part of the work’s political history.',
        'https://www.getty.edu/publications/getty-research-journal/21/shorter-notices/worldwide-emotion/',
        artist_id='978e9fae-5d2a-41a8-9113-933e1d3874c3',
        holding_note='Getty was a conservation partner. No Getty ownership or museum holding inferred; the mural is at Italian Hall, El Pueblo de Los Angeles.')
    return out


EXISTING = [
    ('61e8466a-b9a3-5aaa-947d-7bbaf9adbc53','https://www.moma.org/audio/735','Tarsila’s Abaporu helped inspire Anthropophagy: a programme of cultural independence through transformation of external influences.'),
    ('6f5b6b4c-755a-560e-b4e2-56e427c1104a','https://www.moma.org/audio/playlist/48/736','Anthropophagy develops Brazilian cultural autonomy; a modernist metaphor, not a literal claim about Indigenous communities.'),
    ('b76db65a-2d95-5fc6-976f-386b2a208a75','https://www.monumentos.gob.cl/monumentos/monumentos-historicos/murales-de-la-escuela-mexico','Death to the Invader connects the histories of resistance in Mexico and Chile. Existing image retained.'),
    ('312ac327-348d-5b99-a379-ddce75e54a82','https://www.sfmoma.org/exhibition/pan-american-unity/','Pan American Unity proposes exchange and solidarity across the Americas, including Indigenous artistic traditions. Cultural context rather than an independence scene.'),
    ('b3b1943a-9c2e-4135-b371-dc9041c103f3','https://www.moma.org/collection/works/79146','Collective Suicide addresses Indigenous resistance to Spanish conquest. Existing record retained; no new licensed reproduction located.'),
]


def duplicates(db,c):
    urls=[c['url']]+([c['museum_url']] if c.get('accession') and c.get('museum_url') and c['museum_url'] not in (MET_LABELS,) and 'annual-reports' not in c['museum_url'] else [])
    return db.execute('''SELECT id::text FROM artworks WHERE (current_institution_id=%s AND accession_number=%s)
      OR (normalized_title=%s AND unlinked_creator_label=%s AND creation_year_start=%s AND creation_year_end=%s)
      OR (normalized_title=%s AND creation_year_start=%s AND creation_year_end=%s AND id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s))
      UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)
      UNION SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)''',
      (c['institution_id'],c['accession'],core.norm(c['title']),c['maker'],c['lo'],c['hi'],core.norm(c['title']),c['lo'],c['hi'],c.get('artist_id'),urls,urls)).fetchall()


def plan():
    records=candidates()
    assert len(records)==18 and sum(bool(c.get('image_url')) for c in records)==10
    with core.connect() as db:
        collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s',(COLLECTION,)).fetchone()['record']
        assert collection['curator_kind']=='owner' and collection['institution_id'] is None and collection['status']=='review'
        assert not db.execute("SELECT 1 FROM institutions WHERE name ILIKE '%%pompidou%%'").fetchone()
        institutions=[dict(id=core.uid('institution/pompidou'),slug='decolonization-centre-pompidou',name='Centre Pompidou — Musée national d’art moderne',
            normalized_name=core.norm('Centre Pompidou — Musée national d’art moderne'),kind='museum',status='review',website_url='https://www.centrepompidou.fr/')]
        for c in records:
            assert 1900 <= c['lo'] <= c['hi'] <=1970
            if c.get('image_url'): assert c['hi']<=1955
            matches=duplicates(db,c)
            assert not matches,(c['key'],matches)
            c.update(artwork_id=core.uid(c['key']),slug='decolonization-'+c['key'])
        existing=[]
        for aid,url,reason in EXISTING:
            row=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
            assert row['creation_year_end']<=1970 and row['status']!='archived'
            existing.append(dict(id=aid,slug=row['slug'],title=row['title'],url=url,reason=reason,preimage=row))
        artists=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',
            (sorted(set(c['artist_id'] for c in records if c.get('artist_id'))),)).fetchall()
    captures={p.name:core.sha(p.read_bytes()) for p in (core.RUN/'captures').iterdir() if p.is_file()}
    core.save(core.RUN/'plan.json',dict(records=records,existing_selection=existing,collection_preimage=collection,
        institutions_to_create=institutions,artist_preimages=artists,captures=captures,
        image_policy='Only 10 pinned WikiArt reproductions, creation end <=1955, under the prior user-authorized workflow. Restricted and unknown labels retained; no clearance or verified timestamp invented. Eight records remain metadata only.',
        wikiart_authorization='docs/research/wikiart-selected-images-20260919/README.md',
        selection_basis='Owner editorial selection requested 28 September 2026; distinct from museum highlight designation.'))
    core.save(core.RUN/'plan-pin.json',dict(sha256=core.sha((core.RUN/'plan.json').read_bytes())))
    print('Pinned 18 new records, 5 existing selections and 10 WikiArt images.')


def prepare():
    p=core.pinned()
    core.pinned=lambda:{**p,'records':[c for c in p['records'] if c.get('image_url')]}
    core.prepare()


def apply():
    p=core.pinned()
    if (core.RUN/'applied.json').exists(): return verify()
    backup,qa=core.load('backup.json'),core.load('visual-review.json')
    assert core.sha(Path(backup['path']).read_bytes())==backup['sha256']
    assert qa['approved'] and qa['plan_sha256']==core.load('plan-pin.json')['sha256']
    assert qa['images_sha256']==core.sha((core.RUN/'images.json').read_bytes())
    images={im['key']:im for im in core.load('images.json')}
    assert set(images)=={c['key'] for c in p['records'] if c.get('image_url')}
    for name,digest in p['captures'].items(): assert core.sha((core.RUN/'captures'/name).read_bytes())==digest
    for c in p['records']:
        if c.get('profile_evidence'):
            e=c['profile_evidence'];assert core.sha((core.ROOT/e['path']).read_bytes())==e['sha256']
    with core.connect(False) as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('LOCK TABLE artworks,external_identifiers IN SHARE ROW EXCLUSIVE MODE')
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active',(core.ACTOR,)).fetchone()
        assert db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(COLLECTION,)).fetchone()['record']==p['collection_preimage']
        for c in p['records']: assert not duplicates(db,c),c['key']
        for c in p['existing_selection']: assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['id'],)).fetchone()['record']==c['preimage']
        for row in p['artist_preimages']: assert db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(row['record']['id'],)).fetchone()==row
        for i in p['institutions_to_create']:
            assert not db.execute('SELECT 1 FROM institutions WHERE slug=%s OR normalized_name=%s',(i['slug'],i['normalized_name'])).fetchone()
            core.insert(db,'institutions',i)
        for key,(name,url) in SOURCES.items():
            core.insert(db,'sources',dict(id=core.uid('source/'+key),slug=core.CAMPAIGN+'-'+key,name=name,base_url=url,source_type='collection_page'))
        sid=core.uid('source/research')
        for c in p['records']:
            source=core.uid('source/wikiart') if 'wikiart.org' in c['url'] else sid
            core.insert(db,'artworks',dict(id=c['artwork_id'],slug=c['slug'],title=c['title'],normalized_title=core.norm(c['title']),
                unlinked_creator_label=c['maker'],creation_year_start=c['lo'],creation_year_end=c['hi'],date_display=c['date_display'],date_precision=c['precision'],
                work_type=c['type'],medium_text=c['medium'],dimensions_text=c['dimensions'],current_institution_id=c['institution_id'],accession_number=c['accession'],
                description_md=c['reason'],status='review',research_candidate=True,created_by=core.ACTOR,updated_by=core.ACTOR))
            if c.get('artist_id'):
                core.insert(db,'artwork_artists',dict(artwork_id=c['artwork_id'],artist_id=c['artist_id'],attribution_role='primary',attribution_note='Named maker reconciled with existing catalogue profile; source '+c['url']))
            core.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=c['artwork_id'],scheme='decolonization-research-object',external_id=c.get('source_object_id',c['key']),canonical_url=c['url'],source_id=source,retrieved_at=qa['at']))
            if c['institution_id']:
                url=c.get('museum_url') or c['url']
                core.insert(db,'artwork_location_assertions',dict(artwork_id=c['artwork_id'],claim_type='holding',institution_id=c['institution_id'],context='collection',source_id=sid,
                    source_url=url,evidence_note='Documented collection connection in the retained primary source. '+(c['accession'] or 'No accession supplied.')+' No current display claim.',checked_at=qa['at'],review_state='accepted'))
            core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['artwork_id'],field_name='researched_object_identity',source_id=source,
                source_url=c.get('metadata_source_url') or c['url'],evidence_note=json.dumps(dict(record=c,captures=p['captures'],plan_sha256=core.load('plan-pin.json')['sha256']),ensure_ascii=False),retrieved_at=qa['at'],created_by=core.ACTOR))
            core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['artwork_id'],field_name='decolonization_editorial_selection',source_id=sid,
                source_url=c['theme_url'],evidence_note=c['reason']+' Owner selection; not a museum masterpiece designation.',retrieved_at=qa['at'],created_by=core.ACTOR))
            if c['key'] in images:
                im=images[c['key']];raw=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
                assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
                core.insert(db,'media_assets',dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=c['url'],provider_name='WikiArt',mime_type='image/jpeg',
                    width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=f"{c['title']} — {c['maker']}, {c['date_display']}",
                    rights_status=c['rights_status'],license_label=c['rights_label'],creator_credit=c['maker']+'; reproduction via WikiArt',
                    attribution_text=c['rights_label']+'. Full-frame resize and JPEG compression. Source label retained; no independent clearance claimed. '+c.get('image_note',''),retrieved_at=im['download']['at']))
                core.insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=source,source_record_id=c.get('source_object_id',c['key']),source_checksum=core.sha(core.encode(c)),
                    source_image_url=c['image_url'],policy_url=c['url'],rights_basis=p['image_policy']+' '+c.get('rights_note',''),adapter_version=core.CAMPAIGN,checked_at=qa['at'],
                    evidence_json=core.Jsonb(dict(record=c,download=im['download'],captures=p['captures'],visual_review=qa))))
                core.insert(db,'artwork_media',dict(artwork_id=c['artwork_id'],media_id=im['media_id'],sort_order=0,view_label='Installation view with adjoining panels' if c.get('image_note') else 'WikiArt reproduction'))
                db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['media_id'],c['artwork_id']))
        all_selected=[dict(id=c['artwork_id'],url=c['url'],reason=c['reason']) for c in p['records']]+p['existing_selection']
        pos=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(COLLECTION,)).fetchone()['n']
        for c in all_selected:
            if not db.execute('SELECT 1 FROM curated_collection_items WHERE collection_id=%s AND artwork_id=%s',(COLLECTION,c['id'])).fetchone():
                pos+=1
                core.insert(db,'curated_collection_items',dict(collection_id=COLLECTION,artwork_id=c['id'],position=pos,reason=c['reason']+' Personal editorial selection; not a museum highlight claim.',source_id=sid,source_url=c['url'],checked_at=qa['at']))
        for c in p['existing_selection']:
            core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['id'],field_name='decolonization_editorial_selection',source_id=sid,source_url=c['url'],evidence_note=c['reason'],retrieved_at=qa['at'],created_by=core.ACTOR))
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(COLLECTION,))
        rows=verify_rows(db,p)
    core.save(core.RUN/'applied.json',dict(at=core.now(),records=rows,new_records=18,new_images=10,existing_selected=5,published=False))
    print('Applied 18 real review records and 10 images; selected 5 existing works. No publication.')


def preset():
    assert (core.RUN/'applied.json').exists()
    p=core.pinned();presets=json.loads(PRESETS.read_bytes());before=core.load('presets-before.json')
    for item in presets:
        old=next(x for x in before if x['id']==item['id'])
        if item['id']!='decolonization': assert item==old
    item=next(x for x in presets if x['id']=='decolonization')
    old=next(x for x in before if x['id']=='decolonization')
    if (core.RUN/'preset-after.json').exists(): assert item==core.load('preset-after.json');return
    assert item==old
    item['description']='Independence, colonial violence and cultural self-representation across Africa, Asia and the Americas. Earlier art gives roots to the postwar struggles; later writing and South African democracy extend the story.'
    item['startingScope']='Africa, Asia & the Americas'
    item['focus']['label']='Selected works explore resistance, colonial labour and cultural autonomy. These include earlier artistic roots and later independence-era work; cultural connections do not mean every picture depicts a political event.'
    item['focus']['related']['artwork'] += [c['artwork_id'] for c in p['records']]+[c['id'] for c in p['existing_selection']]
    assert len(set(item['focus']['related']['artwork']))==46 and len(item['focus']['context']['artwork'])==3
    for c in p['records']:
        if c['theme_url'] not in [s['url'] for s in item['sources']]:
            item['sources'].append(dict(name=c['maker']+' — research context',url=c['theme_url']))
    for c in p['existing_selection']:
        if c['url'] not in [s['url'] for s in item['sources']]: item['sources'].append(dict(name=c['title']+' — museum interpretation',url=c['url']))
    PRESETS.write_text(json.dumps(presets,ensure_ascii=False,indent=2)+'\n')
    core.save(core.RUN/'preset-after.json',item)
    print('Decolonisation now selects 49 records: 29 illustrated artworks, with books/events unchanged.')


def verify_rows(db,p):
    rows=db.execute('''SELECT a.id::text,a.title,a.status,a.published_at,a.creation_year_start,a.creation_year_end,a.work_type,a.primary_media_id::text,
      a.unlinked_creator_label,a.current_institution_id::text,a.accession_number,artline_has_selection_evidence(a.id) selected,
      m.rights_status,m.license_label,m.verified_at,m.byte_size,
      (SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_count,
      (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display') displays
      FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',([c['artwork_id'] for c in p['records']],)).fetchall()
    assert len(rows)==18
    for c in p['records']:
        r=next(r for r in rows if r['id']==c['artwork_id'])
        assert r['status']=='review' and r['published_at'] is None and r['selected'] and r['displays']==0,r
        assert (r['creation_year_start'],r['creation_year_end'])==(c['lo'],c['hi'])
        assert r['unlinked_creator_label']==c['maker'] and r['work_type']==c['type'] and r['artist_count']==int(bool(c.get('artist_id')))
        assert (r['current_institution_id'],r['accession_number'])==(c['institution_id'],c['accession'])
        assert bool(r['primary_media_id'])==bool(c.get('image_url'))
        if c.get('image_url'): assert r['rights_status']==c['rights_status'] and r['license_label']==c['rights_label'] and r['verified_at'] is None and r['byte_size']<=100000
    for c in p['existing_selection']: assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['id'],)).fetchone()['record']==c['preimage']
    return rows


def verify():
    p=core.pinned()
    with core.connect() as db: rows=verify_rows(db,p)
    for im in core.load('images.json'):
        raw=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert core.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
    core.save(core.RUN/'verification.json',dict(records=rows,new_records=18,new_images=10,existing_selected=5,new_profiles=0,new_display_claims=0,published=False))
    print('Verified 18 new records, 10 images and unchanged metadata for all 5 reused works.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','prepare','backup','apply','preset','verify'])
    phase=parser.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
