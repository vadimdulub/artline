#!/usr/bin/env python3
"""Source-backed, reproducible key-work selections. No publication changes."""
import argparse
import collections
import concurrent.futures
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import time

import requests
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/painter-key-artworks-20261008'
BACKUP = Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008'
spec = importlib.util.spec_from_file_location('alignment', ROOT / 'ops/align-catalogues-20261008.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def save(name, value):
    base.save(RUN / name, value)


def export(target):
    with base.connect(target) as db:
        artists = db.execute("""SELECT a.id,a.slug,a.display_name,a.status,a.entity_type,
        ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist'
          AND e.entity_id=a.id AND e.scheme='wikidata') wikidata
        FROM artists a WHERE a.status<>'archived' ORDER BY a.id""").fetchall()
        save(target + '-artists.json.gz', artists)
        works = []
        for offset in range(0, len(artists), 500):
            ids = [a['id'] for a in artists[offset:offset+500]]
            rows = db.execute("""SELECT aa.artist_id,aa.attribution_role,aa.representative_order,
            w.id,w.slug,w.title,w.date_display,w.creation_year_start,w.creation_year_end,w.date_precision,
            w.status,w.work_type,w.primary_media_id,w.current_institution_id,
            artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision) creation_scope,
            m.storage_path,m.source_page_url,m.width,m.height
            FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id
            LEFT JOIN media_assets m ON m.id=w.primary_media_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND w.status<>'archived'""", (ids,)).fetchall()
            work_ids = list({w['id'] for w in rows})
            enriched = {w:dict(wikidata=[], identifiers=[], citations=[], highlights=[]) for w in work_ids}
            for e in db.execute("SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(work_ids,)):
                if e['scheme']=='wikidata': enriched[e['entity_id']]['wikidata'].append(e['external_id'])
                if e['canonical_url']: enriched[e['entity_id']]['identifiers'].append(e['canonical_url'])
            for c in db.execute("SELECT entity_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(work_ids,)):
                if c['source_url']: enriched[c['entity_id']]['citations'].append(c['source_url'])
            for c in db.execute("SELECT ci.artwork_id,ci.source_url FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id WHERE ci.artwork_id=ANY(%s::uuid[]) AND cc.curator_kind='museum' AND cc.status<>'archived' AND ci.source_url IS NOT NULL",(work_ids,)):
                enriched[c['artwork_id']]['highlights'].append(c['source_url'])
            for w in rows:
                w.update({k:sorted(set(v)) for k,v in enriched[w['id']].items()})
            works.extend(rows)
            db.commit()
            if offset%5000==0: print(target,'exported',offset+len(ids),'artists',flush=True)
        save(target + '-works.json.gz', works)
        by_artist = collections.defaultdict(list)
        for w in works:
            by_artist[str(w['artist_id'])].append(w)
        summary = dict(artists=len(artists),works=len(works),with_works=len(by_artist),
          with_eligible_image=sum(any(w['creation_scope']=='eligible' and w['storage_path'] for w in ws) for ws in by_artist.values()))
        save(target + '-coverage.json', summary)
        print(target, json.dumps(summary), flush=True)


def notable():
    qids = sorted({q for target in ['local','production'] for a in base.load(RUN / (target+'-artists.json.gz')) for q in a['wikidata']})
    batches = [qids[i:i+150] for i in range(0,len(qids),150)]
    def fetch(batch):
        query = 'SELECT ?artist ?work WHERE { VALUES ?artist { ' + ' '.join('wd:'+q for q in batch) + ' } ?artist wdt:P800 ?work . ?work wdt:P170 ?artist . }'
        key=hashlib.sha256(query.encode()).hexdigest()
        path=RUN / 'notable' / (key+'.json')
        if path.exists(): return len(base.load(path)['results']['bindings'])
        for attempt in range(3):
            try:
                r=requests.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=55)
                r.raise_for_status()
                data=r.json(); base.save(path,data)
                return len(data['results']['bindings'])
            except Exception as e:
                if attempt==2: return {'error':str(e).split('?')[0],'batch':key}
                time.sleep(2*(attempt+1))
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(fetch,batches)):
            results.append(result)
            if (i+1)%10==0: print('notable batches',i+1,'/',len(batches),flush=True)
    save('notable-results.json',results)
    print('notable',len(qids),'artists',sum(r for r in results if isinstance(r,int)),'relations',flush=True)


def research():
    artists=base.load(RUN/'local-artists.json.gz')
    works=base.load(RUN/'local-works.json.gz')
    illustrated={w['artist_id'] for w in works if w['creation_scope']=='eligible' and w['storage_path']}
    qids=sorted({q for a in artists if a['id'] not in illustrated for q in a['wikidata']})
    batches=[qids[i:i+50] for i in range(0,len(qids),50)]
    def fetch(batch):
        # Aggregate on the source: return one selected eligible museum-connected
        # image candidate per painter, never download whole artist oeuvres.
        query='''SELECT ?artist (MIN(STR(?work)) AS ?selected) WHERE { VALUES ?artist { '''+' '.join('wd:'+q for q in batch)+''' }
        ?work wdt:P170 ?artist; wdt:P571 ?date; wdt:P18 ?image; wdt:P195 ?collection .
        FILTER(YEAR(?date)<=1970)
        FILTER NOT EXISTS { ?work wdt:P571 ?later . FILTER(YEAR(?later)>1970) }
        } GROUP BY ?artist'''
        key=hashlib.sha256(query.encode()).hexdigest(); path=RUN/'gap-candidates'/(key+'.json')
        if path.exists(): return len(base.load(path)['results']['bindings'])
        for attempt in range(3):
            try:
                r=requests.get('https://query.wikidata.org/sparql',params={'query':query,'format':'json'},headers={'User-Agent':'Artline/1.0 (selected painter artwork research; artlines.org)'},timeout=55)
                r.raise_for_status(); data=r.json(); base.save(path,data)
                return len(data['results']['bindings'])
            except Exception as e:
                if attempt==2: return dict(error=str(e).split('?')[0],batch=key)
                time.sleep(2*(attempt+1))
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for i,result in enumerate(pool.map(fetch,batches)):
            results.append(result)
            if (i+1)%10==0: print('gap batches',i+1,'/',len(batches),flush=True)
    save('gap-results.json',dict(artists=qids,results=results))
    print('gaps',len(qids),'artists',sum(r for r in results if isinstance(r,int)),'selected candidates',flush=True)


def plan(target):
    artists=base.load(RUN/(target+'-artists.json.gz'))
    works=base.load(RUN/(target+'-works.json.gz'))
    notable_by_artist=collections.defaultdict(set)
    for p in (RUN/'notable').glob('*.json'):
        for row in base.load(p)['results']['bindings']:
            notable_by_artist[row['artist']['value'].split('/')[-1]].add(row['work']['value'].split('/')[-1])
    grouped=collections.defaultdict(list)
    for w in works: grouped[w['artist_id']].append(w)
    selections=[]; unresolved=[]
    for artist in artists:
        candidates=[]
        notable_ids=set().union(*(notable_by_artist[q] for q in artist['wikidata']))
        for work in grouped[artist['id']]:
            sources=sorted({u for u in work['identifiers']+work['citations']+[work['source_page_url']] if u and u.startswith(('https://','http://'))})
            if work['creation_scope']!='eligible' or not sources or work['attribution_role']=='formerly_attributed_to': continue
            notable_matches=sorted(set(work['wikidata'])&notable_ids)
            # Exact canonical source/creator match, reviewed against the captured
            # WikiArt Mona Lisa page. Never a title-only cross-painter match.
            mona=artist['slug']=='leonardo-da-vinci' and any(re.fullmatch(r'https?://(?:www\.)?wikiart.org/en/leonardo-da-vinci/mona-lisa/?',u) for u in sources)
            basis='notable_work' if notable_matches or mona else 'museum_highlight' if work['highlights'] else 'curated_representative' if work['representative_order'] else 'editorial_representative'
            image=bool(re.fullmatch(r'/assets/[a-zA-Z0-9/_-]+\.(?:jpg|jpeg|png|webp|avif)',work['storage_path'] or ''))
            # Published painters must have a public opening work where one exists.
            # Imagery and secure authorship precede editorial tie-breaks. A museum
            # holding alone is NOT labelled a museum-designated highlight.
            score=(artist['status']=='published' and work['status']!='published', not image,
                work['attribution_role']!='primary',not mona,
                ['notable_work','museum_highlight','curated_representative','editorial_representative'].index(basis),
                work['representative_order'] or 99,
                work['work_type'] not in ('painting','fresco','icon'),
                not bool(work['current_institution_id']),
                -min(work['width'] or 0,work['height'] or 0,1600), work['slug'],work['id'])
            evidence=dict(artist_slug=artist['slug'],artist_name=artist['display_name'],artwork_slug=work['slug'],artwork_title=work['title'],
              recorded_date=work['date_display'],creation_scope=work['creation_scope'],attribution_role=work['attribution_role'],
              notable_work_ids=notable_matches,notable_artist_ids=artist['wikidata'] if notable_matches else [],
              museum_highlight_sources=work['highlights'],representative_order=work['representative_order'],
              image_available=image,selection_policy='source-backed opening artwork v1; editorial representative unless an explicit notable/highlight/curated designation exists',
              canonical_source_review='https://www.wikiart.org/en/leonardo-da-vinci/mona-lisa' if mona else None,
              publication_preserved=work['status'],catalogue_metadata_unchanged=True)
            for q in evidence['notable_artist_ids']: sources.append('https://www.wikidata.org/wiki/'+q+'#P800')
            candidates.append((score,dict(artist_id=artist['id'],artwork_id=work['id'],attribution_role=work['attribution_role'],selection_basis=basis,source_urls=sorted(set(sources)),evidence_json=evidence,selection_batch='painter-key-artworks-20261008')))
        if candidates: selections.append(min(candidates,key=lambda c:c[0])[1])
        else: unresolved.append(dict(artist_id=artist['id'],slug=artist['slug'],name=artist['display_name'],wikidata=artist['wikidata'],reason='no_linked_artwork' if not grouped[artist['id']] else 'no_verified_eligible_source_backed_work'))
    save(target+'-plan.json.gz',selections);save(target+'-unresolved.json.gz',unresolved)
    summary=dict(artists=len(artists),selected=len(selections),with_images=sum(s['evidence_json']['image_available'] for s in selections),unresolved=len(unresolved),bases=dict(collections.Counter(s['selection_basis'] for s in selections)))
    save(target+'-plan-summary.json',summary);print(target,json.dumps(summary),flush=True)


def apply(target):
    path=RUN/(target+'-plan.json.gz'); rows=base.load(path)
    migration=ROOT/'apps/server/db/migrations/0037_artist_key_artworks.sql'
    with base.connect(target,readonly=False) as db:
        db.execute('SELECT pg_advisory_xact_lock(%s)',(20250907001,))
        present=db.execute('SELECT 1 FROM schema_migrations WHERE filename=%s',(migration.name,)).fetchone()
        if not present:
            db.execute(migration.read_text())
            db.execute('INSERT INTO schema_migrations(filename) VALUES (%s)',(migration.name,))
        before=db.execute('SELECT * FROM artist_key_artworks ORDER BY artist_id').fetchall()
        base.save(BACKUP/(target+'-key-artworks-before.json.gz'),before)
        assert not before, 'Existing selections require an explicit reconciliation plan'
        for offset in range(0,len(rows),500):
            batch=rows[offset:offset+500]
            valid=db.execute("""SELECT count(*) n FROM jsonb_to_recordset(%s) AS p(artist_id uuid,artwork_id uuid,attribution_role text,evidence_json jsonb)
            JOIN artworks w ON w.id=p.artwork_id JOIN artists a ON a.id=p.artist_id
            JOIN artwork_artists aa ON aa.artwork_id=w.id AND aa.artist_id=a.id AND aa.attribution_role=p.attribution_role
            WHERE a.status<>'archived' AND w.status<>'archived' AND w.slug=p.evidence_json->>'artwork_slug'
            AND w.status=p.evidence_json->>'publication_preserved'
            AND artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision)='eligible'""",(Jsonb(batch),)).fetchone()['n']
            assert valid==len(batch),('stale selection batch',offset)
        with db.cursor() as cur:
            cur.executemany('''INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch)
            VALUES (%s,%s,%s,%s,%s,%s,%s)''',[(r['artist_id'],r['artwork_id'],r['attribution_role'],r['selection_basis'],r['source_urls'],Jsonb(r['evidence_json']),r['selection_batch']) for r in rows])
        after=db.execute('SELECT * FROM artist_key_artworks ORDER BY artist_id').fetchall()
        assert len(after)==len(rows)
        base.save(BACKUP/(target+'-key-artworks-after.json.gz'),after)
    save(target+'-receipt.json',dict(at=base.now(),count=len(rows),plan_sha256=base.digest(path),migration_sha256=base.digest(migration),publication_changes=0,artwork_metadata_changes=0))
    print(target,'applied',len(rows),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['export','notable','research','plan','apply'])
    parser.add_argument('--target',choices=['local','production'],default='local')
    args=parser.parse_args()
    if args.action=='export': export(args.target)
    elif args.action=='notable': notable()
    elif args.action=='research': research()
    elif args.action=='plan': plan(args.target)
    else: apply(args.target)
