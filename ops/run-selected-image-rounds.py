#!/usr/bin/env python3
"""Sequential, bounded research/image rounds for existing museum artworks."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('images',Path(__file__).with_name('enrich-artwork-images.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PLAN=[('cleveland','drawing'),('met','drawing'),('nga','drawing'),('chicago','drawing'),
      ('cleveland','print'),('met','print'),('nga','print')]


def latest(run):
    result={}
    if (run/'events.jsonl').exists():
        for line in (run/'events.jsonl').read_text().splitlines():
            event=json.loads(line)
            if event.get('artwork_id'):result[event['artwork_id']]=event
    return result


def snapshot(dsn,candidates):
    with psycopg.connect(dsn,row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        rows=db.execute('''WITH wanted AS (SELECT * FROM jsonb_to_recordset(%s::jsonb)
          AS x(artwork_id text,scheme text,external_id text))
          SELECT w.artwork_id AS local_id,a.id::text AS target_id,e.source_id::text,
          a.primary_media_id::text,a.status,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) AS scope,
          artline_has_selection_evidence(a.id) AS selected,
          to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] AS metadata,
          coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
            FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) AS creators
          FROM wanted w JOIN external_identifiers e ON e.entity_type='artwork'
          AND e.scheme=w.scheme AND e.external_id=w.external_id JOIN artworks a ON a.id=e.entity_id''',
          (Jsonb([{k:c[k] for k in ('artwork_id','scheme','external_id')} for c in candidates]),)).fetchall()
        if len(rows)!=len(candidates) or len({r['local_id'] for r in rows})!=len(candidates):
            raise ValueError('Missing or ambiguous exact museum identity')
        result={}
        for row in rows:
            if row['scope']!='eligible' or not row['selected'] or row['status']=='archived':
                raise ValueError('Selected artwork no longer eligible')
            result[row['local_id']]={'target_id':row['target_id'],'source_id':row['source_id'],
              'metadata_sha256':core.sha(core.encode(row['metadata'])),
              'creators_sha256':core.sha(core.encode(row['creators'])),'status':row['status']}
        return result


original_record=core.image_record


def reviewed_image_record(c,fetcher,nga,chicago):
    image=original_record(c,fetcher,nga,chicago)
    if image is None:return None
    field={'met':'objectEndDate','cleveland':'creation_date_latest','chicago':'date_end'}.get(c['provider'])
    if field:
        end=image['raw'].get(field)
        if type(end) is not int or not end or end>1970:
            raise ValueError('Metadata needs review: current museum creation endpoint is unknown or later than 1970')
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--rounds',type=int,choices=[5,6,7],default=7)
    parser.add_argument('--per-round',type=int,default=200)
    args=parser.parse_args()
    if not 1<=args.per_round<=250:raise ValueError('Each research round is bounded at 250 selected artworks')
    args.root.mkdir(parents=True,exist_ok=True)
    core.save_new(args.root/'plan.json',{'rounds':PLAN[:args.rounds],'per_round':args.per_round,
      'selection':'Disjoint existing eligible museum artworks; Russian/Greek creator priority, popular creators, chronological order. Fresh per-image rights checks precede downloads.',
      'next_round_gate':'Previous round has terminal research outcomes, successful media verification, and unchanged catalogue metadata/creator snapshots in both databases.'})
    dsn=core.cloud_dsn()
    core.image_record=reviewed_image_record
    for number,(provider,work_type) in enumerate(PLAN[:args.rounds],1):
        run=args.root/f'round-{number:02d}-{provider}-{work_type}s'
        run.mkdir(parents=True,exist_ok=True)
        if (run/'round-complete.json').exists():
            print('Already verified:',run.name,flush=True);continue
        if not (run/'candidates.json').exists():
            previous={p.parent for p in (core.ROOT/'docs/research').glob('image-expansion*/**/candidates.json')}
            previous.update(p.parent for p in args.root.glob('*/candidates.json'))
            previous.discard(run)
            core.select(SimpleNamespace(run=run,providers=provider,per_source=args.per_round,
              work_type=work_type,exclude_run=sorted(previous)))
        candidates=json.loads((run/'candidates.json').read_text())['candidates']
        if not candidates:raise ValueError('Empty research round; choose another useful scope')
        targets=[('local','postgres://localhost/artline'),('cloud',dsn)]
        for target,target_dsn in targets:
            before=run/(target+'-before.json')
            if not before.exists():core.save_new(before,snapshot(target_dsn,candidates))
        terminal={'complete','no_explicit_open_image','source_unavailable_review','metadata_needs_review'}
        events=latest(run)
        pending=[c for c in candidates if events.get(c['artwork_id'],{}).get('outcome') not in terminal]
        print('Research round',number,provider,work_type,'selected',len(candidates),'pending',len(pending),flush=True)
        if pending:core.worker(provider,pending,SimpleNamespace(run=run),dsn)
        events=latest(run)
        for c in candidates:
            event=events.get(c['artwork_id'],{})
            if event.get('outcome')=='failed':
                error=event.get('error','')
                if '403 Client Error' in error or '404 Client Error' in error:
                    core.event(run,{'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                      'outcome':'source_unavailable_review','error':error,'note':'Museum endpoint refused or has no current resource; preserved for review, no alternate access route attempted.'})
                elif error.startswith('Metadata needs review:'):
                    core.event(run,{'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                      'outcome':'metadata_needs_review','error':error})
        events=latest(run)
        if any(events.get(c['artwork_id'],{}).get('outcome') not in terminal for c in candidates):
            raise ValueError('Round has unfinished/error records; inspect before continuing')
        if any(e['outcome']=='complete' and (e.get('local')!='attached' or e.get('cloud')!='attached') for e in events.values()):
            raise ValueError('Image attachment incomplete in one database')
        if not (run/'verification-final.json').exists():
            subprocess.run([sys.executable,str(core.ROOT/'ops/verify-enriched-images.py'),
              '--run',str(run),'--report',str(run/'verification-final.json')],check=True)
        verification=json.loads((run/'verification-final.json').read_text())
        if verification['errors']:raise ValueError('Media audit has unresolved errors')
        for target,target_dsn in targets:
            before=json.loads((run/(target+'-before.json')).read_text())
            after=snapshot(target_dsn,candidates)
            if before!=after:raise ValueError('Non-media catalogue metadata or creators changed during round: '+target)
            core.save_new(run/(target+'-after.json'),after)
        report={'finished_at':core.now(),'round':number,'provider':provider,'work_type':work_type,
          'selected':len(candidates),'outcomes':dict(collections.Counter(e['outcome'] for e in events.values())),
          'images':verification['complete_images'],'bytes':verification['bytes'],'max_bytes':verification['max_bytes'],
          'metadata_and_creator_snapshots_unchanged':True,'verification_errors':verification['errors']}
        core.save_new(run/'round-complete.json',report)
        print('ROUND VERIFIED',json.dumps(report),flush=True)
    print('ALL REQUESTED ROUNDS VERIFIED',flush=True)


if __name__=='__main__':main()
