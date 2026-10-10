#!/usr/bin/env python3
"""Selected local gaps using prior WikiArt research, fresh pages and original bytes."""
import argparse
import collections
import gzip
import importlib.util
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

spec = importlib.util.spec_from_file_location('wiki', Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiki)
base, core = wiki.base, wiki.core
RUN = core.ROOT / 'docs/research/local-wikiart-reused-images-20261006'
AUDIT = RUN.parent / 'local-wikiart-prior-delivery-audit-20261006'
wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-prior-research-reuse-v1'
original_facts, original_attach = wiki.page_facts, wiki.attach
BASIS = 'Existing local object and creator identities match pinned prior research; current WikiArt object/title/date/image evidence and individual visual/version review. Actual rights labels and source credits retained separately from user source approval. Local image-only attachment; no independent copyright-holder permission asserted.'


def image_key(url):
    u = urlparse(url)
    if u.scheme != 'https' or not re.fullmatch(r'uploads\d*\.wikiart\.org', u.hostname or ''):
        raise ValueError('Unexpected WikiArt source image host')
    return u.path.split('!', 1)[0]


def capture_receipts(value, result):
    if isinstance(value, dict):
        if 'body_path' in value and 'sha256' in value:
            p = core.ROOT / value['body_path']
            raw = gzip.decompress(p.read_bytes())
            if core.sha(raw) != value['sha256'] or len(raw) != value['bytes']:
                raise ValueError('Prior source capture changed')
            dest = RUN / 'metadata/prior-captures' / (value['sha256'] + '.body')
            core.save_new(dest, raw)
            result[value['sha256']] = dict(receipt=value, copy=str(dest.relative_to(core.ROOT)))
        for x in value.values():
            capture_receipts(x, result)
    elif isinstance(value, list):
        for x in value:
            capture_receipts(x, result)


def snapshot():
    if (RUN / 'candidates.json').exists():
        return
    audit = json.loads((AUDIT / 'discovery.json').read_bytes())
    leads = {x['artwork_id']: x for x in audit['leads'] if x['category'] == 'matching_local_identity'
             and x['current_local_state']['creation_scope'] == 'eligible' and x['current_local_state']['selection_evidence']}
    packets = {}
    for pin in audit['source_pins']:
        data = (AUDIT / pin['path']).read_bytes()
        if core.sha(data) != pin['sha256']:
            raise ValueError('Pinned prior plan changed')
        plan = json.loads(gzip.decompress(data))
        correction = json.loads((AUDIT / 'prior-plan-captures' / pin['operation'] / 'impression-correction.json').read_bytes())
        for c in plan['claims']:
            aid = c['work']['id']
            if aid not in leads:
                continue
            if core.sha(core.encode(c)) != leads[aid]['prior_claim_sha256']:
                raise ValueError('Discovery claim changed')
            captures = {}
            capture_receipts(c, captures)
            capture_receipts(plan['prepared'][aid], captures)
            packet = dict(claim=c, prepared=plan['prepared'][aid], prior_preimage=plan['preimages'][aid],
                          prior_plan_pin=pin, captures=list(captures.values()),
                          retractions=[x for x in correction['retracted'] if x['artwork_id'] == aid])
            core.save_new(RUN / 'prior-research' / (aid + '.json'), packet)
            packets[aid] = packet
    with base.connect() as db:
        rows = db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,
          a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
          to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,i.wikidata_id institution_qid,
          ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
          (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
          (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
          COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
          FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id
          WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review'
            AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
            AND artline_has_selection_evidence(a.id) ORDER BY a.id''', (list(packets),)).fetchall()
        artists = sorted({c['creator_links'][0]['artist_id'] for c in rows})
        ar = {x['record']['id']: x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])', (artists,))}
        aliases, identifiers = collections.defaultdict(list), collections.defaultdict(list)
        for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY id', (artists,)):
            aliases[x['record']['artist_id']].append(x['record'])
        for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id", (artists,)):
            identifiers[x['record']['entity_id']].append(x['record'])
        baseline = db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    for c in rows:
        packet = packets[c['artwork_id']]
        old = packet['claim']['work']
        if any(c[k] != old[k] for k in ('title', 'creation_year_start', 'creation_year_end', 'date_precision', 'accession_number', 'institution_id')):
            raise ValueError('Local identity changed since the metadata audit')
        if [(x['artist_id'], x['attribution_role']) for x in c['creator_links']] != [(x['artist_id'], x['role']) for x in old['creators']]:
            raise ValueError('Local primary creator differs')
        existing = {(x['scheme'], x['external_id']): x for x in c['identifiers']}
        prior_keys = {(x['scheme'], x['external_id']) for x in old['identifiers']}
        if not prior_keys or not prior_keys.issubset(existing):
            raise ValueError('Existing local source IDs differ')
        chosen = existing[sorted(prior_keys)[0]]
        aid = c['creator_links'][0]['artist_id']
        c.update(scheme=chosen['scheme'], external_id=chosen['external_id'], source_id=chosen['source_id'],
                 page=packet['claim']['page']['url'], provider=wiki.PROVIDER, artist=ar[aid]['display_name'], target_ids={'local':c['artwork_id']},
                 creator_authorities=[dict(artist_record=ar[aid], artist_aliases=aliases[aid], artist_identifiers=identifiers[aid])],
                 prior_research_sha256=core.sha(core.encode(packet)))
    core.save_new(RUN / 'candidates.json', dict(at=core.now(), baseline=baseline, candidates=rows,
        selection='Existing local eligible missing-image records from a bounded audit of earlier WikiArt research. Known print-impression retractions remain explicit holds. Fresh source and local visual review required.'))
    print('Current local candidates:', len(rows), flush=True)


def packet(c):
    data = (RUN / 'prior-research' / (c['artwork_id'] + '.json')).read_bytes()
    if core.sha(data) != c['prior_research_sha256']:
        raise ValueError('Pinned prior research packet changed')
    value = json.loads(data)
    if value['retractions']:
        raise ValueError('Earlier verified print-impression retraction: ' + value['retractions'][0]['reason'])
    for item in value['captures']:
        raw = (core.ROOT / item['copy']).read_bytes()
        if core.sha(raw) != item['receipt']['sha256'] or len(raw) != item['receipt']['bytes']:
            raise ValueError('Archived source evidence changed')
    return value


def page_facts(c, data, rc):
    prior = packet(c)
    claim, prepared = prior['claim'], prior['prepared']
    if c['artwork_id'] != claim['work']['id'] or c['page'] != claim['page']['url']:
        raise ValueError('Wrong prior object or source page')
    expected = claim['page']['metadata']
    source = dict(c, external_id=expected['_id'], title=expected['title'])
    facts = original_facts(source, data, rc)
    current = facts['source_metadata']
    for key in ('_id','title','year','artistUrl','artistName'):
        if wiki.norm(current.get(key)) != wiki.norm(expected.get(key)):
            raise ValueError('Current source identity changed: ' + key)
    if image_key(facts['source_image_url']) != image_key(claim['page']['image_url']):
        raise ValueError('Current WikiArt image/version changed')
    soup = wiki.BeautifulSoup(data, 'html.parser')
    fields = {}
    for li in soup.select('.wiki-layout-artwork-info article > ul > li'):
        label = li.find('s')
        if label:
            fields[label.get_text(' ',strip=True).rstrip(':')] = li.get_text(' ',strip=True).removeprefix(label.get_text(' ',strip=True)).strip()
    for key in ('Location','Dimensions','Media'):
        if wiki.norm(fields.get(key)) != wiki.norm(claim['page']['fields'].get(key)):
            raise ValueError('Current source object details changed: ' + key)
    # Earlier high-confidence matching is retained as evidence. It does not
    # replace this operation's independent source and per-image visual review.
    if not claim['review_outcome'].startswith('high_') or claim.get('missing_target_count') != 1:
        raise ValueError('Prior exact object decision is absent or ambiguous')
    note = 'The existing catalogue object and creator identifiers match the pinned prior WikiArt research. '
    note += f"WikiArt title: {wiki.html.unescape(current['title'])}; displayed date: {wiki.visible_creation_date(soup)}. "
    note += f"Catalogue title and date retained: {c['title']}; {c['date_display']}. No catalogue metadata or holding assertions were changed."
    facts.update(date_note=note, source_fields=fields, prior_research=prior,
                 external_source_links=[dict(text=a.get_text(' ',strip=True),url=a['href']) for a in soup.select('.wiki-layout-artwork-info a[href]')
                                        if a['href'].startswith(('https://','http://')) and 'wikiart.org' not in a['href']])
    return facts


wiki.page_facts = page_facts


def prepare():
    fetch = core.Fetcher(RUN / 'metadata/downloads')
    fetch.defer_long_cooldowns = True
    for p in sorted((RUN / 'selected' / wiki.PROVIDER).glob('*.json')):
        im = json.loads(p.read_bytes())
        dest = RUN / 'images' / p.name
        if dest.exists():
            wiki.verify_image(json.loads(dest.read_bytes()))
            continue
        wiki.verify_image(im)
        prior = packet(im)
        prepared = prior['prepared']
        oldpath = core.ROOT / 'apps/web/public' / prepared['path'].lstrip('/')
        oldbytes = oldpath.read_bytes() if oldpath.exists() else Path(prepared['visual_path']).read_bytes()
        if core.sha(oldbytes) != prepared['sha256'] or len(oldbytes) != prepared['bytes']:
            raise ValueError('Previously reviewed JPEG changed')
        if prepared['reuse']:
            core.HOSTS.add(urlparse(im['source_image_url']).hostname)
            data, headers = fetch.get(im['source_image_url'])
            reuse = dict(kind='fresh_selected_source_download', original_prior_media=prepared['media'], previous_derivative_sha256=prepared['sha256'], at=core.now())
        else:
            rc = prepared['download']
            original = base.ARCHIVE / 'source-images' / prior['prior_plan_pin']['operation'] / (core.sha(rc['url'].encode()) + '.body')
            data = original.read_bytes()
            if core.sha(data) != rc['sha256'] or len(data) != rc['bytes'] or image_key(rc['url']) != image_key(im['source_image_url']):
                raise ValueError('Archived original does not match current source image')
            headers = dict(source_download=rc)
            reuse = dict(kind='previously_archived_source_original', original_archive=str(original), download=rc, previous_derivative_sha256=prepared['sha256'], at=rc['at'])
        source_sha = core.sha(data)
        archive = base.ARCHIVE / 'source-images' / RUN.name / (im['artwork_id'] + '-' + source_sha[:16] + '.image')
        core.save_new(archive, data)
        result, width, height, quality = core.compress(data)
        if min(width,height) < 50 or max(width,height) < 200:
            raise ValueError('Source is too small')
        digest = core.sha(result)
        path = '/assets/artworks/imported/' + RUN.name + '/' + im['artwork_id'] + '-' + digest[:16] + '.jpg'
        core.save_new(core.ROOT / 'apps/web/public' / path.lstrip('/'), result)
        im['raw']['original_reuse'] = reuse
        im.update(path=path,sha256=digest,bytes=len(result),width=width,height=height,jpeg_quality=quality,
                  source_sha256=source_sha,source_bytes=len(data),source_archive=str(archive),downloaded_at=reuse['at'],response_headers=headers,
                  transform='Full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
        core.save_new(dest, im)
        core.event(RUN, dict(provider=wiki.PROVIDER,artwork_id=im['artwork_id'],outcome='prepared'))
        print('Prepared:', im['artist'], im['title'], reuse['kind'], flush=True)
    base.prepare('contact-sheets-only')


def attach(db, im, target):
    verify_version(im, require_approved=True)
    verify_original(im)
    result = original_attach(db, im, target)
    if result == 'attached':
        db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s', (BASIS, im['media_id']))
    return result


base.m.attach = attach


def verify_original(im):
    reuse = im['raw']['original_reuse']
    data = Path(im['source_archive']).read_bytes()
    if core.sha(data) != im['source_sha256'] or len(data) != im['source_bytes']:
        raise ValueError('Canonical original changed')
    prior = packet(im)['prepared']
    if reuse['previous_derivative_sha256'] != prior['sha256']:
        raise ValueError('Prior derivative identity changed')
    if reuse['kind'] == 'previously_archived_source_original':
        rc = reuse['download']
        original = Path(reuse['original_archive']).read_bytes()
        if prior['reuse'] or rc != prior['download'] or original != data or core.sha(original) != rc['sha256'] or len(original) != rc['bytes']:
            raise ValueError('Prior original archive or download evidence changed')
        if image_key(rc['url']) != image_key(im['source_image_url']):
            raise ValueError('Reused original is another source image')
    elif reuse['kind'] == 'fresh_selected_source_download':
        if not prior['reuse'] or reuse['original_prior_media'] != prior['media']:
            raise ValueError('Fresh original download has incorrect prior provenance')
    else:
        raise ValueError('Unknown original provenance')


def verify_version(im, require_approved=False):
    rows = json.loads((RUN / 'object-version-review.json').read_bytes())['images']
    matched = [x for x in rows if x['artwork_id'] == im['artwork_id']]
    if len(matched) != 1:
        raise ValueError('Individual object/version decision missing')
    review = matched[0]
    if require_approved and review['decision'] != 'approved':
        raise ValueError('Object/version remains held')
    for key in ('sha256', 'source_sha256', 'source_image_url', 'external_id', 'scheme'):
        if im[key] != review[key]:
            raise ValueError('Reviewed object or image changed: ' + key)
    if im['raw'].get('object_version_review') != review or review['note'] not in im['attribution_text']:
        raise ValueError('Individual object/version evidence omitted')
    for proof in review.get('additional_evidence', []):
        data = Path(proof['path']).read_bytes()
        if core.sha(data) != proof['sha256'] or len(data) != proof['bytes']:
            raise ValueError('Object/version comparison evidence changed')
    medium = im['raw']['wikiart_facts']['source_fields'].get('Media', '')
    is_print = im['work_type'] == 'print' or re.search(r'lithograph|etching|woodcut|engraving', medium, re.I)
    if is_print and review['decision'] == 'approved':
        proof = review.get('print_identity', {})
        if proof.get('kind') == 'explicit_native_object_source_link':
            links = im['raw']['wikiart_facts']['external_source_links']
            if proof.get('external_id') != im['external_id'] or not any(x['text'] == 'Source' and x['url'] == proof.get('url') for x in links):
                raise ValueError('Exact print-impression source identity absent')
            if im['scheme'] != 'european-chicago-art-institute-of-chicago-object' or urlparse(proof['url']).path != '/aic/collections/artwork/' + im['external_id']:
                raise ValueError('Print source link points to another impression')
        else:
            raise ValueError('A matching print title is insufficient impression evidence')


def verify():
    for im in base.prepared():
        verify_version(im)
        verify_original(im)
    wiki.verify()
    attached = {x['artwork_id'] for x in json.loads((RUN / 'apply-receipt.json').read_bytes())['receipts'] if x['result'] == 'attached'}
    with base.connect() as db:
        for im in base.prepared():
            if im['artwork_id'] not in attached:
                continue
            verify_version(im, require_approved=True)
            row = db.execute('SELECT rights_basis,source_record_id FROM media_rights_evidence WHERE media_id=%s', (im['media_id'],)).fetchone()
            if row != dict(rights_basis=BASIS, source_record_id=im['external_id']):
                raise ValueError('Existing local authority identifier or provenance basis changed')
    core.save_new(RUN / 'reuse-database-verification.json', dict(at=core.now(), passed=True,
        existing_authority_ids_preserved=True, individual_version_decisions_verified=True,
        original_reuse_checksums_verified=True, attached=len(attached)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['snapshot','research','prepare','apply','verify'])
    args = p.parse_args()
    if args.phase == 'snapshot': snapshot()
    elif args.phase == 'research': wiki.research(60)
    elif args.phase == 'prepare': prepare()
    elif args.phase == 'apply': base.apply()
    else: verify()
