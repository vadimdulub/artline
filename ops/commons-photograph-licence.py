"""Verify separately stated artwork PDM and original-photograph CC rights.

Source summaries are retained unchanged. Accept only an explicit approved photo
licence corroborated by the same rendered file revision, with no third licence.
"""
import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PDM = 'https://creativecommons.org/publicdomain/mark/1.0/'
KIND = 'explicit_photo_and_artwork_licences'


def art_photo_terms(text):
    """Accept explicit Art Photo fields; keep extra permission terms on hold."""
    starts = list(re.finditer(r'\{\{\s*Art[ _]Photo\b', text, re.I))
    if not starts:
        return None
    if len(starts) != 1:
        raise ValueError('Unique Art Photo template required')
    body = text[starts[0].start():]
    depth = 0
    for token in re.finditer(r'\{\{|\}\}', body):
        depth += 1 if token.group() == '{{' else -1
        if depth == 0:
            body = body[:token.end()]
            break
    else:
        raise ValueError('Incomplete Art Photo template')
    fields = {}
    for name in ('artwork license', 'photo license', 'source'):
        values = re.findall(r'^\s*\|\s*' + name.replace(' ', '[ _]') +
                            r'\s*=\s*(.*?)(?=^\s*\||^\s*\}\})', body, re.I | re.M | re.S)
        if len(values) != 1:
            raise ValueError('Unique explicit Art Photo rights and source fields required')
        fields[name] = values[0].strip()
    if not re.fullmatch(r'\{\{\s*(?:own(?: photograph)?|self[ _-]photographed)\s*\}\}', fields['source'], re.I):
        raise ValueError('Art Photo source must explicitly identify an original photograph')
    if not re.fullmatch(r'\{\{\s*PD-old(?:-[a-z0-9]+)*(?:\s*\|\s*deathyear\s*=\s*\d{4})?\s*\}\}', fields['artwork license'], re.I):
        raise ValueError('Explicit Art Photo underlying-artwork public-domain statement required')
    match = re.fullmatch(r'\{\{\s*(?:self\s*\|\s*)?cc-(by(?:-sa)?)-(1\.0|2\.0|2\.5|3\.0|4\.0)\s*\}\}', fields['photo license'], re.I)
    if not match:
        raise ValueError('Art Photo licence has additional, unclear or unapproved terms')
    return match.group(1).lower(), match.group(2)


def source_terms(record, page):
    meta = page.get('imageinfo', [{}])[0].get('extmetadata', {})
    field = lambda k: meta.get(k, {}).get('value', '')
    if field('LicenseShortName') != 'Public domain' or field('Copyrighted') != 'False' or field('LicenseUrl') or field('Restrictions'):
        raise ValueError('Not the separately stated artwork/photo rights case')
    text = page.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*', '')
    if not re.search(r'\{\{\s*(?:own(?: photograph)?|self[ _-]photographed)\s*\}\}', text, re.I):
        raise ValueError('Explicit original photograph required')
    pd_art = re.search(r'\{\{\s*(?:Licensed-PD-Art|PD-Art)\s*\|\s*PD-old', text, re.I)
    separate = (re.search(r'Painting\s*:\s*\{\{\s*PD-old', text, re.I)
                and re.search(r'Photo(?: including frame)?\s*:\s*\{\{\s*self\s*\|', text, re.I))
    art_photo = art_photo_terms(text) if not (pd_art or separate) else None
    if not (pd_art or separate or art_photo):
        raise ValueError('Explicit underlying-artwork public-domain statement required')
    creators = record.get('creators') or []
    primary = record.get('roles') == ['primary'] or (len(creators) == 1 and creators[0].get('role') == 'primary')
    if not primary or len(creators) != 1 or not creators[0].get('death') or int(creators[0]['death']) + 70 >= datetime.datetime.now(datetime.timezone.utc).year:
        raise ValueError('Photograph licence does not clear a protected or uncertain artwork')
    pattern = r'cc-(by(?:-sa)?)-(1\.0|2\.0|2\.5|3\.0|4\.0)'
    # A photographer's explicit attribution parameter is not another licence.
    # Keep nested templates unparsed and require agreement with rendered blocks.
    licences = set(re.findall(r'\{\{\s*self\s*\|\s*' + pattern + r'\s*(?:\|\s*attribution\s*=\s*[^{}]+)?\s*\}\}', text, re.I))
    licences.update(re.findall(r'\{\{\s*Licensed-PD-Art\s*\|\s*PD-old[^|{}]*\|\s*' + pattern + r'\s*\}\}', text, re.I))
    if art_photo:
        licences.add(art_photo)
    licences = {(code.lower(), version) for code, version in licences}
    all_codes = {(code.lower(), version) for code, version in re.findall(r'cc-([a-z-]+)-(\d+\.\d+)', text, re.I)}
    if len(licences) != 1 or all_codes != licences:
        raise ValueError('Unique explicit approved photograph licence required')
    code, version = next(iter(licences))
    return 'CC ' + code.upper() + ' ' + version, f'https://creativecommons.org/licenses/{code}/{version}/'


def validate(record, page, evidence, root=ROOT):
    label, uri = source_terms(record, page)
    revision = page['revisions'][0]['revid']
    if evidence.get('kind') != KIND or evidence.get('pageid') != page['pageid'] or evidence.get('revid') != revision or evidence.get('label') != label or evidence.get('uri') != uri:
        raise ValueError('Photographic licence proof identity differs')
    path = (root / evidence['rendered_capture_path']).resolve()
    if not path.is_relative_to((root / 'docs/research').resolve()):
        raise ValueError('Licence evidence path outside research captures')
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != evidence['capture']['sha256']:
        raise ValueError('Rendered licence capture checksum differs')
    parsed = json.loads(content)['parse']
    if parsed.get('pageid') != page['pageid'] or parsed.get('revid') != revision:
        raise ValueError('Rendered photographic licence revision differs')
    soup = BeautifulSoup(parsed.get('text', {}).get('*', ''), 'html.parser')
    uris = {n.get_text(strip=True).replace('http://', 'https://').rstrip('/') + '/'
            for n in soup.select('.licensetpl_link') if n.get_text(strip=True)}
    if uris != {PDM, uri}:
        raise ValueError('Artwork and photograph licence blocks absent or conflicting')
    return label, uri


def structured_ids(structured):
    statements = structured.get('claims', structured.get('statements', {})) or {}
    return {x['mainsnak']['datavalue']['value']['id'] for x in statements.get('P275', [])
            if x.get('rank') != 'deprecated' and x.get('mainsnak', {}).get('snaktype') == 'value'}


def validate_structured(evidence, structured):
    entities = evidence.get('structured_licence_entities', {})
    if set(entities) != structured_ids(structured):
        raise ValueError('Structured photograph licence evidence differs')
    for qid, entity in entities.items():
        urls = {re.sub(r'/(?:deed|legalcode)(?:\.[a-z-]+)?/?$', '/', x['mainsnak']['datavalue']['value'].replace('http://', 'https://')).rstrip('/') + '/'
                for x in entity.get('claims', {}).get('P856', [])
                if x.get('rank') != 'deprecated' and x.get('mainsnak', {}).get('snaktype') == 'value'}
        if entity.get('id') != qid or not urls or urls != {evidence['uri']}:
            raise ValueError('Structured photograph licence conflicts with explicit source terms')


def resolve(fetcher, record, page, common, structured):
    label, uri = source_terms(record, page)
    if not common.photographic_credits(record, page):
        raise ValueError('Original photographer credit required')
    params = {'action': 'parse', 'oldid': page['revisions'][0]['revid'], 'prop': 'text|revid'}
    common.api(fetcher, 'commons.wikimedia.org', params)
    url = 'https://commons.wikimedia.org/w/api.php?' + urlencode(dict(params, format='json', maxlag=5))
    key = hashlib.sha256(url.encode()).hexdigest()
    path = fetcher.cache / (key + '.json')
    evidence = {'kind': KIND, 'pageid': page['pageid'], 'revid': page['revisions'][0]['revid'],
                'label': label, 'uri': uri, 'rendered_capture_path': str(path.resolve().relative_to(ROOT)),
                'capture': json.loads((fetcher.cache / (key + '.receipt.json')).read_text()),
                'interpretation': 'Artwork carries PDM; the original photograph has a separate explicit CC licence. Both blocks verified at the exact file revision; raw source fields remain unchanged.'}
    ids = sorted(structured_ids(structured))
    evidence['structured_licence_entities'] = common.api(fetcher, 'www.wikidata.org', {
        'action': 'wbgetentities', 'ids': '|'.join(ids), 'props': 'claims|labels', 'languages': 'en'})['entities'] if ids else {}
    validate(record, page, evidence)
    validate_structured(evidence, structured)
    return evidence
