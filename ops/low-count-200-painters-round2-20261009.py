#!/usr/bin/env python3
"""Second, separately sampled low-count painter expansion; production only."""
import argparse
import collections
import concurrent.futures
import copy
import datetime
import fcntl
import functools
import csv
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time
import uuid
import requests
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('low_count_base', ROOT/'ops/low-count-200-painters-20261008.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
m, r, q, s = b.m, b.r, b.q, b.s
OP = 'low-count-200-painters-round2-20261009'
PLAN_SCHEMA = 6
RUN = ROOT/'docs/research'/OP
BACKUP = Path.home()/'Library/Application Support/Artline/backups'/OP
PREVIOUS = ROOT/'docs/research/low-count-200-painters-20261008'
b.OP = m.OP = OP
b.RUN = m.RUN = s.RUN = r.RUN = q.RUN = RUN
b.BACKUP = m.BACKUP = s.BACKUP = BACKUP
r.PORT = 55529
USER_AGENT = 'ArtlineCatalogue/1.0 (https://artlines.org; selected source-backed museum metadata research)'
ENTITY_WRITE_LOCK = threading.Lock()
spec = importlib.util.spec_from_file_location('nordic_fields', ROOT/'ops/nordic-museums-20261008.py')
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)
spec = importlib.util.spec_from_file_location('nordic_duplicates', ROOT/'ops/nordic-1000-20261008.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def capture(url, params=None, tag='captures'):
    """Identified public metadata access, with immutable receipts and access-stop."""
    prepared = requests.Request('GET', url, params=params).prepare().url
    key = r.sha(prepared.encode()); path = RUN/tag/(key+'.json'); body = path.with_suffix('.body.gz')
    if path.exists():
        receipt = r.load(path); raw = gzip.decompress(body.read_bytes())
        assert r.sha(raw) == receipt['sha256']
        recovery = RUN/'access-resumes'/(prepared.split('/')[2]+'.json')
        if receipt['status'] == 429 and recovery.exists():
            retry = r.load(recovery)
            if retry['url'] == prepared and retry['status'] == 200:
                raw = gzip.decompress((ROOT/retry['body_path']).read_bytes())
                assert r.sha(raw) == retry['sha256']
                return raw, retry
        if receipt['status'] >= 500 and not tag.endswith('-retry-1'):
            time.sleep(8)
            return capture(url, params, tag+'-retry-1')
        return raw, receipt
    host = prepared.split('/')[2]
    stop = RUN/'access-stops'/(host+'.json')
    resumed = RUN/'access-resumes'/(host+'.json')
    assert not (RUN/'access-stops'/(host+'-repeated.json')).exists(), 'Repeated source restriction: '+host
    assert not stop.exists() or resumed.exists(), 'Source stopped: '+host
    # One shared schedule across this operation's processes: 20 requests/min,
    # one tenth of the provider's documented compliant-bot rate. The stable
    # User-Agent identifies Artline with its full project/contact URL.
    if host.endswith('wikidata.org'):
        with open('/tmp/artline-low-count-round2-wikimedia-rate.lock', 'a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); lock.seek(0)
            last = float(lock.read() or '0'); scheduled = max(time.time(), last+3)
            lock.seek(0); lock.truncate(); lock.write(str(scheduled)); lock.flush()
            fcntl.flock(lock, fcntl.LOCK_UN)
        time.sleep(max(0, scheduled-time.time()))
    for attempt in range(2):
        try:
            response = requests.get(prepared, headers={'User-Agent': USER_AGENT}, timeout=(15, 60))
            break
        except (requests.Timeout, requests.ConnectionError, requests.exceptions.ChunkedEncodingError):
            if attempt: raise
            time.sleep(8)
    raw = response.content
    assert len(raw) < 20_000_000
    body.parent.mkdir(parents=True, exist_ok=True); body.write_bytes(gzip.compress(raw, mtime=0))
    receipt = dict(url=prepared, final_url=response.url, status=response.status_code, retrieved_at=r.now(), bytes=len(raw), sha256=r.sha(raw), body_path=str(body.relative_to(ROOT)),
                   headers={key:response.headers.get(key) for key in ['Retry-After', 'Date', 'Content-Type', 'ETag']})
    r.save(path, receipt)
    if response.status_code in (403, 429):
        if resumed.exists():
            r.save(RUN/'access-stops'/(host+'-repeated.json'), receipt)
        elif not stop.exists(): r.save(stop, receipt)
        raise RuntimeError('Source access restriction; stop '+host)
    return raw, receipt


def resume_source():
    """One exact-endpoint retry, only after the provider's explicit backoff."""
    path = RUN/'access-stops/query.wikidata.org.json'; stop = r.load(path)
    assert stop['status'] == 429
    message = gzip.decompress((ROOT/stop['body_path']).read_bytes()).decode()
    match = re.search(r'retry in (\d+) seconds', message, re.I)
    assert match, 'No provider retry guidance'
    elapsed = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(stop['retrieved_at'].replace('Z', '+00:00'))).total_seconds()
    assert elapsed >= int(match[1])+2, 'Provider backoff has not elapsed'
    proof = RUN/'access-resumes/query.wikidata.org.json'
    assert not proof.exists() and not (RUN/'access-stops/query.wikidata.org-repeated.json').exists()
    url = stop['url']; response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=(15, 60))
    raw = response.content; body = RUN/'provider-backoff-retry.body.gz'; body.write_bytes(gzip.compress(raw, mtime=0))
    receipt = dict(at=r.now(), url=url, status=response.status_code, provider_wait_seconds=int(match[1]), actual_wait_seconds=elapsed,
                   sha256=r.sha(raw), body_path=str(body.relative_to(ROOT)), next_access='Single worker and bounded object-index requests; aggregate research queries stopped.')
    r.save(RUN/'provider-backoff-retry.json', receipt)
    assert response.status_code == 200, 'Retry did not succeed; source remains stopped'
    r.save(proof, receipt)
    print('Provider-guided retry succeeded after', round(elapsed), 'seconds; continuing only bounded source indexes', flush=True)


def resume_api():
    stop = r.load(RUN/'access-stops/www.wikidata.org.json')
    assert stop['status'] == 429
    elapsed = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(stop['retrieved_at'].replace('Z', '+00:00'))).total_seconds()
    assert elapsed >= 600, 'Conservative ten-minute API backoff has not elapsed'
    proof = RUN/'access-resumes/www.wikidata.org.json'
    assert not proof.exists() and not (RUN/'access-stops/www.wikidata.org-repeated.json').exists()
    response = requests.get(stop['url'], headers={'User-Agent': USER_AGENT}, timeout=(15, 60))
    raw = response.content; body = RUN/'provider-backoff-api-retry.body.gz'; body.write_bytes(gzip.compress(raw, mtime=0))
    receipt = dict(url=stop['url'], final_url=response.url, status=response.status_code, retrieved_at=r.now(), bytes=len(raw),
                   sha256=r.sha(raw), body_path=str(body.relative_to(ROOT)), actual_wait_seconds=elapsed,
                   headers={key:response.headers.get(key) for key in ['Retry-After', 'Date', 'Content-Type', 'ETag']},
                   provider_guidance='https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits',
                   compliance='Same public endpoint and client purpose. Added the provider-required full contact URL to the stable User-Agent and a global 8-second request interval; no credential, address or endpoint rotation. Previous response headers were not retained, so a conservative 600-second pause was used.')
    r.save(RUN/'provider-backoff-api-retry.json', receipt)
    assert response.status_code == 200, 'API retry failed; source remains stopped'
    r.save(proof, receipt)
    print('API retry succeeded after', round(elapsed), 'seconds; shared eight-second request pacing', flush=True)


def wd_counts():
    assert not (RUN/'access-resumes/query.wikidata.org.json').exists(), 'Aggregate queries stopped after provider backoff; use saved discovery results'
    ps = r.load(RUN/'low-count-audit.json.gz')['painters']
    qs = sorted({e['external_id'] for p in ps for e in p['identifiers'] if e['scheme'] == 'wikidata'})
    groups = [qs[i:i+300] for i in range(0, len(qs), 300)]
    def one(group):
        key = r.sha('|'.join(group).encode())
        dest = RUN/'wd-counts'/(key+'.json')
        if dest.exists(): return r.load(dest)
        query = 'SELECT ?artist (COUNT(DISTINCT ?work) AS ?count) WHERE { hint:Query hint:optimizer "None" . VALUES ?artist { '+ ' '.join('wd:'+q for q in group) + ''' } ?work wdt:P170 ?artist; wdt:P195 ?museum .
          } GROUP BY ?artist HAVING(COUNT(DISTINCT ?work)>=20)'''
        raw, receipt = capture('https://query.wikidata.org/sparql', dict(query=query, format='json'), 'wd-query-captures')
        assert receipt['status'] == 200
        out = dict(qids=group, receipt=receipt, rows=json.loads(raw)['results']['bindings'])
        r.save(dest, out); time.sleep(8)
        return out
    results = []; errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(one, group): group for group in groups}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try: results += future.result()['rows']
            except requests.RequestException as exc:
                errors.append(dict(qids=futures[future], reason=type(exc).__name__))
            print('Museum-connected artist counts', i, '/', len(groups), 'candidates', len(results), 'transport errors', len(errors), flush=True)
    r.save(RUN/'wd-counts.json', dict(at=r.now(), queried_painters=len(qs), rows=results, transport_errors=errors,
           discovery_scope='Collection-connected objects; preliminary cached groups additionally restrict common painting/drawing/print types. Object types, dates and evidence are checked from full entities before selection.'))


def entities(ids, tag):
    result = {}
    pending = []
    for qid in sorted(set(ids)):
        path = RUN/'entities'/tag/(qid+'.json.gz')
        if path.exists(): result[qid] = r.load(path)
        else: pending.append(qid)
    for start in range(0, len(pending), 50):
        part = pending[start:start+50]
        raw, receipt = capture('https://www.wikidata.org/w/api.php', dict(action='wbgetentities', ids='|'.join(part), props='labels|aliases|claims|descriptions', format='json'), 'wd-entity-captures')
        assert receipt['status'] == 200
        data = json.loads(raw)
        assert 'entities' in data and set(data['entities']) == set(part)
        for key, entity in data['entities'].items():
            item = dict(entity=entity, receipt=receipt)
            dest = RUN/'entities'/tag/(key+'.json.gz')
            with ENTITY_WRITE_LOCK:
                if not dest.exists(): r.save_gz(dest, item)
                result[key] = r.load(dest)
    return result


def creator_review(pair, source):
    e = source['entity']; a = pair['artist']
    if 'missing' in e or n.vals(e, 'P31') != [{'entity-type': 'item', 'numeric-id': 5, 'id': 'Q5'}]:
        return 'Source is not an unambiguous individual human'
    names = {q.norm(v['value']) for v in e.get('labels', {}).values()}
    names.update(q.norm(v['value']) for vs in e.get('aliases', {}).values() for v in vs)
    if not names.intersection(q.norm(v) for v in [a['display_name']]+pair['aliases']):
        return 'Catalogue authority link has no exact source name or alias agreement'
    for key, prop in [('birth_year', 'P569'), ('death_year', 'P570')]:
        years = {int(v['time'][1:5]) for v in n.vals(e, prop) if isinstance(v, dict) and re.match(r'^\+\d{4}-', v.get('time', '')) and v.get('precision', 0) >= 9}
        if a.get(key) is not None and years and a[key] not in years:
            return 'Creator lifespan conflict: '+key
    occupations = {v['id'] for v in n.vals(e, 'P106') if isinstance(v, dict)}
    # The existing catalogue contains many creative professions. This batch
    # requires an explicit painter occupation on the linked creator authority.
    if 'Q1028181' not in occupations:
        return 'No explicit painter occupation on the source creator authority'
    return None


def wd_research():
    ps = r.load(RUN/'low-count-audit.json.gz')['painters']
    byqid = collections.defaultdict(list)
    for p in ps:
        for e in p['identifiers']:
            if e['scheme'] == 'wikidata': byqid[e['external_id']].append(p)
    counts = {}
    for path in sorted((RUN/'wd-counts').glob('*.json')):
        for item in r.load(path)['rows']:
            counts[item['artist']['value'].rsplit('/', 1)[-1]] = int(item['count']['value'])
    choices = sorted(qid for qid in counts if len(byqid[qid]) == 1)
    creators = entities(choices, 'creators')
    accepted = []; held = []
    for qid in choices:
        reason = creator_review(byqid[qid][0], creators[qid])
        if reason: held.append(dict(qid=qid, artist=byqid[qid][0]['artist']['display_name'], reason=reason))
        else: accepted.append(qid)
    r.save(RUN/'creator-review'/(r.sha('|'.join(choices).encode())+'.json'), dict(accepted=accepted, held=held))
    # Investigate stronger source inventories first, to avoid spending requests
    # on a 20-object index that cannot absorb any duplicate/version exclusions.
    accepted.sort(key=lambda qid: (-counts[qid], qid))
    print('Verified painter authorities', len(accepted), 'held', len(held), flush=True)
    def group_job(job):
        start, group = job
        missing = [qid for qid in group if not (RUN/'wd-indexes'/(qid+'.json')).exists()]
        if missing:
            parts = []
            for qid in missing:
                parts.append('''{ { SELECT DISTINCT ?work WHERE { ?work wdt:P170 wd:'''+qid+'''; wdt:P195 ?museum .
                  } LIMIT 80 } BIND(wd:'''+qid+''' AS ?artist) }''')
            query = 'SELECT ?artist ?work WHERE { '+' UNION '.join(parts)+' }'
            try:
                raw, receipt = capture('https://query.wikidata.org/sparql', dict(query=query, format='json'), 'wd-query-captures')
            except requests.RequestException as exc:
                r.save(RUN/'transport-holds'/(r.sha(query.encode())+'.json'), dict(qids=missing, reason=type(exc).__name__))
                print('Preserved transport hold for', len(missing), 'painters; continuing independent groups', flush=True)
                return
            if receipt['status'] != 200:
                r.save(RUN/'transport-holds'/(r.sha(query.encode())+'.json'), dict(qids=missing, receipt=receipt))
                print('Preserved source response', receipt['status'], 'for', len(missing), 'painters', flush=True)
                return
            bindings = json.loads(raw)['results']['bindings']
            for qid in missing:
                ids = [row['work']['value'].rsplit('/', 1)[-1] for row in bindings if row['artist']['value'].endswith('/'+qid)]
                r.save(RUN/'wd-indexes'/(qid+'.json'), dict(qid=qid, ids=ids, receipt=receipt, limit=80))
        work_ids = sorted({work for qid in group for work in r.load(RUN/'wd-indexes'/(qid+'.json'))['ids']})
        needed = [wid for wid in work_ids if not (RUN/'entities/works'/(wid+'.json.gz')).exists()]
        entities(needed, 'works')
        print(f'Bounded source research {min(start+5, len(accepted))} / {len(accepted)} painters; {len(work_ids)} museum-connected works in group', flush=True)
    # Two independent bounded groups share the same 20/min request schedule.
    # This overlaps network latency while staying below the documented three
    # concurrent-request maximum. Each group is captured once under the same
    # stable client identity. Stop queued groups immediately on source failure.
    stop = threading.Event()
    def safe_job(job):
        if stop.is_set() or (RUN/'research-sufficient.json').exists(): return
        try: return group_job(job)
        except BaseException:
            stop.set()
            raise
    jobs = [(start, accepted[start:start+5]) for start in range(0, len(accepted), 5)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(safe_job, jobs))


def museum_crosswalk():
    records = r.load(RUN/'institution-context.json')['rows']
    byqid = collections.defaultdict(list)
    for record in records:
        if record['wikidata_id'] and record['kind'] == 'museum': byqid[record['wikidata_id']].append(record)
    wanted = sorted({v['id'] for path in (RUN/'entities/works').glob('*.json.gz') for v in n.vals(r.load(path)['entity'], 'P195') if isinstance(v, dict) and v.get('id') not in byqid})
    needed = [qid for qid in wanted if not (RUN/'entities/museum-leads'/(qid+'.json.gz')).exists()]
    entities(needed, 'museum-leads')
    source = {path.name.split('.')[0]: r.load(path) for path in (RUN/'entities/museum-leads').glob('*.json.gz')}
    parents = {v['id'] for item in source.values() for v in n.vals(item['entity'], 'P361') if isinstance(v, dict)}
    needed = sorted(qid for qid in parents if qid not in source and qid not in byqid)
    entities(needed, 'museum-leads')
    source.update({path.name.split('.')[0]: r.load(path) for path in (RUN/'entities/museum-leads').glob('*.json.gz')})
    domain = lambda url: (urlsplit(url or '').hostname or '').lower().removeprefix('www.')
    same_domain = lambda a,b: bool(a and b and (a == b or a.endswith('.'+b) or b.endswith('.'+a)))
    namekey = lambda value: q.norm(value).removeprefix('the ')
    property_evidence = entities(['P539'], 'properties')['P539']
    assert n.label(property_evidence['entity']) == 'Museofile ID'
    mapped = {}; held = []
    for qid, matches in byqid.items():
        if len(matches) == 1: mapped[qid] = dict(record=matches[0], source_qid=qid, basis='Exact existing institution Wikidata authority', receipts=[])
    for qid, item in source.items():
        entity = item['entity']
        if n.active(entity, 'P576'): continue
        names = {namekey(x['value']) for x in entity.get('labels', {}).values()} | {namekey(x['value']) for xs in entity.get('aliases', {}).values() for x in xs}
        domains = {domain(url) for url in n.vals(entity, 'P856') if isinstance(url, str)} - {''}
        matches = [record for record in records if record['kind'] == 'museum' and namekey(record['name'].split(' — ')[0]) in names and any(same_domain(domain(record['website_url']), host) for host in domains)]
        if len(matches) == 1 and not matches[0]['wikidata_id']:
            mapped[qid] = dict(record=matches[0], source_qid=qid, basis='Exact source label/alias plus matching official website domain; unique active catalogue museum. Existing institution is preserved without changing its missing authority field.', receipts=[item['receipt']])
        official_ids = {value for value in n.vals(entity, 'P539') if isinstance(value, str) and re.fullmatch(r'M\d{4}', value)}
        official_matches = [record for record in records if record['kind'] == 'museum' and record['country_code'] == 'FR' and any(record['website_url'] == 'https://pop.culture.gouv.fr/notice/museo/'+value for value in official_ids)]
        if len(official_matches) == 1 and not official_matches[0]['wikidata_id']:
            mapped[qid] = dict(record=official_matches[0], source_qid=qid,
                 basis='Exact French Ministry of Culture Museofile identifier in the source authority and the existing museum record official government URL. Names and locality remain preserved; no institution rewrite.',
                 receipts=[item['receipt'], property_evidence['receipt']])
    # Individually reviewed legacy labels include their city and country in the
    # name but have no website. Require both the exact source museum alias and
    # explicit source country and locality evidence; similar names are not enough.
    reviews = [
        ('Q238587', '106ebbde-3796-5981-8eeb-f249bfb16252', 'National Portrait Gallery, London, UK', 'Q145', 'London'),
        ('Q162111', 'd901207e-e514-5881-af04-03b72355640b', 'Alte Nationalgalerie, Berlin, Germany', 'Q183', 'Berlin'),
        ('Q1499958', '4ab04afb-dcb4-5e34-98ad-b3fabfe5eb39', 'Gemeentemuseum den Haag, Hague, Netherlands', 'Q55', 'The Hague'),
    ]
    for qid, iid, expected_name, country, city in reviews:
        if qid not in source: continue
        item = source[qid]; entity = item['entity']
        matches = [record for record in records if record['id'] == iid and record['name'] == expected_name and record['kind'] == 'museum' and not record['wikidata_id']]
        names = {namekey(x['value']) for x in entity.get('labels', {}).values()} | {namekey(x['value']) for xs in entity.get('aliases', {}).values() for x in xs}
        assert len(matches) == 1 and namekey(expected_name.split(',')[0]) in names
        assert country in {value['id'] for value in n.vals(entity, 'P17') if isinstance(value, dict)}
        assert city in entity.get('descriptions', {}).get('en', {}).get('value', '')
        mapped[qid] = dict(record=matches[0], source_qid=qid,
             basis='Individually reviewed exact museum name or historical alias with matching explicit country and locality in the source authority and legacy catalogue label. No institution field changes.',
             receipts=[item['receipt']])
    for qid, item in source.items():
        if qid in mapped or n.active(item['entity'], 'P576'): continue
        kinds = {v['id'] for v in n.vals(item['entity'], 'P31') if isinstance(v, dict)}
        parent_claims = n.active(item['entity'], 'P361')
        if 'Q7328910' in kinds and len(parent_claims) == 1 and not parent_claims[0].get('qualifiers'):
            parent = n.value(parent_claims[0])
            if isinstance(parent, dict) and parent.get('id') in mapped:
                base = mapped[parent['id']]
                mapped[qid] = dict(record=base['record'], source_qid=qid, parent_qid=parent['id'],
                       basis='Explicit art-collection part-of statement to the verified museum authority. Original collection/department label and parent relationship preserved; no branch or display inference.',
                       receipts=[item['receipt']]+base['receipts'])
        if qid not in mapped: held.append(dict(qid=qid, name=n.label(item['entity']), reason='No exact museum authority or unique name-and-official-domain match; institution not created or inferred'))
    fingerprint = r.sha(json.dumps(mapped, sort_keys=True).encode())
    path = RUN/'museum-crosswalks'/(fingerprint+'.json')
    if not path.exists(): r.save(path, dict(at=r.now(), mapped=mapped, held=held))
    print('Museum identity crosswalk', len(mapped), 'authorities,', sum(bool(x['receipts']) for x in mapped.values()), 'source-verified legacy/department mappings;', len(held), 'unresolved', flush=True)


def museum_map():
    paths = list((RUN/'museum-crosswalks').glob('*.json'))
    if paths:
        result = max((r.load(path)['mapped'] for path in paths), key=len)
    else:
        result = {}
        for record in r.load(RUN/'institution-authorities.json')['rows']:
            if record['wikidata_id'] and record['kind'] == 'museum':
                result[record['wikidata_id']] = dict(record=record, source_qid=record['wikidata_id'], basis='Exact existing museum authority', receipts=[])
    alias_path = RUN/'catalogue-consistency-precheck.json'
    if alias_path.exists():
        aliases = {row['id']:row for row in r.load(alias_path)['active_institution_aliases']}
        records = {row['id']:row for row in r.load(RUN/'institution-context.json')['rows']}
        for qid, match in list(result.items()):
            original = match['record']
            if original['id'] not in aliases: continue
            alias = aliases[original['id']]; canonical = records[alias['canonical_institution_id']]
            assert canonical['kind'] == 'museum' and canonical['status'] != 'archived'
            assert canonical['id'] not in aliases, 'Unexpected alias chain'
            result[qid] = dict(match, record=canonical, alias_record=original,
                  catalogue_alias=dict(mapping=alias, proof_path=str(alias_path.relative_to(ROOT)), proof_sha256=r.sha(alias_path.read_bytes())),
                  basis=match['basis']+' Follow the existing, previously reconciled catalogue alias to its canonical institution. Preserve both institution labels and the source authority; no institution edits.')
    return result


def source_date(entity):
    """Retain Wikidata year, decade, century and explicit range precision."""
    claims = n.active(entity, 'P571')
    if not claims: return dict(first=None, last=None, precision='unknown', date_display='Creation date unknown')
    if len(claims) != 1: raise ValueError('Multiple creation dates require review')
    claim = claims[0]; qualifiers = claim.get('qualifiers', {})
    if set(qualifiers)-{'P1319', 'P1326', 'P1480', 'P4241'}: raise ValueError('Creation date qualifier requires review')
    def one(prop):
        values = qualifiers[prop]
        if len(values) != 1 or values[0].get('snaktype') != 'value': raise ValueError('Nonunique date qualifier')
        return values[0]['datavalue']['value']
    circa = bool(qualifiers.get('P1480'))
    if circa and one('P1480').get('id') != 'Q5727902': raise ValueError('Non-circa date qualification requires review')
    late = bool(qualifiers.get('P4241'))
    if late and (one('P4241').get('id') != 'Q40719766' or set(qualifiers) != {'P4241'}):
        raise ValueError('Unreviewed date refinement')
    def interval(value):
        if not isinstance(value, dict) or value.get('calendarmodel') != 'http://www.wikidata.org/entity/Q1985727' or value.get('before') or value.get('after'):
            raise ValueError('Creation calendar or uncertainty requires review')
        match = re.fullmatch(r'\+(\d{4})-\d\d-\d\dT00:00:00Z', value.get('time', ''))
        if not match: raise ValueError('Unsupported source time')
        year = int(match[1]); precision = value.get('precision')
        if precision in (9, 10, 11): return year, year, 'exact', str(year)
        if precision == 8:
            first = year//10*10
            return first, first+9, 'decade', str(first)+'s'
        if precision == 7:
            century = (year+99)//100; first = (century-1)*100+1; last = century*100
            suffix = 'th' if century%100 in (11,12,13) else {1:'st',2:'nd',3:'rd'}.get(century%10,'th')
            return first, last, 'century', str(century)+suffix+' century'
        raise ValueError('Creation date precision requires review')
    if set(qualifiers).intersection({'P1319', 'P1326'}):
        if not {'P1319', 'P1326'} <= set(qualifiers): raise ValueError('One-sided date bound requires review')
        low = interval(one('P1319')); high = interval(one('P1326'))
        if low[0] != low[1] or high[0] != high[1]: raise ValueError('Imprecise range endpoint requires review')
        first, last, precision, display = low[0], high[1], 'range', str(low[0])+'–'+str(high[1])
        if n.value(claim) is not None:
            central = interval(n.value(claim))
            if central[1] < first or central[0] > last: raise ValueError('Main creation date and explicit range conflict')
    elif n.value(claim) is None and not qualifiers:
        return dict(first=None, last=None, precision='unknown', date_display='Creation date unknown')
    else: first, last, precision, display = interval(n.value(claim))
    if not 0 < first <= last <= 1970 or circa and last == 1970:
        raise ValueError('Creation date outside cutoff or crosses it')
    if circa: precision = 'circa' if first == last else 'circa_range'; display = 'c. '+display
    if late:
        if precision != 'century': raise ValueError('Late qualifier requires century precision')
        # Preserve the source century as broad bounds; never invent a start
        # year for the qualitative word "late".
        display = 'late '+display
    return dict(first=first, last=last, precision=precision, date_display=display)


BASE_TYPES = {'Q3305213':'painting', 'Q93184':'drawing', 'Q11060274':'print', 'Q18761202':'watercolor', 'Q860861':'sculpture', 'Q132137':'painting'}


def type_index():
    wanted = {v['id'] for path in (RUN/'entities/works').glob('*.json.gz') for v in n.vals(r.load(path)['entity'], 'P31') if isinstance(v, dict)}
    wanted.update(BASE_TYPES)
    for depth in range(4):
        entities(sorted(wanted), 'types')
        data = {path.name.split('.')[0]:r.load(path) for path in (RUN/'entities/types').glob('*.json.gz')}
        parents = {v['id'] for qid, item in data.items() if qid not in BASE_TYPES for v in n.vals(item['entity'], 'P279') if isinstance(v, dict)}
        pending = parents-set(data)-set(BASE_TYPES)
        if not pending: break
        wanted = pending
    print('Preserved type hierarchy evidence', len(data), 'entities', flush=True)
    for qid in sorted(BASE_TYPES): print(qid, n.label(data[qid]['entity']), BASE_TYPES[qid], flush=True)


def source_kind(entity, types):
    claims = n.active(entity, 'P31')
    if not claims or any(claim.get('qualifiers') or not isinstance(n.value(claim), dict) for claim in claims):
        return None
    if any(n.value(claim)['id'] in {'Q56055236', 'Q125191'} for claim in claims): return None
    def bases(qid, depth=0, seen=None):
        if qid in BASE_TYPES: return {BASE_TYPES[qid]}
        seen = (seen or set()) | {qid}
        if depth >= 4 or qid not in types: return set()
        result = set()
        for claim in n.active(types[qid]['entity'], 'P279'):
            value = n.value(claim)
            if not claim.get('qualifiers') and isinstance(value, dict) and value.get('id') not in seen:
                result.update(bases(value['id'], depth+1, seen))
        return result
    resolved = [bases(n.value(claim)['id']) for claim in claims]
    if any(not kinds for kinds in resolved): return None
    kinds = set.union(*resolved)
    if len(kinds) == 1: return next(iter(kinds))
    if 'watercolor' in kinds and kinds <= {'watercolor','drawing','painting'}: return 'watercolor'
    return 'unknown'  # Multiple explicit visual-art forms; retain original classes.


def has_holding_reference(claim):
    for reference in claim.get('references', []):
        for prop in ('P854', 'P248'):
            for snak in reference.get('snaks', {}).get(prop, []):
                if snak.get('snaktype', 'value') != 'value': continue
                value = snak.get('datavalue', {}).get('value')
                if prop == 'P854' and isinstance(value, str) and urlsplit(value).scheme in ('http', 'https') and urlsplit(value).hostname:
                    return True
                if prop == 'P248' and isinstance(value, dict) and re.fullmatch(r'Q\d+', value.get('id', '')):
                    return True
    return False


def source_rows(wanted=None):
    museums = museum_map()
    creators = {p.stem.removesuffix('.json'): r.load(p) for p in (RUN/'entities/creators').glob('*.json.gz')}
    types = {p.name.split('.')[0]:r.load(p) for p in (RUN/'entities/types').glob('*.json.gz')}
    byqid = collections.defaultdict(list)
    for pair in r.load(RUN/'low-count-audit.json.gz')['painters']:
        for e in pair['identifiers']:
            if e['scheme'] == 'wikidata': byqid[e['external_id']].append(pair)
    rows = []; held = []
    for path in sorted((RUN/'entities/works').glob('*.json.gz')):
        if wanted is not None and path.name.split('.')[0] not in wanted: continue
        item = r.load(path); entity = item['entity']; qid = entity['id']
        cq = n.vals(entity, 'P170'); mq = n.vals(entity, 'P195')
        reason = None
        if len(cq) != 1 or not isinstance(cq[0], dict) or len(byqid.get(cq[0].get('id'), [])) != 1:
            reason = 'No unique existing low-count creator authority'
        elif cq[0]['id'] not in creators or creator_review(byqid[cq[0]['id']][0], creators[cq[0]['id']]):
            reason = 'Painter identity not verified'
        elif not mq or any(not isinstance(v, dict) or v.get('id') not in museums for v in mq) or len({museums[v['id']]['record']['id'] for v in mq}) != 1:
            reason = 'Single documented museum identity unavailable in current catalogue'
        elif any(not n.qualified_holding(claim) for claim in n.active(entity, 'P195')):
            reason = 'Collection qualifier needs review'
        if reason:
            held.append(dict(qid=qid, reason=reason)); continue
        holding_claims = n.active(entity, 'P195')
        referenced = [claim for claim in holding_claims if has_holding_reference(claim)]
        if not referenced:
            held.append(dict(qid=qid, reason='Collection statement lacks source reference')); continue
        chosen_holding = (referenced or holding_claims)[0]
        painter_qid = cq[0]['id']; pair = byqid[painter_qid][0]; museum_qid = n.value(chosen_holding)['id']; match = museums[museum_qid]; museum = match['record']
        kinds = {v['id'] for v in n.vals(entity, 'P31') if isinstance(v, dict)}
        kind = source_kind(entity, types)
        if not kind:
            held.append(dict(qid=qid, reason='Object type or ensemble needs review', kinds=sorted(kinds))); continue
        try: dates = source_date(entity)
        except ValueError as exc:
            held.append(dict(qid=qid, reason=str(exc))); continue
        # Reuse the established date/attribution/collection validator. Its type
        # switch predates prints/watercolors; keep the unmodified source entity
        # as evidence and restore the explicitly checked source type below.
        parser_entity = copy.deepcopy(entity)
        # Multiple collection statements are accepted only when every explicit
        # collection/department resolves to the very same museum identity.
        # The full original claims remain in the citation and mapping evidence.
        parser_entity['claims']['P195'] = [copy.deepcopy(chosen_holding)]
        # Creation dates are normalized above, including source decade/century
        # precision and explicit earliest/latest bounds. No inferred lifespan.
        parser_entity['claims'].pop('P571', None)
        parser_entity['claims']['P31'] = [dict(rank='normal', mainsnak=dict(datavalue=dict(value=dict(id='Q93184', **{'entity-type':'item', 'numeric-id':93184}))))]
        row, reason = n.work_fields(parser_entity, dict(qid=museum_qid, institution_id=museum['id']), creators, item['receipt'])
        if row:
            row.update(dates)
            row['uncertainty'] = ['Creation date unknown; retained in review without inferred years.'] if dates['precision'] == 'unknown' else []
            row['work_type'] = kind
            row['object_form'] = 'icon' if 'Q132137' in kinds else None
            if re.fullmatch(r'Q\d+', row['title'] or ''): reason = 'Source has no actual artwork title'
            first = row['first']; a = pair['artist']
            if first is not None and ((a.get('birth_year') and row['last'] < a['birth_year']) or (a.get('death_year') and first > a['death_year'])):
                reason = 'Artwork date lies outside documented creator lifespan'
        if reason:
            held.append(dict(qid=qid, artist=pair['artist']['display_name'], reason=reason)); continue
        row.update(key='wikidata/'+qid, external_id=qid, source_scheme='wikidata', source_evidence=entity,
                   artist_ids=[pair['artist']['id']], artist_id=pair['artist']['id'], painter_qid=painter_qid,
                   source_id=qid, source_provider='wikidata', museum_name=museum['name'], museum_match=match,
                   source_collection_matches=[museums[v['id']] for v in mq], pair=pair, type_qids=sorted(kinds),
                   source_image_names=[v for v in n.vals(entity, 'P18') if isinstance(v, str)])
        row['confidence_basis'] = 'Explicit non-deprecated collection statements all resolve to one verified existing institution, with at least one source reference. Exact object and unqualified creator authority, compatible lifespan, supplied inventory and creation precision checked. Actual source is Wikidata; cited native pages were not independently verified. Editorial confidence, not a calibrated probability.'
        rows.append(row)
    return rows, held, creators


def object_urls(row):
    # The older Nordic checker knows its native museum IDs. This wider batch
    # also preserves explicit described-at URLs and WikiArt object identifiers.
    return sorted(set(d.object_urls(row)) | {url for url in row.get('native_urls', []) if urlsplit(url).scheme in ('http', 'https') and urlsplit(url).hostname})


def identity_inventories(row):
    values = set(row['inventories'])
    museum_qids = {match['source_qid'] for match in row.get('source_collection_matches', [])}
    museum_qids.update(match.get('parent_qid') for match in row.get('source_collection_matches', []) if match.get('parent_qid'))
    for claim in n.active(row['source_evidence'], 'P217'):
        qualifiers = claim.get('qualifiers', {})
        value = n.value(claim)
        if set(qualifiers) == {'P195'} and isinstance(value, str) and d.acc(value):
            scopes = qualifiers['P195']
            if scopes and all(snak.get('snaktype') == 'value' and snak.get('datavalue', {}).get('value', {}).get('id') in museum_qids for snak in scopes):
                values.add(value)
    return sorted(values)


def collision_reason(row, candidates):
    exact, allids, urls, inventories, titles, bycreator, creator_names = candidates.get('_lookups') or d.collision_lookups(candidates)
    matches = {identity for url in object_urls(row) for identity in urls[url]}
    matches.update(exact[(row['source_scheme'], row.get('external_id'))])
    if row['source_scheme'] == 'wikidata': matches.update(allids[row.get('external_id')])
    if matches: return 'Existing exact source identity', sorted(matches)
    artworks = {item['id']:item for item in candidates['artworks']}
    def distinct(wid):
        proof = identity_waivers().get((row.get('artwork_id'), wid))
        if not proof or wid not in artworks: return False
        expected = proof['expected_existing']
        return all(artworks[wid].get(k) == v for k,v in expected.items() if k != 'artist_ids') and bycreator[wid] == set(expected['artist_ids'])
    matches = {wid for inv in identity_inventories(row) for wid in inventories[(row['institution_id'], d.acc(inv))] if not distinct(wid)}
    if matches: return 'Existing institution inventory', sorted(matches)
    possible = {}
    for title in row['title_aliases']: possible.update(titles[d.norm(title)])
    for wid, art in possible.items():
        same = art['current_institution_id'] == row['institution_id'] or (row['artist_ids'] and bycreator[wid] == set(row['artist_ids'])) or (row['creator_label'] and (d.norm(art['unlinked_creator_label']) == d.norm(row['creator_label']) or d.norm(row['creator_label']) in creator_names[wid]))
        if same and not distinct(wid): return 'Possible existing title/creator version; withheld from new-object count', [wid]
    return None, []


@functools.lru_cache(maxsize=1)
def identity_waivers():
    path = RUN/'source-identity-review.json'
    if not path.exists(): return {}
    review = r.load(path)
    return {(item['artwork_id'],item['existing_id']):item for item in review['distinct_pairs']}


def collision_candidates(db, rows, progress=False):
    """Resolve indexed candidate IDs before fetching full artwork fields once.

    This preserves the established source/inventory/title collision semantics.
    Active title candidates already include all institutions; only archived
    museum-title candidates need a separate scoped lookup.
    """
    keys = sorted({d.norm(title) for row in rows for title in row['title_aliases']})
    mids = sorted({row['institution_id'] for row in rows})
    inventories = sorted({d.acc(value) for row in rows for value in identity_inventories(row)})
    museum_inventories = collections.defaultdict(set)
    for row in rows:
        museum_inventories[row['institution_id']].update(d.acc(value) for value in identity_inventories(row))
    extids = sorted({row['external_id'] for row in rows})
    urls = sorted({url for row in rows for url in object_urls(row)})
    external = [dict(item) for item in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))", (extids, urls))]
    citations = [dict(item) for item in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (urls,))]
    if progress: print('Duplicate check: source identifiers and citations complete', flush=True)
    ids = set()
    for part in d.m.chunks(mids, 5):
        ids.update(item['id'] for item in db.execute("SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status='archived' AND normalized_title=ANY(%s)", (part, keys)))
        scoped = sorted(set().union(*(museum_inventories[mid] for mid in part)))
        if scoped:
            nonnull = ' AND accession_number IS NOT NULL' if '' not in scoped else ''
            ids.update(item['id'] for item in db.execute("SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[])"+nonnull+" AND regexp_replace(lower(coalesce(accession_number,'')),'[^a-z0-9]','','g')=ANY(%s)", (part, scoped)))
    for part in d.m.chunks(keys, 250):
        ids.update(item['id'] for item in db.execute("SELECT id::text FROM artworks WHERE status<>'archived' AND normalized_title=ANY(%s)", (part,)))
    if progress: print('Duplicate check: institution inventories and titles resolved;', len(ids), 'existing candidate IDs', flush=True)
    artworks = []
    creators = []
    for part in d.m.chunks(sorted(ids), 1000):
        artworks.extend(dict(item) for item in db.execute('SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,unlinked_creator_label,status FROM artworks WHERE id=ANY(%s::uuid[])', (part,)))
        creators.extend(dict(item) for item in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name creator_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])', (part,)))
    result = dict(external=external, citations=citations, artworks=artworks, creators=creators)
    result['_lookups'] = d.collision_lookups(result)
    if progress: print('Duplicate check: existing object and creator details complete', flush=True)
    return result


def prepare():
    rows, held, creators = source_rows()
    fingerprint = r.sha((f'schema-{PLAN_SCHEMA}/'+r.now()+'/'+json.dumps(sorted((x['qid'], x['institution_id']) for x in rows))).encode())
    dest = RUN/'prepared'/(fingerprint+'.json.gz')
    if dest.exists():
        data = r.load(dest)
        print('Existing prepared source set', len(data['painters']), 'painters with 20+ additions', flush=True)
        return
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        collisions = collision_candidates(db, rows, progress=True)
        canonical = {str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikidata.org/entity/'+row['qid'])):row['qid'] for row in rows}
        existing_canonical = {canonical[item['id']]:item['id'] for item in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (list(canonical),))}
        artist_ids = sorted({x['artist_id'] for x in rows})
        linked = db.execute('''SELECT aa.artist_id::text,to_jsonb(a) artwork FROM artwork_artists aa
             JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])''', (artist_ids,)).fetchall()
    r.save_gz(RUN/'deduplication'/(fingerprint+'.json.gz'), {k:v for k,v in collisions.items() if k != '_lookups'})
    prior = collections.defaultdict(list)
    for x in linked: prior[x['artist_id']].append(x['artwork'])
    source_images = collections.defaultdict(set)
    inventories = collections.defaultdict(set)
    for row in rows:
        for im in row['source_image_names']: source_images[im].add(row['qid'])
        for inventory in row['inventories']: inventories[(row['institution_id'], d.acc(inventory))].add(row['qid'])
    accepted = collections.defaultdict(list)
    for row in rows:
        reason, matches = collision_reason(row, collisions)
        if not reason and row['qid'] in existing_canonical:
            reason = 'Existing deterministic source object ID'; matches = [existing_canonical[row['qid']]]
        if not reason and any(len(source_images[im]) > 1 for im in row['source_image_names']):
            reason = 'Multiple source entities share the same reproduction; object version unresolved'
        if not reason and any(len(inventories[(row['institution_id'], d.acc(inv))]) > 1 for inv in row['inventories']):
            reason = 'Multiple source entities share a museum inventory'
        if not reason:
            names = {q.norm(t) for t in row['title_aliases']}
            for work in prior[row['artist_id']]:
                old_names = {q.norm(t) for t in [work['title'], work['alternate_title']] if t}
                if names.intersection(old_names):
                    reason = 'Existing same-creator title or translation; retain for version review'; matches = [work['id']]; break
                if any(len(a) > 14 and len(z) > 14 and b.difflib.SequenceMatcher(None, a, z).ratio() >= .92 for a in names for z in old_names):
                    reason = 'Near-matching existing creator/title needs version review'; matches = [work['id']]; break
        if reason:
            held.append(dict(qid=row['qid'], artist=row['pair']['artist']['display_name'], reason=reason, existing=matches)); continue
        accepted[row['artist_id']].append(row)
    plans = []
    for aid, values in accepted.items():
        if len(values) < 20: continue
        pair = values[0]['pair']; pair['source'] = dict(url='https://www.wikidata.org/wiki/'+values[0]['painter_qid'], name=n.label(creators[values[0]['painter_qid']]['entity']))
        plans.append(dict(pair=pair, rows=values, profile=creators[values[0]['painter_qid']]))
    data = dict(at=r.now(), schema_version=PLAN_SCHEMA, painters=plans, held=held, source_rows=len(rows), fingerprint=fingerprint)
    r.save_gz(dest, data)
    print(json.dumps(dict(source_rows=len(rows), painters_with_20_additions=len(plans), holds=dict(collections.Counter(x['reason'] for x in held)))), flush=True)


def freeze():
    if (RUN/'cohort.json').exists():
        print('Preserving frozen sample', flush=True); return
    snapshots = [(path, r.load(path)) for path in (RUN/'prepared').glob('*.json.gz')]
    snapshots = [(path, data) for path, data in snapshots if data.get('schema_version') == PLAN_SCHEMA]
    path, data = max(snapshots, key=lambda p: p[1]['at'])
    prospects = data['painters']; ids = [p['pair']['artist']['id'] for p in prospects]
    previous = {p['artist']['id'] for p in r.load(PREVIOUS/'cohort.json')['painters']}
    with r.connect('production') as db:
        counts = db.execute('''SELECT ar.id::text,ar.status,count(DISTINCT a.id) n FROM artists ar
          LEFT JOIN artwork_artists aa ON aa.artist_id=ar.id
          LEFT JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
          WHERE ar.id=ANY(%s::uuid[]) GROUP BY ar.id''', (ids,)).fetchall()
    current = {x['id']:x for x in counts}; eligible = []
    for plan in prospects:
        aid = plan['pair']['artist']['id']; now = current[aid]
        if aid not in previous and now['status'] != 'archived' and 0 <= now['n'] <= 10:
            plan['pair']['count_at_selection'] = now['n']; eligible.append(plan)
    assert len(eligible) >= 200, 'Only '+str(len(eligible))+' fully verified eligible painters; continue research'
    seed = secrets.token_hex(16)
    chosen = sorted(eligible, key=lambda p: r.sha((seed+'/'+p['pair']['artist']['id']).encode()))[:200]
    type_evidence = {p.name.split('.')[0]:r.load(p) for p in (RUN/'entities/types').glob('*.json.gz')}
    r.save_gz(RUN/'type-review.json.gz', type_evidence)
    r.save(RUN/'sampling-frame.json', dict(at=r.now(), seed=seed, count=len(eligible),
          eligible_artist_ids=[p['pair']['artist']['id'] for p in eligible],
          prepared_evidence=str(path.relative_to(ROOT)), prepared_sha256=r.sha(path.read_bytes()),
          method='Uniform random ordering by SHA256(seed / artist UUID), without replacement, from fully source-verified low-count painters. Previous 200 excluded. No country or popularity weighting.',
          limitation='Bounded source-supported sampling frame, not a uniform sample of every low-count catalogue artist. Source indexes are discovery leads; entity statements and production duplicate checks determine eligibility.'))
    r.save(RUN/'cohort.json', dict(at=r.now(), seed=seed, painters=[p['pair'] for p in chosen]))
    r.save(RUN/'authorization.json', dict(at=r.now(), target='production',
          user_instruction='ok, pick 200 random painters that have 0-10 artworks and for each of them add at least 20-100 artworks',
          operation=OP, previous_batch_excluded=True, cohort_sha256=r.sha((RUN/'cohort.json').read_bytes()),
          agents_sha256=r.sha((ROOT/'AGENTS.md').read_bytes()),
          scope='20–100 new source-backed artwork records per selected painter. Review status and unknown fields preserved; referenced museum holdings separate from current display. No local database writes or image downloads.'))
    for rank, plan in enumerate(chosen, 1):
        plan['rank'] = rank
        plan['rows'] = sorted(plan['rows'], key=lambda row: (row['first'] is None, r.sha((seed+'/'+row['qid']).encode())))[:100]
        for row in plan['rows']:
            row.pop('pair', None)
            wid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikidata.org/entity/'+row['qid']))
            row.update(artwork_id=wid, source_id=row['qid'])
            row['work'] = dict(id=wid, slug='wikidata-'+row['qid'].lower(), title=row['title'], alternate_title=None,
                 normalized_title=q.norm(row['title']), date_display=row['date_display'], creation_year_start=row['first'],
                 creation_year_end=row['last'], date_precision=row['precision'], work_type=row['work_type'],
                 object_form=row['object_form'], medium_text=row['medium'], dimensions_text=row['dimensions'],
                 accession_number=row['accession'])
        plan['authorization_sha256'] = r.sha((RUN/'authorization.json').read_bytes())
        plan['type_review_sha256'] = r.sha((RUN/'type-review.json.gz').read_bytes())
        dest = RUN/'delivery-plans'/(plan['pair']['artist']['id']+'.json.gz')
        r.save_gz(dest, plan)
        r.save(RUN/'delivery-pins'/(plan['pair']['artist']['id']+'.json'), dict(sha256=r.sha(dest.read_bytes())))
    print('Frozen 200 painters from', len(eligible), 'verified candidates;', sum(len(p['rows']) for p in chosen), 'new artwork records planned', flush=True)


QUALIFIED_FILENAME = re.compile(r'\((?:attributed to|after|circle of|studio of|workshop of|follower of|school of|manner of|style of|formerly attributed to|imitator of|copy after|possibly|probably|and studio|and workshop)\)', re.I)


def deliveries(include_held=False):
    cohort = r.load(RUN/'cohort.json')['painters']
    review_path = RUN/'source-qualification-review.json'
    review = r.load(review_path) if review_path.exists() else None
    held = {row['artwork_id'] for row in review['held']} if review else set()
    identity_path = RUN/'source-identity-review.json'
    identity = r.load(identity_path) if identity_path.exists() and not include_held else None
    assert len(cohort) == len({p['artist']['id'] for p in cohort}) == 200
    for pair in cohort:
        aid = pair['artist']['id']; path = RUN/'delivery-plans'/(aid+'.json.gz')
        pin = r.load(RUN/'delivery-pins'/(aid+'.json'))['sha256']
        assert r.sha(path.read_bytes()) == pin
        plan = r.load(path)
        assert plan['pair'] == pair
        assert plan['authorization_sha256'] == r.sha((RUN/'authorization.json').read_bytes())
        assert plan['type_review_sha256'] == r.sha((RUN/'type-review.json.gz').read_bytes())
        if review and not include_held:
            plan['rows'] = [row for row in plan['rows'] if row['artwork_id'] not in held]
            plan['rows'].extend(item['row'] for item in review.get('supplements', []) if item['artist_id'] == aid)
            plan['qualification_review_sha256'] = r.sha(review_path.read_bytes())
            assert not any(QUALIFIED_FILENAME.search(name) for row in plan['rows'] for name in row['source_image_names'])
        if identity:
            excluded = {item['artwork_id'] for item in identity['held']}
            final_conflicts = RUN/'final-inventory-conflicts.json'
            if final_conflicts.exists(): excluded.update(item['artwork_id'] for item in r.load(final_conflicts))
            plan['rows'] = [row for row in plan['rows'] if row['artwork_id'] not in excluded]
            plan['rows'].extend(item['row'] for item in identity.get('supplements',[]) if item['artist_id'] == aid)
            for row in plan['rows']:
                if row['artwork_id'] in identity.get('row_notes',{}): row['identity_review_note'] = identity['row_notes'][row['artwork_id']]
            plan['identity_review_sha256'] = r.sha(identity_path.read_bytes())
            if final_conflicts.exists(): plan['final_inventory_conflicts_sha256'] = r.sha(final_conflicts.read_bytes())
        validate_plan(plan)
        yield plan, pin


def crawford_copy(plan):
    """One specifically reviewed copy: Crawford is its painter, not its model."""
    item = r.load(RUN/'entities/works/Q119157407.json.gz'); entity = item['entity']
    property_evidence = r.load(RUN/'entities/copy-review/P1877.json.gz')
    model = r.load(RUN/'entities/copy-review/Q18671748.json.gz')
    assert n.label(property_evidence['entity']) == 'after a work by'
    creator = n.active(entity, 'P170'); assert len(creator) == 1 and n.value(creator[0])['id'] == 'Q19672293'
    assert set(creator[0]['qualifiers']) == {'P1877'}
    qualifier = creator[0]['qualifiers']['P1877']; assert len(qualifier) == 1 and qualifier[0]['datavalue']['value']['id'] == 'Q18671748'
    assert n.vals(entity, 'P217') == ['1191'] and source_date(entity)['first'] == 1906
    assert n.vals(entity, 'P1679') == ['archibald-mclellan-17951854-83635']
    match = museum_map()['Q41661713']; museum = match['record']
    parser = copy.deepcopy(entity); parser['claims']['P170'][0].pop('qualifiers'); parser['claims']['P170'][0].pop('qualifiers-order', None)
    row, reason = n.work_fields(parser, dict(qid='Q41661713', institution_id=museum['id']), {'Q19672293':plan['profile']}, item['receipt'])
    assert not reason and 'after John Graham-Gilbert' in row['title']
    aid = plan['pair']['artist']['id']; wid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikidata.org/entity/'+entity['id']))
    row.update(key='wikidata/'+entity['id'], external_id=entity['id'], source_scheme='wikidata', source_evidence=entity,
         artist_ids=[aid], artist_id=aid, painter_qid='Q19672293', source_id=entity['id'], source_provider='wikidata',
         museum_name=museum['name'], museum_match=match, source_collection_matches=[match], type_qids=['Q3305213'],
         source_image_names=n.vals(entity, 'P18'), artwork_id=wid,
         creator_note='Robert Cree Crawford painted this 1906 copy after a work by John Graham Gilbert. The source explicitly qualifies P170 with P1877 (after a work by); this describes the model, not uncertainty about Crawford as the copyist. Museum inventory 1191 and Art UK object identifier retained. The copy is not merged with its model.',
         creator_copy_review=dict(after_qid='Q18671748', property_evidence=property_evidence, model_creator=model,
              decision='P1877 is an explicit derivative-work relationship, not a possible/attributed creator assertion. Preserve the source qualifier and the after-label in the artwork title; link only Crawford as the maker of this distinct copy.'))
    row['work'] = dict(id=wid, slug='wikidata-'+entity['id'].lower(), title=row['title'], alternate_title=None, normalized_title=q.norm(row['title']),
         date_display=row['date_display'], creation_year_start=row['first'], creation_year_end=row['last'], date_precision=row['precision'],
         work_type=row['work_type'], object_form=row['object_form'], medium_text=row['medium'], dimensions_text=row['dimensions'], accession_number=row['accession'])
    return row


def quality_review():
    original = list(deliveries(include_held=True)); held = []; counts = []; supplements = []
    for plan, pin in original:
        aid = plan['pair']['artist']['id']; exclusions = []
        for row in plan['rows']:
            flags = [name for name in row['source_image_names'] if QUALIFIED_FILENAME.search(name)]
            if flags:
                exclusions.append(row['artwork_id'])
                held.append(dict(artist_id=aid, artist=plan['pair']['artist']['display_name'], artwork_id=row['artwork_id'], qid=row['qid'], filenames=flags,
                     source_url=row['source_url'], source_receipt=row['receipt'], original_plan_sha256=pin,
                     creator_label=flags[0].split(' - ',1)[0], already_added=(RUN/'applied'/(aid+'.json')).exists(),
                     reason='Source image filename explicitly qualifies the creator despite an unqualified Wikidata creator statement. Conflicting evidence: withhold the painter link; do not assert a specific qualified role from a filename alone. No native-page verification claimed.'))
        count = len(plan['rows'])-len(exclusions)
        if count < 20:
            assert aid == 'a1e3013c-7b0b-50c8-9529-28172b2e83bd' and count == 19
            supplements.append(dict(artist_id=aid, row=crawford_copy(plan), original_plan_sha256=pin)); count += 1
        assert 20 <= count <= 100
        counts.append(dict(artist_id=aid, original=len(plan['rows']), held=len(exclusions), eligible=count))
    r.save(RUN/'source-qualification-review.json', dict(at=r.now(), held=held, counts=counts, supplements=supplements,
         original_plan_pins={p['pair']['artist']['id']:pin for p,pin in original},
         scope='Original cohort and source plans remain immutable. This pinned amendment excludes uncertain creator links and includes one separately source-reviewed Crawford copy to preserve the 20-new-work minimum. Already created uncertain works remain review records with exact source-level creator wording and no artist authority link.',
         native_access='Art UK returned 403 through the web tool; no attempt was made to bypass its restriction or claim its pages were independently verified.'))
    print('Qualified creator evidence:', len(held), 'withheld painter links;', sum(x['already_added'] for x in held), 'already-created records need correction;', sum(x['eligible'] for x in counts), 'eligible additions remain', flush=True)


def repair_attributions():
    review_path = RUN/'source-qualification-review.json'; review = r.load(review_path); digest = r.sha(review_path.read_bytes())
    selected = [row for row in review['held'] if row['already_added']]; ids = [row['artwork_id'] for row in selected]
    marker = m.uid('attribution-quality-correction'); sid = m.uid('source/wikidata'); actor = 'local-european-research'
    with r.connect('production', readonly=False) as db:
        with db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(2026100607)')
            prior = db.execute('SELECT after_json FROM audit_log WHERE id=%s', (marker,)).fetchone()
            if not prior:
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) FOR UPDATE', (ids,)).fetchall()
                before = s.snapshots(db, ids)
                assert len(before) == len(ids)
                r.save_gz(BACKUP/'attribution-correction-before.json.gz', before)
                for row in selected:
                    state = before[row['artwork_id']]; work = state['artwork']
                    assert work['status'] == 'review' and work['primary_media_id'] is None and not state['attachments']
                    assert len(state['creators']) == 1 and state['creators'][0]['artist_id'] == row['artist_id'] and state['creators'][0]['attribution_role'] == 'primary'
                    receipt = r.load(RUN/'applied'/(row['artist_id']+'.json'))
                    assert row['artwork_id'] in receipt['new_ids'] and receipt['plan_sha256'] == row['original_plan_sha256']
                    db.execute('DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role=%s', (row['artwork_id'], row['artist_id'], 'primary'))
                    db.execute('UPDATE artworks SET unlinked_creator_label=%s,description_md=%s,updated_by=%s WHERE id=%s',
                         (row['creator_label'], 'Creator attribution remains unresolved. The source image filename gives this qualified wording: '+row['creator_label']+'. The conflicting creator statements are retained for review.', actor, row['artwork_id']))
                    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,%s,%s,%s,%s,%s,%s)",
                         (m.uid('qualification/'+row['qid']), row['artwork_id'], sid, OP+'-qualified-creator-hold', row['qid'], row['source_url'], json.dumps(dict(qualification_review_sha256=digest, evidence=row), ensure_ascii=False), r.now(), actor))
                result = dict(at=r.now(), review_sha256=digest, artwork_ids=ids, records_retained_in_review=len(ids), artist_links_removed=len(ids), original_catalogue_records_changed=0)
                db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,before_json,after_json) VALUES(%s,%s,'source_qualification_correction','artwork',%s,%s,%s)", (marker, actor, ids[0], m.Jsonb(before), m.Jsonb(result)))
            else:
                result = prior['after_json']; assert result['review_sha256'] == digest and result['artwork_ids'] == ids
        after = s.snapshots(db, ids)
        for row in selected:
            state = after[row['artwork_id']]
            assert not state['creators'] and state['artwork']['unlinked_creator_label'] == row['creator_label'] and state['artwork']['status'] == 'review'
            assert not state['attachments'] and state['artwork']['primary_media_id'] is None
    r.save_gz(BACKUP/'attribution-correction-after.json.gz', after)
    r.save(RUN/'attribution-correction.json', result)
    print('Preserved', len(ids), 'uncertain review artworks with exact source-level creator labels; removed unsupported primary links', flush=True)


def quality_preflight():
    review_path = RUN/'source-qualification-review.json'; digest = r.sha(review_path.read_bytes())
    assert r.load(RUN/'attribution-correction.json')['review_sha256'] == digest
    identity_path = RUN/'source-identity-review.json'; identity_digest = r.sha(identity_path.read_bytes())
    assert r.load(RUN/'identity-correction.json')['review_sha256'] == identity_digest
    identity = r.load(identity_path)
    assert identity['qualification_review_sha256'] == digest
    final_conflicts_digest = r.sha((RUN/'final-inventory-conflicts.json').read_bytes())
    final = list(deliveries()); pending = [(p,pin) for p,pin in final if not (RUN/'applied'/(p['pair']['artist']['id']+'.json')).exists()]
    rows = [row for p,pin in pending for row in p['rows']]
    all_ids = [row['artwork_id'] for p,pin in final for row in p['rows']]
    assert len(all_ids) == len(set(all_ids))
    for row in rows:
        if row.get('date_qualifier_review'):
            evidence = row['date_qualifier_review']
            for item in [dict(entity=row['source_evidence'], receipt=row['receipt']), evidence['property'], evidence['refinement']]:
                raw = gzip.decompress((ROOT/item['receipt']['body_path']).read_bytes())
                assert r.sha(raw) == item['receipt']['sha256'] and item['entity'] in json.loads(raw)['entities'].values()
        if row.get('creator_copy_review'):
            evidence = row['creator_copy_review']
            for item in [dict(entity=row['source_evidence'], receipt=row['receipt']), evidence['property_evidence'], evidence['model_creator']]:
                raw = gzip.decompress((ROOT/item['receipt']['body_path']).read_bytes())
                assert r.sha(raw) == item['receipt']['sha256']
                assert item['entity'] in json.loads(raw)['entities'].values()
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        candidates = collision_candidates(db, rows, progress=True)
        snapshot = {key:value for key,value in candidates.items() if key != '_lookups'}
        snapshot_path = BACKUP/'duplicate-checks'/(r.sha(json.dumps(snapshot,sort_keys=True).encode())+'.json.gz')
        r.save_gz(snapshot_path,snapshot)
        conflicts = []
        for row in rows:
            why, matches = collision_reason(row, candidates)
            if why: conflicts.append(dict(qid=row['qid'], artwork_id=row['artwork_id'], reason=why, matches=matches))
        if conflicts:
            path = RUN/'qualification-conflicts'/(r.sha(json.dumps(conflicts, sort_keys=True).encode())+'.json')
            if not path.exists(): r.save(path, conflicts)
            print('Saved', len(conflicts), 'identity conflicts:', str(path.relative_to(ROOT)), flush=True)
        assert not conflicts, conflicts
        assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])', ([row['artwork_id'] for row in rows],)).fetchall()
        for plan,pin in final:
            if (RUN/'applied'/(plan['pair']['artist']['id']+'.json')).exists(): check_new(db, plan, pin)
    r.save(RUN/'qualification-preflight.json', dict(at=r.now(), review_sha256=digest, painters=len(final), pending_painters=len(pending),
         identity_review_sha256=identity_digest,
         final_inventory_conflicts_sha256=final_conflicts_digest,
         effective_new_records=sum(len(p['rows']) for p,pin in final), minimum=min(len(p['rows']) for p,pin in final), maximum=max(len(p['rows']) for p,pin in final),
         plan_pins={p['pair']['artist']['id']:pin for p,pin in final}, source_plans_unchanged=True, cohort_unchanged=True))
    print('Qualification amendment preflight passed:', len(final), 'painters;', sum(len(p['rows']) for p,pin in final), 'eligible additions', flush=True)


def validate_plan(plan):
    pair = plan['pair']; rows = plan['rows']; aid = pair['artist']['id']
    assert 0 <= pair['count_at_selection'] <= 10 and 20 <= len(rows) <= 100
    assert len({row['artwork_id'] for row in rows}) == len(rows)
    assert len({row['qid'] for row in rows}) == len(rows)
    assert not creator_review(pair, plan['profile'])
    for row in rows:
        w = row['work']
        assert row['artist_id'] == aid and row['artist_ids'] == [aid]
        assert row['source_scheme'] == 'wikidata' and row['source_url'] == 'https://www.wikidata.org/wiki/'+row['qid']
        assert row['source_evidence']['id'] == row['qid'] and row['source_id'] == row['qid']
        assert w['id'] == row['artwork_id'] and w['title'] == row['title'] and w['title'].strip()
        assert w['id'] == str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikidata.org/entity/'+row['qid']))
        assert row['institution_id'] and row['confidence'] >= .8
        assert row['receipt']['status'] == 200
        assert w['creation_year_start'] == row['first'] and w['creation_year_end'] == row['last']
        assert w['date_precision'] == row['precision'] and w['date_display'] == row['date_display']
        dates = source_date(row['source_evidence'])
        assert all(row[k] == dates[k] for k in ['first', 'last', 'precision', 'date_display'])
        if row['first'] is None:
            assert row['last'] is None and w['date_precision'] == 'unknown' and row['uncertainty']
        else:
            assert 0 < row['first'] <= row['last'] <= 1970
        creator = n.active(row['source_evidence'], 'P170')
        assert len(creator) == 1 and n.value(creator[0])['id'] == row['painter_qid']
        if row.get('creator_copy_review'):
            assert row['qid'] == 'Q119157407' and row['painter_qid'] == 'Q19672293'
            assert set(creator[0]['qualifiers']) == {'P1877'} and len(creator[0]['qualifiers']['P1877']) == 1
            assert creator[0]['qualifiers']['P1877'][0]['datavalue']['value']['id'] == row['creator_copy_review']['after_qid'] == 'Q18671748'
            assert row['work']['creation_year_start'] == 1906 and '1191' in identity_inventories(row) and 'after John Graham-Gilbert' in row['title']
        else: assert not creator[0].get('qualifiers')
        holding = n.active(row['source_evidence'], 'P195')
        assert holding and all(n.qualified_holding(claim) for claim in holding)
        assert {n.value(claim)['id'] for claim in holding} == {match['source_qid'] for match in row['source_collection_matches']}
        assert {match['record']['id'] for match in row['source_collection_matches']} == {row['institution_id']}
        assert row['institution_qid'] in {n.value(claim)['id'] for claim in holding}
        assert any(has_holding_reference(claim) for claim in holding)


def backup():
    description = 'Before low-count random 200 painter second batch 20261009'
    if not (BACKUP/'cloud-backup-request.json').exists():
        raw = subprocess.check_output(['gcloud', 'sql', 'backups', 'create', '--instance=artline-postgres', '--project=artline-508319', '--description='+description, '--async', '--format=json'], text=True)
        r.save(BACKUP/'cloud-backup-request.json', json.loads(raw))
    rows = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'list', '--instance=artline-postgres', '--project=artline-508319', '--limit=30', '--format=json'], text=True))
    matches = [row for row in rows if row.get('description') == description]
    if len(matches) == 1 and matches[0]['status'] == 'SUCCESSFUL':
        if not (BACKUP/'cloud-backup.json').exists():
            r.save(BACKUP/'cloud-backup.json', matches[0]); r.save(RUN/'cloud-backup.json', matches[0])
        print('Recovery backup successful', matches[0]['id'], flush=True)
    else: print('Recovery backup pending', [(v['id'], v['status']) for v in matches], flush=True)


def preflight():
    final = list(deliveries()); rows = [row for plan, pin in final for row in plan['rows']]
    ids = [row['artwork_id'] for row in rows]; assert len(ids) == len(set(ids))
    receipts = {plan['profile']['receipt']['body_path']: plan['profile']['receipt'] for plan, pin in final}
    receipts.update({row['receipt']['body_path']: row['receipt'] for row in rows})
    receipts.update({rc['body_path']:rc for row in rows for rc in row['museum_match']['receipts']})
    receipts.update({rc['body_path']:rc for row in rows for match in row['source_collection_matches'] for rc in match['receipts']})
    types = r.load(RUN/'type-review.json.gz')
    receipts.update({item['receipt']['body_path']:item['receipt'] for item in types.values()})
    assert all(source_kind(row['source_evidence'], types) == row['work_type'] for row in rows)
    for row in rows:
        for match in row['source_collection_matches']:
            if match.get('catalogue_alias'):
                alias = match['catalogue_alias']
                assert r.sha((ROOT/alias['proof_path']).read_bytes()) == alias['proof_sha256']
    source_entities = collections.defaultdict(list)
    for plan, pin in final:
        item = plan['profile']
        source_entities[item['receipt']['body_path']].append(item['entity'])
    for row in rows:
        source_entities[row['receipt']['body_path']].append(row['source_evidence'])
    for item in types.values():
        source_entities[item['receipt']['body_path']].append(item['entity'])
    source_redirects = []
    for path, receipt in receipts.items():
        raw = gzip.decompress((ROOT/path).read_bytes())
        assert r.sha(raw) == receipt['sha256']
        if path in source_entities:
            original = json.loads(raw)['entities']
            for entity in source_entities[path]:
                if entity['id'] in original:
                    assert original[entity['id']] == entity
                else:
                    # wbgetentities can retain the requested key while returning
                    # a merged entity's canonical ID. Verify the full unchanged
                    # object against that response key and preserve the redirect.
                    keys = [key for key, value in original.items() if value == entity]
                    assert len(keys) == 1, 'Source entity not uniquely present in its captured response'
                    source_redirects.append(dict(requested_id=keys[0], canonical_id=entity['id'], body_path=path, sha256=receipt['sha256']))
    artist_ids = [plan['pair']['artist']['id'] for plan, pin in final]
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        assert db.execute('SELECT user_id FROM editor_accounts WHERE user_id=%s', ('local-european-research',)).fetchone()
        collisions = collision_candidates(db, rows, progress=True)
        for row in rows:
            reason, matches = collision_reason(row, collisions)
            assert not reason, (row['qid'], reason, matches)
        assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
        old_ids = [x['id'] for x in db.execute('SELECT DISTINCT artwork_id::text id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])', (artist_ids,))]
        before = s.snapshots(db, old_ids)
        query_plan = db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT aa.artwork_id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>%s', (artist_ids[0], 'archived')).fetchone()
    r.save_gz(BACKUP/'original-records-before.json.gz', before)
    r.save(RUN/'preflight.json', dict(at=r.now(), painters=len(final), new_records=len(ids), source_bodies_verified=len(receipts),
           original_records=len(before), plan_pins={plan['pair']['artist']['id']: pin for plan, pin in final},
           minimum_additions=min(len(p['rows']) for p, pin in final), maximum_additions=max(len(p['rows']) for p, pin in final),
           unknown_dates=sum(row['first'] is None for row in rows), source_redirects=source_redirects, query_plan=query_plan, local_database_connected=False))
    print('Preflight passed:', len(final), 'painters,', len(ids), 'new works;', len(before), 'pre-existing records preserved in backup', flush=True)


def check_new(db, plan, pin):
    ids = [row['artwork_id'] for row in plan['rows']]; sid = m.uid('source/wikidata')
    states = s.snapshots(db, ids)
    refs = {row['entity_id']: row for row in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])", (ids,))}
    cites = {row['entity_id']: row for row in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND source_id=%s AND entity_id=ANY(%s::uuid[])", (sid, ids))}
    assert len(states) == len(refs) == len(cites) == len(ids)
    for row in plan['rows']:
        value = states[row['artwork_id']]; work = value['artwork']; reference = refs[work['id']]; citation = cites[work['id']]
        assert all(work[k] == v for k, v in row['work'].items())
        assert work['status'] == 'review' and work['published_at'] is None and work['research_candidate']
        assert work['current_institution_id'] == row['institution_id'] and work['primary_media_id'] is None and not value['attachments']
        assert len(value['creators']) == 1 and value['creators'][0]['artist_id'] == row['artist_id'] and value['creators'][0]['attribution_role'] == 'primary'
        assert len(value['locations']) == 1
        holding = value['locations'][0]
        assert holding['claim_type'] == 'holding' and holding['review_state'] == 'accepted' and holding['display_state'] is None
        assert holding['institution_id'] == row['institution_id'] and holding['source_id'] == sid
        assert reference['scheme'] == 'wikidata' and reference['external_id'] == row['qid'] and reference['canonical_url'] == row['source_url'] and reference['source_id'] == sid
        assert citation['source_record_id'] == row['qid'] and citation['source_url'] == row['source_url'] and json.loads(citation['evidence_note'])['plan_sha256'] == pin
    selected = db.execute('SELECT id,artline_has_selection_evidence(id) selected FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
    assert len(selected) == len(ids) and all(row['selected'] for row in selected)
    return states


def apply():
    assert r.load(BACKUP/'cloud-backup.json')['status'] == 'SUCCESSFUL'
    final = list(deliveries()); pre = r.load(RUN/'preflight.json')
    assert pre['plan_pins'] == {plan['pair']['artist']['id']: pin for plan, pin in final}
    if (RUN/'source-qualification-review.json').exists():
        amendment = r.load(RUN/'qualification-preflight.json')
        assert amendment['review_sha256'] == r.sha((RUN/'source-qualification-review.json').read_bytes())
        assert amendment['identity_review_sha256'] == r.sha((RUN/'source-identity-review.json').read_bytes())
        assert amendment['final_inventory_conflicts_sha256'] == r.sha((RUN/'final-inventory-conflicts.json').read_bytes())
        assert amendment['plan_pins'] == pre['plan_pins'] and amendment['effective_new_records'] == sum(len(p['rows']) for p,pin in final)
    sid = m.uid('source/wikidata'); actor = 'local-european-research'
    with r.connect('production', readonly=False) as db:
        for number, (plan, pin) in enumerate(final, 1):
            pair = plan['pair']; aid = pair['artist']['id']; rows = plan['rows']; ids = [row['artwork_id'] for row in rows]
            done = RUN/'applied'/(aid+'.json'); marker = m.uid('applied/'+aid)
            if done.exists():
                assert r.load(done)['plan_sha256'] == pin
                continue
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='15s'")
                db.execute('SELECT pg_advisory_xact_lock(2026100607)')
                prior = db.execute('SELECT after_json FROM audit_log WHERE id=%s', (marker,)).fetchone()
                if prior:
                    result = prior['after_json']
                    assert result['plan_sha256'] == pin and result['new_ids'] == ids
                    check_new(db, plan, pin)
                else:
                    creator = db.execute('SELECT id::text,display_name,status FROM artists WHERE id=%s FOR SHARE', (aid,)).fetchone()
                    assert creator and creator['display_name'] == pair['artist']['display_name'] and creator['status'] != 'archived'
                    old = db.execute('SELECT a.id::text,a.status FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s', (aid,)).fetchall()
                    old_ids = sorted({x['id'] for x in old}); count_before = len({x['id'] for x in old if x['status'] != 'archived'})
                    assert 0 <= count_before <= 10, 'Frozen painter no longer has 0–10 active artworks'
                    assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
                    collisions = collision_candidates(db, rows)
                    for row in rows:
                        why, matches = collision_reason(row, collisions)
                        assert not why, (row['qid'], why, matches)
                    museums = {row['id']: row for row in db.execute('SELECT id::text,name,wikidata_id,status,website_url,canonical_institution_id::text FROM institutions WHERE id=ANY(%s::uuid[]) FOR SHARE', (sorted({x['institution_id'] for x in rows}),))}
                    aliases = {match['catalogue_alias']['mapping']['id']:match['catalogue_alias']['mapping']['canonical_institution_id'] for row in rows for match in row['source_collection_matches'] if match.get('catalogue_alias')}
                    if aliases:
                        current_aliases = {value['id']:value['canonical_institution_id'] for value in db.execute('SELECT id::text,canonical_institution_id::text FROM institutions WHERE id=ANY(%s::uuid[]) FOR SHARE', (list(aliases),))}
                        assert current_aliases == aliases, 'Reviewed museum alias changed since source selection'
                    for row in rows:
                        current = museums[row['institution_id']]; expected = row['museum_match']['record']
                        assert current['canonical_institution_id'] is None
                        assert current['status'] != 'archived' and all(current[k] == expected[k] for k in ['id','name','wikidata_id'])
                        if expected.get('website_url'): assert current['website_url'] == expected['website_url']
                    before = s.snapshots(db, old_ids)
                    preimage = BACKUP/'artist-preimages'/aid/(r.sha(json.dumps(before, sort_keys=True, default=str).encode())+'.json.gz')
                    r.save_gz(preimage, dict(plan_sha256=pin, records=before))
                    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'authority_data','https://www.wikidata.org/') ON CONFLICT(id) DO NOTHING", (sid, OP+'-wikidata', 'Wikidata: referenced museum objects for the second low-count painter sample'))
                    with db.pipeline():
                        for row in rows:
                            work = row['work']; wid = row['artwork_id']
                            keys = ['id','slug','title','alternate_title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','object_form','medium_text','dimensions_text','accession_number']
                            db.execute('''INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,object_form,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by)
                              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''', tuple(work[k] for k in keys)+(actor,actor))
                            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)", (wid, aid, row.get('creator_note') or 'Unique unqualified source creator authority '+row['painter_qid']+'; exact catalogue name/alias and lifespan checked. Source label: '+row['creator_label']))
                            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikidata',%s,%s,%s,%s)", (wid, row['qid'], row['source_url'], sid, row['receipt']['retrieved_at']))
                            note = dict(operation=OP, plan_sha256=pin, type_review_sha256=plan['type_review_sha256'], source_entity=row['source_evidence'], source_receipt=row['receipt'], creator_profile_receipt=plan['profile']['receipt'],
                                 qualification_review_sha256=plan.get('qualification_review_sha256'),
                                 identity_review_sha256=plan.get('identity_review_sha256'), identity_review_note=row.get('identity_review_note'),
                                 final_inventory_conflicts_sha256=plan.get('final_inventory_conflicts_sha256'),
                                 date_qualifier_review=row.get('date_qualifier_review'),
                                 creator_copy_review=row.get('creator_copy_review'),
                                 identity_basis='Exact source object and creator authority, separately preserved reviewed copy relationship where applicable, catalogue identity/lifespan checks and source/museum inventory/title/translation duplicate review.',
                                 source_label='Wikidata; referenced museum collection statements. Cited native pages are not independently verified unless separately captured.',
                                 collection=row['institution_qid'], museum_identity=row['museum_match'], source_collections=row['source_collection_matches'], confidence=row['confidence'], confidence_basis=row['confidence_basis'], uncertainty=row['uncertainty'],
                                 source_titles=row['title_aliases'], source_references=row['references'], native_urls=row['native_urls'],
                                 publication='New review record with unknown fields preserved. Museum holding only, no current-display claim. No image reuse.')
                            db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,%s,%s,%s,%s,%s,%s)",
                                 (m.uid('citation/'+row['qid']), wid, sid, OP, row['qid'], row['source_url'], json.dumps(note, ensure_ascii=False), row['receipt']['retrieved_at'], actor))
                            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",
                                 (m.uid('holding/'+row['qid']), wid, row['institution_id'], sid, row['source_url'], json.dumps(dict(plan_sha256=pin, confidence=row['confidence'], basis=row['confidence_basis'], uncertainty=row['uncertainty']), ensure_ascii=False), row['receipt']['retrieved_at']))
                    check_new(db, plan, pin)
                    assert s.snapshots(db, old_ids) == before, 'An existing artwork changed inside this import transaction'
                    result = dict(at=r.now(), artist_id=aid, artist=pair['artist']['display_name'], plan_sha256=pin, new_records=len(rows), new_ids=ids,
                                  existing_records_before=count_before, existing_records_preserved_in_transaction=True, preimages=str(preimage), local_database_changed=False, images_attached=0)
                    db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'low_count_200_additions','artist',%s,%s)", (marker, actor, aid, m.Jsonb(result)))
            r.save(done, result)
            print('Committed', number, '/ 200:', pair['artist']['display_name'], len(rows), 'new artworks', flush=True)


def verify():
    final = list(deliveries()); results = []; states = {}
    with r.connect('production') as db:
        for plan, pin in final:
            pair = plan['pair']; aid = pair['artist']['id']; receipt = r.load(RUN/'applied'/(aid+'.json'))
            assert receipt['plan_sha256'] == pin
            states.update(check_new(db, plan, pin))
            total = db.execute("SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'", (aid,)).fetchone()['n']
            assert total >= receipt['existing_records_before']+len(plan['rows'])
            results.append(dict(artist_id=aid, artist=pair['artist']['display_name'], slug=pair['artist']['slug'], before=receipt['existing_records_before'],
                          added=len(plan['rows']), after=total, unknown_dates=sum(row['first'] is None for row in plan['rows']), source=pair['source']['url']))
        before = r.load(BACKUP/'original-records-before.json.gz'); after_old = s.snapshots(db, list(before))
    changed = {wid: dict(before=value, after=after_old.get(wid)) for wid, value in before.items() if value != after_old.get(wid)}
    retained = r.load(RUN/'attribution-correction.json') if (RUN/'attribution-correction.json').exists() else None
    if retained:
        with r.connect('production') as db:
            assert s.snapshots(db, retained['artwork_ids']) == r.load(BACKUP/'attribution-correction-after.json.gz')
    identity_correction = r.load(RUN/'identity-correction.json')
    with r.connect('production') as db:
        assert s.snapshots(db, identity_correction['artwork_ids']) == r.load(BACKUP/'identity-correction-after.json.gz')
    r.save_gz(RUN/'concurrent-original-record-changes.json.gz', changed)
    r.save_gz(BACKUP/'new-records-after.json.gz', states)
    proof = dict(at=r.now(), painters=len(results), added=len(states), minimum=min(x['added'] for x in results), maximum=max(x['added'] for x in results),
                 unknown_dates=sum(x['unknown_dates'] for x in results), source_citations=len(states), documented_holdings=len(states), current_display_claims=0,
                 all_new_records_remain_review=True, all_source_selections_verified=True, images_attached=0, concurrent_existing_record_changes=len(changed), local_database_changed=False, results=results)
    proof['additional_unlinked_qualified_review_records'] = len(retained['artwork_ids']) if retained else 0
    proof['own_new_identity_conflicts_archived'] = len(identity_correction['artwork_ids'])
    proof['total_rows_created_including_corrections'] = sum(r.load(path)['new_records'] for path in (RUN/'applied').glob('*.json'))
    assert proof['total_rows_created_including_corrections'] == proof['added'] + proof['additional_unlinked_qualified_review_records'] + proof['own_new_identity_conflicts_archived']
    r.save(RUN/'production-verification.json', proof)
    print(json.dumps({k:v for k,v in proof.items() if k != 'results'}), flush=True)


def api_verify():
    b.deliveries = deliveries
    b.api_verify()


def report():
    proof = r.load(RUN/'production-verification.json'); api = r.load(RUN/'api-verification.json')
    frame = r.load(RUN/'sampling-frame.json'); final = list(deliveries())
    assert proof['painters'] == api['painters'] == 200 and proof['added'] == api['new_records_found'] and api['missing'] == 0
    previous = {row['artist']['id'] for row in r.load(PREVIOUS/'cohort.json')['painters']}
    assert not previous.intersection(row['artist_id'] for row in proof['results'])
    assert all(0 <= row['before'] <= 10 and 20 <= row['added'] <= 100 for row in proof['results'])
    def write_csv(path, rows):
        buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
        if path.exists(): assert path.read_text() == buffer.getvalue()
        else: path.write_text(buffer.getvalue())
    counts = [dict(**row, live_url='https://artlines.org/artists/'+row['slug']) for row in proof['results']]
    write_csv(RUN/'painters.csv', counts)
    records = []
    for plan, pin in final:
        for row in plan['rows']:
            work = row['work']
            records.append(dict(artist=plan['pair']['artist']['display_name'], artist_id=row['artist_id'], artwork_id=work['id'], title=work['title'],
                 date_display=work['date_display'], creation_year_start=work['creation_year_start'], creation_year_end=work['creation_year_end'],
                 type=work['work_type'], museum=row['museum_name'], accession=work['accession_number'], source_url=row['source_url'], status='review'))
    write_csv(RUN/'new-artworks.csv', records)
    types = collections.Counter(row['type'] for row in records); museums = {row['museum'] for row in records}
    audit = r.load(RUN/'audit-summary.json'); backup_id = r.load(BACKUP/'cloud-backup.json')['id']
    qualification_review = r.load(RUN/'source-qualification-review.json')
    identity_review = r.load(RUN/'source-identity-review.json')
    text = f'''# Second random low-count painter expansion

Completed and verified {proof['at']}.

- **{proof['added']:,} new production artwork records for 200 additional painters.** The previous 200-painter batch is excluded.
- Every painter had **0–10 active artworks**, across all nonarchived statuses, and received **{proof['minimum']}–{proof['maximum']} new artworks**.
- All additions passed database validation and were found through the live unified catalogue API: {api['bounded_pages']} bounded pages, at most 50 records per page, no missing records.
- All additions remain in review. **{proof['unknown_dates']:,} dates remain explicitly unknown**; no artist lifespan was substituted for an artwork date.
- These are metadata additions: **no catalogue images were uploaded or attached**. Two small, public-domain Commons reproductions were inspected solely to distinguish two portraits with a conflicting source inventory number; their research receipts are retained.
- A later qualification audit withheld {len(qualification_review['held'])} uncertain painter links found in source filenames. Seven had already been created: they remain separate review records with exact qualified creator wording and no painter authority link. They are excluded from the {proof['added']:,} painter additions above. One separately reviewed 1906 copy by Robert Cree Crawford, museum inventory 1191, replaced his two uncertain entries while preserving his minimum of 20 additions. Its explicit relationship to a work by John Graham Gilbert remains in the title, source qualifier and creator note; the copy is not merged with its model. The original 200-painter cohort and immutable source plans were preserved; the pinned amendment and corrections are audited in `source-qualification-review.json`, `qualification-preflight.json` and `attribution-correction.json`.
- The expanded inventory review excluded {len(identity_review['held'])+len(r.load(RUN/'final-inventory-conflicts.json'))} existing objects, duplicate source entities or unresolved inventory conflicts. Five records created earlier in this operation were archived with recovery snapshots; no pre-existing catalogue record was deleted or rewritten. One independently checked NGA drawing replaced a duplicate Beatrix Whistler entry, preserving her minimum of 20. Its date remains “late 19th century,” without an invented precise year. See `source-identity-review.json`, `final-inventory-conflicts.json` and `identity-correction.json`.
- Individually catalogued album compositions and explicit recto/verso works retain their source titles and object identifiers. These counts refer to artwork records, not separate physical supports or albums. Shared generic titles do not merge works with distinct museum object evidence. Exact source accession conflicts, including the two visually distinct Arbuckle portraits, remain documented without invented replacement numbers.

[Painter counts](painters.csv), [new artworks](new-artworks.csv), [production verification](production-verification.json), [live API verification](api-verification.json), [authorization](authorization.json).

## Sources and selection

The fresh production audit found {audit['current_low_count_painters']:,} painters with 0–10 active works. The final 200 were randomly sampled without replacement from {frame['count']} candidates that passed the initial source and duplicate checks, using seed `{frame['seed']}`. Subsequent qualification and inventory review amended their work selections while preserving the same cohort. This is a bounded source-supported sample, not a uniform sample of every low-count painter. Discovery counts came from saved Wikidata collection-connected indexes; research prioritized stronger source inventories and was capped at 80 object leads per painter. Source requests followed the provider's explicit retry interval after a temporary rate limit. All exclusions, captured source bodies, retrieval times and SHA-256 receipts are retained.

The principal source is **Wikidata**, with referenced collection statements, explicit object and creator identities, and source creation precision. Native pages cited by Wikidata are not represented as independently verified, except the specifically recorded NGA drawing review. Creator identity requires an existing unique authority, exact name/alias agreement, compatible lifespan and explicit painter occupation. Uncertain attributions, unresolved ensembles, post-1970 dates, unresolved source conflicts and possible existing object versions were withheld. Supplied museum accession numbers, collection-scoped inventory qualifiers and multilingual titles remain in source evidence even where the original parser left the normalized catalogue accession field empty.

The {len(museums)} documented holding institutions are distinct from current display. Existing museums without Wikidata IDs were matched by a unique source name/alias plus official website domain, an exact French Ministry of Culture Museofile identifier, or an individually reviewed exact name/alias with matching explicit country and locality. Explicit collection/department relationships were reconciled to their parent museum while preserving original source labels and evidence. Multiple collection statements were accepted only when all resolve to the same museum. Existing institution records were not rewritten. No current-display claim or museum masterpiece designation was invented.

Artwork types: {', '.join(f'{kind}: {count:,}' for kind, count in sorted(types.items()))}.

## Recovery and validation

Successful Cloud SQL backup: `{backup_id}`. Recovery snapshots and receipts: `{BACKUP}`. Each painter is imported atomically from an immutable pinned plan, with a deterministic audit marker that makes interrupted receipt writing recoverable without duplicate insertion. Existing records are compared before and after inside each transaction. {proof['concurrent_existing_record_changes']} pre-existing records changed outside these import transactions between preflight and final verification; retained differences are in `concurrent-original-record-changes.json.gz`.

The real local catalogue was never connected to or changed. No application deployment or commit was performed. Source and validation code: `ops/{OP}.py`; pure tests: `ops/test_low_count_200_painters_round2_20261009.py`. Query plans and bounded API checks describe this operation; they are not a ten-million-row performance claim.
'''
    path = RUN/'README.md'
    if path.exists(): assert path.read_text() == text
    else: path.write_text(text)
    completion = dict(at=r.now(), painters=200, new_artworks=proof['added'], previous_batch_overlap=0, api_missing=0,
                      minimum=proof['minimum'], maximum=proof['maximum'], report_sha256=r.sha(path.read_bytes()), local_database_changed=False)
    r.save(RUN/'completion.json', completion)
    print(json.dumps(completion), flush=True)


def audit():
    b.audit()
    rows = r.load(RUN/'low-count-audit.json.gz')['painters']
    previous = {x['artist']['id'] for x in r.load(PREVIOUS/'cohort.json')['painters']}
    assert not previous.intersection(x['artist']['id'] for x in rows)
    with r.connect('production') as db:
        position = db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (m.COLLECTION,)).fetchone()['n']
    report = {'at': r.now(), 'previous_painters_excluded': len(previous), 'current_low_count_painters': len(rows),
              'artist_identifier_schemes': dict(collections.Counter(e['scheme'] for x in rows for e in x['identifiers'])),
              'personal_collection_position': position, 'personal_selection_capacity': 100000-position,
              'local_database_connected': False}
    r.save(RUN/'audit-summary.json', report)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['audit', 'wd_counts', 'wd_research', 'museum_crosswalk', 'type_index', 'resume_source', 'resume_api', 'prepare', 'freeze', 'backup', 'preflight', 'quality_review', 'repair_attributions', 'quality_preflight', 'apply', 'verify', 'api_verify', 'report'])
    args = p.parse_args()
    RUN.mkdir(parents=True, exist_ok=True)
    BACKUP.mkdir(parents=True, exist_ok=True)
    globals()[args.phase]()
