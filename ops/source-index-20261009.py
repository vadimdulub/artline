#!/usr/bin/env python3
"""Local evidence index and read-only catalogue discovery for source enrichment.

This program never writes to either catalogue. Delivery is a separate pinned plan.
The JSONL index is canonical; SQLite is a rebuildable local search companion.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/source-index-20261009'
OP = RUN.name
ARTISTS = ROOT / 'docs/research/painter-influences-round4-20261009/production-artists.json.gz'


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def save(path, value, immutable=True):
    path = Path(path)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, indent=None if path.suffix == '.gz' else 2).encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and immutable:
        if path.read_bytes() != raw:
            raise ValueError('Immutable evidence already exists: ' + str(path))
        return
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(raw)
    temp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def connect(target='production'):
    spec = importlib.util.spec_from_file_location('alignment', ROOT / 'ops/align-catalogues-20261008.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.connect(target, readonly=True)


def canonical_url(url):
    """Preserve identity-bearing paths, query order and fragments; drop only tracking."""
    if not isinstance(url, str):
        return None
    try:
        p = urlsplit(url.strip())
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
            return None
        _ = p.port
    except ValueError:
        return None
    query = '&'.join(part for part in p.query.split('&') if part and not re.match(r'(?i)(utm_[^=]*|fbclid|gclid)=', part))
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', query, p.fragment))


def host(url):
    h = urlsplit(url).hostname or ''
    return h.removeprefix('www.')


def excluded(url):
    h = host(url)
    return (h == 'wikidata.org' or h.endswith('.wikidata.org') or h.endswith('.wikipedia.org')
            or h == 'wikipedia.org' or h == 'pantheon.world' or h in ('artlines.org','artline.app')
            or (h in ('storage.googleapis.com','storage.cloud.google.com') and '/artline-' in urlsplit(url).path))


MUSEUM_PATTERNS = [
    'Cleveland', 'Art Institute of Chicago', 'Minneapolis', 'National Gallery of Art',
    'Walters', 'Statens Museum', 'Nationalmuseum', 'National Museum of Norway',
    'Rijksmuseum', 'Tate', 'Scottish National', 'National Gallery, London',
    'Yale', 'Harvard', 'Philadelphia', 'Detroit', 'Brooklyn', 'Museum of Fine Arts, Boston',
    'Los Angeles County', 'Saint Louis', 'Indianapolis', 'Cincinnati', 'Baltimore',
    'Prado', 'Louvre', 'Orsay', 'Le Havre', 'Rouen', 'Mauritshuis', 'Van Gogh',
    'Tretyakov', 'Russian Museum', 'Hermitage', 'Benaki', 'Byzantine', 'Leventis',
    'National Gallery.*Greece', 'National Gallery.*Athens', 'Thessaloniki',
    'Goulandris', 'Historical Museum of Crete', 'Cyprus', 'Nicosia',
    'Kiasma', 'Ateneum', 'Kunsthistorisches', 'Belvedere', 'Kunsthaus',
    'Narodni', 'National Gallery Prague', 'National Museum.*Warsaw', 'Krak',
    'Tokyo', 'Kyoto', 'Shanghai', 'Palace Museum', 'National Museum.*Korea',
    'Victoria and Albert', 'British Museum', 'Fitzwilliam', 'Ashmolean',
    'Museo del Novecento', 'Uffizi', 'Bargello', 'Capodimonte', 'Getty',
    'Smithsonian American Art', 'Freer', 'Sackler', 'National Gallery of Victoria',
    'Art Gallery of South Australia', 'Auckland', 'Groninger', 'Kröller',
]


def export():
    if (RUN / 'catalogue-export.json.gz').exists():
        raise ValueError('Export already pinned')
    with connect('local') as db:
        local = dict(at=now(), read_only=db.execute("SELECT current_setting('transaction_read_only') v").fetchone()['v'],
                     counts={t: db.execute('SELECT count(*) n FROM ' + t).fetchone()['n'] for t in ('artworks', 'artists', 'institutions', 'media_assets')})
    save(RUN / 'local-readonly-baseline.json', local)
    with connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        sources = db.execute('SELECT * FROM sources ORDER BY slug').fetchall()
        institutions = db.execute('SELECT * FROM institutions WHERE status<>\'archived\' ORDER BY name,id').fetchall()
        selected = [i for i in institutions if not i.get('canonical_institution_id') and any(re.search(p, i['name'], re.I) for p in MUSEUM_PATTERNS)]
        # A fixed bounded selection by institution, never a global artwork enrichment CTE.
        works, citations, identifiers, creators, plans = [], [], [], [], []
        sql = """SELECT * FROM artworks WHERE current_institution_id=%s AND status<>'archived'
                 ORDER BY (primary_media_id IS NULL) DESC, id LIMIT 160"""
        for n, inst in enumerate(selected):
            rows = db.execute(sql, (inst['id'],)).fetchall()
            if not rows:
                continue
            ids = [r['id'] for r in rows]
            works.extend(rows)
            citations.extend(db.execute("SELECT * FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id", (ids,)).fetchall())
            identifiers.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id", (ids,)).fetchall())
            creators.extend(db.execute("SELECT aa.*,a.display_name,a.slug artist_slug FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id", (ids,)).fetchall())
            if len(plans) < 3:
                plans.append(dict(institution=inst['name'], plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) ' + sql, (inst['id'],)).fetchone()))
            if n % 20 == 0:
                print('Read-only institution discovery', n, len(selected), 'objects', len(works), flush=True)
        save(RUN / 'catalogue-export.json.gz', dict(at=now(), read_only=True, sources=sources, institutions=institutions,
             selected_institution_ids=[i['id'] for i in selected], artworks=works, citations=citations, identifiers=identifiers, creators=creators))
        save(RUN / 'scoped-query-plans.json', plans)
    print(json.dumps(dict(sources=len(sources), institutions=len(institutions), scoped_institutions=len(selected),
                         artworks=len(works), citations=len(citations), identifiers=len(identifiers))), flush=True)


def resource_kind(url, entity_type=None, source_type=None):
    h, p = host(url), urlsplit(url).path.lower()
    if h in ('raw.githubusercontent.com','media.githubusercontent.com') or p.endswith(('.csv','.jsonl','.zip')):
        return 'reference_dataset'
    if 'vocab.getty.edu' == h or h in ('rkd.nl', 'rkdartists.nl', 'viaf.org', 'id.loc.gov', 'd-nb.info'):
        return 'artist_authority' if 'ulan' in p or entity_type == 'artist' else 'authority_record'
    if any(x in p for x in ['/publications/', '/metpublications/', '/virtuallibrary/', '/books/', '/catalogues/']) or source_type == 'book':
        return 'book_or_catalogue'
    if any(x in p for x in ['/artists/', '/artist/', '/people/', '/person/', '/author/', '/authors/', '/creators/']):
        return 'artist_reference'
    if entity_type == 'institution':
        return 'museum_directory_or_collection'
    if entity_type in ('artwork', 'artist'):
        return 'object_or_artist_reference' if entity_type == 'artist' else 'museum_or_collection_object'
    return 'research_resource'


def build(limit=20000):
    if (RUN / 'delivery-plan-pin.json').exists():
        raise ValueError('Index is pinned by a delivery plan. Preserve this revision and build future additions in a new versioned run.')
    data = load(RUN / 'catalogue-export.json.gz')
    providers_path = RUN / 'providers.json'
    providers = load(providers_path) if providers_path.exists() else []
    byhost = {h: p for p in providers for h in p['hosts']}
    checks = {p.stem:load(p) for p in (RUN / 'provider-checks').glob('*.json')}
    sources = {s['id']: s for s in data['sources']}
    works = {r['id']: r for r in data['artworks']}
    institutions = {r['id']: r for r in data['institutions']}
    records = {}
    dropped = Counter()

    def add(url, title, entity_type=None, entity_id=None, citation=None, identifier=None, evidence=None, kind=None, verified=None, facts=None):
        url = canonical_url(url)
        if not url or excluded(url):
            dropped['invalid_or_excluded'] += 1
            return
        if len(url) > 2400:
            dropped['oversized_url'] += 1
            return
        h = host(url)
        provider = byhost.get(h)
        source = sources.get((citation or {}).get('source_id'), {})
        rid = 'src_' + hashlib.sha256(url.encode()).hexdigest()[:24]
        r = records.setdefault(url, dict(id=rid, url=url, host=h, title=title or url,
            kind=kind or resource_kind(url, entity_type, source.get('source_type')),
            provider_id=provider['id'] if provider else 'domain:' + h,
            provider_name=provider['name'] if provider else source.get('name') or h,
            authority_scope=provider['authority_scope'] if provider else ['existing_citation_requires_field_review'],
            review_state='fresh_metadata_verified' if verified else 'existing_catalogue_reference_not_rechecked',
            checked_at=verified, artline_bindings=[], citation_evidence=[], external_identifiers=[],
            discovery_evidence=[], facts=facts or {},
            image_permission='per_object_review_required', update_eligibility='requires_exact_object_and_field_review'))
        if provider and provider['id'] in checks:
            check = checks[provider['id']]
            r['provider_availability'] = dict(state=check['state'],checked_at=check['at'],
                checked_url=check.get('receipt',{}).get('url') or check['url'],
                evidence_file=str((RUN/'provider-checks'/(provider['id']+'.json')).relative_to(ROOT)))
        binding = dict(catalogue='production', entity_type=entity_type, entity_id=entity_id, label=title)
        if entity_id and binding not in r['artline_bindings']:
            r['artline_bindings'].append(binding)
        if citation:
            item = {k: citation.get(k) for k in ('id', 'field_name', 'source_id', 'source_record_id', 'source_url', 'page_or_locator', 'retrieved_at') if citation.get(k) is not None}
            if citation.get('evidence_note'):
                note=citation['evidence_note']
                item.update(evidence_note_preview=note[:320],evidence_note_truncated=len(note)>320,
                    evidence_note_sha256=hashlib.sha256(note.encode()).hexdigest(),
                    full_evidence_file=evidence.get('path') if evidence else None)
            if item not in r['citation_evidence']:
                r['citation_evidence'].append(item)
        if identifier and identifier not in r['external_identifiers']:
            r['external_identifiers'].append(identifier)
        if evidence and evidence not in r['discovery_evidence']:
            r['discovery_evidence'].append(evidence)
        if verified:
            r['review_state'], r['checked_at'] = 'fresh_metadata_verified', verified
        if facts:
            r['facts'].update(facts)

    provenance = dict(path=str(ARTISTS.relative_to(ROOT)), sha256=sha(ARTISTS), note='Previously exported production artist source references; not a fresh page verification.')
    for a in load(ARTISTS):
        for c in a['citations']:
            add(c.get('source_url'), a['display_name'], 'artist', a['id'], citation=c, evidence=provenance)
        for i in a['identifiers']:
            add(i.get('canonical_url'), a['display_name'], 'artist', a['id'], identifier=i, evidence=provenance)
    export_ref = dict(path=str((RUN / 'catalogue-export.json.gz').relative_to(ROOT)), sha256=sha(RUN / 'catalogue-export.json.gz'), captured_at=data['at'])
    for c in data['citations']:
        w = works[c['entity_id']]
        add(c.get('source_url'), w['title'], 'artwork', w['id'], citation=c, evidence=export_ref)
    for i in data['identifiers']:
        w = works[i['entity_id']]
        add(i.get('canonical_url'), w['title'], 'artwork', w['id'], identifier=i, evidence=export_ref)
    # Institution homepages are discovery leads, never evidence for invented objects.
    for i in data['institutions']:
        add(i.get('website_url'), i['name'], 'institution', i['id'], evidence=export_ref)
    for path in sorted((RUN / 'fresh-resources').glob('*.json')) if (RUN / 'fresh-resources').exists() else []:
        for row in load(path):
            add(**row)
    for p in providers:
        add(p['url'], p['name'], kind='provider_entrypoint', evidence=dict(path=str(providers_path.relative_to(ROOT)), sha256=sha(providers_path)))
    # Long-standing APIs also expose collection pages referenced by hundreds of entities.
    # Each URL remains one resource; membership of this index never creates an artwork.
    # Balanced deterministic selection: fresh evidence first, then round-robin providers.
    chosen = [r for r in records.values() if r['review_state'] == 'fresh_metadata_verified']
    chosen.sort(key=lambda r: r['id'])
    groups = defaultdict(list)
    for r in records.values():
        if r['review_state'] != 'fresh_metadata_verified':
            groups[r['provider_id']].append(r)
    for rows in groups.values():
        rows.sort(key=lambda r: (r['kind'] == 'provider_entrypoint', -len(r['artline_bindings']), r['id']))
    offset = 0
    while len(chosen) < limit:
        added = 0
        for k in sorted(groups):
            if offset < len(groups[k]):
                chosen.append(groups[k][offset]); added += 1
                if len(chosen) == limit:
                    break
        if not added:
            break
        offset += 1
    chosen = sorted(chosen[:limit], key=lambda r: r['id'])
    RUN.mkdir(parents=True, exist_ok=True)
    out = RUN / 'sources.jsonl'
    tmp = out.with_suffix('.jsonl.tmp')
    with tmp.open('w') as f:
        for r in chosen:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
    tmp.replace(out)
    rebuild_search(chosen)
    summary = dict(at=now(), index_path=str(out.relative_to(ROOT)), index_sha256=sha(out), records=len(chosen),
        distinct_urls=len({r['url'] for r in chosen}), provider_groups=len({r['provider_id'] for r in chosen}),
        hosts=len({r['host'] for r in chosen}), by_kind=dict(Counter(r['kind'] for r in chosen)),
        by_review_state=dict(Counter(r['review_state'] for r in chosen)),
        by_provider=dict(Counter(r['provider_id'] for r in chosen)),
        artline_bindings=sum(len(r['artline_bindings']) for r in chosen),
        available_deduplicated_candidates=len(records), excluded=dict(dropped),
        limitation='Index records are distinct source resources, not distinct publishers or independently verified truths. Existing citations retain their original limitations; only fresh_metadata_verified rows have fresh content checks. No automatic bulk overwrite is authorized by inclusion.')
    save(RUN / 'index-summary.json', summary, immutable=False)
    print(json.dumps({k:v for k,v in summary.items() if k != 'by_provider'}, indent=2))


def rebuild_search(records):
    path = RUN / 'sources.sqlite'
    temp = RUN / 'sources.sqlite.tmp'
    if temp.exists():
        temp.unlink()
    with sqlite3.connect(temp) as db:
        db.executescript('''CREATE TABLE resources(id TEXT PRIMARY KEY,url TEXT UNIQUE NOT NULL,title TEXT,kind TEXT,provider_id TEXT,review_state TEXT,record_json TEXT NOT NULL);
            CREATE INDEX resources_provider ON resources(provider_id,kind);
            CREATE TABLE bindings(resource_id TEXT,entity_type TEXT,entity_id TEXT,label TEXT,PRIMARY KEY(resource_id,entity_type,entity_id));
            CREATE INDEX bindings_entity ON bindings(entity_type,entity_id);
            CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED,title,provider,url,labels);''')
        for r in records:
            db.execute('INSERT INTO resources VALUES(?,?,?,?,?,?,?)', (r['id'],r['url'],r['title'],r['kind'],r['provider_id'],r['review_state'],json.dumps(r,ensure_ascii=False)))
            db.executemany('INSERT OR IGNORE INTO bindings VALUES(?,?,?,?)', [(r['id'],b['entity_type'],b['entity_id'],b['label']) for b in r['artline_bindings']])
            db.execute('INSERT INTO search VALUES(?,?,?,?,?)', (r['id'],r['title'],r['provider_name'],r['url'],' '.join(b['label'] for b in r['artline_bindings'])))
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    temp.replace(path)


def search(query, limit=15):
    with sqlite3.connect(f'file:{RUN / "sources.sqlite"}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for r in db.execute('SELECT r.id,r.title,r.kind,r.provider_id,r.review_state,r.url FROM search s JOIN resources r ON r.id=s.id WHERE search MATCH ? ORDER BY rank LIMIT ?', (query,limit)):
            print(json.dumps(dict(r),ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['export','build','search','activity'])
    parser.add_argument('--limit', type=int, default=20000)
    parser.add_argument('--query')
    args = parser.parse_args()
    if args.command == 'export':
        export()
    elif args.command == 'build':
        build(args.limit)
    elif args.command == 'activity':
        with connect() as db:
            for r in db.execute("SELECT pid,state,wait_event_type,wait_event,extract(epoch from now()-query_start)::int seconds,left(query,160) query FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() AND application_name='' AND query NOT ILIKE '%member%' ORDER BY query_start LIMIT 15"):
                print(json.dumps(r,default=str))
    else:
        search(args.query, min(args.limit,100))
