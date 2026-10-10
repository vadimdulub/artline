#!/usr/bin/env python3
"""Two individually reviewed alternative WikiArt images for held local objects."""
import argparse
import importlib.util
import json
import uuid
from pathlib import Path

s = importlib.util.spec_from_file_location('wiki', Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki = importlib.util.module_from_spec(s)
s.loader.exec_module(wiki)
base, core = wiki.base, wiki.core
RUN = core.ROOT / 'docs/research/local-wikiart-version-correction-images-20261006'
PREVIOUS = RUN.parent / 'local-wikiart-reused-images-20261006'
wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-individual-alternative-version-v1'
original_facts, original_attach = wiki.page_facts, wiki.attach
BASIS = 'Existing local artwork and creator identities, independently inspected authority or museum photographs and individually pinned alternative WikiArt image. Actual source rights labels and user source approval retained separately. Existing titles, dates, holdings and review status preserved; image-only local attachment.'
PAGES = {
    '10464bbb-5757-5c4b-8fb3-76811411511d': 'https://www.wikiart.org/en/henri-matisse/dishes-and-fruit-on-a-red-and-black-carpet-1901',
    '83b1c160-ace0-4039-9b20-7951e7962901': 'https://www.wikiart.org/en/edgar-degas/the-dancing-class-1874',
}


def snapshot():
    if (RUN / 'candidates.json').exists():
        return
    candidates = []
    with base.connect() as db:
        for aid, page in PAGES.items():
            old = json.loads((PREVIOUS / 'images' / (aid + '.json')).read_bytes())
            current = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (aid,)).fetchone()['record']
            if current != old['before_record'] or current['primary_media_id'] is not None or current['status'] != 'review':
                raise ValueError('Previously held local record changed')
            wiki.chicago.authority_unchanged(db, old)
            keys = set(json.loads((PREVIOUS / 'candidates.json').read_bytes())['candidates'][0])
            c = {k: old[k] for k in keys}
            c.update(page=page)
            candidates.append(c)
        baseline = db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    core.save_new(RUN / 'candidates.json', dict(at=core.now(), baseline=baseline, candidates=candidates,
        selection='Two previously held, eligible existing local objects; correct alternative source images identified through independent visual comparison. No metadata or publication changes.'))
    documents = []
    for name in ('AGENTS.md', 'docs/ARTLINE_IMAGE_USE.md'):
        data = (core.ROOT / name).read_bytes()
        capture = 'metadata/authorization/' + Path(name).name
        core.save_new(RUN / capture, data)
        documents.append(dict(source_path=name, capture=capture, sha256=core.sha(data)))
    core.save_new(RUN / 'source-authorization.json', dict(at=core.now(), source='WikiArt', target='local',
        record_actual_rights_separately=True, documents=documents, user_instruction='see new md file - wiki art is fully approved',
        scope='Selected existing local missing-image attachments; preserve actual rights assertions and catalogue metadata, holdings and review status.'))


def proof_bytes(proof):
    data = Path(proof['path']).read_bytes()
    if core.sha(data) != proof['sha256'] or len(data) != proof['bytes']:
        raise ValueError('Individually reviewed evidence changed')
    return data


def page_facts(c, data, rc):
    rows = json.loads((RUN / 'object-version-review.json').read_bytes())['images']
    matches = [x for x in rows if x['artwork_id'] == c['artwork_id']]
    if len(matches) != 1 or matches[0]['decision'] != 'approved':
        raise ValueError('Unique individual alternative image approval absent')
    review = matches[0]
    for key in ('scheme', 'external_id', 'title', 'accession_number', 'institution_id'):
        if c[key] != review['catalogue_identity'][key]:
            raise ValueError('Reviewed local identity changed: ' + key)
    if PAGES.get(c['artwork_id']) != c['page'] or review['page'] != c['page'] or rc['url'] != c['page'] or rc['sha256'] != review['wikiart_page_sha256']:
        raise ValueError('Individually reviewed source page changed')
    for proof in review['comparison_evidence']:
        proof_bytes(proof)
    source = dict(c, external_id=review['wikiart_id'], title=review['wikiart_title'])
    facts = original_facts(source, data, rc)
    if facts['source_metadata']['year'] != review['wikiart_year']:
        raise ValueError('Individually reviewed source date changed')
    chosen = review['source_image']
    proof_bytes(chosen)
    if review['selection'] == 'published_variant':
        if facts['source_image_url'] != review['page_primary_image_url']:
            raise ValueError('Expected default photograph changed')
        variants = [v for v in facts['source_image_variants'] if v.get('data-image-url') == chosen['url']]
        if len(variants) != 1 or variants[0] != review['published_variant']:
            raise ValueError('Reviewed variant is not explicitly published on this exact artwork page')
        facts['page_primary_image_url'] = facts['source_image_url']
        facts['selected_source_variant'] = variants[0]
        facts['source_image_url'] = chosen['url']
    elif review['selection'] != 'page_primary' or facts['source_image_url'] != chosen['url']:
        raise ValueError('Reviewed primary photograph differs')
    facts.update(date_note=review['note'], individual_version_review=review)
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
        proof = im['raw']['wikiart_facts']['individual_version_review']['source_image']
        data = proof_bytes(proof)
        if proof['url'] != im['source_image_url']:
            raise ValueError('Selected inspected source differs')
        with base.connect() as db:
            if db.execute('SELECT primary_media_id FROM artworks WHERE id=%s', (im['artwork_id'],)).fetchone()['primary_media_id']:
                raise ValueError('An image has already been attached')
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
        print('Prepared from inspected alternative:', im['title'], flush=True)
    base.prepare('contact-sheets-only')


def attach(db, im, target):
    review = im['raw']['wikiart_facts']['individual_version_review']
    if im['source_sha256'] != review['source_image']['sha256'] or im['source_bytes'] != review['source_image']['bytes']:
        raise ValueError('Prepared source is not the individually inspected photograph')
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
                raise ValueError('Existing artwork authority or individual review basis differs')
    core.save_new(RUN / 'alternative-image-database-verification.json', dict(at=core.now(), passed=True,
        existing_authority_ids_preserved=True, individual_alternative_image_reviews_verified=True))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['snapshot', 'research', 'prepare', 'apply', 'verify'])
    args = p.parse_args()
    if args.phase == 'snapshot': snapshot()
    elif args.phase == 'research': wiki.research(2)
    elif args.phase == 'prepare': prepare()
    elif args.phase == 'apply': base.apply()
    else: verify()
