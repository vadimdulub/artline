#!/usr/bin/env python3
"""Exact French national catalogue -> Wikidata -> individually licensed Commons images."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,time,unicodedata
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('common','ops/overnight-commons-images.py');common=importlib.util.module_from_spec(s);s.loader.exec_module(common)
core=common.core;core.VERSION='overnight-joconde-commons-exact-v1';core.PROVIDERS['night-joconde']='French museum catalogue / Wikimedia Commons'
def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')
def titlekey(s):
    s=unicodedata.normalize('NFC',s.replace('_',' '));prefix,sep,title=s.partition(':')
    return 'File:'+title[:1].upper()+title[1:] if sep else s

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    rows=json.loads((run/'candidates-local.json').read_text());held=[];prepared=[];qcounts=collections.Counter(c['qid'] for c in rows)
    for c in rows:
        if qcounts[c['qid']]!=1:held.append({'id':c['artwork_id'],'reason':'Several catalogue works share discovery authority; preserve separate objects'});continue
        if not c.get('creators'):held.append({'id':c['artwork_id'],'reason':'Existing artist authority absent'});continue
        prepared.append(dict(c,provider='night-joconde',artist='; '.join(p['name'] for p in c['creators']),target_ids={'local':c['artwork_id']}))
    with ro(dsn) as db:
        remote=db.execute("""SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.primary_media_id::text,e.scheme,e.external_id FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
          WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND e.external_id=ANY(%s) AND a.status='review' AND artline_has_selection_evidence(a.id)""",(list({c['scheme'] for c in prepared}),list({c['external_id'] for c in prepared}))).fetchall()
        index=collections.defaultdict(list)
        for x in remote:index[(x['scheme'],x['external_id'])].append(x)
        accepted=[]
        for c in prepared:
            hits=index[(c['scheme'],c['external_id'])]
            if len(hits)!=1 or any(hits[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):held.append({'id':c['artwork_id'],'reason':'Production object identity differs'});continue
            if hits[0]['primary_media_id']:continue
            c['target_ids']['cloud']=hits[0]['id'];accepted.append(c)
    for target,dsn_ in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(dsn_) as db:
            authorities=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",([c['qid'] for c in accepted],)).fetchall();owners={x['external_id']:x['entity_id'] for x in authorities}
            keep=[]
            for c in accepted:
                if owners.get(c['qid'],c['target_ids'][target])!=c['target_ids'][target]:held.append({'id':c['artwork_id'],'reason':target+' separate record already owns authority'});continue
                keep.append(c)
            accepted=keep
    for target,dsn_ in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(dsn_) as db:
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.id=ANY(%s::uuid[])',([c['target_ids'][target] for c in accepted],)).fetchall();core.save_new(run/(target+'-before.json'),before)
    core.save_new(path,{'created_at':core.now(),'candidates':accepted});core.save_new(run/'target-held.json',held)
    print('Joconde selected',len(accepted),'popular',sum(c['popular'] for c in accepted),'held',len(held),flush=True);return accepted

def research(group,run,fetcher):
    index=json.loads((run/'existing-authority-cache-index.json').read_text());entities={};captures={};filenames={}
    for c in group:
        if (run/'selected/night-joconde'/(c['artwork_id']+'.json')).exists():continue
        paths=index.get(c['qid'],[])
        if not paths:continue # Authority capture runs separately; leave resumable.
        capture=json.loads((ROOT/paths[0]).read_text());e=capture['entity']
        try:
            if c['external_id'] not in common.values(e,'P347'):raise ValueError('Exact Joconde national object identifier differs')
            filename=common.entity_match(c,e)
            entities[c['artwork_id']]=e;captures[c['artwork_id']]=capture['receipt'];filenames[c['artwork_id']]='File:'+filename
        except ValueError as exc:core.event(run,{'provider':'night-joconde','artwork_id':c['artwork_id'],'external_id':c['external_id'],'outcome':'manual_review','reason':str(exc)})
    if filenames:
        d=common.api(fetcher,'commons.wikimedia.org',{'action':'query','titles':'|'.join(dict.fromkeys(filenames.values())),'redirects':1,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
        query=d.get('query',{});pages={titlekey(p['title']):p for p in query.get('pages',{}).values()};redirect={titlekey(x['from']):titlekey(x['to']) for x in query.get('redirects',[])}
        available=[p for p in pages.values() if p.get('imageinfo')];sdcs={}
        if available:sdcs=common.api(fetcher,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join('M'+str(p['pageid']) for p in available),'props':'claims'}).get('entities',{})
        for c in group:
            aid=c['artwork_id']
            if aid not in filenames:continue
            try:
                key=titlekey(filenames[aid]);key=redirect.get(key,key);page=pages.get(key,{})
                if not page.get('imageinfo'):raise ValueError('Exact linked Commons file unavailable')
                sdc=sdcs.get('M'+str(page['pageid']),{});rendered=common.rendered_rights_uri(fetcher,page)
                info,credit,label,uri,status,url,original=common.rights_and_identity(c,entities[aid],page,sdc,rendered)
                im=dict(c,page=info['descriptionurl'],source_image_url=url,policy_url=uri,rights_status=status,license_label=label,checked_at=core.now(),
                  raw={'wikidata':entities[aid],'wikidata_capture':captures[aid],'commons':page,'structured_data':sdc},creator_credit=credit,
                  source_name=core.PROVIDERS['night-joconde'],source_record_url='https://pop.culture.gouv.fr/notice/joconde/'+c['external_id'],image_url=url,image_license=label,image_license_url=uri,
                  rights_statement=label,creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=core.now())
                if rendered:im['rendered_licence_evidence']=rendered
                if original:im['commons_original_sha1']=info['sha1']
                im['attribution_text']=c['artist']+'. '+c['title']+'. Image credit: '+credit+'. '+info['descriptionurl']+'. '+label+' ('+uri+'). Full-frame proportional resize and JPEG compression; applicable ShareAlike terms retained.'
                core.save_new(run/'selected/night-joconde'/(aid+'.json'),im)
            except (ValueError,KeyError) as exc:core.event(run,{'provider':'night-joconde','artwork_id':aid,'external_id':c['external_id'],'outcome':'manual_review','reason':str(exc)[:300]})
    return [c for c in group if (run/'selected/night-joconde'/(c['artwork_id']+'.json')).exists()]

original_attach=common.original_attach
def attach(db,im,target):
    e=im['raw']['wikidata'];common.entity_match(im,e,require_primary_image=False)
    if im['external_id'] not in common.values(e,'P347'):raise ValueError('Joconde exact national authority mismatch')
    common.rights_and_identity(im,e,im['raw']['commons'],im['raw']['structured_data'],im.get('rendered_licence_evidence'))
    with db.transaction():
        rows=db.execute("SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s",(im['scheme'],im['external_id'])).fetchall()
        if len(rows)!=1 or rows[0]['id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):raise ValueError('Target catalogue object changed')
        result=original_attach(db,im,target)
        if result=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
            db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact Joconde object identifier, current holding, artist authority and artwork metadata corroborated by Wikidata. Exact Commons physical-object identity and approved per-file image licence verified independently.',im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Verified backups required')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=select(a.run,dsn);latest={}
    if (a.run/'events.jsonl').exists():
        for line in (a.run/'events.jsonl').read_text().splitlines():
            r=json.loads(line)
            if r.get('artwork_id'):latest[r['artwork_id']]=r
    index=json.loads((a.run/'existing-authority-cache-index.json').read_text());pending=[c for c in rows if c['qid'] in index and latest.get(c['artwork_id'],{}).get('outcome') not in (('complete','manual_review','failed','prepared') if a.prepare_only else ('complete','manual_review','failed'))][:a.limit];fetcher=core.Fetcher(a.run/'commons-evidence')
    for start in range(0,len(pending),40):
        if time.time()>=a.deadline:break
        group=pending[start:start+40];ready=research(group,a.run,fetcher)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-joconde',ready[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if ready[n::3]]
            for job in jobs:job.result()
        print(core.now(),'Joconde checked',start+len(group),'of',len(pending),'ready',len(ready),dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
