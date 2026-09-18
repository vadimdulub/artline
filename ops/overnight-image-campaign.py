#!/usr/bin/env python3
"""Resumable selected-image campaign; no artwork metadata or review-state changes.

Exact existing museum identifiers are matched in both catalogues before work.
Fresh museum media rights and artwork classification precede every download.
Receipts include canonical licence URIs and the museum policy separately.
"""
import argparse, collections, concurrent.futures, importlib.util, json, re, time
from pathlib import Path
from types import SimpleNamespace

import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('museum_core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
VERSION='overnight-exact-painted-images-v1'
core.VERSION=VERSION
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
PDM='https://creativecommons.org/publicdomain/mark/1.0/'
SCHEMES={p:[core.SCHEMES[p]] for p in ('met','chicago','cleveland','smk')}
SCHEMES['met']+=['met-object'];SCHEMES['chicago']+=['aic-object'];SCHEMES['cleveland']+=['cleveland-object']
POLICIES=dict(core.POLICIES)
TERMINAL={'complete','no_explicit_open_image','metadata_needs_review','source_missing','failed'}

BaseFetcher=core.Fetcher
class CampaignFetcher(BaseFetcher):
    def metadata(self,url):
        if url.startswith('https://api.artic.edu/api/v1/artworks?ids='):
            url=url.replace('main_reference_number','main_reference_number,artwork_type_title,classification_title,credit_line')
        return super().metadata(url)
core.Fetcher=CampaignFetcher

original_event=core.event
def event(run,value):
    if value.get('outcome')=='failed':
        error=value.get('error','')
        if '404 Client Error' in error:value={**value,'outcome':'source_missing'}
        elif error.startswith(('Current source','Current museum','Reversed source','Fresh museum')):
            value={**value,'outcome':'metadata_needs_review'}
    return original_event(run,value)
core.event=event

def fresh_scope(provider,raw,candidate):
    """The source must support the existing artwork class and dates <=1970."""
    if provider=='met':
        kind=' '.join(str(raw.get(k,'')) for k in ('objectName','classification')).casefold()
        dates=[raw.get('objectBeginDate'),raw.get('objectEndDate')]
    elif provider=='chicago':
        kind=' '.join(str(raw.get(k,'')) for k in ('artwork_type_title','classification_title')).casefold()
        dates=[raw.get('date_start'),raw.get('date_end')]
    elif provider=='cleveland':
        kind=str(raw.get('type','')).casefold()
        dates=[raw.get('creation_date_earliest'),raw.get('creation_date_latest')]
    elif provider=='smk':
        kinds=raw.get('object_names') or []
        kind=' '.join(str(x) for x in kinds).casefold()
        spans=raw.get('production_date') or []
        if not spans:raise ValueError('Current source date missing')
        dates=[]
        for s in spans:
            for k in ('start','end'):
                if not re.match(r'^\d{4}-',str(s.get(k,''))):raise ValueError('Current source date needs review')
                dates.append(int(s[k][:4]))
    else:raise ValueError('Unreviewed source adapter')
    expected=candidate.get('work_type','painting')
    allowed={'painting':('painting','maleri','ikon'),'fresco':('fresco','painting','maleri'),
      'watercolor':('watercolor','watercolour','akvarel','painting'),
      'drawing':('drawing','tegning','pastel','watercolor','watercolour','akvarel'),
      'print':('print','etching','engraving','lithograph','woodcut','tryk','radering','kobberstik','træsnit','litografi','grafik')}
    if expected not in allowed or not any(x in kind for x in allowed[expected]):
        raise ValueError('Current source classification needs review')
    denied=('photograph','sculpture')+(('print','etching','engraving') if expected in ('painting','fresco','watercolor') else ())
    if any(x in kind for x in denied):
        raise ValueError('Current source classification conflict')
    if not dates or any(not isinstance(y,int) or isinstance(y,bool) or not 1000<=y<=1970 for y in dates):
        raise ValueError('Current source date outside 1000–1970 or missing')
    if dates[0]>dates[-1]:raise ValueError('Reversed source date')
    lo,hi=min(dates),max(dates)
    if hi<candidate['creation_year_start'] or lo>candidate['creation_year_end']:
        raise ValueError('Current museum date contradicts catalogue interval')
    return {'source_classification':kind,'source_year_start':lo,'source_year_end':hi}

original_record=core.image_record
def image_record(c,fetcher,nga,chicago):
    if c['provider']=='chicago':
        # The older shared batch adapter omits type fields; fetch the exact record.
        raw=chicago.get(c['external_id'])
        if raw is None or 'artwork_type_title' not in raw:
            raw=fetcher.metadata('https://api.artic.edu/api/v1/artworks/'+c['external_id'])['data']
        if str(raw.get('id'))!=c['external_id']:raise ValueError('Chicago identity mismatch')
        chicago={c['external_id']:raw}
    im=original_record(c,fetcher,nga,chicago)
    if im is None:return None
    im['scope_evidence']=fresh_scope(c['provider'],im['raw'],c)
    im['museum_policy_url']=POLICIES[c['provider']]
    im['policy_url']=PDM if im['rights_status']=='public_domain' else CC0
    raw=im['raw']; credit=raw.get('credit_line') or raw.get('creditLine') or raw.get('creditline') or ''
    if not isinstance(credit,str):credit=''
    im.update(source_name=core.PROVIDERS[c['provider']],source_record_url=c['page'],
       image_url=im['source_image_url'],image_license=im['license_label'],image_license_url=im['policy_url'],
       rights_statement=im['license_label'],creator=c['artist'],creation_date=c['date_display'],
       source_object_id=c['external_id'],rights_verified_at=im['checked_at'],
       creator_credit=c['artist']+'; '+core.PROVIDERS[c['provider']]+('; '+credit if credit else ''))
    im['attribution_text']=f"{c['artist']}. {c['title']}. {im['creator_credit']}. {im['license_label']} ({im['policy_url']}). Full-frame proportional resize and JPEG compression."
    return im
core.image_record=image_record

original_attach=core.attach
def attach(db,image,target):
    if image['policy_url'] not in (PDM,CC0):raise ValueError('Missing approved canonical image licence')
    fresh_scope(image['provider'],image['raw'],image)
    with db.transaction():
        rows=db.execute('''SELECT a.id::text,a.title,a.creation_year_start,a.creation_year_end,a.work_type
          FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
          WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s''',
          (image['scheme'],image['external_id'])).fetchall()
        if len(rows)!=1 or any(rows[0][k]!=image[k] for k in ('title','creation_year_start','creation_year_end','work_type')):
            raise ValueError('Target identity changed or ambiguous')
        if rows[0]['id']!=image['target_ids'][target]:raise ValueError('Target UUID changed')
        result=original_attach(db,image,target)
        if result=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
              (image['creator_credit'],image['attribution_text'],image['media_id']))
        return result
core.attach=attach

def read_only(dsn):
    return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=180000')

def candidates(run,dsn,work_types):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    attempted={(r.get('provider'),r['artwork_id']):r for r in json.loads((run/'previous_latest.json').read_text())}
    rows=[];deferred=[]
    with read_only('postgres://localhost/artline') as db:
        for provider,schemes in SCHEMES.items():
            result=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.work_type,
              e.scheme,e.external_id,e.canonical_url page,e.source_id::text,
              (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
              EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
              FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
              WHERE e.scheme=ANY(%s) AND a.status<>'archived' AND a.primary_media_id IS NULL
              AND a.work_type=ANY(%s) AND e.source_id IS NOT NULL
              AND a.creation_year_start>=1000 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
              AND artline_has_selection_evidence(a.id)
              ORDER BY popular DESC,a.creation_year_start,a.id''',(schemes,work_types)).fetchall()
            seen=set()
            for c in result:
                if c['artwork_id'] in seen:continue
                seen.add(c['artwork_id']);prev=attempted.get((provider,c['artwork_id']))
                if prev and prev['outcome']=='no_explicit_open_image':
                    deferred.append(dict(c,provider=provider,reason='previous_direct_source_no_reusable_image; alternative source needed'));continue
                if not c['artist'] or not c['page']:
                    deferred.append(dict(c,provider=provider,reason='identity_metadata_missing'));continue
                rows.append(dict(c,provider=provider,target_ids={'local':c['artwork_id']}))
    valid=[]
    with read_only(dsn) as db:
        for provider in SCHEMES:
            group=[c for c in rows if c['provider']==provider]
            if not group:continue
            cloud=db.execute('''SELECT a.id::text,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.primary_media_id::text,e.scheme,e.external_id,
              artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) selected
              FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=ANY(%s)
              AND e.external_id=ANY(%s) AND a.status<>'archived' ''',(SCHEMES[provider],[c['external_id'] for c in group])).fetchall()
            index=collections.defaultdict(list)
            for r in cloud:index[(r['scheme'],r['external_id'])].append(r)
            for c in group:
                matches=index[(c['scheme'],c['external_id'])]
                if len(matches)!=1 or any(matches[0][k]!=c[k] for k in ('title','creation_year_start','creation_year_end','work_type')) or matches[0]['scope']!='eligible' or not matches[0]['selected']:
                    deferred.append(dict(c,reason='production_identity_needs_review'));continue
                c['target_ids']['cloud']=matches[0]['id'];valid.append(c)
    valid.sort(key=lambda c:(not c['popular'],c['creation_year_start'],c['artwork_id']))
    core.save_new(path,{'created_at':core.now(),'version':VERSION,'candidates':valid})
    core.save_new(run/'direct-source-deferred.json',deferred)
    print('Selected exact direct-source gaps',len(valid),dict(collections.Counter(c['provider'] for c in valid)),flush=True)
    for target,conn in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with read_only(conn) as db:
            before=db.execute('''SELECT to_jsonb(a) artwork,
              (SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators
              FROM artworks a WHERE a.id=ANY(%s::uuid[])''',([c['target_ids'][target] for c in valid],)).fetchall()
            core.save_new(run/(target+'-direct-before.json'),before)
    return valid

def status(run):
    latest={}
    if (run/'events.jsonl').exists():
        for line in (run/'events.jsonl').read_text().splitlines():
            try:r=json.loads(line)
            except ValueError:continue
            if r.get('artwork_id'):latest[r['artwork_id']]=r
    stats=collections.Counter(r['outcome'] for r in latest.values())
    both=sum(r['outcome']=='complete' and r.get('local')=='attached' and r.get('cloud')=='attached' for r in latest.values())
    (run/'direct-progress.json').write_text(json.dumps({'at':core.now(),'outcomes':dict(stats),'attached_both':both},indent=2))
    return latest

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','run','status']);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--limit',type=int,default=100);p.add_argument('--deadline',type=float,required=False)
    p.add_argument('--work-types',default='painting,watercolor,fresco');p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args();args.run.mkdir(parents=True,exist_ok=True)
    if args.phase=='status':status(args.run);print((args.run/'direct-progress.json').read_text());return
    dsn=None if args.prepare_only else core.cloud_dsn()
    if args.prepare_only and not (args.run/'candidates.json').exists():raise SystemExit('Prepared cross-database selection required')
    rows=candidates(args.run,dsn,args.work_types.split(','))
    if args.phase=='select':return
    if not (args.run/'backups.json').exists():raise SystemExit('Verified backup manifest required before writes')
    latest=status(args.run);pending=[c for c in rows if latest.get(c['artwork_id'],{}).get('outcome') not in (TERMINAL|({'prepared'} if args.prepare_only else set()))]
    image_index=args.run.parent/'smk-open-image-index.json'
    if image_index.exists():
        available=set(json.loads(image_index.read_text())['object_numbers'])
        pending.sort(key=lambda c:(not c['popular'],c['provider']=='smk' and c['external_id'] not in available))
    pause_path=args.run/'source-pauses.json'
    pauses=json.loads(pause_path.read_text()) if pause_path.exists() else {}
    pending=[c for c in pending if time.time()>=pauses.get(c['provider'],{}).get('until',0)]
    # Bounded, diverse canary chunks; a source pause cannot hold the whole campaign.
    grouped=collections.defaultdict(list)
    for c in pending:
        if len(grouped[c['provider']])<args.limit:grouped[c['provider']].append(c)
    if args.deadline and time.time()>=args.deadline:return
    # Interleave independent network/storage/database stages. Every HTTP request
    # still takes the shared cross-process 1.1-second host rate slot.
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        jobs={}
        for provider,group in grouped.items():
            count=1 if provider=='chicago' else (4 if provider in ('met','cleveland') else 2)
            for start in range(count):
                part=group[start::count]
                if part:jobs[pool.submit(core.worker,provider,part,SimpleNamespace(run=args.run,prepare_only=args.prepare_only),dsn)]=provider
        while jobs:
            done,_=concurrent.futures.wait(jobs,timeout=30,return_when=concurrent.futures.FIRST_COMPLETED)
            for job in done:
                provider=jobs.pop(job)
                try:job.result()
                except Exception as e:core.event(args.run,{'provider':provider,'outcome':'source_batch_failed','error_type':type(e).__name__})
            status(args.run);print(core.now(),json.loads((args.run/'direct-progress.json').read_text()),flush=True)
    status(args.run)

if __name__=='__main__':main()
