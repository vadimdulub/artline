#!/usr/bin/env python3
"""Run the pinned owner-authorized batch on local/proxied production Artline."""
import argparse, hashlib, importlib.util, json, os, subprocess
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/russian-painters-20260913'
PIN='846bc4236a223be12b7ef85665ae99b8457ce782eb6277ba70ac4ab23f989fe6'
spec=importlib.util.spec_from_file_location('images',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

def dsn(target):return 'postgres://127.0.0.1/artline?sslmode=disable' if target=='local' else core.cloud_dsn()

def audit(target,label):
    with psycopg.connect(dsn(target),row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        totals=db.execute("SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM media_assets) media_assets,(SELECT count(*) FROM artworks WHERE status='published') published_artworks,(SELECT count(*) FROM artwork_location_assertions WHERE claim_type='on_view') display_assertions").fetchone()
        rows=db.execute("""SELECT e.external_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.primary_media_id::text,
         (SELECT jsonb_agg(x.external_id ORDER BY x.external_id) FROM artwork_artists aa JOIN external_identifiers x ON x.entity_type='artist' AND x.entity_id=aa.artist_id AND x.scheme='wikidata' WHERE aa.artwork_id=a.id) painters,
         (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_id=e.source_id) citations,
         (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='accepted') holdings,
         artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope
         FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='european-russian-session-museum-object' ORDER BY e.external_id""").fetchall()
        jobs=db.execute("SELECT idempotency_key,status,total_records,accepted_records FROM import_jobs WHERE idempotency_key LIKE 'russian-painters-20260913-%' ORDER BY idempotency_key").fetchall()
        result={'target':target,'totals':totals,'works':rows,'jobs':jobs}
        core.save_new(RUN/f'{target}-{label}-audit.json',result)
        print(target,label,totals,'session works',len(rows),'session jobs',len(jobs),flush=True)

def run(target,apply,receipt,batch):
    pin={'batch':PIN,'date-review-batch':'581d8927ee46c2db76a780f11cab461da1e1e46d678068280d169a7d709b4fbd'}[batch]
    path=RUN/batch/'manifest.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=pin:raise ValueError('Manifest changed')
    env=dict(os.environ);env['DATABASE_URL']=dsn(target);env.pop('ARTLINE_TEST_DATABASE_URL',None)
    cmd=['/tmp/artline-ingest-russian','-dir',str(path.parent),'-manifest-sha',pin,'-reports',str(RUN/receipt),'-target',target]
    if apply:cmd.append('-apply')
    subprocess.run(cmd,env=env,check=True)

def monitor(target):
    with psycopg.connect(dsn(target),row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        rows=db.execute("SELECT pid,application_name,state,wait_event_type,wait_event,extract(epoch FROM now()-xact_start)::int transaction_seconds,left(query,110) statement FROM pg_stat_activity WHERE datname=current_database() AND xact_start<now()-interval '30 seconds' ORDER BY xact_start").fetchall()
        print(json.dumps(rows,default=str),flush=True)

def logs(execution):
    if not execution.startswith('artline-russian-import-20260913-'):raise ValueError('Unexpected execution')
    query='resource.type="cloud_run_job" AND labels."run.googleapis.com/execution_name"="'+execution+'"'
    rows=json.loads(subprocess.check_output(['gcloud','logging','read',query,'--project=artline-508319','--limit=200','--format=json'],text=True))
    core.save_new(RUN/(execution+'-logs.json'),rows)
    receipts=[r['jsonPayload'] for r in rows if 'snapshot_sha256' in r.get('jsonPayload',{})]
    core.save_new(RUN/(execution+'-receipts.json'),receipts)
    print({'execution':execution,'receipts':len(receipts),'artworks':sum(r['created_artworks'] for r in receipts),'artists':sum(r['created_artists'] for r in receipts),'all_applied':all(r['applied'] for r in receipts)},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','preview','apply','monitor','logs']);p.add_argument('--target',required=True,choices=['local','production']);p.add_argument('--label',required=True);p.add_argument('--batch',choices=['batch','date-review-batch'],default='batch');a=p.parse_args()
    if a.phase=='audit':audit(a.target,a.label)
    elif a.phase=='monitor':monitor(a.target)
    elif a.phase=='logs':logs(a.label)
    else:run(a.target,a.phase=='apply',a.label,a.batch)
