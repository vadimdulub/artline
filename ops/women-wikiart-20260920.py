#!/usr/bin/env python3
"""Review every recorded woman artist and deliver selected WikiArt highlights."""
import argparse
import collections
import concurrent.futures
import csv
import difflib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coverage', ROOT / 'ops/wikiart-artist-coverage.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
m = c.m
PRIOR = c.RUN
RUN = ROOT / 'docs/research/women-wikiart-20260920'
c.RUN = m.RUN = RUN
m.BACKUP = Path.home() / 'Library/Application Support/Artline/backups/women-wikiart-20260920'
m.ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images/women-wikiart-20260920'
BaseFetcher = m.Fetcher


def save(path, value):
    m.save_atomic(path, value)


class Fetcher(BaseFetcher):
    def get(self, url, limit=5_000_000, image=False):
        # Same-day source captures are immutable provenance, reusable without
        # downloading the complete WikiArt directory a second time.
        key = m.core.sha(url.encode())
        if not image:
            for previous in (PRIOR, ROOT / 'docs/research/wikiart-artist-followup-20260920', c.PREVIOUS):
                path = previous / 'captures' / (key + '.body')
                receipt = path.with_suffix('.json')
                if path.exists() and receipt.exists():
                    raw, record = path.read_bytes(), json.loads(receipt.read_bytes())
                    if m.core.sha(raw) != record['sha256']:
                        raise ValueError('Prior capture checksum mismatch')
                    save(RUN / 'captures' / path.name, raw)
                    save(RUN / 'captures' / receipt.name, record)
                    return raw, record
        return super().get(url, limit, image)


c.SharedFetcher = Fetcher


def audit():
    path = RUN / 'catalogue-baseline.json'
    if not path.exists():
        with m.read_only() as db:
            rows = db.execute("""SELECT to_jsonb(a) artist,
                coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e
                  WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
                (SELECT to_jsonb(g) FROM artist_gender_evidence g WHERE g.artist_id=a.id) gender
                FROM artists a ORDER BY a.id""").fetchall()
        save(path, {'at': m.core.now(), 'artists': rows})
    baseline = json.loads(path.read_bytes())['artists']
    print('Catalogue artists', len(baseline), 'recorded women', sum(bool(x['gender'] and x['gender']['is_woman']) for x in baseline), flush=True)
    raw, receipt = Fetcher().get('https://www.wikiart.org/en/female-artists')
    soup = c.BeautifulSoup(raw, 'html.parser')
    print(json.dumps({'receipt': receipt, 'initializers': [x['ng-init'] for x in soup.select('[ng-init]')],
        'scripts': [x.get('src') for x in soup.select('script[src]')]}, ensure_ascii=False), flush=True)


def directory():
    raw, receipt = Fetcher().get('https://www.wikiart.org/en/App/Search/female-artists?json=3&layout=new')
    data = json.loads(raw)
    save(RUN / 'female-directory-first.json', {'data': data, 'receipt': receipt})
    print(str(data)[:6500], flush=True)


def directory_pages():
    first = json.loads((RUN / 'female-directory-first.json').read_bytes())
    rows = {a['id']: a for a in first['data']['Artists']}
    total = first['data']['AllArtistsCount']
    receipts = [first['receipt']]
    for page in range(2, (total + 59) // 60 + 1):
        raw, receipt = Fetcher().get('https://www.wikiart.org/en/App/Search/female-artists?json=3&layout=new&page=' + str(page))
        data = json.loads(raw)
        new = {a['id']: a for a in data['Artists']}
        if not set(new) - set(rows):
            raise ValueError('Directory pagination did not advance: ' + str(page))
        rows.update(new)
        receipts.append(receipt)
        print('Female directory', page, len(rows), 'of', total, flush=True)
    if len(rows) != total:
        raise ValueError('Directory count differs from source total')
    save(RUN / 'female-directory.json', {'artists': list(rows.values()), 'receipts': receipts, 'total': total})


def match_artists():
    baseline = json.loads((RUN / 'catalogue-baseline.json').read_bytes())['artists']
    active = {x['artist']['id']: x for x in baseline if x['artist']['status'] != 'archived'}
    directory = json.loads((RUN / 'female-directory.json').read_bytes())
    female = {urljoin('https://www.wikiart.org', x['artistUrl']): x for x in directory['artists']}
    names, qids, source_ids = (collections.defaultdict(set) for _ in range(3))
    for aid, row in active.items():
        for name in [row['artist']['display_name']] + row['aliases']:
            names[m.norm(name)].add(aid)
        for e in row['identifiers']:
            if e['scheme'] == 'wikidata':
                qids[e['external_id']].add(aid)
            if e['scheme'] == 'wikiart-artist':
                source_ids[e['external_id']].add(aid)
    sources, previous_ids = {}, collections.defaultdict(set)
    inventory = json.loads((PRIOR / 'artist-matches.json').read_bytes())
    for source in inventory['unmatched_source_artists']:
        sources[source['url']] = source
    for group in ('matches', 'ambiguous'):
        for pair in inventory[group]:
            sources[pair['wikiart']['url']] = pair['wikiart']
    for filename in ('artist-matches.json', 'extra-artist-matches.json', 'supplemental-artist-matches.json'):
        for pair in json.loads((PRIOR / filename).read_bytes())['matches']:
            sources[pair['wikiart']['url']] = pair['wikiart']
            if pair['artist']['id'] in active:
                previous_ids[pair['wikiart']['url']].add(pair['artist']['id'])
    for url, a in female.items():
        if url not in sources:
            sources[url] = {'url': url, 'name': a['title'], 'life_display': a['year']}
    pairs, ambiguous, unmatched = [], [], []
    for url, source in sources.items():
        slug = urlparse(url).path.rsplit('/', 1)[-1]
        path = PRIOR / 'profiles' / (slug + '.json')
        profile = json.loads(path.read_bytes()) if path.exists() else {}
        identifiers = set(source_ids[slug])
        for qid in profile.get('wikidata_ids', []):
            identifiers.update(qids[qid])
        if identifiers:
            candidates, basis = identifiers, 'Explicit WikiArt or linked Wikidata identifier'
        elif previous_ids[url]:
            candidates, basis = previous_ids[url], 'Previously reconciled source identity; current DB identity retained'
        else:
            candidates = set()
            for name in (source['name'], profile.get('name')):
                candidates.update(names[m.norm(name)])
            life = c.source_life(source)
            candidates = {aid for aid in candidates if all(life.get(k) is None or active[aid]['artist'].get(k) is None
                or life[k] == active[aid]['artist'][k] for k in ('birth_year', 'death_year'))}
            basis = 'Exact normalized source/profile name or alias; no conflicting lifespan'
        if len(candidates) == 1:
            aid = next(iter(candidates))
            is_woman = bool(active[aid]['gender'] and active[aid]['gender']['is_woman'])
            if not is_woman and url not in female:
                continue
            if active[aid]['gender'] and not active[aid]['gender']['is_woman']:
                ambiguous.append({'url': url, 'reason': 'Existing gender evidence conflicts', 'ids': [aid]})
                continue
            pairs.append({'artist': active[aid]['artist'], 'wikiart': source, 'identity_basis': basis,
                'female_directory_entry': female.get(url), 'existing_woman_evidence': is_woman})
        elif url in female:
            (ambiguous if candidates else unmatched).append({'url': url, 'source': source, 'ids': sorted(candidates)})
    by_artist = collections.defaultdict(list)
    for pair in pairs:
        by_artist[pair['artist']['id']].append(pair)
    chosen = []
    for aid, options in by_artist.items():
        if len(options) == 1:
            chosen.extend(options)
        else:
            explicit = [p for p in options if source_ids[urlparse(p['wikiart']['url']).path.rsplit('/', 1)[-1]] == {aid}]
            if len(explicit) == 1:
                chosen.extend(explicit)
            else:
                ambiguous.append({'artist_id': aid, 'reason': 'Multiple artist profiles require review', 'options': options})
    chosen.sort(key=lambda p: (p['artist']['slug'] != 'frida-kahlo-q5588', p['artist']['display_name']))
    scope = {x['artist']['id']: x for x in baseline if x['gender'] and x['gender']['is_woman']}
    scope.update({p['artist']['id']: active[p['artist']['id']] for p in chosen})
    save(RUN / 'artist-matches.json', {'at': m.core.now(), 'matches': chosen, 'ambiguous': ambiguous,
        'source_women_not_matched_to_db': unmatched, 'scope': list(scope.values()),
        'known_women_without_profile_match': [x for aid, x in scope.items() if aid not in {p['artist']['id'] for p in chosen}]})
    print(json.dumps({'review_scope': len(scope), 'matched_artists': len(chosen), 'missing_women_flags': sum(not p['existing_woman_evidence'] for p in chosen),
        'ambiguous': len(ambiguous), 'known_women_without_profile': len(scope) - len(chosen)}), flush=True)


def select():
    inventory = json.loads((RUN / 'artist-matches.json').read_bytes())
    pairs = inventory['matches']
    # Metadata selection is bounded to the explicitly featured works on each
    # matched profile, with a hard maximum of twelve per existing artist.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        profiles = list(pool.map(c.profile_one, [p['wikiart'] for p in pairs]))
    with m.read_only() as db:
        excluded = {r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork'").fetchall()}
        reviews = []
        for pair, profile in zip(pairs, profiles):
            artist = pair['artist']
            works = c.artist_works(db, artist['id'])
            save(RUN / 'artwork-baselines' / (artist['id'] + '.json'), {'artist_id': artist['id'], 'works': works})
            # Direct source identifiers prevent duplicate records even when a
            # prior delivery preserved a different local-language title.
            pair = dict(pair, artist=dict(artist, selection_limit=12))
            c.select_one(pair, db, excluded)
            result = json.loads((RUN / 'discovery-v2' / (artist['id'] + '.json')).read_bytes())
            for match in result['matches']:
                match['selection_basis'] = 'Owner-requested review of every existing woman artist, beginning with Frida Kahlo; selected from explicit WikiArt famous-works, at most twelve additional works per artist; creation date ends by 1955.'
            # Preserve original selector evidence; the campaign-specific basis
            # is also pinned in the per-artist review ledger.
            reviews.append({'artist_id': artist['id'], 'name': artist['display_name'], 'slug': artist['slug'],
                'source_url': pair['wikiart']['url'], 'identity_basis': pair['identity_basis'],
                'existing_artworks': len(works), 'existing_images': sum(bool(w['primary_media_id']) for w in works),
                'profile_outcome': profile['outcome'], 'featured': len(profile['featured']),
                'eligible_featured': sum(bool(c.dated(w.get('year'))) for w in profile['featured']),
                'selected': len(result['matches']), 'held': result['held'],
                'missing_woman_evidence': not pair['existing_woman_evidence']})
    save(RUN / 'artist-review.json', {'at': m.core.now(), 'artists': reviews,
        'without_source': [{'id': x['artist']['id'], 'name': x['artist']['display_name'], 'status': x['artist']['status'],
            'outcome': 'No reconciled profile in complete WikiArt directory; existing catalogue retained'} for x in inventory['known_women_without_profile_match']]})
    matches = m.discovered_matches()
    save(RUN / 'discovered-v2.json', {'at': m.core.now(), 'matches': matches})
    print(json.dumps({'selected_images': len(matches), 'artists_with_selection': sum(r['selected'] > 0 for r in reviews),
        'reviewed_profiles': len(reviews), 'new_artworks': sum(bool(x['work'].get('new_record')) for x in matches)}), flush=True)


def prepare():
    configure_preparation()
    m.prepare()


def configure_preparation():
    c.configure_preparation()
    original = m.page_record
    def record(match, raw, receipt):
        result = original(match, raw, receipt)
        result['selection_basis'] = match.get('women_selection_basis') or 'Owner-requested review of every existing woman artist, beginning with Frida Kahlo; selected from explicit WikiArt famous-works, at most twelve additional works per artist; creation date ends by 1955.'
        return result
    m.page_record = record


def prepare_frida():
    configure_preparation()
    matches = [x for x in m.discovered_matches() if x['work']['artist']['slug'] == 'frida-kahlo-q5588']
    for match in matches:
        m.prepare_one(match)


def identity_review():
    candidates = []
    for match in m.discovered_matches():
        w = match['work']
        if not w.get('new_record'):
            continue
        rows = json.loads((RUN / 'artwork-baselines' / (w['artist']['id'] + '.json')).read_bytes())['works']
        title = m.norm(re.sub(r'\([^)]*\)', '', w['title']))
        possible = []
        for row in rows:
            if row['status'] == 'archived' or row['creation_year_start'] is None or row['creation_year_end'] is None:
                continue
            if row['creation_year_end'] < w['creation_year_start'] or row['creation_year_start'] > w['creation_year_end']:
                continue
            for candidate in (row['title'], row.get('alternate_title')):
                if not candidate:
                    continue
                other = m.norm(re.sub(r'\([^)]*\)', '', candidate))
                score = difflib.SequenceMatcher(None, title, other).ratio()
                if title == other or (min(len(title), len(other)) >= 10 and score >= 0.78):
                    possible.append({'id': row['artwork_id'], 'title': row['title'], 'date': row['date_display'],
                        'has_image': bool(row['primary_media_id']), 'score': score, 'identifiers': row['identifiers']})
                    break
        if possible:
            candidates.append({'artwork_id': w['artwork_id'], 'artist': w['artist']['display_name'], 'title': w['title'],
                'year': w['date_display'], 'source_url': match['wikiart']['url'], 'candidates': possible})
    save(RUN / 'near-title-identity-review.json', candidates)
    print(json.dumps(candidates, ensure_ascii=False, indent=2), flush=True)


def replace_evidence(path, value):
    raw = m.core.encode(value)
    if path.exists() and path.read_bytes() == raw:
        return
    if path.exists():
        save(RUN / 'selection-history' / path.relative_to(RUN), path.read_bytes())
    path.write_bytes(raw)


def reconcile_selection():
    near = json.loads((RUN / 'near-title-identity-review.json').read_bytes())
    distinct = {'5131f18f-1cc1-56b8-bdf5-b0c102a88ebe', '51078828-460d-5b21-bf2c-57fc0c55fffe',
        '28182018-d7b3-5d72-a0ec-6945de9cf4a7', '007fb5c1-c7b1-5356-9270-b1b66819981f',
        '1e7ffe22-41f9-5179-b9bd-18440e4110c4', '0365ecd1-85ef-59fa-acdb-d3aa78e11466'}
    frida_old = 'b99f4796-e5f2-5a7e-b302-0ec64cbe5da4'
    held = {x['artwork_id']: x for x in near if x['artwork_id'] not in distinct | {frida_old}}
    for path in sorted((RUN / 'discovery-v2').glob('*.json')):
        row = json.loads(path.read_bytes())
        matches = []
        for match in row['matches']:
            aid = match['work']['artwork_id']
            if aid in held:
                row['held'].append({'url': match['wikiart']['url'], 'reason': 'Near-title existing object requires exact reproduction/edition reconciliation; no duplicate created',
                    'identity_review': held[aid]})
            elif aid != frida_old:
                matches.append(match)
            else:
                works = json.loads((RUN / 'artwork-baselines' / path.name).read_bytes())['works']
                existing = next(w for w in works if w['artwork_id'] == '0937efc0-ef41-4356-b409-e90bdb2eeafc')
                work = dict(existing, artist=match['work']['artist'], alternate_title='The Two Fridas')
                matches.append(dict(match, work=work, women_selection_basis='Existing Museo de Arte Moderno record: WikiArt explicitly names The Two Fridas / Las Dos Fridas, 1939, at the same museum. Preserve existing title, museum claim and review state; attach image without creating a second artwork.'))
                for folder in ('images', 'selected'):
                    old = RUN / folder / (aid + '.json')
                    if old.exists():
                        dest = RUN / 'selection-history' / folder / old.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        old.rename(dest)
        if row['artist']['slug'] == 'frida-kahlo-q5588':
            aid = 'af813a28-f384-4a07-8460-bde984fc2847'
            if not any(x['work']['artwork_id'] == aid for x in matches):
                works = json.loads((RUN / 'artwork-baselines' / path.name).read_bytes())['works']
                work = dict(next(w for w in works if w['artwork_id'] == aid), artist=row['artist'], alternate_title='My Grandparents, My Parents, and I (Family Tree)')
                url = 'https://www.wikiart.org/en/frida-kahlo/my-grandparents-my-parents-and-me-1936'
                raw, receipt = Fetcher().get(url)
                soup = c.BeautifulSoup(raw, 'html.parser')
                source = json.loads(soup.select_one('.wiki-layout-painting-info-bottom[ng-init]')['ng-init'].split('=', 1)[1].strip())
                assert source['year'] == '1936' and source['artistUrl'] == '/en/frida-kahlo'
                matches.append({'work': work, 'wikiart': {'url': url, 'title': source['title'], 'year': 1936, 'source_id': source['_id']},
                    'index_receipt': receipt, 'selection_basis': 'Existing catalogue record with documented MoMA object 78784; selected image gap.',
                    'women_selection_basis': 'Existing catalogue record carrying MoMA object 78784, accession 102.1976: same artist, 1936 creation date and full Family Tree title on WikiArt. Preserve unvalidated museum metadata and review state.'})
        row['matches'] = matches
        replace_evidence(path, row)
    replace_evidence(RUN / 'discovered-v2.json', {'matches': m.discovered_matches(), 'identity_review': 'near-title-identity-review.json'})
    save(RUN / 'identity-review-decisions.json', {'held': list(held.values()), 'distinct_subjects_or_numbered_objects': sorted(distinct),
        'frida_reconciled': {'source_candidate': frida_old, 'existing_artwork': '0937efc0-ef41-4356-b409-e90bdb2eeafc'},
        'frida_existing_family_tree_selected': 'af813a28-f384-4a07-8460-bde984fc2847'})
    print('Final selection', len(m.discovered_matches()), 'near-title holds', len(held), flush=True)


def deliver_frida():
    bucket = m.storage.Client(project='artline-508319', credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    dsns = {'local': 'postgres://localhost/artline', 'cloud': m.core.cloud_dsn()}
    dbs = {t: m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) for t, dsn in dsns.items()}
    try:
        for path in sorted((RUN / 'images').glob('*.json')):
            if json.loads(path.read_bytes())['artist_slug'] == 'frida-kahlo-q5588':
                c.deliver_one(path, dbs, bucket)
    finally:
        for db in dbs.values():
            db.close()
    save(RUN / 'frida-delivery-finished.json', {'at': m.core.now()})
    c.sync_selection(finished_marker='frida-delivery-finished.json', output_marker='frida-selection-finished.json')


def deliver():
    c.deliver_ready()
    c.sync_selection()


def sync_remaining():
    c.sync_selection(output_marker='personal-selection-final.json')


def apply_artist_reviews():
    pairs = json.loads((RUN / 'artist-matches.json').read_bytes())['matches']
    if (RUN / 'supplemental-artist-matches.json').exists():
        pairs += json.loads((RUN / 'supplemental-artist-matches.json').read_bytes())['matches']
    directory = json.loads((RUN / 'female-directory.json').read_bytes())
    directory_receipts = {}
    for receipt in directory['receipts']:
        data = json.loads((RUN / 'captures' / (m.core.sha(receipt['url'].encode()) + '.body')).read_bytes())
        for row in data['Artists']:
            directory_receipts[row['id']] = receipt
    counts = {}
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        totals = collections.Counter()
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            sid_before = db.execute("SELECT to_jsonb(s) record FROM sources s WHERE slug='women-wikiart-20260920'").fetchall()
            backup = m.BACKUP / 'artist-reviews' / (target + '-source-before.json')
            if not backup.exists():
                save(backup, sid_before)
            sid = db.execute("""INSERT INTO sources(slug,name,source_type,base_url)
                VALUES('women-wikiart-20260920','WikiArt women artists review — 20 September 2026','collection_page','https://www.wikiart.org/en/female-artists')
                ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""").fetchone()['id']
            for pair in pairs:
                artist = pair['artist']
                path = RUN / 'artist-applications' / target / (artist['id'] + '.json')
                if path.exists():
                    prior = json.loads(path.read_bytes())
                    totals[prior['outcome']] += 1
                    totals['women_evidence_added'] += prior.get('women_evidence_added', False)
                    continue
                slug = urlparse(pair['wikiart']['url']).path.rsplit('/', 1)[-1]
                profile = json.loads((RUN / 'profiles' / (slug + '.json')).read_bytes())
                if profile['outcome'] != 'inspected':
                    raise ValueError('Cannot cite an uninspected profile')
                with db.transaction():
                    row = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE slug=%s FOR SHARE', (artist['slug'],)).fetchone()
                    if not row or m.norm(row['record']['display_name']) != m.norm(artist['display_name']) or row['record']['status'] == 'archived':
                        result = {'outcome': 'held_target_identity', 'slug': artist['slug']}
                    else:
                        before = row['record']
                        gender = db.execute('SELECT to_jsonb(g) record FROM artist_gender_evidence g WHERE artist_id=%s', (before['id'],)).fetchone()
                        citations = db.execute("SELECT to_jsonb(c) record FROM citations c WHERE entity_type='artist' AND entity_id=%s AND source_id=%s", (before['id'], sid)).fetchall()
                        backup = m.BACKUP / 'artist-reviews' / target / path.name
                        save(backup, {'artist': before, 'gender': gender, 'citations': citations})
                        evidence = {'identity_basis': pair['identity_basis'], 'profile_receipt': profile['receipt'],
                            'source_name': profile['name'], 'directory_entry': pair['female_directory_entry'],
                            'directory_receipt': directory_receipts.get((pair['female_directory_entry'] or {}).get('id')),
                            'scope': 'Existing artist identity reviewed against WikiArt; biography, lifespan, publication and holdings preserved.'}
                        added = False
                        if gender is None and pair['female_directory_entry']:
                            entry = pair['female_directory_entry']
                            db.execute("""INSERT INTO artist_gender_evidence(artist_id,is_woman,basis,source_url,source_record_id,source_checksum,evidence_json,checked_at)
                                VALUES(%s,true,%s,%s,%s,%s,%s,%s)""", (before['id'], 'WikiArt explicitly includes the reconciled artist in its Female artists directory; no inference from name or appearance.',
                                'https://www.wikiart.org/en/female-artists', entry['id'], m.core.sha(m.core.encode(evidence)), m.Jsonb(evidence), directory_receipts[entry['id']]['checked_at']))
                            added = True
                        elif gender is not None and not gender['record']['is_woman']:
                            raise ValueError('Conflicting gender evidence preserved for separate review')
                        if not citations:
                            db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                                VALUES('artist',%s,%s,'wikiart_woman_artist_review',%s,%s,%s,%s,%s)""", (before['id'], sid, slug, pair['wikiart']['url'],
                                json.dumps(evidence, ensure_ascii=False), profile['receipt']['checked_at'], m.ACTOR))
                        after = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s', (before['id'],)).fetchone()['record']
                        if after != before:
                            raise ValueError('Artist metadata changed during evidence-only review')
                        result = {'outcome': 'review_evidence_added', 'artist_id': before['id'], 'slug': artist['slug'],
                            'women_evidence_added': added, 'artist_unchanged': True, 'backup': str(backup),
                            'backup_sha256': m.core.sha(backup.read_bytes()), 'at': m.core.now()}
                save(path, result)
                totals[result['outcome']] += 1
                totals['women_evidence_added'] += result.get('women_evidence_added', False)
            counts[target] = dict(totals)
            print('Artist reviews', target, dict(totals), flush=True)
    save(RUN / ('artist-review-application-summary-' + str(len(pairs)) + '.json'), counts)


def reconcile_artists():
    inventory = json.loads((RUN / 'artist-matches.json').read_bytes())
    targets = {'Valentine Hugo': ('Q3553651', 'valentine-hugo'), 'Leonor Fini': ('Q464011', 'leonor-fini'),
        'Rosalba Carriera': ('Q237726', 'rosalba-carriera')}
    female = {x['artistUrl']: x for x in json.loads((RUN / 'female-directory.json').read_bytes())['artists']}
    pairs = []
    for row in inventory['known_women_without_profile_match']:
        artist = row['artist']
        if artist['display_name'] not in targets:
            continue
        qid, slug = targets[artist['display_name']]
        assert any(e['scheme'] == 'wikidata' and e['external_id'] == qid for e in row['identifiers'])
        path = RUN / 'identity-authorities' / (qid + '.json')
        if not path.exists():
            url = 'https://www.wikidata.org/wiki/Special:EntityData/' + qid + '.json'
            response = m.requests.get(url, timeout=(15, 40), headers={'User-Agent': 'Artline/1.0 selected artist identity research'})
            response.raise_for_status()
            assert len(response.content) <= 5_000_000
            save(path, {'url': url, 'checked_at': m.core.now(), 'sha256': m.core.sha(response.content), 'data': response.json()})
        entity = json.loads(path.read_bytes())['data']['entities'][qid]
        wikiart_ids = [x['mainsnak'].get('datavalue', {}).get('value') for x in entity['claims'].get('P6002', []) if x.get('rank') != 'deprecated']
        assert slug in wikiart_ids, (qid, wikiart_ids)
        entry = female['/en/' + slug]
        source = {'url': 'https://www.wikiart.org/en/' + slug, 'name': entry['title'], 'life_display': entry['year']}
        pair = {'artist': artist, 'wikiart': source, 'existing_woman_evidence': True, 'female_directory_entry': entry,
            'identity_basis': 'Existing Wikidata ' + qid + ' explicitly links WikiArt P6002=' + slug + '. Lifespan disagreement retained; no birth/death metadata overwritten.',
            'identity_capture': str(path)}
        profile = c.profile_one(source)
        with m.read_only() as db:
            works = c.artist_works(db, artist['id'])
            save(RUN / 'artwork-baselines' / (artist['id'] + '.json'), {'artist_id': artist['id'], 'works': works})
            excluded = {r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork'").fetchall()}
            c.select_one(dict(pair, artist=dict(artist, selection_limit=12)), db, excluded)
        pairs.append(pair)
    save(RUN / 'supplemental-artist-matches.json', {'matches': pairs, 'basis': 'Explicit identifier reconciliation of three lifespan conflicts'})
    print('Reconciled', len(pairs), 'artist identities with lifespan disagreements preserved', flush=True)


def select_existing():
    collection_id = str(c.uuid.uuid5(c.uuid.NAMESPACE_URL, 'https://artline.local/personal-artwork-collection'))
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        added = 0
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            sid = db.execute("SELECT id FROM sources WHERE slug='women-wikiart-20260920'").fetchone()['id']
            for path in sorted((RUN / 'delivery').glob('*.json')):
                im = json.loads((RUN / 'images' / path.name).read_bytes())
                result = json.loads(path.read_bytes())['targets'][target]
                if im['work'].get('new_record') or result['outcome'] not in ('attached', 'already_attached'):
                    continue
                out = RUN / 'existing-selections' / target / path.name
                if out.exists():
                    continue
                aid = result['after']['id']
                with db.transaction():
                    row = db.execute('SELECT to_jsonb(a) record,artline_has_selection_evidence(a.id) selected FROM artworks a WHERE id=%s', (aid,)).fetchone()
                    before = row['record']
                    if row['selected']:
                        receipt = {'artwork_id': aid, 'action': 'existing_selection_preserved'}
                    else:
                        assert before['creation_year_end'] <= 1955 and before['status'] != 'archived'
                        collection = db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE', (collection_id,)).fetchone()['record']
                        assert collection['curator_kind'] == 'owner' and collection['institution_id'] is None
                        backup = m.BACKUP / 'existing-selections' / target / path.name
                        save(backup, {'artwork': before, 'collection': collection, 'items': db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE artwork_id=%s', (aid,)).fetchall()})
                        db.execute("""INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                            SELECT %s,%s,coalesce(max(position),0)+1,%s,%s,%s,%s FROM curated_collection_items WHERE collection_id=%s
                            ON CONFLICT(collection_id,artwork_id) DO NOTHING""", (collection_id, aid,
                            'Owner-selected historical artwork in the requested women-artists WikiArt review; personal selection, without validating a museum holding or changing editorial publication.',
                            sid, im['page'], im['checked_at'], collection_id))
                        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s', (collection_id,))
                        after = db.execute('SELECT to_jsonb(a) record,artline_has_selection_evidence(a.id) selected FROM artworks a WHERE id=%s', (aid,)).fetchone()
                        assert after['record'] == before and after['selected']
                        receipt = {'artwork_id': aid, 'action': 'personal_selection_added', 'backup': str(backup), 'backup_sha256': m.core.sha(backup.read_bytes())}
                        added += 1
                save(out, dict(receipt, at=m.core.now()))
        print('Existing image selections', target, added, flush=True)


def frida_verify():
    results = {}
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            works = db.execute("""SELECT a.id::text,a.title,a.status,ma.storage_path,ma.checksum_sha256,ma.byte_size,
                ma.source_page_url,artline_has_selection_evidence(a.id) selected
                FROM artists p JOIN artwork_artists aa ON aa.artist_id=p.id JOIN artworks a ON a.id=aa.artwork_id
                LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE p.slug='frida-kahlo-q5588' AND a.status<>'archived' ORDER BY a.id""").fetchall()
        assert len(works) == 10 and all(w['storage_path'] and w['byte_size'] <= 100000 and w['status'] == 'review' for w in works)
        results[target] = works
    for work in results['cloud']:
        response = m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app' + work['storage_path'], timeout=(15, 40))
        assert response.status_code == 200 and m.core.sha(response.content) == work['checksum_sha256']
        api = m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/artists/frida-kahlo-q5588/works/' + work['id'], timeout=(15, 40))
        assert api.status_code == 200 and api.json()['media_url'] == work['storage_path']
        work['public_image_and_api_verified'] = True
    save(RUN / 'frida-verification.json', {'at': m.core.now(), 'databases': results, 'errors': []})
    print('Frida verified: ten illustrated review artworks in each database; all ten public images and artwork API responses passed', flush=True)


def verify_women_filter():
    pairs = [p for p in json.loads((RUN / 'artist-matches.json').read_bytes())['matches'] if not p['existing_woman_evidence']]
    def check(pair):
        artist = pair['artist']
        response = m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/painters/options',
            params={'women': 'true', 'popular': 'false', 'q': artist['display_name']}, timeout=(15, 40))
        data = response.json() if response.status_code == 200 else {}
        return {'artist_id': artist['id'], 'slug': artist['slug'], 'http_status': response.status_code,
            'verified': any(x['slug'] == artist['slug'] for x in data.get('items', []))}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, pairs))
    save(RUN / 'public-women-filter-verification.json', {'at': m.core.now(), 'checks': rows, 'errors': [r for r in rows if not r['verified']]})
    print('New women-filter memberships verified through public API', sum(r['verified'] for r in rows), 'of', len(rows), flush=True)
    if not all(r['verified'] for r in rows):
        raise SystemExit(1)


def inspect_target_identity():
    aid = '66da1733-02b6-41fd-9c3f-b5b3330c0e85'
    im = json.loads((RUN / 'images' / (aid + '.json')).read_bytes())
    with m.read_only(m.core.cloud_dsn()) as db:
        artist = db.execute('SELECT id FROM artists WHERE slug=%s', (im['artist_slug'],)).fetchone()
        works = c.artist_works(db, artist['id'])
    save(RUN / 'gwen-john-target-candidates.json', {'local_work': im['work'], 'cloud_works': works})
    print(json.dumps({'local': {k: im['work'].get(k) for k in ('title', 'date_display', 'identifiers', 'institution')},
        'cloud': [{k: w.get(k) for k in ('artwork_id', 'title', 'date_display', 'primary_media_id', 'identifiers', 'institution')}
            for w in works if 'nude' in w['title'].casefold()]}, ensure_ascii=False), flush=True)


def resolve_target_identity():
    aid = '66da1733-02b6-41fd-9c3f-b5b3330c0e85'
    output = RUN / 'target-identity-resolutions' / (aid + '.json')
    if output.exists():
        return
    im = json.loads((RUN / 'images' / (aid + '.json')).read_bytes())
    with m.psycopg.connect(m.core.cloud_dsn(), autocommit=True, row_factory=m.dict_row) as db:
        candidates = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE slug=%s', (im['work']['slug'],)).fetchall()
        assert len(candidates) == 1
        before = candidates[0]['record']
        assert before['id'] == '09b120c8-90f0-4805-b03b-79b936a7aa6e' and before['primary_media_id'] is None
        assert m.same_artwork(before, im['work']['before_record'])
        creators = db.execute('SELECT p.slug,aa.attribution_role FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=%s', (before['id'],)).fetchall()
        assert creators == [{'slug': im['artist_slug'], 'attribution_role': 'primary'}]
        backup = m.BACKUP / 'target-identity-resolutions' / (aid + '.json')
        save(backup, {'artwork': before, 'creators': creators, 'local_original': im['work']['before_record']})
        outcome = m.attach(db, im, before)
        after = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (before['id'],)).fetchone()['record']
        result = {'outcome': outcome, 'created': False, 'before_attachment': before, 'after': after,
            'identity_basis': 'Identical deterministic research-candidate slug, artist, title, date range, dimensions, medium and every non-operational artwork field; only UUID and import/update timestamps differ.',
            'backup': str(backup), 'backup_sha256': m.core.sha(backup.read_bytes())}
        save(output, result)
    for folder in ('applied/cloud', 'delivery'):
        path = RUN / folder / (aid + '.json')
        previous = json.loads(path.read_bytes())
        replacement = result if folder.startswith('applied/') else dict(previous, targets={**previous['targets'], 'cloud': result})
        save(RUN / 'target-identity-history' / folder / path.name, previous)
        temporary = path.with_suffix('.replacement')
        temporary.write_bytes(m.core.encode(replacement))
        temporary.replace(path)
    print('Gwen John Nude Girl attached to the existing production identity', flush=True)


def title_contact_sheet():
    from PIL import Image, ImageOps, ImageDraw
    sheets = []
    images = {p.stem: json.loads(p.read_bytes()) for p in (RUN / 'images').glob('*.json')}
    with m.read_only() as db:
        for path in sorted((RUN / 'delivery').glob('*.json')):
            result = json.loads(path.read_bytes())['targets']['local']
            if result['outcome'] != 'held' or result['reason'] != 'Title already exists in target':
                continue
            plan = json.loads((RUN / 'delivery-plans' / path.name).read_bytes())
            im = images[path.stem]
            ids = plan['targets']['local']['ids']
            peers = db.execute('SELECT a.id::text,a.title,a.date_display,ma.storage_path,ma.checksum_sha256,ma.source_page_url FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])', (ids,)).fetchall()
            sheets.append({'held_id': path.stem, 'artist': im['artist'], 'title': im['title'], 'date': im['work']['date_display'],
                'path': im['path'], 'sha256': im['sha256'], 'source': im['page'], 'peers': peers})
    if not sheets:
        return
    canvas = Image.new('RGB', (1200, 330 * len(sheets)), 'white')
    draw = ImageDraw.Draw(canvas)
    for n, group in enumerate(sheets):
        items = [{'storage_path': group['path'], 'title': 'HELD ' + group['title'], 'date_display': group['date']}]+group['peers']
        for j, item in enumerate(items[:4]):
            data = ROOT / 'apps/web/public' / item['storage_path'].lstrip('/')
            thumb = ImageOps.contain(Image.open(data).convert('RGB'), (290, 260))
            canvas.paste(thumb, (j * 300, n * 330))
            draw.text((j * 300 + 3, n * 330 + 264), str(n + 1) + ' ' + group['artist'][:33], fill='black')
            draw.text((j * 300 + 3, n * 330 + 281), item['title'][:40], fill='black')
            draw.text((j * 300 + 3, n * 330 + 298), str(item['date_display']), fill='black')
    filename = 'same-title-review-' + str(len(sheets)) + '-' + m.core.sha(m.core.encode(sheets))[:8]
    save(RUN / (filename + '.json'), sheets)
    canvas.save('/tmp/artline-women-' + filename + '.jpg', quality=88)
    print('/tmp/artline-women-' + filename + '.jpg', flush=True)


def resolve_titles():
    decisions = json.loads((RUN / 'reviewed-title-decisions.json').read_bytes())
    for aid, decision in decisions.items():
        im = json.loads((RUN / 'images' / (aid + '.json')).read_bytes())
        save(RUN / 'title-identity-resolutions' / (aid + '.json'), {'image_sha256': im['sha256'],
            'distinct_from': decision['distinct_from'], 'basis': decision['basis'], 'visual_review': decision['visual_review']})
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            for aid, decision in decisions.items():
                filename = aid + '.json'
                output = RUN / 'resolved-titles' / target / filename
                im = json.loads((RUN / 'images' / filename).read_bytes())
                if output.exists():
                    result = json.loads(output.read_bytes())
                else:
                    state = c.target_before(db, im)
                    assert state['outcome'] == 'create', state
                    backup = m.BACKUP / 'resolved-titles' / target / filename
                    save(backup, state)
                    result = c.apply_image(db, im, state)
                    assert result['outcome'] == 'attached'
                    result.update(backup=str(backup), backup_sha256=m.core.sha(backup.read_bytes()), visual_review=decision)
                    save(output, result)
                for folder in ('applied/' + target, 'delivery'):
                    path = RUN / folder / filename
                    previous = json.loads(path.read_bytes())
                    replacement = result if folder.startswith('applied/') else dict(previous, targets={**previous['targets'], target: result})
                    if previous == replacement:
                        continue
                    save(RUN / 'title-resolution-history' / target / folder / filename, previous)
                    temporary = path.with_suffix('.replacement')
                    temporary.write_bytes(m.core.encode(replacement))
                    temporary.replace(path)
                print('Visually resolved', target, im['artist'], im['title'], flush=True)


def verify():
    c.verify()


def report():
    inventory = json.loads((RUN / 'artist-matches.json').read_bytes())
    pairs = inventory['matches'] + json.loads((RUN / 'supplemental-artist-matches.json').read_bytes())['matches']
    paired = {p['artist']['id']: p for p in pairs}
    scope = {x['artist']['id']: x['artist'] for x in inventory['scope']}
    images = {p.stem: json.loads(p.read_bytes()) for p in (RUN / 'images').glob('*.json')}
    receipts = [json.loads(p.read_bytes()) for p in (RUN / 'delivery').glob('*.json')]
    discoveries = {p.stem: json.loads(p.read_bytes()) for p in (RUN / 'discovery-v2').glob('*.json')}
    final_matches = m.discovered_matches()
    final_path = RUN / 'final-selected.json'
    if not final_path.exists():
        save(final_path, {'matches': final_matches, 'scope': 'Existing women artists only; at most twelve additional WikiArt featured works per artist, plus Frida existing-record image gaps.'})
    for receipt in receipts:
        plan = json.loads((RUN / 'delivery-plans' / (receipt['artwork_id'] + '.json')).read_bytes())
        assert m.core.sha(Path(plan['backup']).read_bytes()) == plan['backup_sha256']
        im = images[receipt['artwork_id']]
        assert im['work']['creation_year_end'] <= 1955
        assert im['work']['artist']['id'] in scope
        assert im['page_receipt']['sha256'] == m.core.sha((RUN / 'captures' / (m.core.sha(im['page_receipt']['url'].encode()) + '.body')).read_bytes())
    checks, errors = {}, []
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            actual = db.execute("""SELECT p.id::text,p.slug,p.display_name,p.status,g.is_woman,
                stats.artworks,stats.images
                FROM artists p LEFT JOIN artist_gender_evidence g ON g.artist_id=p.id
                LEFT JOIN LATERAL(SELECT count(*) artworks,count(a.primary_media_id) images
                  FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
                  WHERE aa.artist_id=p.id AND a.status<>'archived') stats ON true
                WHERE p.slug=ANY(%s) ORDER BY p.slug""", ([a['slug'] for a in scope.values()],)).fetchall()
            byslug = {x['slug']: x for x in actual}
            for aid, artist in scope.items():
                row = byslug.get(artist['slug'])
                if row is None:
                    errors.append({'target': target, 'artist_id': aid, 'error': 'Scope artist missing in target'})
                elif row['is_woman'] is not True:
                    errors.append({'target': target, 'artist_id': aid, 'error': 'Woman evidence missing'})
            reviewed = 0
            for path in (RUN / 'artist-applications' / target).glob('*.json'):
                receipt = json.loads(path.read_bytes())
                if receipt['outcome'] != 'review_evidence_added':
                    errors.append({'target': target, 'error': 'Artist review held', 'receipt': receipt})
                    continue
                raw = Path(receipt['backup']).read_bytes()
                assert m.core.sha(raw) == receipt['backup_sha256']
                before = json.loads(raw)['artist']
                current = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s', (before['id'],)).fetchone()['record']
                if current != before:
                    errors.append({'target': target, 'artist_id': before['id'], 'error': 'Artist metadata changed'})
                citation = db.execute("""SELECT count(*) n FROM citations ci JOIN sources s ON s.id=ci.source_id
                    WHERE ci.entity_type='artist' AND ci.entity_id=%s AND s.slug='women-wikiart-20260920'""", (before['id'],)).fetchone()['n']
                if citation != 1:
                    errors.append({'target': target, 'artist_id': before['id'], 'error': 'Review citation count differs'})
                reviewed += 1
            attached = [r for r in receipts if r['targets'][target]['outcome'] in ('attached', 'already_attached')]
            ids = [r['targets'][target]['after']['id'] for r in attached]
            missing_selections = db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[]) AND NOT artline_has_selection_evidence(id)', (ids,)).fetchall()
            if missing_selections:
                errors.append({'target': target, 'error': 'Updated images lack collection selection', 'rows': missing_selections})
            checks[target] = {'artists': actual, 'review_citations_checked': reviewed, 'scope_artists': len(actual),
                'scope_women': sum(x['is_woman'] is True for x in actual), 'image_attachments': len(attached),
                'new_review_artworks': sum(bool(r['targets'][target].get('created')) for r in attached),
                'attachment_holds': [dict(artwork_id=r['artwork_id'], **r['targets'][target]) for r in receipts if r['targets'][target]['outcome'] == 'held']}
            # Identical delivered JPEGs under multiple object identities need
            # explicit review, even when WikiArt assigned separate source IDs.
            shared = db.execute("""SELECT ma.checksum_sha256,jsonb_agg(jsonb_build_object('artwork_id',a.id,'title',a.title,'source_url',ma.source_page_url)) artworks
                FROM media_assets ma JOIN artworks a ON a.primary_media_id=ma.id
                WHERE ma.checksum_sha256=ANY(%s) AND a.status<>'archived'
                GROUP BY ma.checksum_sha256 HAVING count(*)>1""", ([im['sha256'] for im in images.values()],)).fetchall()
            checks[target]['shared_image_hashes'] = shared
    rows = []
    for aid, artist in sorted(scope.items(), key=lambda x: x[1]['display_name']):
        pair = paired.get(aid)
        discovery = discoveries.get(aid, {})
        delivered = [r for r in receipts if images[r['artwork_id']]['work']['artist']['id'] == aid]
        row = {'artist_id': aid, 'artist': artist['display_name'], 'slug': artist['slug'],
            'wikiart_profile': pair['wikiart']['url'] if pair else '',
            'review_outcome': 'WikiArt profile reviewed' if pair else 'No reconciled WikiArt profile in complete directory',
            'selected_candidates': len(discovery.get('matches', [])), 'selection_identity_holds': len(discovery.get('held', []))}
        for target in ('local', 'cloud'):
            actual = next((x for x in checks[target]['artists'] if x['slug'] == artist['slug']), {})
            row[target + '_new_images'] = sum(r['targets'][target]['outcome'] in ('attached', 'already_attached') for r in delivered)
            row[target + '_total_images'] = actual.get('images')
            row[target + '_total_artworks'] = actual.get('artworks')
        rows.append(row)
    with (RUN / 'all-women-review.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {'at': m.core.now(), 'scope_women': len(scope), 'profiles_reviewed': len(pairs),
        'without_reconciled_profile': len(scope) - len(pairs), 'missing_women_flags_added': 147,
        'prepared': len(images), 'uploaded': len(receipts), 'artists_with_new_images': sum(r['local_new_images'] > 0 for r in rows),
        'bytes': sum(im['bytes'] for im in images.values()), 'max_bytes': max(im['bytes'] for im in images.values()),
        'rights_labels': dict(collections.Counter(im['rights_status'] for im in images.values())),
        'preparation_holds': [json.loads(p.read_bytes()) for p in (RUN / 'prepare-held').glob('*.json')],
        'databases': checks, 'errors': errors}
    save(RUN / ('completion-audit-' + str(int(c.time.time())) + '.json'), result)
    print(json.dumps({k: v for k, v in result.items() if k != 'databases'}, ensure_ascii=False), flush=True)
    for target, value in checks.items():
        print(target, {k: len(v) if isinstance(v, list) else v for k, v in value.items()}, flush=True)
    if errors:
        raise SystemExit(1)


def annotate_source_duplicates():
    images = [json.loads(p.read_bytes()) for p in (RUN / 'images').glob('*.json')]
    hashes = list({im['sha256'] for im in images})
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            groups = db.execute("""SELECT ma.checksum_sha256,jsonb_agg(jsonb_build_object('artwork_id',a.id,'title',a.title,'source_url',ma.source_page_url)) artworks
                FROM media_assets ma JOIN artworks a ON a.primary_media_id=ma.id
                WHERE ma.checksum_sha256=ANY(%s) AND a.status<>'archived'
                GROUP BY ma.checksum_sha256 HAVING count(*)>1""", (hashes,)).fetchall()
            sid = db.execute("SELECT id FROM sources WHERE slug='women-wikiart-20260920'").fetchone()['id']
            for group in groups:
                digest = group['checksum_sha256']
                output = RUN / 'source-duplicate-evidence' / target / (digest + '.json')
                if output.exists():
                    continue
                with db.transaction():
                    ids = [x['artwork_id'] for x in group['artworks']]
                    before = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
                    citations = db.execute("SELECT to_jsonb(c) record FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_id=%s", (ids, sid)).fetchall()
                    backup = m.BACKUP / 'source-duplicate-evidence' / target / (digest + '.json')
                    save(backup, {'artworks': before, 'citations': citations})
                    for row in group['artworks']:
                        exists = db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='wikiart_shared_reproduction_review'", (row['artwork_id'], sid)).fetchone()
                        if not exists:
                            db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                                VALUES('artwork',%s,%s,'wikiart_shared_reproduction_review',%s,%s,%s,%s,%s)""", (row['artwork_id'], sid, digest,
                                row['source_url'], json.dumps({'finding': 'These separate source records reproduce identical delivered image bytes. They are probable source duplicates or an identity conflict, not evidence of distinct compositions. Supplied source titles and identifiers retained for editorial reconciliation.',
                                    'members': group['artworks'], 'sha256': digest}, ensure_ascii=False), m.core.now(), m.ACTOR))
                    after = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
                    assert {x['record']['id']: x for x in before} == {x['record']['id']: x for x in after}
                save(output, {'group': group, 'backup': str(backup), 'backup_sha256': m.core.sha(backup.read_bytes()), 'at': m.core.now()})
            print('Shared source reproductions documented', target, len(groups), flush=True)


def link_duplicate_source():
    candidate = 'f3629708-7f8d-50c5-aa16-755e6f61d0d2'
    existing_id = '1901330c-2ee2-54e0-a0a8-575dd4f4dbcc'
    im = json.loads((RUN / 'images' / (candidate + '.json')).read_bytes())
    decision = json.loads((RUN / 'held-source-duplicates.json').read_bytes())
    for target, dsn in [('local', 'postgres://localhost/artline'), ('cloud', m.core.cloud_dsn())]:
        output = RUN / 'duplicate-source-mapping' / (target + '.json')
        if output.exists():
            continue
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            with db.transaction():
                before = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (existing_id,)).fetchone()['record']
                assert before['title'] == im['title'] and before['creation_year_start'] == 1914 and before['primary_media_id']
                creator = db.execute('SELECT p.slug FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=%s', (existing_id,)).fetchall()
                assert creator == [{'slug': im['artist_slug']}]
                identifiers = db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=%s", (existing_id,)).fetchall()
                sid = db.execute("SELECT id FROM sources WHERE slug='women-wikiart-20260920'").fetchone()['id']
                citations = db.execute("SELECT to_jsonb(c) record FROM citations c WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s", (existing_id, sid)).fetchall()
                backup = m.BACKUP / 'duplicate-source-mapping' / (target + '.json')
                save(backup, {'artwork': before, 'identifiers': identifiers, 'citations': citations})
                prior = db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=%s", (im['source_id'],)).fetchall()
                assert not prior or prior == [{'entity_id': existing_id}]
                # The catalogue intentionally permits one identifier per
                # entity/scheme. Retain the canonical ID and record this source
                # variant as a citation with its own source_record_id.
                db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                    VALUES('artwork',%s,%s,'wikiart_same_composition_source_variant',%s,%s,%s,%s,%s)""", (existing_id, sid, im['source_id'], im['page'],
                    json.dumps({'decision': decision, 'uploaded_variant_path': im['path'], 'image_sha256': im['sha256'],
                        'action': 'Additional source ID retained in a source-variant citation on the existing composition; canonical external ID, original primary image and artwork metadata preserved.'}, ensure_ascii=False), im['checked_at'], m.ACTOR))
                after = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s', (existing_id,)).fetchone()['record']
                assert after == before
                assert db.execute("SELECT count(*) n FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='wikiart_same_composition_source_variant' AND source_record_id=%s", (existing_id, sid, im['source_id'])).fetchone()['n'] == 1
            save(output, {'candidate': candidate, 'existing_artwork_id': existing_id, 'source_id': im['source_id'], 'backup': str(backup),
                'backup_sha256': m.core.sha(backup.read_bytes()), 'mapping_kind': 'source_variant_citation', 'at': m.core.now()})
        print('Duplicate source linked without another artwork record', target, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['audit', 'directory', 'directory_pages', 'match_artists', 'select', 'identity_review', 'reconcile_selection', 'reconcile_artists', 'prepare', 'prepare_frida', 'deliver_frida', 'apply_artist_reviews', 'select_existing', 'frida_verify', 'verify_women_filter', 'inspect_target_identity', 'resolve_target_identity', 'title_contact_sheet', 'resolve_titles', 'deliver', 'sync_remaining', 'verify', 'report', 'annotate_source_duplicates', 'link_duplicate_source'])
    args = parser.parse_args()
    globals()[args.phase]()
