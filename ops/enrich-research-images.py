#!/usr/bin/env python3
"""Attach exact, rights-cleared SMK images to existing research review records.

Uses the immutable research identity chain; does not assert accepted holdings,
resolve creators, change source metadata, or publish review records.
"""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import quote

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image

spec = importlib.util.spec_from_file_location('museum_images', Path(__file__).with_name('enrich-artwork-images.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
VERSION = 'verified-research-smk-images-v1'
PROVIDER = 'smk'

IDENTITY = '''SELECT a.id::text AS artwork_id,a.primary_media_id::text,a.title,
 a.slug,a.creation_year_start,a.creation_year_end,a.date_precision,
 l.snapshot_id::text,l.source_key,l.record_kind,l.research_record_id,l.object_key,
 l.entry_sha256,l.plan_sha256,r.facts_sha256,r.facts_json,r.source_object_id AS external_id,
 r.object_url AS page,c.source_id::text
 FROM research_artwork_links l JOIN artworks a ON a.id=l.artwork_id
 JOIN research_resolutions r ON r.snapshot_id=l.snapshot_id
 AND r.research_source_key=l.source_key AND r.research_record_kind=l.record_kind
 AND r.research_record_id=l.research_record_id AND 'smk:'||r.source_object_id=l.object_key
 JOIN citations c ON c.entity_type='artwork' AND c.entity_id=a.id
 AND c.field_name='unresolved_source_match' AND c.source_record_id=r.source_object_id
 AND c.source_url=r.object_url
 WHERE l.disposition='created' AND r.source_kind='smk'
 AND a.research_candidate AND a.status='review' AND r.date_scope='eligible'
 AND a.title=r.facts_json->>'title'
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
'''
KEYS = ('artwork_id','slug','title','creation_year_start','creation_year_end','date_precision',
        'snapshot_id','source_key','record_kind','research_record_id','object_key',
        'entry_sha256','plan_sha256','facts_sha256','external_id','page','source_id')


def lookup(db, candidate, lock=False):
    rows = db.execute(IDENTITY + ''' AND l.source_key=%s AND l.record_kind=%s
        AND l.research_record_id=%s AND a.id=%s''' + (' FOR UPDATE OF a' if lock else ''),
        (candidate['source_key'],candidate['record_kind'],candidate['research_record_id'],candidate['artwork_id'])).fetchall()
    if len(rows) != 1 or any(rows[0][k] != candidate[k] for k in KEYS):
        raise ValueError('Research identity or eligibility changed')
    return rows[0]


def unchanged_state(db, ids):
    # Capture every artwork field except the four fields this media-only action owns,
    # plus complete creator links. No materialized collection-wide joins.
    rows = db.execute('''SELECT a.id::text AS id,
      to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] AS metadata,
      coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
        FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) AS creators
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
    return {r['id']:core.sha(core.encode(r)) for r in rows}


def select(args):
    if (args.run/'candidates.json').exists():
        candidates=json.loads((args.run/'candidates.json').read_text())['candidates']
        return preflight(args,candidates)
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        candidates = db.execute(IDENTITY + " AND a.primary_media_id IS NULL ORDER BY a.id LIMIT 1000").fetchall()
        if len(candidates) == 1000:
            raise ValueError('Selection bound reached; review scope before increasing')
        if len({c['artwork_id'] for c in candidates}) != len(candidates):
            raise ValueError('Ambiguous research identity')
        for c in candidates:
            c.update(provider='smk',scheme='research-artwork-link',
                     artist=c['facts_json']['painter']['name'])
        core.save_new(args.run/'candidates.json',{'selected_at':core.now(),'candidates':candidates,
          'selection_basis':'Existing dated review paintings with exact official SMK research object and source citation; images do not resolve creator or holding assertions'})
        if candidates:
            plan=db.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+IDENTITY+
              ' AND l.source_key=%s AND l.record_kind=%s AND l.research_record_id=%s AND a.id=%s',
              tuple(candidates[0][k] for k in ('source_key','record_kind','research_record_id','artwork_id'))).fetchone()
            core.save_new(args.run/'identity-query-plan.json',plan)
    preflight(args,candidates)


def preflight(args,candidates):
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            identities={}
            rows=db.execute(IDENTITY+' AND l.source_key=%s AND l.record_kind=%s AND l.research_record_id=ANY(%s)',
              ('supplied-registry','catalogue_object',[c['research_record_id'] for c in candidates])).fetchall()
            grouped=collections.defaultdict(list)
            for row in rows:grouped[row['research_record_id']].append(row)
            for c in candidates:
                rows=grouped[c['research_record_id']]
                varying=('artwork_id','snapshot_id','source_id')
                if len(rows)!=1 or any(rows[0][k]!=c[k] for k in KEYS if k not in varying):
                    raise ValueError('Cross-database research provenance mismatch')
                identities[c['artwork_id']]={k:rows[0][k] for k in varying}
            core.save_new(args.run/(target+'-identities.json'),identities)
            ids=[r['artwork_id'] for r in identities.values()]
            core.save_new(args.run/(target+'-before.json'),unchanged_state(db,ids))
    print('Selected and matched in both databases:',len(candidates),flush=True)


original_image_record=core.image_record


def validate_current(c, raw):
    if raw.get('object_number') != c['external_id']:
        raise ValueError('Exact SMK object/side mismatch')
    if c['title'] not in [t.get('title') for t in raw.get('titles',[])]:
        raise ValueError('Current museum title differs from research record')
    creator_id=c['facts_json']['painter']['source_id']
    if creator_id not in [p.get('creator_lref') for p in raw.get('production',[])]:
        raise ValueError('Current museum source creator differs')
    dates=raw.get('production_date',[])
    if not dates or any(not d.get('start') or not d.get('end') for d in dates):
        raise ValueError('Fresh museum date needs review')
    starts=[int(d['start'][:4]) for d in dates]
    ends=[int(d['end'][:4]) for d in dates]
    if max(ends)>1970 or min(starts)!=c['creation_year_start'] or max(ends)!=c['creation_year_end']:
        raise ValueError('Fresh museum date differs or exceeds cutoff')


def image_record(c, fetcher, nga, chicago):
    image=original_image_record(c,fetcher,nga,chicago)
    if image is None:
        items=fetcher.metadata('https://api.smk.dk/api/v1/art?object_number='+quote(c['external_id'],safe='')).get('items',[])
        raw=next((r for r in items if r.get('object_number')==c['external_id']),None)
        if raw and raw.get('public_domain') is True and raw.get('rights')==core.POLICIES['smk'] and raw.get('has_image'):
            # Some official primary JPEGs use accession filenames instead of UUIDs.
            urls=[raw.get('image_native',''),raw.get('image_thumbnail','')]
            url=next((u for u in urls if re.fullmatch(r'https://api\.smk\.dk/api/v1/thumbnail/[A-Za-z0-9_-]{1,100}\.(?:jpg|JPG)',u or '')),None)
            if url:
                image={**c,'source_image_url':url,'raw':raw,'rights_status':'public_domain',
                  'license_label':'Public Domain Mark 1.0','policy_url':core.POLICIES['smk'],'checked_at':core.now()}
    if image:
        validate_current(c,image['raw'])
        image['research_image_only']=True
    return image


def attach(db, image, target):
    with db.transaction(),db.pipeline() as pipeline:
        db.execute("SET LOCAL lock_timeout='2s'")
        pipeline.sync()
        row=lookup(db,{**image,**image['targets'][target]},lock=True)
        if row['primary_media_id']:
            if row['primary_media_id']!=image['media_id']:
                raise ValueError('Existing media preserved; attachment requires review')
            return 'attached'
        db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,
          mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,
          creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
          VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(id) DO NOTHING''',(image['media_id'],image['path'],image['page'],core.PROVIDERS[image['provider']],
          image['width'],image['height'],image['bytes'],image['sha256'],image['title']+' — '+image['artist'],
          image['rights_status'],image['license_label'],image['policy_url'],image['artist'],
          image['artist']+'. '+image['title']+'. '+core.PROVIDERS[image['provider']]+'. '+image['license_label']+'. Compressed full-frame reproduction; catalogue record remains in review.',
          image['downloaded_at'],image['checked_at'],core.ACTOR))
        db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,
          source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(media_id) DO NOTHING''',
          (image['media_id'],row['source_id'],image['external_id'],core.sha(core.encode(image['raw'])),
          image['source_image_url'],image['policy_url'],
          image.get('identity_basis','Exact immutable research object link, current museum title, creator source ID, creation dates and explicit per-image public-domain evidence. Image only; unresolved catalogue metadata remains in review.'),
          VERSION,image['checked_at'],Jsonb(image)))
        db.execute('''UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s
          WHERE id=%s AND primary_media_id IS NULL''',(image['media_id'],core.ACTOR,row['artwork_id']))
    return 'attached'


def validate_rights(image):
    if image['raw'].get('public_domain') is not True or image['raw'].get('rights')!=core.POLICIES['smk']:
        raise ValueError('Missing explicit current museum image rights')


def verify(args, candidates):
    latest={}
    for line in (args.run/'events.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r.get('artwork_id'):latest[r['artwork_id']]=r
    receipts=[json.loads(p.read_text()) for p in (args.run/'images'/PROVIDER).glob('*.json')]
    errors=[]
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    objects={b.name:b for b in bucket.list_blobs(prefix='assets/artworks/open-museums/'+PROVIDER+'/')}
    for r in receipts:
        data=(core.ROOT/'apps/web/public'/r['path'].lstrip('/')).read_bytes()
        with Image.open(core.ROOT/'apps/web/public'/r['path'].lstrip('/')) as im:im.verify()
        blob=objects.get(r['path'].lstrip('/'))
        if len(data)>100000 or len(data)!=r['bytes'] or core.sha(data)!=r['sha256']:
            errors.append([r['artwork_id'],'local bytes/hash'])
        if not blob or blob.size!=len(data) or blob.md5_hash!=base64.b64encode(hashlib.md5(data).digest()).decode():
            errors.append([r['artwork_id'],'GCS bytes/hash'])
        validate_current(r,r['raw'])
        validate_rights(r)
        if latest.get(r['artwork_id'],{}).get('outcome')!='complete':
            errors.append([r['artwork_id'],'not completed'])
    databases={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            before=json.loads((args.run/(target+'-before.json')).read_text())
            identities=json.loads((args.run/(target+'-identities.json')).read_text())
            after=unchanged_state(db,[r['artwork_id'] for r in identities.values()])
            expected=dict(before)
            external=0
            reconciliation=args.run/'verified-concurrent-creator-changes.json'
            if reconciliation.exists():
                record=json.loads(reconciliation.read_text())
                if record['target']==target:
                    if core.sha((core.ROOT/record['external_plan']).read_bytes())!=record['external_plan_sha256']:
                        raise ValueError('Concurrent creator plan changed')
                    for change in record['changes']:
                        if before.get(change['artwork_id'])!=change['before_sha256'] or change['reconstructed_baseline_matches'] is not True:
                            raise ValueError('Concurrent change does not match original baseline')
                        expected[change['artwork_id']]=change['after_sha256']
                        external+=1
            if expected!=after:errors.append([target,'unaccounted review metadata/creator link changes'])
            identity_rows=db.execute(IDENTITY+' AND a.id=ANY(%s::uuid[])',
              ([r['targets'][target]['artwork_id'] for r in receipts],)).fetchall()
            identity_map={r['artwork_id']:r for r in identity_rows}
            media_rows=db.execute('''SELECT m.*,e.source_id::text AS evidence_source_id,e.source_record_id,
              e.source_checksum,e.evidence_json FROM media_assets m
              JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])''',
              ([r['media_id'] for r in receipts],)).fetchall()
            media_map={str(r['id']):r for r in media_rows}
            for r in receipts:
                expected={**r,**r['targets'][target]}
                row=identity_map.get(expected['artwork_id'])
                if not row or any(row[k]!=expected[k] for k in KEYS):
                    errors.append([target,r['artwork_id'],'research identity mismatch']);continue
                m=media_map.get(r['media_id'])
                if row['primary_media_id']!=r['media_id'] or not m:
                    errors.append([target,r['artwork_id'],'missing attachment/evidence']);continue
                mapping={'storage_path':'path','checksum_sha256':'sha256','byte_size':'bytes','width':'width',
                  'height':'height','rights_status':'rights_status','license_label':'license_label',
                  'license_url':'policy_url','source_page_url':'page','creator_credit':'artist',
                  'source_record_id':'external_id'}
                if any(m[k]!=r[v] for k,v in mapping.items()) or m['source_checksum']!=core.sha(core.encode(r['raw'])) or m['evidence_json']!=r:
                    errors.append([target,r['artwork_id'],'media/evidence mismatch'])
                if m['evidence_source_id']!=r['targets'][target]['source_id']:
                    errors.append([target,r['artwork_id'],'source provenance mismatch'])
            databases[target]={'verified_images':len(receipts),'unchanged_review_records':sum(after[k]==before.get(k) for k in after),
              'verified_external_creator_updates':external}
    report={'checked_at':core.now(),'selected':len(candidates),'images':len(receipts),
      'bytes':sum(r['bytes'] for r in receipts),'max_bytes':max((r['bytes'] for r in receipts),default=0),
      'outcomes':dict(collections.Counter(r['outcome'] for r in latest.values())),
      'databases':databases,'errors':errors}
    core.save_new(args.run/args.report,report)
    print(json.dumps(report,indent=2),flush=True)
    if errors:raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['select','apply','verify'])
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--retry-no-image',action='store_true',help='Recheck cached unavailable-image metadata after an adapter fix')
    parser.add_argument('--report',default='verification-final.json')
    args=parser.parse_args()
    args.run.mkdir(parents=True,exist_ok=True)
    if args.phase=='select':return select(args)
    candidates=json.loads((args.run/'candidates.json').read_text())['candidates']
    identities={t:json.loads((args.run/(t+'-identities.json')).read_text()) for t in ['local','cloud']}
    for c in candidates:
        c['targets']={t:identities[t][c['artwork_id']] for t in identities}
    if args.phase=='verify':return verify(args,candidates)
    for target in ['local','cloud']:
        if not (args.run/(target+'-before.json')).exists():raise ValueError('Both preflight snapshots required')
    done=set()
    if (args.run/'events.jsonl').exists():
        for line in (args.run/'events.jsonl').read_text().splitlines():
            e=json.loads(line)
            if e['outcome']=='complete' or (e['outcome']=='no_explicit_open_image' and not args.retry_no_image) or (args.prepare_only and e['outcome']=='prepared'):
                done.add(e['artwork_id'])
    pending=[c for c in candidates if c['artwork_id'] not in done]
    core.attach=attach
    core.image_record=image_record
    core.VERSION=VERSION
    print('Pending:',len(pending),flush=True)
    core.worker('smk',pending[:args.limit] if args.limit else pending,args,None if args.prepare_only else core.cloud_dsn())
    print(dict(core.COUNTS),flush=True)


if __name__=='__main__':main()
