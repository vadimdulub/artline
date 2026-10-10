#!/usr/bin/env python3
"""One selected Polenov image through an explicitly authority-linked reference photograph."""
import argparse
import importlib.util
import json
import hashlib
import uuid
from pathlib import Path
from urllib.parse import urlparse

s = importlib.util.spec_from_file_location('wiki', Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki = importlib.util.module_from_spec(s)
s.loader.exec_module(wiki)
base, core = wiki.base, wiki.core
RUN = core.ROOT / 'docs/research/local-wikiart-polenov-abbey-image-20261007'
wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-polenov-authority-photo-v1'
original_facts = wiki.page_facts
original_attach = wiki.attach
BASIS = 'Existing local Wikidata artwork identity and its explicitly named Commons P18 photograph, unchanged primary creator authority and individual full-source visual comparison with WikiArt. Source c. 1875 and catalogue/authority 1911 remain separate; unknown catalogue fields remain unknown. WikiArt source approval and actual rights label are recorded separately. Local image-only attachment, with no P6002 artwork crosswalk or publication claimed.'
REVIEW_SHA256 = '25be54dec1bc8ca658099d35b60da6d077836d29f974e692d2c4871490390327'


def values(entity, prop):
    return [x['mainsnak']['datavalue']['value'] for x in entity.get('claims', {}).get(prop, [])
            if x.get('rank') != 'deprecated' and x['mainsnak'].get('snaktype') == 'value']


def page_facts(c, data, rc):
    raw_review=(RUN / 'object-version-review.json').read_bytes()
    if core.sha(raw_review)!=REVIEW_SHA256:raise ValueError('Frozen individual photo/version review changed')
    if c['artwork_id']!='bf39b4d9-516b-5196-8e7f-b66cbe20b275':raise ValueError('Outside the individual approved object')
    rows = json.loads(raw_review)['images']
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
    if entity['id']!='Q124246496' or values(entity,'P18')!=[review['authority_image_filename']] or values(entity,'P6002'):
        raise ValueError('Exact authority-linked image or absent WikiArt artwork crosswalk changed')
    dates=values(entity,'P571')
    if len(dates)!=1 or dates[0].get('time')!='+1911-00-00T00:00:00Z' or dates[0].get('precision')!=9:raise ValueError('Preserved authority date changed')
    if {k:c[k] for k in review['catalogue_date_fields']}!=review['catalogue_date_fields']:raise ValueError('Frozen catalogue date changed')
    for pin in review['file_metadata_pins']:
        b=(core.ROOT/pin['path']).read_bytes()
        if core.sha(b)!=pin['sha256'] or len(b)!=pin['bytes']:raise ValueError('Pinned Commons file identity metadata changed')
    file_page=next(iter(json.loads((RUN/'metadata/authority-image/commons-file-review.json').read_bytes())['data']['query']['pages'].values()))
    info=file_page['imageinfo'][0]
    if file_page['pageid']!=23472123 or file_page['title']!='File:'+review['authority_image_filename'] or info['url']!=review['authority_image_url'] or info['sha1']!=review['authority_image_sha1']:raise ValueError('Different Commons file photograph')
    reference=[x for x in review['comparison_evidence'] if x['role']=='comparison-only']
    if len(reference)!=1 or reference[0]['url']!=info['url'] or hashlib.sha1(Path(reference[0]['path']).read_bytes()).hexdigest()!=info['sha1']:raise ValueError('Authority reference original differs')
    creators = {x['external_id'] for p in c['creator_authorities'] for x in p['artist_identifiers'] if x['scheme'] == 'wikidata'}
    claims = [x for x in entity.get('claims', {}).get('P170', []) if x.get('rank') != 'deprecated']
    if len(creators) != 1 or {x['id'] for x in values(entity, 'P170')} != creators or any(set(x.get('qualifiers', {})) - {'P7452'} for x in claims):
        raise ValueError('Primary creator crosswalk is different or qualified')
    names = {wiki.norm(x['value']) for x in entity.get('labels', {}).values()}
    names.update(wiki.norm(x['value']) for rows in entity.get('aliases', {}).values() for x in rows)
    if wiki.norm(c['title']) not in names:
        raise ValueError('Catalogue title does not identify the captured artwork entity')
    institution=review['institution_identity_review'];stored=institution['institution_record']
    if (c['institution_id'],c['institution_slug'],c['institution_qid'],c['museum'])!=(stored['id'],stored['slug'],stored['wikidata_id'],stored['name']):raise ValueError('Reviewed local institution identity changed')
    if institution!=json.loads((RUN/'institution-identity-review.json').read_bytes()):raise ValueError('Individual institution identity proof changed')
    ib=(core.ROOT/institution['authority_path']).read_bytes();irc=institution['authority_capture']
    if core.sha(ib)!=irc['sha256'] or len(ib)!=irc['bytes']:raise ValueError('Captured institution authority changed')
    ie=json.loads(ib)['entities']['Q211043']
    sites=values(ie,'P856');host=lambda u:(urlparse(u).hostname or '').removeprefix('www.')
    if sites!=institution['official_websites'] or host(stored['website_url'])!='rusmuseum.ru' or 'rusmuseum.ru' not in {host(u) for u in sites}:raise ValueError('Museum official website identity differs')
    if {x['id'] for x in values(entity,'P195')}!={'Q211043'}:raise ValueError('Existing holding reference does not match artwork authority')
    if any('P582' in x.get('qualifiers',{}) for x in entity.get('claims',{}).get('P195',[]) if x.get('rank')!='deprecated'):raise ValueError('Current versus historical holding needs review')
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
    # The individually reviewed photo comparison supplies the WikiArt object ID and
    # title. The candidate keeps its real, existing database scheme and ID.
    soup=wiki.BeautifulSoup(data,'html.parser')
    original=[li.get_text(' ',strip=True).split(':',1)[1].strip() for li in soup.select('.wiki-layout-artwork-info article li') if li.get_text(' ',strip=True).startswith('Original Title:')]
    if original!=[c['title']]:raise ValueError('Exact Russian source title differs')
    source = dict(c, external_id=review['wikiart_id'], title=review['wikiart_title'])
    facts = original_facts(source, data, rc)
    inspected = [x for x in review['comparison_evidence'] if x['role'] == 'wikiart-source']
    if len(inspected) != 1 or inspected[0]['url'] != facts['source_image_url']:
        raise ValueError('Selected WikiArt photograph differs from inspected version')
    if wiki.visible_creation_date(wiki.BeautifulSoup(data, 'html.parser')) != review['source_date']:
        raise ValueError('Reviewed displayed source date differs')
    facts['date_note'] = review['note']
    facts['authority_image_review'] = dict(entity=entity, receipt=receipt, review=review)
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
    institution=json.loads((RUN/'institution-identity-review.json').read_bytes())['institution_record']
    if db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE id=%s',(im['institution_id'],)).fetchone()['record']!=institution:raise ValueError('Frozen institution changed before image write')
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
        wiki.research(1)
    elif a.phase == 'prepare':
        prepare()
    elif a.phase == 'apply':
        base.apply()
    else:
        verify()
