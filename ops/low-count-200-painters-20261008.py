#!/usr/bin/env python3
"""Source-backed additions for a random sample of low-count production painters.

Read-only inventory/research; explicitly requested additions are applied separately.
The real local catalogue is never connected to by this operation.
"""
import argparse
import collections
import concurrent.futures
import csv
import difflib
import gzip
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import secrets
import subprocess
import time
import uuid
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('low_count_selection', ROOT/'ops/select-random-200-painters-round6-20261007.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
m = s.m
r = m.r
q = m.q
OP = 'low-count-200-painters-20261008'
RUN = ROOT/'docs/research'/OP
BACKUP = Path.home()/'Library/Application Support/Artline/backups'/OP
m.OP = OP
m.RUN = s.RUN = r.RUN = q.RUN = RUN
m.BACKUP = s.BACKUP = BACKUP
r.PORT = 55445


def audit():
    dest = RUN/'low-count-audit.json.gz'
    if dest.exists():
        rows = r.load(dest)['painters']
    else:
        with r.connect('production') as db, db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            query = """SELECT to_jsonb(ar) artist, count(distinct a.id) artwork_count
              FROM artists ar LEFT JOIN artwork_artists aa ON aa.artist_id=ar.id
              LEFT JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
              WHERE ar.entity_type='person' AND ar.status<>'archived' GROUP BY ar.id
              HAVING count(distinct a.id) BETWEEN 0 AND 10 ORDER BY ar.id"""
            r.save(RUN/'inventory-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query).fetchone())
            rows = db.execute(query).fetchall()
            ids = [x['artist']['id'] for x in rows]
            aliases = collections.defaultdict(list)
            identifiers = collections.defaultdict(list)
            for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])', (ids,)).fetchall():
                aliases[x['artist_id']].append(x['alias'])
            for x in db.execute("SELECT to_jsonb(e) e FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])", (ids,)).fetchall():
                identifiers[x['e']['entity_id']].append(x['e'])
        directory = r.load(ROOT/'docs/research/production-wikiart-images-20261006/wikiart-directory.json.gz')
        byname = collections.defaultdict(dict)
        byurl = {x['url']: x for x in directory}
        for x in directory:
            byname[q.norm(x['name'])][x['url']] = x
        for x in rows:
            a = x['artist']; aid = a['id']; sources = {}
            x['aliases'] = aliases[aid]; x['identifiers'] = identifiers[aid]
            for name in [a['display_name']]+aliases[aid]:
                sources.update(byname[q.norm(name)])
            for e in identifiers[aid]:
                url = (e.get('canonical_url') or '').rstrip('/')
                if url in byurl:
                    sources[url] = byurl[url]
            sources = {url: src for url, src in sources.items() if all(a.get(k) is None or src.get(k) is None or a[k] == src[k] for k in ['birth_year', 'death_year'])}
            x['source'] = next(iter(sources.values())) if len(sources) == 1 else None
        r.save_gz(dest, {'at': r.now(), 'target': 'production', 'read_only': True, 'painters': rows})
    matched = [x for x in rows if x['source']]
    enough = [x for x in matched if x['source']['count'] >= 20+x['artwork_count']]
    print(json.dumps({'eligible_painters': len(rows), 'counts': dict(collections.Counter(x['artwork_count'] for x in rows)), 'wikiart_matches': len(matched), 'potential_minimum_20': len(enough), 'examples': [(x['artist']['display_name'], x['artwork_count'], x['source']['count']) for x in enough[:20]]}, ensure_ascii=False), flush=True)


def candidates():
    return [x for x in r.load(RUN/'low-count-audit.json.gz')['painters'] if x['source'] and x['source']['count'] >= 20+x['artwork_count']]


def indexes():
    m.CACHE = m.cache_catalogue()
    def one(pair):
        aid = pair['artist']['id']; dest = RUN/'source-indexes'/(aid+'.json.gz')
        if dest.exists():
            return r.load(dest)
        url = pair['source']['url']; slug = urlsplit(url).path.rsplit('/', 1)[-1]
        result = {'artist_id': aid, 'artist': pair['artist']['display_name'], 'source': pair['source']}
        try:
            raw, receipt = m.capture(url+'/all-works/text-list', 'index-captures')
            if receipt['status'] != 200:
                raise ValueError('Text index HTTP '+str(receipt['status']))
            soup = m.BeautifulSoup(raw, 'html.parser'); prefix = urlsplit(url).path+'/'
            items = {}
            for link in soup.select('li a[href]'):
                if link['href'].startswith(prefix):
                    title = link.get_text(' ', strip=True)
                    date = link.parent.get_text(' ', strip=True).removeprefix(title).strip(' ,')
                    link_url = urljoin(url, link['href'])
                    items[link_url] = {'title': title, 'url': link_url, 'source_date': date, 'date': m.dates.creation_date(date)}
            api = 'https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
            body, api_receipt = m.capture(api, 'translation-captures')
            if api_receipt['status'] != 200:
                raise ValueError('Artist metadata HTTP '+str(api_receipt['status']))
            metadata = json.loads(body)
            assert isinstance(metadata, list)
            result.update(outcome='indexed', items=list(items.values()), metadata=metadata, receipt=receipt, metadata_receipt=api_receipt)
        except Exception as exc:
            result.update(outcome='source_unavailable', error=str(exc)[:400], items=[], metadata=[])
        r.save_gz(dest, result)
        return result
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, result in enumerate(pool.map(one, candidates()), 1):
            counts[result['outcome']] += 1
            if i % 10 == 0:
                print('Source indexes', i, '/', len(candidates()), dict(counts), flush=True)
    r.save(RUN/'index-summary.json', {'at': r.now(), 'counts': dict(counts)})


def source_candidates(pair):
    """Require concordance between explicit creator metadata and visible object list."""
    idx = r.load(RUN/'source-indexes'/(pair['artist']['id']+'.json.gz'))
    rows = []; held = []
    if idx['outcome'] != 'indexed':
        return [], [{'reason': idx.get('error', idx['outcome'])}]
    names = {q.norm(n) for n in [pair['artist']['display_name'], pair['source']['name']]+pair['aliases']}
    prefix = urlsplit(pair['source']['url']).path+'/'
    for meta in idx['metadata']:
        if q.norm(meta.get('artistName')) not in names:
            held.append({'metadata': meta, 'reason': 'Explicit source creator name needs reconciliation'}); continue
        title = html.unescape(meta['title'])
        image_slug = unquote(urlsplit(meta.get('image', '')).path.rsplit('/', 1)[-1]).split('!')[0].rsplit('.', 1)[0]
        exact = [i for i in idx['items'] if unquote(urlsplit(i['url']).path) == prefix+image_slug]
        if len(exact) != 1:
            exact = [i for i in idx['items'] if q.norm(i['title']) == q.norm(title) and i['date'] == m.dates.creation_date(meta.get('yearAsString'))]
        if len(exact) != 1:
            held.append({'metadata': meta, 'reason': 'Artwork title/version cannot be uniquely reconciled with visible index'}); continue
        item = exact[0]
        if q.norm(item['title']) != q.norm(title):
            held.append({'metadata': meta, 'index': item, 'reason': 'Image slug matches but source titles conflict'}); continue
        date = item['date']; api_date = m.dates.creation_date(meta.get('yearAsString'))
        if date and api_date and not s.years_overlap(date, api_date):
            held.append({'metadata': meta, 'index': item, 'reason': 'Source date conflict'}); continue
        date = date or api_date
        if date and date['creation_year_end'] > 1970:
            held.append({'metadata': meta, 'index': item, 'reason': 'After 1970 or date range crossing cutoff'}); continue
        if re.search(r'\b(detail|fragment|reverse|verso|reproduction|after [a-z]|copy of)\b', q.norm(title)):
            held.append({'metadata': meta, 'index': item, 'reason': 'Copy/detail/version requires object-level reconciliation'}); continue
        sid = str(meta['contentId'])
        assert sid.isdigit() and int(sid) > 0
        wid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikiart.org/artwork/content-id/'+sid))
        work = {'id': wid, 'slug': 'wikiart-content-'+sid, 'title': title, 'alternate_title': None,
                'normalized_title': q.norm(title), 'creation_year_start': date['creation_year_start'] if date else None,
                'creation_year_end': date['creation_year_end'] if date else None,
                'date_display': item['source_date'] or meta.get('yearAsString') or 'Unknown date',
                'date_precision': date['date_precision'] if date else 'unknown', 'work_type': 'unknown',
                'medium_text': None, 'dimensions_text': None}
        rows.append({'artist_id': pair['artist']['id'], 'artwork_id': wid, 'source_id': sid,
                     'source_scheme': 'wikiart-legacy-content-id', 'source_url': item['url'], 'work': work,
                     'metadata': meta, 'index': item, 'source_receipt': idx['receipt'], 'metadata_receipt': idx['metadata_receipt'],
                     'confidence': .99, 'identity_basis': 'Explicit artistName and stable WikiArt contentId in the artist metadata list, reconciled to exactly one object link and title in the same artist visible index; source dates agree.'})
    counts = collections.Counter(x['source_url'] for x in rows)
    images = collections.Counter(q.image_key(x['metadata'].get('image')) for x in rows)
    clear = []
    for row in rows:
        if counts[row['source_url']] > 1 or images[q.image_key(row['metadata'].get('image'))] > 1:
            held.append({**row, 'reason': 'Duplicate source URL or reproduction requires version review'})
        else:
            clear.append(row)
    return clear, held


def frame():
    records = []
    for pair in candidates():
        rows, held = source_candidates(pair)
        records.append({'artist': pair['artist']['display_name'], 'artist_id': pair['artist']['id'],
                        'existing': pair['artwork_count'], 'supported': len(rows),
                        'known_pre1971': sum(x['work']['creation_year_end'] is not None for x in rows),
                        'holds': dict(collections.Counter(x['reason'] for x in held))})
    r.save(RUN/'source-feasibility.json', records)
    print(json.dumps({'painters': len(records), 'enough_including_unknown_dates': sum(x['supported'] >= 20+x['existing'] for x in records),
                      'enough_dated': sum(x['known_pre1971'] >= 20+x['existing'] for x in records),
                      'holds': dict(sum((collections.Counter(x['holds']) for x in records), collections.Counter()))}, ensure_ascii=False), flush=True)


def inventory():
    dest = RUN/'candidate-inventory.json.gz'
    if dest.exists():
        print('Preserving candidate inventory', flush=True); return
    ids = [x['artist']['id'] for x in candidates()]
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        query = """SELECT to_jsonb(a) artwork, aa.artist_id::text,
          ma.source_page_url image_source_url, ma.checksum_sha256 image_sha256
          FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
          LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
          WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ORDER BY a.id,aa.artist_id"""
        r.save(RUN/'scoped-inventory-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query, (ids,)).fetchone())
        works = db.execute(query, (ids,)).fetchall()
        wids = list({x['artwork']['id'] for x in works})
        identifiers = db.execute("SELECT to_jsonb(e) e FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (wids,)).fetchall()
        citations = db.execute("SELECT entity_id::text,field_name,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (wids,)).fetchall()
        creators = db.execute('SELECT to_jsonb(aa) aa FROM artwork_artists aa WHERE artwork_id=ANY(%s::uuid[])', (wids,)).fetchall()
        byname = collections.defaultdict(set)
        for pair in candidates():
            for name in [pair['artist']['display_name'], pair['source']['name']]+pair['aliases']:
                key = q.norm(name)
                byname[key].add(pair['artist']['id'])
                words = key.split()
                byname[' '.join(words[-1:]+words[:-1])].add(pair['artist']['id'])
        labels = db.execute("SELECT DISTINCT unlinked_creator_label FROM artworks WHERE unlinked_creator_label IS NOT NULL AND status<>'archived'").fetchall()
        matched = {x['unlinked_creator_label']: sorted(byname[q.norm(re.sub(r'\([^)]*\)', '', x['unlinked_creator_label']))]) for x in labels if q.norm(re.sub(r'\([^)]*\)', '', x['unlinked_creator_label'])) in byname}
        leads = db.execute("SELECT to_jsonb(a) artwork FROM artworks a WHERE unlinked_creator_label=ANY(%s) AND status<>'archived'", (list(matched),)).fetchall() if matched else []
        collection = db.execute('SELECT to_jsonb(c) c FROM curated_collections c WHERE id=%s', (m.COLLECTION,)).fetchone()
        positions = db.execute('SELECT max(position) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()
    r.save_gz(dest, {'at': r.now(), 'works': works, 'identifiers': [x['e'] for x in identifiers], 'citations': citations,
                    'creators': [x['aa'] for x in creators], 'unlinked': [{'artist_ids': matched[x['artwork']['unlinked_creator_label']], **x} for x in leads],
                    'personal_collection': collection, 'collection_position': positions})
    print('Scoped inventory:', len(works), 'linked works;', len(leads), 'unlinked-creator leads; collection position', positions['n'], flush=True)


def eligible_plans():
    """Preflight duplicates before random sampling; do not replace a frozen painter."""
    dest = RUN/'eligible-plans.json.gz'
    if dest.exists():
        data = r.load(dest); print('Preserved eligible plans', len(data['painters']), flush=True); return
    inv = r.load(RUN/'candidate-inventory.json.gz')
    sources = []; source_holds = []
    for pair in candidates():
        rows, held = source_candidates(pair)
        sources.extend(rows)
        source_holds.extend({'artist_id': pair['artist']['id'], **x} for x in held)
    urls = sorted({x['source_url'] for x in sources})
    legacy = sorted({x['source_id'] for x in sources})
    with r.connect('production') as db:
        query = "SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='wikiart-legacy-content-id' AND external_id=ANY(%s)))"
        r.save(RUN/'source-identity-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query, (urls, legacy)).fetchone())
        global_ids = db.execute(query, (urls, legacy)).fetchall()
        query = "SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)"
        r.save(RUN/'source-citation-query-plan.json', db.execute('EXPLAIN (FORMAT JSON) '+query, (urls,)).fetchone())
        global_cites = db.execute(query, (urls,)).fetchall()
        query = 'SELECT id::text,source_page_url FROM media_assets WHERE source_page_url=ANY(%s)'
        global_media = db.execute(query, (urls,)).fetchall()
        media_links = db.execute('SELECT artwork_id::text,media_id::text FROM artwork_media WHERE media_id=ANY(%s::uuid[])', ([x['id'] for x in global_media],)).fetchall()
    r.save_gz(RUN/'global-source-matches.json.gz', {'identifiers': global_ids, 'citations': global_cites, 'media': global_media, 'media_links': media_links})
    byurl = collections.defaultdict(set); bylegacy = collections.defaultdict(set)
    for x in global_ids:
        byurl[x['canonical_url']].add(x['entity_id'])
        if x['scheme'] == 'wikiart-legacy-content-id':
            bylegacy[x['external_id']].add(x['entity_id'])
    for x in global_cites:
        byurl[x['source_url']].add(x['entity_id'])
    media_urls = {x['id']: x['source_page_url'] for x in global_media}
    for x in media_links:
        byurl[media_urls[x['media_id']]].add(x['artwork_id'])
    works = collections.defaultdict(dict)
    for x in inv['works']:
        works[x['artist_id']][x['artwork']['id']] = x['artwork']
    for x in inv['unlinked']:
        for aid in x['artist_ids']:
            works[aid][x['artwork']['id']] = x['artwork']
    clear = collections.defaultdict(list); holds = []
    for row in sources:
        matched = byurl[row['source_url']] | bylegacy[row['source_id']]
        if matched:
            holds.append({**row, 'reason': 'Already represented by source evidence in production', 'existing_ids': sorted(matched)}); continue
        names = [q.norm(row['work']['title'])]
        possible = []
        for w in works[row['artist_id']].values():
            for old in {q.norm(w['title']), q.norm(w.get('alternate_title'))}-{''}:
                for name in names:
                    contained = min(len(old), len(name)) >= 18 and (old in name or name in old)
                    if old == name or contained or (min(len(old), len(name)) >= 9 and difflib.SequenceMatcher(None, old, name).ratio() >= .88):
                        possible.append(w['id'])
        if possible:
            holds.append({**row, 'reason': 'Existing title/variant or unlinked creator needs same-object reconciliation', 'existing_ids': sorted(set(possible))}); continue
        clear[row['artist_id']].append(row)
    url_multiplicity = collections.Counter(x['source']['url'] for x in candidates())
    plans = []
    for pair in candidates():
        if url_multiplicity[pair['source']['url']] != 1:
            holds.append({'artist_id': pair['artist']['id'], 'reason': 'Duplicate catalogue artist authorities for one source profile'}); continue
        rows = clear[pair['artist']['id']]
        # Repeated titles at compatible dates need object-level version review.
        ambiguous = set()
        for i, left in enumerate(rows):
            for right in rows[i+1:]:
                if left['work']['normalized_title'] == right['work']['normalized_title'] and s.indistinct_dates(left['work'], right['work']):
                    ambiguous.update([left['source_id'], right['source_id']])
        for row in rows:
            if row['source_id'] in ambiguous:
                holds.append({**row, 'reason': 'Repeated source title at overlapping/unknown dates needs version review'})
        rows = [x for x in rows if x['source_id'] not in ambiguous]
        if len(rows) >= 20:
            plans.append({'pair': pair, 'rows': rows})
    r.save_gz(RUN/'duplicate-and-version-holds.json.gz', holds)
    r.save_gz(RUN/'source-dispositions.json.gz', source_holds)
    r.save_gz(dest, {'at': r.now(), 'painters': plans, 'sampling_scope': 'Active individual production painters with 0–10 artworks at inventory, a unique exact WikiArt identity, and at least 20 additional source-backed records after object/version/date checks. Source coverage is an explicit eligibility restriction, not a sample of all 20,300 low-count artists.'})
    print(json.dumps({'eligible_painters': len(plans), 'available_new_works': sum(len(x['rows']) for x in plans), 'duplicate_holds': dict(collections.Counter(x['reason'] for x in holds))}), flush=True)


def profiles():
    m.CACHE = m.cache_catalogue()
    plans = r.load(RUN/'eligible-plans.json.gz')['painters']
    def one(plan):
        pair = plan['pair']; aid = pair['artist']['id']; dest = RUN/'profiles'/(aid+'.json')
        if dest.exists():
            return r.load(dest)
        result = {'artist_id': aid, 'artist': pair['artist']['display_name']}
        try:
            raw, receipt = m.capture(pair['source']['url'], 'artist-captures')
            assert receipt['status'] == 200, 'Profile HTTP '+str(receipt['status'])
            soup = m.BeautifulSoup(raw, 'html.parser'); info = soup.select_one('.wiki-layout-artist-info')
            assert info
            fields = {}
            for li in info.select('li'):
                key = li.find('s')
                if key:
                    name = key.get_text(' ', strip=True).rstrip(':'); key.extract()
                    fields[name] = li.get_text(' ', strip=True)
            dates = {}
            for key in ['birthDate', 'deathDate']:
                tag = soup.select_one('[itemprop="'+key+'"]')
                value = tag.get_text(' ', strip=True) if tag else None
                years = re.findall(r'\b\d{4}\b', value or '')
                dates[key] = {'label': value, 'year': int(years[-1]) if years else None}
            result.update(outcome='captured', fields=fields, dates=dates, receipt=receipt,
                          profile_text=info.get_text(' ', strip=True))
        except Exception as exc:
            result.update(outcome='held', error=str(exc)[:400])
        r.save(dest, result)
        return result
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, result in enumerate(pool.map(one, plans), 1):
            counts[result['outcome']] += 1
            if i % 20 == 0:
                print('Creator profiles', i, '/', len(plans), dict(counts), flush=True)
    print('Profile checks', dict(counts), flush=True)


def freeze():
    dest = RUN/'cohort.json'
    if dest.exists():
        assert r.load(RUN/'authorization.json')['cohort_sha256'] == r.sha(dest.read_bytes())
        print('Preserving frozen 200-painter sample', flush=True); return
    prospects = r.load(RUN/'eligible-plans.json.gz')['painters']
    manual_exclusions = {
        'aztec-art': 'Cultural tradition, not an individual painter.',
        'viking-art': 'Cultural tradition, not an individual painter.',
        'limbourg-brothers': 'Collective creator, not an individual painter.',
        'le-nain-brothers': 'Collective creator, not an individual painter.',
        'vicente-juan-masip': 'Catalogue authority Q1287248 identifies the elder Vicente Masip; the matched WikiArt profile identifies his son Vicente Juan Masip. A supplied alias conflates father and son. No authority changes in this pass.',
    }
    accepted = []; exclusions = []; date_holds = []
    for plan in prospects:
        pair = plan['pair']; a = pair['artist']; profile = r.load(RUN/'profiles'/(a['id']+'.json'))
        reason = manual_exclusions.get(pair['source']['url'].rsplit('/', 1)[-1])
        if profile['outcome'] != 'captured':
            reason = 'Creator profile unavailable for identity review'
        else:
            field = profile['fields'].get('Field', '')
            if field in ['architecture', 'photography', 'sculpture']:
                reason = 'Source field is exclusively '+field+'; excluded from this painter sample.'
            for key, prop in [('birth_year', 'birthDate'), ('death_year', 'deathDate')]:
                year = profile['dates'][prop]['year']
                if a.get(key) and year and abs(a[key]-year) > 1:
                    reason = 'Catalogue/profile lifespan disagreement requires review: '+key
        if reason:
            exclusions.append({'artist_id': a['id'], 'artist': a['display_name'], 'source': pair['source']['url'], 'reason': reason}); continue
        birth = profile['dates']['birthDate']['year'] or a.get('birth_year')
        death = profile['dates']['deathDate']['year'] or a.get('death_year')
        rows = []
        for row in plan['rows']:
            first = row['work']['creation_year_start']
            if first and ((birth and first < birth) or (death and first > death)):
                date_holds.append({**row, 'reason': 'Source date outside documented creator lifespan; may describe a later reproduction or a source error.'})
            else:
                rows.append(row)
        if len(rows) < 20:
            exclusions.append({'artist_id': a['id'], 'artist': a['display_name'], 'reason': 'Fewer than 20 additions after date review', 'remaining': len(rows)}); continue
        accepted.append({'pair': pair, 'rows': rows, 'profile': profile})
    ids = [x['pair']['artist']['id'] for x in accepted]
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        counts = db.execute("""SELECT ar.id::text,ar.status,count(DISTINCT a.id) n
          FROM artists ar LEFT JOIN artwork_artists aa ON aa.artist_id=ar.id
          LEFT JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
          WHERE ar.id=ANY(%s::uuid[]) GROUP BY ar.id""", (ids,)).fetchall()
    current = {x['id']: x for x in counts}
    qualifying = []
    for plan in accepted:
        a = plan['pair']['artist']; now = current.get(a['id'])
        if not now or now['status'] == 'archived' or now['n'] > 10:
            exclusions.append({'artist_id': a['id'], 'artist': a['display_name'], 'reason': 'No longer has 0–10 active works at sampling time', 'current': now}); continue
        plan['pair']['count_at_selection'] = now['n']
        qualifying.append(plan)
    assert len(qualifying) >= 200, 'Need more independently verified qualifying painters: '+str(len(qualifying))
    seed = secrets.token_hex(16)
    ordering = sorted(qualifying, key=lambda x: hashlib.sha256((seed+'/'+x['pair']['artist']['id']).encode()).digest())
    chosen = ordering[:200]
    r.save(RUN/'sampling-frame.json', {'at': r.now(), 'seed': seed, 'count': len(qualifying),
            'eligible_artist_ids': [x['pair']['artist']['id'] for x in qualifying], 'exclusions': exclusions,
            'method': 'Uniform random ordering without replacement by SHA256(seed + / + artist UUID), after source feasibility, individual identity, object/version and date review. No country/popularity weighting.',
            'scope': r.load(RUN/'eligible-plans.json.gz')['sampling_scope'],
            'source_coverage_limit': 'This is a random sample of verified source-supported candidates, not a uniform sample of all 20,300 low-count catalogue artists.',
            'unknown_dates': 'Unknown creation dates remain unknown in review. Historical creator dates are not assigned to artworks or treated as proven creation dates.',
            'artist_identities': 'Exact source name or supplied alias without lifespan conflict, checked against each full creator profile; reviewed father/son and nonindividual exclusions are explicit.'})
    r.save_gz(RUN/'lifespan-date-holds.json.gz', date_holds)
    r.save(dest, {'at': r.now(), 'seed': seed, 'painters': [x['pair'] for x in chosen]})
    r.save(RUN/'authorization.json', {'at': r.now(), 'target': 'production', 'user_instruction': 'pick 200 random painters that have 0-10 artworks and for each of them add at least 20-100 artworks',
            'cohort_sha256': r.sha(dest.read_bytes()), 'agents_sha256': r.sha((ROOT/'AGENTS.md').read_bytes()),
            'source_policy': 'User-approved WikiArt source policy, 6 October 2026.',
            'operation': '20–100 additional artwork records per selected painter; review status, exact source labels and unknown fields preserved. No local catalogue writes, existing-record replacement, inferred holdings or current display.'})
    for rank, plan in enumerate(chosen, 1):
        # Prefer explicitly dated entries; bounded selection never exceeds 100.
        rows = sorted(plan['rows'], key=lambda x: (x['work']['creation_year_start'] is None, hashlib.sha256((seed+'/'+x['source_id']).encode()).digest()))[:100]
        data = {'rank': rank, 'pair': plan['pair'], 'rows': rows, 'profile': plan['profile'],
                'authorization_sha256': r.sha((RUN/'authorization.json').read_bytes())}
        path = RUN/'plans'/(plan['pair']['artist']['id']+'.json.gz')
        r.save_gz(path, data)
        r.save(RUN/'plan-pins'/(plan['pair']['artist']['id']+'.json'), {'sha256': r.sha(path.read_bytes())})
    print(json.dumps({'painters': len(chosen), 'frame': len(qualifying), 'seed': seed,
                     'new_records_planned': sum(min(100, len(x['rows'])) for x in chosen), 'range': [min(len(x['rows']) for x in chosen), 100], 'exclusions': len(exclusions)}), flush=True)


def backup():
    description = 'Before low-count random 200 painter additions 20261008'
    dest = BACKUP/'cloud-backup-request.json'
    if not dest.exists():
        raw = subprocess.check_output(['gcloud', 'sql', 'backups', 'create', '--instance=artline-postgres', '--project=artline-508319', '--description='+description, '--async', '--format=json'], text=True)
        r.save(dest, json.loads(raw)); print('Requested production recovery backup', flush=True)
    rows = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'list', '--instance=artline-postgres', '--project=artline-508319', '--limit=30', '--format=json'], text=True))
    matches = [x for x in rows if x.get('description') == description]
    if len(matches) == 1 and matches[0]['status'] == 'SUCCESSFUL':
        r.save(BACKUP/'cloud-backup.json', matches[0]); r.save(RUN/'cloud-backup.json', matches[0])
        print('Backup successful:', matches[0]['id'], flush=True)
    else:
        print('Backup pending:', [(x.get('id'), x.get('status')) for x in matches], flush=True)


def plans():
    for pair in r.load(RUN/'cohort.json')['painters']:
        aid = pair['artist']['id']; path = RUN/'plans'/(aid+'.json.gz')
        assert r.load(RUN/'plan-pins'/(aid+'.json'))['sha256'] == r.sha(path.read_bytes())
        data = r.load(path)
        assert data['authorization_sha256'] == r.sha((RUN/'authorization.json').read_bytes())
        yield data


def evidence(extra_dates=False):
    """Cross-language duplicate checks and bounded direct-page corroboration."""
    m.CACHE = m.cache_catalogue(); selected = list(plans())
    inventory = r.load(RUN/'candidate-inventory.json.gz')
    workmap = collections.defaultdict(list)
    for x in inventory['works']:
        workmap[x['artist_id']].append(x['artwork'])
    for x in inventory['unlinked']:
        for aid in x['artist_ids']:
            workmap[aid].append(x['artwork'])
    translation_jobs = []
    for plan in selected:
        pair = plan['pair']; aid = pair['artist']['id']
        titles = ' '.join(w['title']+' '+(w.get('alternate_title') or '') for w in workmap[aid])
        langs = set()
        if re.search('[А-Яа-яЁё]', titles): langs.add('ru')
        if re.search(r'\b(?:der|die|das|mit|und|bei|im|bildnis|landschaft)\b', q.norm(titles)): langs.add('de')
        if re.search(r'\b(?:le|la|les|du|des|de|et|portrait|paysage)\b', q.norm(titles)): langs.add('fr')
        if re.search(r'\b(?:retrato|paisaje|el|los|las)\b', q.norm(titles)): langs.add('es')
        if re.search(r'\b(?:della|delle|con|ritratto|madonna|paesaggio|il)\b', q.norm(titles)): langs.add('it')
        for lang in sorted(langs): translation_jobs.append((pair, lang))
    def translation(job):
        pair, lang = job; aid = pair['artist']['id']; dest = RUN/'translations'/(aid+'-'+lang+'.json.gz')
        if dest.exists(): return r.load(dest)
        slug = pair['source']['url'].rsplit('/', 1)[-1]
        url = 'https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
        result = {'artist_id': aid, 'language': lang}
        try:
            raw, receipt = m.capture(url, 'translation-captures')
            assert receipt['status'] == 200
            items = json.loads(raw); assert isinstance(items, list)
            result.update(outcome='captured', items=items, receipt=receipt)
        except Exception as exc: result.update(outcome='unavailable', error=str(exc)[:300], items=[])
        r.save_gz(dest, result); return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        counts = collections.Counter(x['outcome'] for x in pool.map(translation, translation_jobs))
    print('Translated source indexes', len(translation_jobs), dict(counts), flush=True)
    jobs = []
    for plan in selected:
        rows = plan['rows']
        sample = {rows[0]['source_id']}
        unknown = next((x for x in rows if x['work']['creation_year_start'] is None), None)
        if unknown: sample.add(unknown['source_id'])
        jobs.extend((plan['pair'], row) for row in rows if row['source_id'] in sample or row['source_url'] in m.CACHE or (extra_dates and row['work']['creation_year_start'] is None))
    def page(job):
        pair, row = job; dest = RUN/'page-checks'/(row['source_id']+'.json.gz')
        if dest.exists(): return r.load(dest)
        result = {'source_id': row['source_id'], 'artist_id': pair['artist']['id'], 'source_url': row['source_url']}
        try:
            raw, receipt = m.capture(row['source_url'], 'page-captures')
            assert receipt['status'] == 200, 'HTTP '+str(receipt['status'])
            data = q.page_metadata(raw, receipt)
            assert data['metadata']['artistUrl'] == urlsplit(pair['source']['url']).path, 'Artwork page creator differs'
            assert q.norm(data['metadata']['title']) == row['work']['normalized_title'], 'Artwork page title differs'
            assert q.image_key(data['metadata']['image']) == q.image_key(row['metadata']['image']), 'Artwork page image/version differs'
            data['date'] = s.source_date(data)
            if data['date']:
                assert data['date']['creation_year_end'] <= 1970, 'Artwork page creation after 1970/crossing scope'
                assert row['work']['creation_year_start'] is None or s.years_overlap(row['work'], data['date']), 'Artwork page date conflicts with index'
            result.update(outcome='corroborated', page=data)
        except AssertionError as exc:
            result.update(outcome='conflict' if not str(exc).startswith('HTTP ') else 'page_unavailable', error=str(exc)[:400])
        except Exception as exc: result.update(outcome='page_unavailable', error=str(exc)[:400])
        r.save_gz(dest, result); return result
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, result in enumerate(pool.map(page, jobs), 1):
            counts[result['outcome']] += 1
            if i % 25 == 0: print('Direct artwork checks', i, '/', len(jobs), dict(counts), flush=True)
    r.save(RUN/('date-evidence-summary.json' if extra_dates else 'evidence-summary.json'), {'at': r.now(), 'translated_indexes': len(translation_jobs), 'direct_pages': len(jobs), 'page_outcomes': dict(counts),
            'scope': 'Every new record is grounded in its exact artist JSON entry and reconciled visible artwork index. Direct-page corroboration checks at least one selected work per artist and '+('every selected undated work' if extra_dates else 'one unknown-date example where present')+', plus already cached selected artwork pages. This does not claim every object page was fetched.'})


def date_evidence():
    evidence(extra_dates=True)


def museum_supplement():
    """A separately inventoried drawing sheet fills the frozen painter's shortfall."""
    aid = '2db6d8ed-19a1-4eb6-9b85-97047e01c183'
    url = 'https://collection.artsacademymuseum.org/entity/OBJECT/49112'
    raw, receipt = m.capture(url, 'museum-captures')
    assert receipt['status'] == 200
    text = m.BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True)
    title = '1. На горной дороге в дождь – набросок и 2. три карикатуры.'
    accession = 'НИМ РАХ КП-610/4139. Р-2197'
    for value in [title, accession, 'XIX век', 'Мясоедов Григорий Григорьевич (1834-1911)', 'Бумага; графит', '35,5х44,2']:
        assert value in text, 'Museum evidence changed: '+value
    author_url = 'https://collection.artsacademymuseum.org/entity/PERSON/3590830'
    author_raw, author_receipt = m.capture(author_url, 'museum-captures')
    assert author_receipt['status'] == 200 and 'Мясоедов Григорий Григорьевич' in author_raw.decode()
    wid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
    with r.connect('production') as db:
        ids = db.execute("SELECT entity_id::text FROM external_identifiers WHERE canonical_url LIKE %s OR (scheme='artsacademymuseum-object' AND external_id='49112')", (url+'%',)).fetchall()
        cites = db.execute('SELECT entity_id::text FROM citations WHERE source_url LIKE %s', (url+'%',)).fetchall()
        works = db.execute('SELECT id::text FROM artworks WHERE id=%s OR accession_number=%s OR title=%s OR normalized_title=%s', (wid, accession, title, q.norm(title))).fetchall()
    assert not ids and not cites and not works, 'Museum sheet already represented in production'
    row = {'artist_id': aid, 'artwork_id': wid, 'source_id': '49112', 'source_scheme': 'artsacademymuseum-object', 'source_provider': 'artsacademy',
           'source_url': url, 'work': {'id': wid, 'slug': 'artsacademymuseum-object-49112', 'title': title, 'alternate_title': None,
            'normalized_title': q.norm(title), 'creation_year_start': 1801, 'creation_year_end': 1900, 'date_display': 'XIX век', 'date_precision': 'century',
            'work_type': 'drawing', 'medium_text': 'Бумага; графит', 'dimensions_text': '35,5х44,2', 'accession_number': accession},
           'metadata': {'contentId': 49112, 'title': title, 'artistName': 'Мясоедов Григорий Григорьевич (1834-1911)',
                        'date_label': 'XIX век', 'medium': 'Бумага; графит', 'dimensions': '35,5х44,2', 'inventory': accession,
                        'provenance': 'из библиотеки ВАХ. 14.03.1941', 'collection_label': 'Рисунок', 'institution': 'Музей Академии художеств',
                        'creator_authority_url': author_url, 'creator_authority_receipt': author_receipt},
           'index': {'title': title, 'url': url, 'source_date': 'XIX век'}, 'source_receipt': receipt, 'metadata_receipt': receipt,
           'confidence': .99, 'identity_basis': 'Official Academy Museum object 49112 and accession НИМ РАХ КП-610/4139. Р-2197 explicitly name Grigoriy Grigoryevich Myasoyedov (1834–1911). One graphite drawing sheet contains a mountain-road sketch and three caricatures; counted as one object, not four. Distinct title, medium and inventory from the existing catalogue and selected WikiArt paintings. Source nineteenth-century date retained with century precision; no exact year invented.',
           'creator_evidence_note': 'The official Museum of the Academy of Arts object record and linked creator authority explicitly identify Мясоедов Григорий Григорьевич (1834-1911), matching the frozen painter identity.',
           'supplement_review': {'reason': 'Two translated WikiArt titles duplicated existing Russian-language works, leaving 19. A separately inventoried museum drawing sheet supplies the twentieth addition without replacing the sampled painter.',
                                 'study_hold_preserved': 'WikiArt Zemstvo study remains held because it may be a detail of the existing finished composition.'}}
    r.save_gz(RUN/'supplements'/(aid+'.json.gz'), [row])
    print('Verified one separately inventoried museum drawing sheet for Grigoriy Myasoyedov', flush=True)


def delivery_plans():
    inv = r.load(RUN/'candidate-inventory.json.gz'); old = collections.defaultdict(list)
    for x in inv['works']: old[x['artist_id']].append(x['artwork'])
    for x in inv['unlinked']:
        for aid in x['artist_ids']: old[aid].append(x['artwork'])
    all_holds = []; ready = []
    for plan in plans():
        aid = plan['pair']['artist']['id']; translations = collections.defaultdict(set)
        for path in (RUN/'translations').glob(aid+'-*.json.gz'):
            for item in r.load(path)['items']:
                translations[str(item['contentId'])].add(q.norm(item['title']))
        rows = []; holds = []
        for row in plan['rows']:
            prior = [w['id'] for w in old[aid] if ({q.norm(w['title']), q.norm(w.get('alternate_title'))}-{''}) & translations[row['source_id']]]
            if prior:
                holds.append({**row, 'reason': 'Translated source title matches an existing object', 'existing_ids': sorted(set(prior))}); continue
            proof = RUN/'page-checks'/(row['source_id']+'.json.gz')
            if proof.exists():
                check = r.load(proof)
                if check['outcome'] == 'conflict':
                    holds.append({**row, 'reason': check['error'], 'page_check': str(proof.relative_to(ROOT))}); continue
                row['page_check'] = check
                if check['outcome'] == 'corroborated':
                    page = check['page']; w = row['work']; meta = page['metadata']
                    w.update(alternate_title=page['fields'].get('Original Title'), work_type=s.kind(page['fields'].get('Media')),
                             medium_text=page['fields'].get('Media'), dimensions_text=page['fields'].get('Dimensions'))
                    if page['date']:
                        w.update(page['date'])
                    row['wikiart_artwork_id'] = meta['_id']
                    # Maintain the standard canonical object ID when the source supplies it.
                    row['artwork_id'] = w['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikiart.org/artwork/'+meta['_id']))
                    w['slug'] = 'wikiart-'+meta['_id']
            if row['work']['creation_year_start'] is None:
                row['work']['date_display'] = 'Unknown date'
                row['date_review'] = 'Creation date remains unknown. Source labels are retained in the index and metadata evidence. This record is not asserted to have proven pre-1971 eligibility.'
            row['translated_titles_checked'] = sorted(translations[row['source_id']])
            rows.append(row)
        all_holds.extend(holds)
        supplement = RUN/'supplements'/(aid+'.json.gz')
        if supplement.exists():
            rows.extend(r.load(supplement))
        data = {**plan, 'rows': rows, 'additional_holds': holds}
        ready.append(data)
    # Recheck canonical IDs revealed by direct pages and all URL/legacy identities.
    ids = [row['artwork_id'] for plan in ready for row in plan['rows']]
    urls = [row['source_url'] for plan in ready for row in plan['rows']]
    source_ids = [row['source_id'] for plan in ready for row in plan['rows'] if row['source_scheme']=='wikiart-legacy-content-id']
    canonical_ids = [row['wikiart_artwork_id'] for plan in ready for row in plan['rows'] if row.get('wikiart_artwork_id')]
    with r.connect('production') as db:
        existing = db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
        matches = db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='wikiart-legacy-content-id' AND external_id=ANY(%s)) OR (scheme='wikiart-artwork' AND external_id=ANY(%s)))", (urls, source_ids, canonical_ids)).fetchall()
    r.save(RUN/'delivery-source-recheck.json', {'at': r.now(), 'existing_ids': existing, 'source_matches': matches})
    assert not existing and not matches, 'New source identities overlap current production; reconcile before delivery'
    r.save_gz(RUN/'final-evidence-holds.json.gz', all_holds)
    shortfalls = [{'artist': x['pair']['artist']['display_name'], 'artist_id': x['pair']['artist']['id'], 'ready': len(x['rows']), 'holds': len(x['additional_holds'])} for x in ready if len(x['rows']) < 20]
    r.save(RUN/'delivery-readiness.json', {'at': r.now(), 'painters': len(ready), 'new_artworks': sum(len(x['rows']) for x in ready), 'shortfalls': shortfalls, 'holds': len(all_holds)})
    for plan in ready:
        aid = plan['pair']['artist']['id']; path = RUN/'delivery-plans'/(aid+'.json.gz')
        r.save_gz(path, plan); r.save(RUN/'delivery-pins'/(aid+'.json'), {'sha256': r.sha(path.read_bytes())})
    print(json.dumps(r.load(RUN/'delivery-readiness.json')), flush=True)


def deliveries():
    assert r.load(RUN/'authorization.json')['cohort_sha256'] == r.sha((RUN/'cohort.json').read_bytes())
    for pair in r.load(RUN/'cohort.json')['painters']:
        aid = pair['artist']['id']; path = RUN/'delivery-plans'/(aid+'.json.gz')
        pin = r.load(RUN/'delivery-pins'/(aid+'.json'))['sha256']
        assert pin == r.sha(path.read_bytes())
        plan = r.load(path)
        assert plan['pair']['artist']['id'] == aid
        assert plan['authorization_sha256'] == r.sha((RUN/'authorization.json').read_bytes())
        yield plan, pin


def validate_plan(plan):
    pair = plan['pair']; rows = plan['rows']
    assert 0 <= pair['count_at_selection'] <= 10
    assert 20 <= len(rows) <= 100
    assert len({x['artwork_id'] for x in rows}) == len(rows)
    assert len({x['source_id'] for x in rows}) == len(rows)
    assert len({x['source_url'] for x in rows}) == len(rows)
    for row in rows:
        w = row['work']; first = w['creation_year_start']; last = w['creation_year_end']
        assert row['artist_id'] == pair['artist']['id']
        if row['source_scheme'] == 'wikiart-legacy-content-id':
            assert row['source_url'].startswith(pair['source']['url']+'/')
        else:
            assert row['source_scheme'] == 'artsacademymuseum-object' and row['source_provider'] == 'artsacademy'
            assert row['source_url'] == 'https://collection.artsacademymuseum.org/entity/OBJECT/'+row['source_id']
            assert row.get('supplement_review') and w.get('accession_number')
        assert w['id'] == row['artwork_id'] and w['title'].strip()
        assert str(row['metadata']['contentId']) == row['source_id']
        if first is None:
            assert last is None and w['date_precision'] == 'unknown' and row.get('date_review')
        else:
            assert first != 0 and last is not None and first <= last <= 1970
        if row.get('page_check'):
            assert row['page_check']['outcome'] != 'conflict'


def preflight():
    final = list(deliveries()); assert len(final) == 200
    ids = []; urls = []; legacy = []; canon = []; receipts = {}
    for plan, pin in final:
        validate_plan(plan)
        for row in plan['rows']:
            ids.append(row['artwork_id']); urls.append(row['source_url'])
            if row['source_scheme'] == 'wikiart-legacy-content-id': legacy.append(row['source_id'])
            if row.get('wikiart_artwork_id'): canon.append(row['wikiart_artwork_id'])
            for receipt in [row['source_receipt'], row['metadata_receipt'], plan['profile']['receipt']]:
                receipts[receipt['body_path']] = receipt
            check = row.get('page_check', {})
            if check.get('page'): receipts[check['page']['receipt']['body_path']] = check['page']['receipt']
    assert len(ids) == len(set(ids)) and len(urls) == len(set(urls)) and len(legacy) == len(set(legacy))
    for path, receipt in receipts.items():
        body = (ROOT/path).read_bytes()
        if path.endswith('.gz'): body = gzip.decompress(body)
        assert r.sha(body) == receipt['sha256'], 'Source receipt checksum differs: '+path
    artist_ids = [x['pair']['artist']['id'] for x, _ in final]
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        occupied = db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
        identities = db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='wikiart-legacy-content-id' AND external_id=ANY(%s)) OR (scheme='wikiart-artwork' AND external_id=ANY(%s)))", (urls, legacy, canon)).fetchall()
        citations = db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (urls,)).fetchall()
        originals = db.execute("SELECT DISTINCT a.id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'", (artist_ids,)).fetchall()
        before = s.snapshots(db, [x['id'] for x in originals])
        collection = db.execute('SELECT to_jsonb(c) c FROM curated_collections c WHERE id=%s', (m.COLLECTION,)).fetchone()['c']
        position = db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()['n']
    assert not occupied and not identities and not citations, 'Concurrent source identity appeared; reconcile before insertion'
    assert collection['curator_kind'] == 'owner' and collection['institution_id'] is None
    assert position+len(ids) <= 100000
    r.save_gz(BACKUP/'original-records-before.json.gz', before)
    proof = {'at': r.now(), 'painters': 200, 'new_records': len(ids), 'new_record_ids_sha256': r.sha(json.dumps(sorted(ids)).encode()),
             'source_bodies_verified': len(receipts), 'original_records': len(before), 'personal_collection_position': position,
             'cohort_sha256': r.sha((RUN/'cohort.json').read_bytes()), 'plan_pins': {p['pair']['artist']['id']: pin for p, pin in final},
             'minimum_additions': min(len(p['rows']) for p, _ in final), 'maximum_additions': max(len(p['rows']) for p, _ in final),
             'unknown_dates_preserved': sum(row['work']['creation_year_start'] is None for p, _ in final for row in p['rows']),
             'read_only': True, 'local_database_connected': False}
    r.save(RUN/'preflight.json', proof)
    print(json.dumps({k:v for k,v in proof.items() if k!='plan_pins'}), flush=True)


def apply():
    assert r.load(BACKUP/'cloud-backup.json')['status'] == 'SUCCESSFUL'
    final = list(deliveries()); assert len(final) == 200
    pre = r.load(RUN/'preflight.json')
    assert pre['plan_pins'] == {p['pair']['artist']['id']: pin for p, pin in final}
    source = m.uid('source/wikiart-indexes'); museum_source = m.uid('source/artsacademy'); actor = 'local-european-research'
    with r.connect('production', readonly=False) as db:
        for number, (plan, pin) in enumerate(final, 1):
            validate_plan(plan)
            pair = plan['pair']; artist = pair['artist']; aid = artist['id']; rows = plan['rows']
            done = RUN/'applied'/(aid+'.json')
            if done.exists():
                assert r.load(done)['plan_sha256'] == pin
                continue
            ids = [row['artwork_id'] for row in rows]
            marker = m.uid('applied/'+aid)
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='15s'")
                db.execute('SELECT pg_advisory_xact_lock(2026100607)')
                previous = db.execute('SELECT after_json FROM audit_log WHERE id=%s', (marker,)).fetchone()
                if previous:
                    result = previous['after_json']
                    assert result['plan_sha256'] == pin and result['new_ids'] == ids
                    assert len(s.snapshots(db, ids)) == len(ids)
                else:
                    creator = db.execute('SELECT id::text,display_name,status FROM artists WHERE id=%s FOR SHARE', (aid,)).fetchone()
                    assert creator and creator['display_name'] == artist['display_name'] and creator['status'] != 'archived'
                    collision = db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
                    assert not collision, 'A planned new artwork already exists'
                    source_ids = [row['source_id'] for row in rows]
                    duplicate_ids = db.execute("SELECT e.entity_id::text FROM external_identifiers e JOIN unnest(%s::text[],%s::text[]) AS wanted(scheme,external_id) ON wanted.scheme=e.scheme AND wanted.external_id=e.external_id WHERE e.entity_type='artwork'", ([row['source_scheme'] for row in rows], source_ids)).fetchall()
                    assert not duplicate_ids, 'Source identity was concurrently inserted'
                    old_ids = [x['id'] for x in db.execute("SELECT DISTINCT a.id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'", (aid,)).fetchall()]
                    before = s.snapshots(db, old_ids)
                    before_hash = r.sha(json.dumps(before, sort_keys=True, default=str).encode())
                    before_path = BACKUP/'artist-preimages'/aid/(before_hash+'.json.gz')
                    r.save_gz(before_path, {'plan_sha256': pin, 'records': before})
                    collection = db.execute('SELECT curator_kind,institution_id FROM curated_collections WHERE id=%s FOR UPDATE', (m.COLLECTION,)).fetchone()
                    assert collection == {'curator_kind': 'owner', 'institution_id': None}
                    pos = db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()['n']
                    assert pos+len(rows) <= 100000
                    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/') ON CONFLICT(id) DO NOTHING",
                               (source, OP+'-wikiart', 'WikiArt low-count 200-painter selection, October 2026'))
                    if any(row.get('source_provider') == 'artsacademy' for row in rows):
                        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://collection.artsacademymuseum.org/') ON CONFLICT(id) DO NOTHING",
                                   (museum_source, OP+'-artsacademy', 'Museum of the Academy of Arts: separately inventoried Myasoyedov drawing'))
                    with db.pipeline():
                        for row in rows:
                            row_source = museum_source if row.get('source_provider') == 'artsacademy' else source
                            w = row['work']; wid = row['artwork_id']; keys = ['id','slug','title','alternate_title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium_text','dimensions_text']
                            db.execute('''INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,
                              creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by)
                              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''', tuple(w[k] for k in keys)+(w.get('accession_number'),actor,actor))
                            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                                       (wid, aid, row.get('creator_evidence_note') or 'WikiArt explicitly names this creator in the source metadata list; exact object title, source ID and artist-index link reconciled. '+row['identity_basis']))
                            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",
                                       (wid, row['source_scheme'], row['source_id'], row['source_url'], row_source, row['metadata_receipt']['retrieved_at']))
                            if row.get('wikiart_artwork_id'):
                                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikiart-artwork',%s,%s,%s,%s)",
                                           (wid, row['wikiart_artwork_id'], row['source_url'], source, row['page_check']['page']['receipt']['retrieved_at']))
                            note = {'operation': OP, 'plan_sha256': pin, 'source_identity': row['identity_basis'], 'editorial_confidence': row['confidence'],
                                    'confidence_note': 'Editorial assessment, not a calibrated probability.', 'metadata': row['metadata'], 'visible_index': row['index'],
                                    'metadata_receipt': row['metadata_receipt'], 'index_receipt': row['source_receipt'],
                                    'creator_profile_receipt': plan['profile']['receipt'], 'page_check': row.get('page_check'),
                                    'translated_titles_checked': row.get('translated_titles_checked', []), 'date_review': row.get('date_review'),
                                    'selection': 'User-requested personal study selection; not a museum designation. Unknown metadata remains unknown. No holdings or current display inferred.',
                                    'source_policy': 'Official museum object catalogue; no image reuse or current-display claim.' if row.get('source_provider')=='artsacademy' else 'WikiArt approved by the user on 6 October 2026; source labels are preserved separately from user approval.',
                                    'supplement_review': row.get('supplement_review')}
                            db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                              VALUES(%s,'artwork',%s,%s,'low_count_200_source_identity',%s,%s,%s,%s,%s)""",
                                       (m.uid('citation/'+row['source_scheme']+'/'+row['source_id']), wid, row_source, row['source_id'], row['source_url'], json.dumps(note, ensure_ascii=False), row['metadata_receipt']['retrieved_at'], actor))
                            pos += 1
                            db.execute('''INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                              VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''', (m.uid('selection/'+wid), m.COLLECTION, wid, pos,
                              'Personal study selection requested 8 October 2026: 20–100 additions for each of 200 randomly selected low-count painters. Separate from museum highlights. Unknown dates retain explicit editorial uncertainty.', row_source, row['source_url'], row['metadata_receipt']['retrieved_at']))
                        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s', (m.COLLECTION,))
                    after = s.snapshots(db, ids)
                    assert len(after) == len(rows)
                    for row in rows:
                        current = after[row['artwork_id']]
                        assert all(current['artwork'][key] == value for key, value in row['work'].items())
                        assert current['artwork']['status'] == 'review' and current['artwork']['published_at'] is None and current['artwork']['research_candidate']
                        assert current['artwork']['current_institution_id'] is None and current['artwork']['primary_media_id'] is None
                        assert not current['locations'] and not current['attachments']
                        assert len(current['creators']) == 1 and current['creators'][0]['artist_id'] == aid
                    assert s.snapshots(db, old_ids) == before, 'Existing records changed inside the import transaction'
                    result = {'at': r.now(), 'artist_id': aid, 'artist': artist['display_name'], 'plan_sha256': pin,
                              'new_records': len(rows), 'new_ids': ids, 'existing_records_before': len(before),
                              'existing_records_preserved_in_transaction': True, 'preimages': str(before_path),
                              'local_database_changed': False, 'images_attached': 0}
                    db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'low_count_200_additions','artist',%s,%s)",
                               (marker, actor, aid, m.Jsonb(result)))
            r.save(done, result)
            print('Committed', number, '/ 200:', artist['display_name'], len(rows), 'new artworks', flush=True)


def verify():
    final = list(deliveries()); ids = [row['artwork_id'] for plan, pin in final for row in plan['rows']]
    assert len(final) == 200 and all((RUN/'applied'/(plan['pair']['artist']['id']+'.json')).exists() for plan, pin in final)
    with r.connect('production') as db:
        actual = s.snapshots(db, ids)
        refs = db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (ids,)).fetchall()
        citations = db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND source_id=ANY(%s::uuid[]) AND entity_id=ANY(%s::uuid[])", ([m.uid('source/wikiart-indexes'),m.uid('source/artsacademy')], ids)).fetchall()
        selected = db.execute('SELECT id::text,artline_has_selection_evidence(id) selected FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
        totals = db.execute("SELECT aa.artist_id::text,count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY aa.artist_id", ([plan['pair']['artist']['id'] for plan, pin in final],)).fetchall()
        before = r.load(BACKUP/'original-records-before.json.gz')
        after_old = s.snapshots(db, list(before))
    assert len(actual) == len(ids) and len(citations) == len(ids)
    assert len(selected) == len(ids) and all(x['selected'] for x in selected)
    citation_map = {x['entity_id']: x for x in citations}; reference_map = collections.defaultdict(list)
    for x in refs: reference_map[x['entity_id']].append(x)
    counts = {x['artist_id']: x['n'] for x in totals}; results = []
    for plan, pin in final:
        pair = plan['pair']; aid = pair['artist']['id']
        for row in plan['rows']:
            value = actual[row['artwork_id']]; w = value['artwork']; cite = citation_map[w['id']]
            assert all(w[k] == v for k, v in row['work'].items())
            assert w['status'] == 'review' and w['research_candidate'] and w['published_at'] is None
            assert w['primary_media_id'] is None and w['current_institution_id'] is None and not value['locations'] and not value['attachments']
            assert len(value['creators']) == 1 and value['creators'][0]['artist_id'] == aid
            assert cite['source_record_id'] == row['source_id'] and cite['source_url'] == row['source_url'] and json.loads(cite['evidence_note'])['plan_sha256'] == pin
            assert any(x['scheme'] == row['source_scheme'] and x['external_id'] == row['source_id'] for x in reference_map[w['id']])
        assert 20 <= len(plan['rows']) <= 100 and counts[aid] >= pair['count_at_selection']+len(plan['rows'])
        results.append({'artist_id': aid, 'artist': pair['artist']['display_name'], 'slug': pair['artist']['slug'],
                        'before': pair['count_at_selection'], 'added': len(plan['rows']), 'after': counts[aid],
                        'unknown_dates': sum(x['work']['creation_year_start'] is None for x in plan['rows']), 'source': pair['source']['url']})
    changes = {wid: {'before': before[wid], 'after': after_old.get(wid)} for wid in before if before[wid] != after_old.get(wid)}
    r.save_gz(RUN/'concurrent-original-record-changes.json.gz', changes)
    r.save_gz(BACKUP/'new-records-after.json.gz', actual)
    proof = {'at': r.now(), 'painters': len(results), 'added': len(ids), 'minimum': min(x['added'] for x in results), 'maximum': max(x['added'] for x in results),
             'unknown_dates': sum(x['unknown_dates'] for x in results), 'source_citations': len(citations), 'all_source_selections_verified': True,
             'all_new_records_remain_review': True, 'images_attached': 0, 'concurrent_existing_record_changes': len(changes), 'local_database_changed': False, 'results': results}
    r.save(RUN/'production-verification.json', proof)
    print(json.dumps({k:v for k,v in proof.items() if k!='results'}), flush=True)


def api_verify():
    final = list(deliveries())
    def one(job):
        plan, pin = job; artist = plan['pair']['artist']; dest = RUN/'api-verification'/(artist['id']+'.json.gz')
        if dest.exists():
            proof = r.load(dest)
            assert proof['plan_sha256'] == pin and not proof['missing_ids']
            return proof
        expected = {row['artwork_id']: row for row in plan['rows']}
        found = {}; pages = []; cursors = set(); params = {'limit': 50}
        url = 'https://artlines.org/api/backend/v1/artists/'+artist['slug']+'/works'
        with m.requests.Session() as session:
            while True:
                for attempt in range(4):
                    try:
                        response = session.get(url, params=params, timeout=(15, 60))
                        if response.status_code not in [500, 502, 503, 504]: break
                    except (m.requests.Timeout, m.requests.ConnectionError):
                        if attempt == 3: raise
                    time.sleep(2+attempt*2)
                response.raise_for_status(); data = response.json()
                items = data['items']; assert len(items) <= 50
                for item in items:
                    if item['id'] in expected:
                        row = expected[item['id']]
                        assert item['title'] == row['work']['title']
                        assert item['creation_year_start'] == row['work']['creation_year_start']
                        assert item['creation_year_end'] == row['work']['creation_year_end']
                        assert item['status'] == 'review'
                        found[item['id']] = item
                pages.append({'url': response.url, 'status': response.status_code, 'returned_ids': [x['id'] for x in items], 'next_cursor': data.get('next_cursor')})
                cursor = data.get('next_cursor')
                if not cursor: break
                assert cursor not in cursors and len(pages) < 20, 'Unexpected unbounded or repeating API cursor'
                cursors.add(cursor); params['cursor'] = cursor
        proof = {'at': r.now(), 'artist_id': artist['id'], 'artist': artist['display_name'], 'plan_sha256': pin,
                 'expected': len(expected), 'found': len(found), 'missing_ids': sorted(set(expected)-set(found)), 'pages': pages,
                 'bounded_page_limit': 50, 'no_preview_or_status_parameters': True}
        assert not proof['missing_ids'], 'Imported records missing from unified catalogue API: '+artist['display_name']
        r.save_gz(dest, proof)
        print('Live API verified:', artist['display_name'], len(found), 'new records;', len(pages), 'bounded pages', flush=True)
        return proof
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, final))
    summary = {'at': r.now(), 'painters': len(results), 'new_records_found': sum(x['found'] for x in results),
               'bounded_pages': sum(len(x['pages']) for x in results), 'missing': 0, 'page_limit': 50, 'preview_flags_used': False}
    r.save(RUN/'api-verification.json', summary)
    print(json.dumps(summary), flush=True)


def report():
    proof = r.load(RUN/'production-verification.json'); api = r.load(RUN/'api-verification.json')
    assert proof['painters'] == api['painters'] == 200 and proof['added'] == api['new_records_found']
    rows = proof['results']
    def csv_file(name, values):
        path = RUN/name
        with path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(values[0]))
            writer.writeheader(); writer.writerows(values)
    csv_file('painters.csv', rows)
    works = []
    for plan, pin in deliveries():
        for row in plan['rows']:
            w = row['work']
            works.append({'artist': plan['pair']['artist']['display_name'], 'artist_id': row['artist_id'], 'artwork_id': w['id'],
                          'title': w['title'], 'date_display': w['date_display'], 'creation_year_start': w['creation_year_start'],
                          'creation_year_end': w['creation_year_end'], 'work_type': w['work_type'], 'source_url': row['source_url'],
                          'source_content_id': row['source_id'], 'status': 'review', 'images_added': 0})
    csv_file('new-artworks.csv', works)
    seed = r.load(RUN/'cohort.json')['seed']; backup_id = r.load(RUN/'cloud-backup.json')['id']; frame = r.load(RUN/'sampling-frame.json')['count']
    content = f'''# Random low-count painter expansion

Completed and verified {r.now()}.

- **{proof['added']:,} new production artwork records** for **200 randomly selected painters**.
- Every selected painter had **0–10 active artworks** at selection time and received **{proof['minimum']}–{proof['maximum']} additional artworks**.
- All {proof['added']:,} additions were checked in PostgreSQL and found through the live unified catalogue API ({api['bounded_pages']} pages, at most 50 records per page).
- New records retain review status as audit metadata and are available through the unified catalogue. Existing records were preserved inside each import transaction.
- **{proof['unknown_dates']:,} creation dates remain explicitly unknown.** Unknown dates are retained for editorial review; no artist lifespan was substituted for an artwork date. Explicit post-1970 dates, date conflicts and unresolved versions were excluded.
- This delivery adds catalogue metadata. **No new images were uploaded or attached.** Source image URLs remain preserved as identity evidence; no source rights label was converted into a different claim.

[Painter counts](painters.csv), [new artwork records](new-artworks.csv), [production verification](production-verification.json), [live API verification](api-verification.json), and [authorization](authorization.json).

## Sampling and evidence

The frozen seed is `{seed}`. The sample was drawn uniformly without replacement from {frame} verified candidates: active individual production artists with 0–10 artworks, an unambiguous WikiArt identity, and enough additional source-supported objects to meet the requested minimum after duplicate, version and date checks. It is a source-supported sample, **not** a uniform sample of all 20,300 low-count catalogue artists. No country or popularity weighting was used, and no selected painter was substituted after freezing the cohort.

The audit found 824 exact WikiArt matches among 20,300 low-count artists; 388 had sufficiently large source lists for research. The frame excludes cultural traditions, collective creator profiles, exclusively architectural/photographic/sculptural profiles, a father–son alias conflation for Vicente Masip, and unresolved lifespan conflicts. See [sampling frame](sampling-frame.json), [cohort](cohort.json), [source feasibility](source-feasibility.json), and [preflight](preflight.json).

The WikiArt additions are grounded in explicit named-creator entries with stable content IDs and reconciled object links/titles in the artist's visible list. Source bodies, SHA-256 receipts, original retrieval times, translated-title checks and catalogue deduplication evidence are retained. Direct object pages were checked for every selected undated work and a sample of dated works, plus already captured pages. Missing types, media, dimensions, dates and holdings remain unknown. The selection is a user-requested personal study collection, distinct from museum designations. No holdings or current-display claims were inferred.

Two translated titles revealed existing works for Grigoriy Myasoyedov, leaving 19 WikiArt additions. The twentieth is a separately inventoried [Museum of the Academy of Arts drawing sheet](https://collection.artsacademymuseum.org/entity/OBJECT/49112), accession `НИМ РАХ КП-610/4139. Р-2197`. It contains a mountain-road sketch and three caricatures and is counted as one object. Its explicit nineteenth-century date, graphite/paper medium, dimensions and source provenance are preserved. The museum source remains separately labelled. A WikiArt entry labelled as a Zemstvo study remains held because it may be a detail of an existing composition; visual/source review did not establish a separate object.

WikiArt is used under the [user-approved source policy](../../ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026). Any source rights labels are preserved separately from that approval.

## Recovery and limits

Successful Cloud SQL backup: `{backup_id}`. Recovery snapshots and logs: `{BACKUP}/`. Per-painter transactions have immutable plan pins, source citations and a database audit marker; interrupted receipt writing can be recovered without creating duplicate records. Source code: `ops/low-count-200-painters-20261008.py`; pure source/plan tests: `ops/test_low_count_200_painters_20261008.py`.

The local catalogue was never connected to or changed. No commit or deployment was performed. Other workflows changed {proof['concurrent_existing_record_changes']} pre-existing records between the preflight and final verification; exact before/after differences are retained separately in `concurrent-original-record-changes.json.gz`, and this importer writes only its new artwork IDs. These are selected additions, not exhaustive catalogues raisonnés. Saved query plans and bounded live API checks do not establish performance at ten million artworks; representative scale/load testing remains separate work.
'''
    (RUN/'README.md').write_text(content)
    r.save(RUN/'completion.json', {'at': r.now(), 'painters': 200, 'new_artworks': proof['added'], 'min_per_painter': proof['minimum'],
             'max_per_painter': proof['maximum'], 'all_live_api_verified': True, 'backup_id': backup_id, 'seed': seed,
             'images_added': 0, 'local_database_changed': False})
    print('Report written:', RUN/'README.md', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['audit', 'indexes', 'frame', 'inventory', 'eligible_plans', 'profiles', 'freeze', 'backup', 'evidence', 'date_evidence', 'museum_supplement', 'delivery_plans', 'preflight', 'apply', 'verify', 'api_verify', 'report'])
    args = parser.parse_args()
    globals()[args.command]()
