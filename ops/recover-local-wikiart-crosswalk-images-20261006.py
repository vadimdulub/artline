#!/usr/bin/env python3
"""Three selected local WikiArt matches through existing artwork authorities."""
import argparse
import importlib.util
import json
import uuid
from pathlib import Path

s = importlib.util.spec_from_file_location('wiki', Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki = importlib.util.module_from_spec(s)
s.loader.exec_module(wiki)
base, core = wiki.base, wiki.core
RUN = core.ROOT / 'docs/research/local-wikiart-crosswalk-images-20261006'
wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-reviewed-object-crosswalk-v1'
original_facts = wiki.page_facts
original_attach = wiki.attach
BASIS = 'Existing local Wikidata artwork identity, fresh explicit P6002 WikiArt artwork crosswalk, unchanged primary creator authority and individually reviewed source title/date/version with private comparison evidence. Actual source rights labels retained; separate user source approval, with no independent copyright-holder permission asserted. Local image-only attachment.'


def values(entity, prop):
    return [x['mainsnak']['datavalue']['value'] for x in entity.get('claims', {}).get(prop, [])
            if x.get('rank') != 'deprecated' and x['mainsnak'].get('snaktype') == 'value']


def page_facts(c, data, rc):
    rows = json.loads((RUN / 'object-version-review.json').read_bytes())['images']
    matched = [x for x in rows if x['artwork_id'] == c['artwork_id']]
    if len(matched) != 1 or matched[0]['decision'] != 'approved':
        raise ValueError('Individually approved artwork/version review missing')
    review = matched[0]
    if c['scheme'] != 'wikidata' or c['external_id'] != review['qid'] or c['title'] != review['catalogue_title']:
        raise ValueError('Existing artwork identity differs from reviewed crosswalk')
    if c['page'] != review['page'] or rc['url'] != review['page'] or rc['sha256'] != review['wikiart_page_sha256']:
        raise ValueError('Reviewed exact WikiArt page changed')
    url = 'https://www.wikidata.org/wiki/Special:EntityData/' + c['external_id'] + '.json'
    path = RUN / 'metadata' / (core.sha(url.encode()) + '.json')
    raw = path.read_bytes()
    receipt = json.loads(path.with_suffix('.receipt.json').read_bytes())
    if receipt['url'] != url or receipt['sha256'] != core.sha(raw) or receipt['bytes'] != len(raw):
        raise ValueError('Pinned artwork authority capture differs')
    entity = json.loads(raw)['entities'][c['external_id']]
    if entity['id'] != c['external_id'] or values(entity, 'P6002') != [review['page'].removeprefix('https://www.wikiart.org/en/')]:
        raise ValueError('Explicit artwork-to-WikiArt crosswalk differs')
    creators = {x['external_id'] for p in c['creator_authorities'] for x in p['artist_identifiers'] if x['scheme'] == 'wikidata'}
    claims = [x for x in entity.get('claims', {}).get('P170', []) if x.get('rank') != 'deprecated']
    if len(creators) != 1 or {x['id'] for x in values(entity, 'P170')} != creators or any(set(x.get('qualifiers', {})) - {'P7452'} for x in claims):
        raise ValueError('Primary creator crosswalk is different or qualified')
    names = {wiki.norm(x['value']) for x in entity.get('labels', {}).values()}
    names.update(wiki.norm(x['value']) for rows in entity.get('aliases', {}).values() for x in rows)
    if wiki.norm(c['title']) not in names:
        raise ValueError('Catalogue title does not identify the captured artwork entity')
    if c['institution_qid'] not in {x['id'] for x in values(entity, 'P195')}:
        raise ValueError('Existing holding reference does not match artwork authority')
    if c['accession_number'] and c['accession_number'] not in values(entity, 'P217'):
        raise ValueError('Existing accession conflicts with artwork authority')
    for proof in review['comparison_evidence']:
        image_bytes = Path(proof['path']).read_bytes()
        if core.sha(image_bytes) != proof['sha256'] or len(image_bytes) != proof['bytes']:
            raise ValueError('Reviewed private comparison image changed')
        capture = proof.get('page_capture')
        if capture and core.sha((core.ROOT / capture['path']).read_bytes()) != capture['sha256']:
            raise ValueError('Comparison page changed')
    extra = review.get('additional_date_evidence')
    if extra and core.sha((core.ROOT / extra['path']).read_bytes()) != extra['sha256']:
        raise ValueError('Additional source-date evidence changed')
    # The explicitly reviewed crosswalk supplies the WikiArt object ID and
    # title. The candidate keeps its real, existing database scheme and ID.
    source = dict(c, external_id=review['wikiart_id'], title=review['wikiart_title'])
    facts = original_facts(source, data, rc)
    inspected = [x for x in review['comparison_evidence'] if x['role'] == 'wikiart-source']
    if len(inspected) != 1 or inspected[0]['url'] != facts['source_image_url']:
        raise ValueError('Selected WikiArt photograph differs from inspected version')
    if wiki.visible_creation_date(wiki.BeautifulSoup(data, 'html.parser')) != review['source_date']:
        raise ValueError('Reviewed displayed source date differs')
    facts['date_note'] = review['note']
    facts['object_crosswalk'] = dict(entity=entity, receipt=receipt, review=review)
    return facts


wiki.page_facts = page_facts


def prepare():
    for path in sorted((RUN / 'selected' / wiki.PROVIDER).glob('*.json')):
        im = json.loads(path.read_bytes())
        dest = RUN / 'images' / path.name
        if dest.exists():
            wiki.verify_image(json.loads(dest.read_bytes()))
            continue
        wiki.verify_image(im)
        proof = json.loads((RUN / 'metadata/comparisons' / (im['artwork_id'] + '-wikiart-source.json')).read_bytes())
        data = Path(proof['path']).read_bytes()
        if proof['url'] != im['source_image_url'] or core.sha(data) != proof['sha256'] or len(data) != proof['bytes']:
            raise ValueError('Already inspected WikiArt source bytes differ')
        with base.connect() as db:
            if db.execute('SELECT primary_media_id FROM artworks WHERE id=%s', (im['artwork_id'],)).fetchone()['primary_media_id']:
                core.event(RUN, dict(provider=wiki.PROVIDER, artwork_id=im['artwork_id'], outcome='existing_image_preserved'))
                continue
        source_sha = core.sha(data)
        archive = base.ARCHIVE / 'source-images' / RUN.name / (im['artwork_id'] + '-' + source_sha[:16] + '.image')
        core.save_new(archive, data)
        result, width, height, quality = core.compress(data)
        digest = core.sha(result)
        public_path = '/assets/artworks/imported/' + RUN.name + '/' + im['artwork_id'] + '-' + digest[:16] + '.jpg'
        core.save_new(core.ROOT / 'apps/web/public' / public_path.lstrip('/'), result)
        im.update(path=public_path, sha256=digest, bytes=len(result), width=width, height=height, jpeg_quality=quality,
                  source_sha256=source_sha, source_bytes=len(data), source_archive=str(archive), downloaded_at=proof['at'],
                  response_headers=proof['response_headers'], transform='Full-frame proportional resize and JPEG compression; no crop or generated content',
                  media_id=str(uuid.uuid5(uuid.NAMESPACE_URL, public_path)))
        core.save_new(dest, im)
        core.event(RUN, dict(provider=wiki.PROVIDER, artwork_id=im['artwork_id'], outcome='prepared'))
        print('Prepared from inspected source:', im['title'], flush=True)
    base.prepare('contact-sheets-only')


def attach(db, im, target):
    result = original_attach(db, im, target)
    if result == 'attached':
        db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s', (BASIS, im['media_id']))
    return result


base.m.attach = attach


def verify():
    wiki.verify()
    with base.connect() as db:
        for im in base.prepared():
            row = db.execute('SELECT rights_basis,source_record_id FROM media_rights_evidence WHERE media_id=%s', (im['media_id'],)).fetchone()
            if row != dict(rights_basis=BASIS, source_record_id=im['external_id']):
                raise ValueError('Existing authority identifier or crosswalk basis not preserved')
    core.save_new(RUN / 'crosswalk-database-verification.json', dict(at=core.now(), passed=True, existing_authority_ids_preserved=True))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['research', 'prepare', 'apply', 'verify'])
    a = p.parse_args()
    if a.phase == 'research':
        wiki.research(3)
    elif a.phase == 'prepare':
        prepare()
    elif a.phase == 'apply':
        base.apply()
    else:
        verify()
