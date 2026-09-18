#!/usr/bin/env python3
"""Verify selected museum-donated Commons images against Reims inventory records.

The museum's own website must identify the uploading account. Exact Commons
file-revision licences, photographer, inventory, creator and institution must
agree; the aggregate API's public-domain summary cannot clear a photograph.
Only the France-ported CC BY-SA 2.0 release is supported here. No publication or
catalogue fact changes. Use the existing prepared-image delivery commands.
"""
import importlib.util
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


reims = load('donation_reims', 'popular-reims-images.py')
common = load('donation_common', 'overnight-commons-images.py')
core = reims.core
PROVIDER = 'popular-reims-donation'
LICENSE = 'https://creativecommons.org/licenses/by-sa/2.0/fr/'
BY_LICENSE = 'https://creativecommons.org/licenses/by/2.0/fr/'
DONOR = 'Musée des Beaux-Arts de Reims'
DONATION_PAGE = 'https://musees-reims.fr/fr/musee-numerique/article/culture-libre-le-projet-wikipedia'
core.PROVIDERS[PROVIDER] = 'Musées de Reims / Wikimedia Commons'
core.HOSTS.add('thumb.wikimedia.org')
core.VERSION = 'reims-institutional-donation-exact-fr-sa-v1'


def canonical(uri):
    uri = ('https:' + uri if uri.startswith('//') else uri).replace('http://', 'https://')
    match = re.fullmatch(r'(https://creativecommons.org/(?:licenses/(?:by|by-sa)/2\.0/fr|publicdomain/mark/1\.0))(?:/(?:deed|legalcode)(?:\.[a-zA-Z-]+)?)?/?', uri)
    return match[1] + '/' if match else uri


def verify_donor(proof):
    if proof['url'] != DONATION_PAGE or not proof['retrieved_at'] or not proof['response_sha256']:
        raise ValueError('Missing official museum donor evidence')
    targets = []
    for link in proof['links']:
        u = urlparse(link['href'])
        if u.scheme == 'https' and u.hostname == 'commons.wikimedia.org' and u.path == '/w/index.php':
            targets.extend(parse_qs(u.query).get('title', []))
    if 'Special:ListFiles/' + DONOR.replace(' ', '_') not in targets:
        raise ValueError('Uploader not linked by the museum')


def text_field(text, name):
    values = re.findall(r'^\s*\|\s*' + re.escape(name) + r'\s*=\s*([^\n]*)', text, re.I | re.M)
    if len(values) != 1: raise ValueError('Missing or ambiguous Commons field: ' + name)
    return values[0].strip()


def photographer(page):
    text = page['revisions'][0]['slots']['main']['*']
    names = [v.strip() for field in ('photographer', 'author') for v in re.findall(r'^\s*\|\s*'+field+r'\s*=\s*([^\n]+)', text, re.I | re.M)]
    if len(names) != 1 or not re.fullmatch(r'[\wÀ-ÿ .’\'-]+', names[0]):
        raise ValueError('Missing or ambiguous donated photograph credit')
    return names[0]


def verify_file(c, obj, page, sdc, rendered):
    """Independent exact-file media licence; no inheritance from collection data."""
    info = page['imageinfo'][0]; text = page['revisions'][0]['slots']['main']['*']
    if info.get('user') != DONOR or not info.get('timestamp'):
        raise ValueError('Exact image version is not an institutional donation')
    if info.get('mime') != 'image/jpeg' or min(info['width'], info['height']) < 300:
        raise ValueError('Unsupported or inadequate donated image')
    if info.get('extmetadata', {}).get('Restrictions', {}).get('value', '').strip():
        raise ValueError('Conflicting media restriction')
    if re.search(r'cc-by-(?:nc|nd)|all rights reserved|non.commercial|permission required|copyright violation|copyvio|delete\s*\|', text, re.I):
        raise ValueError('Restricted or disputed photograph')
    template = '{{Institution:Musée des Beaux-Arts, Reims}}'
    if text_field(text, 'institution') != template or text_field(text, 'source') not in (template, 'Musée des Beaux-Arts, Reims'):
        raise ValueError('Source or holding institution differs')
    if text_field(text, 'accession number') != obj['accession_number']:
        raise ValueError('Commons inventory differs')
    if reims.norm(text_field(text, 'title')) not in set(map(reims.norm, [obj['title'], *obj['titles']])):
        raise ValueError('Commons title differs')
    artist = re.fullmatch(r'\{\{creator:([^{}|]+)\}\}', text_field(text, 'artist'), re.I)
    if not artist or reims.norm(artist[1]) not in set(map(reims.norm, c['artist_names'])):
        raise ValueError('Commons creator differs or attribution is qualified')
    photographer(page)  # The exact donated file can have a different photographer.
    if text_field(text, 'object type') != 'painting': raise ValueError('Commons classification differs')
    # Separate public-domain artwork evidence from the photographer's licence.
    deaths = re.findall(r'\bdeathyear\s*=\s*(\d{4})', text)
    death = c['creators'][0].get('death')
    if not death or death > 1955 or deaths != [str(death)]:
        raise ValueError('Underlying artwork copyright needs review')
    if not re.search(r'PD-old-auto(?:-expired|\s*\|\s*PD-US-expired)', text, re.I):
        raise ValueError('Underlying artwork public-domain evidence incomplete')
    if not re.search(r'(?:\{\{|\|)\s*Cc-by-sa-2\.0-fr\s*(?:\}\}|\|)', text, re.I):
        raise ValueError('Exact photograph has no approved ported licence')
    if rendered['pageid'] != page['pageid'] or rendered['revision'] != page['revisions'][0]['revid']:
        raise ValueError('Rendered licence belongs to a different file revision')
    html = rendered['licence_html']
    if core.sha(html.encode()) != rendered['selected_fields_sha256']:
        raise ValueError('Rendered licence capture checksum differs')
    soup = BeautifulSoup(html, 'html.parser')
    uris = {canonical(x.get_text(' ', strip=True)) for x in soup.select('.licensetpl_link')}
    if LICENSE not in uris or not uris <= {LICENSE, BY_LICENSE, common.PDM}:
        raise ValueError('Missing or conflicting exact-file licence')
    # Wikibase's P275 must agree with the rendered and wikitext licences.
    licences = common.ids(sdc, 'P275')
    if 'Q77355872' not in licences or not licences <= {'Q77355872', 'Q75470422'}:
        raise ValueError('Structured media licence conflicts')
    if 'Q75470422' in licences and BY_LICENSE not in uris:
        raise ValueError('Structured extra licence lacks file evidence')
    if sdc.get('id') != 'M' + str(page['pageid']): raise ValueError('Structured file identity differs')
    if c.get('qid'):
        common.verify_structured_object(c, sdc)
    if obj['page'] not in text and (not c.get('qid') or common.ids(sdc, 'P6243') != {c['qid']}):
        raise ValueError('No exact museum object or structured physical-object link')
    url = info.get('thumburl') or info['url']
    for address in (url, info['url']):
        u = urlparse(address)
        if u.scheme != 'https' or u.hostname not in ('upload.wikimedia.org', 'thumb.wikimedia.org') or not u.path.startswith('/wikipedia/commons/'):
            raise ValueError('Not a direct Commons image resource')
    if re.search(r'\b(detail|cropped|montage|collage|colorized)\b', page['title'], re.I):
        raise ValueError('Detail or modified rendition needs separate review')
    return url


def verify(im):
    raw = im['raw']; capture = raw['capture']
    if core.sha(capture['html'].encode()) != capture['selected_fields_sha256']:
        raise ValueError('Museum source capture checksum differs')
    obj = reims.parse_object(capture['html'], capture['url'], media_rights=False)
    if obj != raw['object']: raise ValueError('Museum source fields changed')
    reims.verify_object_identity(im, obj, allow_narrower_dates=True)
    verify_donor(raw['donor_proof'])
    image_url = verify_file(im, obj, raw['commons'], raw['structured_data'], raw['rendered_licence'])
    if raw.get('wikidata'):
        authority_candidate = dict(im, institution_qid='Q3330225', accession_number=obj['accession_number'])
        common.entity_match(authority_candidate, raw['wikidata'], require_primary_image=False)
        if im['external_id'] not in common.values(raw['wikidata'], 'P347'):
            raise ValueError('National catalogue identity conflicts')
    if im['policy_url'] != LICENSE or im['rights_status'] != 'cc_by_sa' or im['license_label'] != 'CC BY-SA 2.0 France':
        raise ValueError('Exact ported photograph licence changed')
    if im['page'] != raw['commons']['imageinfo'][0]['descriptionurl'] or im['source_record_url'] != obj['page'] or im['source_image_url'] != image_url:
        raise ValueError('Source or exact image resource changed')
    if im.get('source_sha256') and im['source_sha256'] != raw['visual_review']['image_sha256']:
        raise ValueError('Downloaded photograph changed after visual review')
    review = raw['visual_review']
    if not review['confirmed'] or review['artwork_id'] != im['artwork_id'] or review['pageid'] != raw['commons']['pageid'] or review['reference_url'] != obj['page']:
        raise ValueError('Full-painting visual comparison not confirmed')
    for field in ('creator_credit', 'attribution_text'):
        if photographer(raw['commons']) not in im[field]: raise ValueError('Photographer attribution missing')
    if LICENSE not in im['attribution_text'] or 'Full-frame proportional resize' not in im['attribution_text']:
        raise ValueError('Licence or modification notice missing')
    if not capture['retrieved_at'] or not im['rights_verified_at']: raise ValueError('Verification date missing')


def attach(db, im, target):
    verify(im)
    return reims.attach_verified(db, im, target)


core.attach = attach
