#!/usr/bin/env python3
"""Upload verified local campaign assets with bounded cross-database identity checks."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,time
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('audit',ROOT/'ops/audit-overnight-local-images.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
s=importlib.util.spec_from_file_location('upload_core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
INSTITUTIONS={'night-fng':'wikimedia-museum-q2983474','night-walters':'wikimedia-museum-q210081','night-saam':'smithsonian-american-art-museum','night-fsg':'smithsonian-national-museum-of-asian-art','night-mia':'minneapolis-institute-of-art','night-smk':'statens-museum-for-kunst','night-cleveland':'cleveland-museum-of-art','night-rijks':'rijksmuseum'}
def complete_ids(run):
    result=set()
    exclusion=run/'withdrawn-images.json'
    blocked={r['artwork_id'] for r in json.loads(exclusion.read_text())['records'] if r['status']=='withdrawn'} if exclusion.exists() else set()
    for path in run.glob('**/events.jsonl'):
        for line in path.read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if v.get('outcome')=='complete' and v.get('local')=='attached' and v.get('cloud')=='attached':result.add(v['artwork_id'])
    return result-blocked

def pending_journal(run,done,held):
    exclusion=run/'withdrawn-images.json'
    blocked={r['artwork_id'] for r in json.loads(exclusion.read_text())['records'] if r['status']=='withdrawn'} if exclusion.exists() else set()
    journal={};excluded=done|held|blocked
    for line in (run/'local-attachments.jsonl').read_text().splitlines():
        try:j=json.loads(line)
        except ValueError:continue
        if j['outcome'] in ('attached','already_attached') and j['artwork_id'] not in excluded:journal[j['artwork_id']]=j
        elif j['outcome']=='withdrawn':journal.pop(j['artwork_id'],None)
    return journal

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--once',action='store_true');p.add_argument('--per-provider',type=int,default=150);a=p.parse_args();delivery=a.run/'production-resume';delivery.mkdir(exist_ok=True)
    lock=(delivery/'uploader.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (a.run/'backups.json').exists();dsn=core.cloud_dsn();modules={};held=set();checked=0
    while time.time()<a.deadline:
        done=complete_ids(a.run);journal=pending_journal(a.run,done,held)
        candidates=[]
        for aid,j in journal.items():
            path=Path(j['receipt']);path=path if path.is_absolute() else ROOT/path;im=json.loads(path.read_text())
            candidates.append({'artwork_id':aid,'provider':im['provider'],'scheme':im['scheme'],'external_id':im['external_id'],'title':im['title'],'creation_year_start':im['creation_year_start'],'creation_year_end':im['creation_year_end'],'work_type':im['work_type'],'media_id':im['media_id'],'popular':im.get('popular',False),'receipt':str(path)})
        candidates.sort(key=lambda c:(not c['popular'],c['work_type']!='painting',c['artwork_id']));chosen=[];per=collections.Counter()
        # Inspect beyond the first delivery page: pending metadata must not
        # starve already-present production objects from the same provider.
        preflight_limit=max(2000,a.per_provider*8)
        for c in candidates:
            if per[c['provider']]<preflight_limit:chosen.append(c);per[c['provider']]+=1
        if not chosen:
            print(core.now(),'All currently attached local images have production completion receipts',len(done),flush=True)
            if a.once:break
            time.sleep(25);continue
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            rows=db.execute("""WITH requested AS (SELECT * FROM jsonb_to_recordset(%s) AS x(artwork_id text,scheme text,external_id text))
              SELECT r.artwork_id local_artwork_id,a.id::text,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.status,a.primary_media_id::text,
                 artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope
              FROM requested r JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=r.scheme AND e.external_id=r.external_id JOIN artworks a ON a.id=e.entity_id""",(Jsonb([{k:c[k] for k in ('artwork_id','scheme','external_id')} for c in chosen]),)).fetchall()
            index=collections.defaultdict(list)
            for row in rows:index[row['local_artwork_id']].append(row)
            institutions={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM institutions WHERE slug=ANY(%s) AND status<>\'archived\'',(list(INSTITUTIONS.values()),)).fetchall()}
        ready=collections.defaultdict(list);pending=0;conflicts=[]
        for c in chosen:
            hits=index[c['artwork_id']]
            if not hits:pending+=1;continue
            if len(ready[c['provider']])>=a.per_provider:continue
            if len(hits)!=1 or hits[0]['status']!='review' or hits[0]['scope']!='eligible' or any(hits[0][k]!=c[k] for k in ('title','creation_year_start','creation_year_end','work_type')):
                conflicts.append({'artwork_id':c['artwork_id'],'reason':'Production metadata differs from the selected local source-backed record'});held.add(c['artwork_id']);continue
            remote=hits[0]
            if remote['primary_media_id'] and remote['primary_media_id']!=c['media_id']:
                conflicts.append({'artwork_id':c['artwork_id'],'reason':'Production already has a different primary image; preserve it'});held.add(c['artwork_id']);continue
            im=json.loads(Path(c['receipt']).read_text());name=audit.MODULES[c['provider']]
            if name not in modules:
                spec=importlib.util.spec_from_file_location('upload_'+c['provider'].replace('-','_'),ROOT/'ops'/name);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules[name]=module
            module=modules[name]
            try:
                audit.validate_source(module,im);assert audit.allowed(im['policy_url'])
                old_target=im.get('target_ids',{}).get('cloud');assert old_target in (None,remote['id']),'Production ID changed since selection'
                im.setdefault('target_ids',{})['cloud']=remote['id']
                if c['provider'] in INSTITUTIONS:
                    iid=institutions.get(INSTITUTIONS[c['provider']]);assert iid,'Verified production institution absent'
                    assert im.get('institution_ids',{}).get('cloud') in (None,iid),'Institution identity changed'
                    im.setdefault('institution_ids',{})['cloud']=iid
                dest=delivery/c['provider']/'images'/c['provider']/(c['artwork_id']+'.json')
                if dest.exists():
                    old=json.loads(dest.read_text());assert all(old[k]==im[k] for k in ('media_id','sha256','policy_url','target_ids')),'Prepared delivery receipt changed'
                else:core.save_new(dest,im)
                ready[c['provider']].append(c)
            except Exception as exc:conflicts.append({'artwork_id':c['artwork_id'],'reason':str(exc)[:300]});held.add(c['artwork_id'])
        if conflicts:
            with (delivery/'held.jsonl').open('a') as f:
                for row in conflicts:f.write(json.dumps({'at':core.now(),**row})+'\n')
        print(core.now(),'Prepared production batch',sum(map(len,ready.values())),'metadata pending',pending,'held',len(conflicts),'completed both so far',len(done),flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            jobs=[]
            for provider,cs in ready.items():
                module=modules[audit.MODULES[provider]];folder=delivery/provider;folder.mkdir(exist_ok=True)
                # Isolated provider journals; use only prepared bytes, never repeat source image downloads.
                stripes=4 if provider in ('met','night-nga-commons') else 2
                for stripe in range(stripes):
                    if cs[stripe::stripes]:jobs.append(pool.submit(module.core.worker,provider,cs[stripe::stripes],SimpleNamespace(run=folder,upload_prepared_only=True),dsn))
            for job in jobs:job.result()
        checked+=sum(map(len,ready.values()));print(core.now(),'Production delivery attempts this process',checked,'both-target completions',len(complete_ids(a.run)),flush=True)
        # Leave expired-credential work queued rather than looping over failed cloud writes.
        recent=[]
        for path in delivery.glob('*/events.jsonl'):
            for line in path.read_text().splitlines()[-20:]:
                try:x=json.loads(line)
                except ValueError:continue
                if x.get('outcome')=='failed' and ('Reauthentication failed' in x.get('error','') or 'auth print-access-token' in x.get('error','')):recent.append(x)
        if recent:raise SystemExit('Production credentials expired again; uploaded assets retained and remaining images stay queued')
        if a.once:break
        time.sleep(10 if ready else 25)
if __name__=='__main__':main()
