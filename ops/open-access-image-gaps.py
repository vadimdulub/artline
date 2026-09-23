#!/usr/bin/env python3
"""Bounded, artist-balanced Met/Cleveland image gaps; preserve catalogue metadata."""
import argparse
import collections
import concurrent.futures
import csv
import fcntl
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unicodedata

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT/'ops/overnight-image-campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)
core = campaign.core
SCHEMES = {p: campaign.SCHEMES[p] for p in ('met', 'cleveland')}
VERSION = 'artist-balanced-open-access-gaps-v1'


def norm(value):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(
        c for c in unicodedata.normalize('NFKD', str(value or '').casefold())
        if not unicodedata.combining(c))))


def verify_identity(image):
    raw = image['raw']
    provider = image['provider']
    if provider == 'met':
        accession = raw.get('accessionNumber')
        names = [raw.get('artistDisplayName')]
        if raw.get('isPublicDomain') is not True or raw.get('rightsAndReproduction'):
            raise ValueError('Current source image rights are not explicitly open')
        expected_url = raw.get('primaryImage') if image.get('source_view')=='original' else raw.get('primaryImageSmall')
        core.validate_source_image_identity(dict(image,source_image_url=raw.get('primaryImageSmall')))
    else:
        accession = raw.get('accession_number')
        makers = raw.get('creators') or []
        principal = [m for m in makers if m.get('role') == 'artist' and not m.get('qualifier')]
        if len(principal) != 1 or principal[0].get('extent'):
            raise ValueError('Current source primary creator requires review')
        names = [principal[0].get('description', '').split(' (')[0]]
        if raw.get('share_license_status') != 'CC0' or raw.get('copyright') or raw.get('rights_and_reproductions'):
            raise ValueError('Current source image rights are not explicitly open')
        expected_url = ((raw.get('images') or {}).get('web') or {}).get('url')
    if not accession or norm(accession) != norm(image['accession_number']):
        raise ValueError('Current source accession differs')
    if norm(raw.get('title')) != norm(image['title']):
        raise ValueError('Current source title differs')
    if len(image['artist_slugs']) != 1 or image['roles'] != ['primary']:
        raise ValueError('Current source attribution needs separate review')
    known = {norm(n) for n in [image['artist']] + image['aliases']}
    if len(names) != 1 or norm(names[0]) not in known:
        raise ValueError('Current source artist differs')
    if expected_url != image['source_image_url']:
        raise ValueError('Current source primary image differs')
    campaign.fresh_scope(provider, raw, image)
    core.validate_source_image_identity(image)


original_record = core.image_record
original_attach = core.attach


def image_record(*args):
    image = original_record(*args)
    if image is not None:
        verify_identity(image)
    return image


def attach(db, image, target):
    verify_identity(image)
    with db.transaction():
        row = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',
                         (image['target_ids'][target],)).fetchone()
        if not row:
            raise ValueError('Target record missing')
        current = row['record']
        before = image['before'][target]
        excluded = {'primary_media_id', 'revision', 'updated_at', 'updated_by'}
        if {k:v for k,v in current.items() if k not in excluded} != {k:v for k,v in before.items() if k not in excluded}:
            raise ValueError('Target metadata changed since selection')
        slugs = [r['slug'] for r in db.execute('''SELECT p.slug FROM artwork_artists aa
            JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=%s ORDER BY p.slug''',
            (image['target_ids'][target],)).fetchall()]
        if slugs != image['artist_slugs']:
            raise ValueError('Target creator changed since selection')
        return original_attach(db, image, target)


core.image_record = image_record
core.attach = attach


QUERY = '''SELECT a.id::text artwork_id,a.slug,a.title,a.date_display,a.creation_year_start,
    a.creation_year_end,a.date_precision,a.work_type,a.accession_number,a.status,
    a.primary_media_id::text,e.scheme,e.external_id,e.canonical_url page,e.source_id::text,
    to_jsonb(a) before_record,
    COALESCE((SELECT jsonb_agg(aa.attribution_role ORDER BY aa.attribution_role)
      FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') roles,
    COALESCE((SELECT jsonb_agg(p.slug ORDER BY p.slug) FROM artwork_artists aa
      JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artist_slugs,
    COALESCE((SELECT jsonb_agg(al.alias) FROM artwork_artists aa
      JOIN artist_aliases al ON al.artist_id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') aliases,
    (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa
      JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
    EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id
      WHERE aa.artwork_id=a.id AND ac.country_code IN ('RU','GR')) priority_tradition,
    EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id
      WHERE aa.artwork_id=a.id AND d.is_popular) popular
    FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
    WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND a.status<>'archived'
    AND a.primary_media_id IS NULL AND e.source_id IS NOT NULL
    AND a.work_type IN ('painting','drawing','print','watercolor','fresco')
    AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
    AND artline_has_selection_evidence(a.id)'''


def select(args):
    if (args.run/'candidates.json').exists():
        raise ValueError('Selection already exists; resume its prepare/apply phase')
    dsn = core.cloud_dsn()
    selected, held, availability = [], [], {}
    for provider in args.providers.split(','):
        schemes = SCHEMES[provider]
        with campaign.read_only('postgres://localhost/artline') as db:
            rows = db.execute(QUERY+' ORDER BY a.id,e.scheme', (schemes,)).fetchall()
        by_id = {}
        for r in rows:
            by_id.setdefault(r['artwork_id'], r)
        rows = list(by_id.values())
        availability[provider] = {'eligible_gaps':len(rows), 'artists':len({s for r in rows for s in r['artist_slugs']})}
        if provider == 'met' and args.met_public_domain_index:
            with args.met_public_domain_index.open(encoding='utf-8-sig') as stream:
                hints = {r['Object ID'] for r in csv.DictReader(stream) if r['Is Public Domain']=='True'}
            rows = [r for r in rows if r['external_id'] in hints]
            availability[provider]['public_domain_metadata_leads'] = len(rows)
        if provider == 'cleveland' and args.cleveland_open_index:
            reference = args.cleveland_open_index
            capture = json.loads((reference/'capture.json').read_text())
            hints = set()
            for receipt in capture['pages']:
                data = (reference/'metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes()
                if core.sha(data) != receipt['sha256']:
                    raise ValueError('Cleveland metadata capture checksum differs')
                for record in json.loads(data)['data']:
                    if record.get('share_license_status') == 'CC0' and (record.get('images') or {}).get('web',{}).get('url'):
                        hints.add(str(record['id']))
            rows = [r for r in rows if r['external_id'] in hints]
            availability[provider]['cc0_image_metadata_leads'] = len(rows)
        # A balanced queue visits each creator before adding more of one creator.
        groups = collections.defaultdict(list)
        for row in rows:
            if not row['artist'] or not row['page'] or not row['accession_number']:
                held.append({'artwork_id':row['artwork_id'], 'provider':provider, 'reason':'Required source identity absent'})
                continue
            groups[tuple(row['artist_slugs'])].append(row)
        queue = []
        for key, group in groups.items():
            group.sort(key=lambda r:(r['work_type'] not in ('painting','fresco','watercolor'),
                                     r['creation_year_start'],r['artwork_id']))
            queue.extend((rank,row) for rank,row in enumerate(group[:args.per_artist]))
        queue.sort(key=lambda pair:(pair[0],not pair[1]['priority_tradition'],
                                  pair[1]['work_type'] not in ('painting','fresco','watercolor'),pair[1]['artist']))
        rows = [row for _,row in queue[:args.per_provider]]
        with campaign.read_only(dsn) as db:
            remote = db.execute(QUERY+' AND e.external_id=ANY(%s)',
                                (schemes,[r['external_id'] for r in rows])).fetchall()
        index = collections.defaultdict(list)
        for row in remote:
            index[(row['scheme'],row['external_id'])].append(row)
        for row in rows:
            hits = index[(row['scheme'],row['external_id'])]
            keys = ('title','creation_year_start','creation_year_end','date_precision','work_type',
                    'accession_number','artist_slugs','roles','status')
            if len(hits) != 1 or any(row[k] != hits[0][k] for k in keys):
                held.append({'artwork_id':row['artwork_id'], 'provider':provider,
                             'reason':'Production identity differs, is absent, or already has an image'})
                continue
            remote_row = hits[0]
            before = {'local':row.pop('before_record'), 'cloud':remote_row['before_record']}
            row.update(provider=provider, before=before,
                       target_ids={'local':row['artwork_id'],'cloud':remote_row['artwork_id']})
            selected.append(row)
        print(provider, availability[provider], 'selected', sum(c['provider']==provider for c in selected), flush=True)
    backup = Path('/Users/vadimdulub/Library/Application Support/Artline/backups')/args.run.name
    manifests = {}
    for target in ('local','cloud'):
        value = [{'artwork':c['before'][target], 'artist_slugs':c['artist_slugs'], 'roles':c['roles'],
                  'scheme':c['scheme'],'external_id':c['external_id']} for c in selected]
        path = backup/(target+'-before-images.json')
        core.save_new(path,value)
        manifests[target] = {'path':str(path), 'sha256':core.sha(path.read_bytes()),'records':len(value)}
    core.save_new(args.run/'backups.json',{'at':core.now(),'targets':manifests})
    core.save_new(args.run/'candidates.json',{'created_at':core.now(),'version':VERSION,'candidates':selected})
    core.save_new(args.run/'selection.json',{'at':core.now(),'availability':availability,
        'selected':len(selected),'artists':len({s for c in selected for s in c['artist_slugs']}),
        'per_artist_limit_per_provider':args.per_artist,'per_provider_limit':args.per_provider,
        'types':dict(collections.Counter(c['work_type'] for c in selected)), 'held':held,
        'policy':'Existing museum-connected eligible records; all painters considered, artist-balanced bounded selection. Current object-specific CC0 and identity checks precede image downloads. No new artworks or publication.'})


def run_phase(args):
    for target, entry in json.loads((args.run/'backups.json').read_text())['targets'].items():
        if core.sha(Path(entry['path']).read_bytes()) != entry['sha256']:
            raise ValueError('Recovery preimage checksum differs: '+target)
    rows = json.loads((args.run/'candidates.json').read_text())['candidates']
    latest = core.latest_events(args.run)
    if args.phase == 'prepare':
        done = campaign.TERMINAL | {'prepared','source_rate_limited'}
        rows = [r for r in rows if latest.get(r['artwork_id'],{}).get('outcome') not in done]
        dsn = None
    else:
        reviewed = json.loads((args.run/'reviewed-images.json').read_text())['images']
        approved = {r['artwork_id']:r['sha256'] for r in reviewed}
        rows = [r for r in rows if r['artwork_id'] in approved and latest.get(r['artwork_id'],{}).get('outcome') != 'complete']
        for c in rows:
            image = json.loads((args.run/'images'/c['provider']/(c['artwork_id']+'.json')).read_text())
            if image['sha256'] != approved[c['artwork_id']]:
                raise ValueError('Reviewed image changed')
            verify_identity(image)
        dsn = core.cloud_dsn()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        jobs = []
        for provider in SCHEMES:
            group = [c for c in rows if c['provider']==provider]
            for stripe in range(4):
                part = group[stripe::4]
                if part:
                    jobs.append(pool.submit(core.worker,provider,part,
                        SimpleNamespace(run=args.run,prepare_only=args.phase=='prepare',
                                        upload_prepared_only=args.phase=='apply'),dsn))
        while jobs:
            done, pending = concurrent.futures.wait(jobs,timeout=25,return_when=concurrent.futures.FIRST_COMPLETED)
            for job in done:
                job.result()
            jobs = list(pending)
            events = core.latest_events(args.run)
            print(core.now(),dict(collections.Counter(e['outcome'] for e in events.values())),flush=True)


def select_original_fallback(args):
    if not args.reference_run or not args.external_id:
        raise ValueError('Exact reference run and external object ID required')
    reference=args.reference_run
    candidates=json.loads((reference/'candidates.json').read_text())['candidates']
    hits=[c for c in candidates if c['provider']=='met' and c['external_id']==args.external_id]
    if len(hits)!=1:raise ValueError('Exact candidate identity required')
    c=hits[0]
    event=core.latest_events(reference).get(c['artwork_id'],{})
    if event.get('outcome')!='source_missing' or 'images.metmuseum.org/' not in event.get('error',''):
        raise ValueError('Only a documented missing image derivative permits this fallback')
    im=json.loads((reference/'selected/met'/(c['artwork_id']+'.json')).read_text())
    verify_identity(im)
    im['source_view']='original'
    im['source_image_url']=im['raw']['primaryImage']
    im['fallback_evidence']=event
    verify_identity(im)
    core.save_new(args.run/'backups.json',json.loads((reference/'backups.json').read_text()))
    core.save_new(args.run/'candidates.json',{'candidates':[c],'reference_run':str(reference)})
    core.save_new(args.run/'selected/met'/(c['artwork_id']+'.json'),im)
    print('Selected one exact original image fallback',args.external_id,flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['select','select-original-fallback','prepare','apply'])
    parser.add_argument('--run',required=True,type=Path)
    parser.add_argument('--per-provider',type=int,default=1200)
    parser.add_argument('--per-artist',type=int,default=4)
    parser.add_argument('--providers',default='met,cleveland',choices=['met','cleveland','met,cleveland'])
    parser.add_argument('--met-public-domain-index',type=Path,help='Metadata-only prefilter; current object API rights must still pass')
    parser.add_argument('--cleveland-open-index',type=Path,help='Captured metadata directory prefilter; current object API rights must still pass')
    parser.add_argument('--reference-run',type=Path)
    parser.add_argument('--external-id')
    args = parser.parse_args()
    if not 1 <= args.per_provider <= 2500 or not 1 <= args.per_artist <= 10:
        raise ValueError('Use a bounded selection of at most 2,500 works per provider and 10 per artist')
    args.run.mkdir(parents=True,exist_ok=True)
    with (args.run/'campaign.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.phase=='select':
            select(args)
        elif args.phase=='select-original-fallback':
            select_original_fallback(args)
        else:
            run_phase(args)


if __name__=='__main__':
    main()
