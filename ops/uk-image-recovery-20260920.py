#!/usr/bin/env python3
"""Retry selected deferred images, preserving every prior decision and DB receipt."""
import argparse,concurrent.futures,importlib.util,json,os,subprocess,sys,uuid
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('uk',Path(__file__).with_name('uk-painters-20260920.py'));u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
RUN,m,w=u.RUN,u.m,u.w
RECOVERY=RUN/'image-recovery'

def read(path):return json.loads(path.read_bytes())

def prepare():
    plan_path=RECOVERY/'plan.json'
    if not plan_path.exists():
        selected={v['qid'] for v in read(RUN/'selected-museum/catalogue-index.json')['selected']}
        candidates=[]
        for path in sorted((RUN/'museum-images/shards').glob('*/*/ready/*.json')):
            data=read(path);reason=data.get('image_reason','')
            if data['record']['qid'] not in selected or data['image'] or data['image_outcome']!='metadata_retained_image_deferred':continue
            if not reason or any(text in reason.lower() for text in ('unavailable','timed out','timeout','429','502','503','504')):
                candidates.append({'qid':data['record']['qid'],'original_ready':str(path),'original_sha256':m.core.sha(path.read_bytes()),'reason':reason})
        assert len({v['qid'] for v in candidates})==len(candidates)
        u.save(plan_path,{'at':m.core.now(),'reason':'Re-evaluate bounded selected-image failures after correcting legacy Creative Commons HTTP licence handling; all date, identity and rights checks remain enabled.','selected':candidates})
    candidates=read(plan_path)['selected']
    for shard in range(3):
        folder=RECOVERY/'shards'/str(shard);records=[]
        for item in candidates[shard::3]:
            original=Path(item['original_ready']);record=read(original)['record'];records.append(record)
            url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'File:'+record['images'][0],'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5})
            key=m.core.sha(url.encode())
            for suffix in ('.json','.receipt.json'):
                source=original.parent.parent/'captures'/(key+suffix)
                if source.exists():u.save(folder/'captures'/source.name,source.read_bytes())
        u.save(folder/'selected/records.json',{'selected':records})
    print('Selected image recoveries',len(candidates),flush=True)
    def worker(shard):
        log=Path('/tmp/artline-uk-image-recovery-'+str(shard)+'.log')
        with log.open('a') as stream:
            result=subprocess.run([sys.executable,'-B','-u',str(Path(__file__)),'child','--shard',str(shard)],stdout=stream,stderr=subprocess.STDOUT)
        assert result.returncode==0,(shard,str(log))
        return shard
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for shard in pool.map(worker,range(3)):print('Image recovery completed shard',shard,flush=True)
    u.save(RECOVERY/'prepared.json',{'at':m.core.now(),'records':len(candidates)})

def child(shard):
    s=importlib.util.spec_from_file_location('prep',u.ROOT/'ops/prepare-wikimedia-catalogue-images.py');prep=importlib.util.module_from_spec(s);s.loader.exec_module(prep)
    s=importlib.util.spec_from_file_location('downloads',u.ROOT/'ops/uk-source-downloads-20260920.py');downloads=importlib.util.module_from_spec(s);s.loader.exec_module(downloads);downloads.install(w)
    w.RUN=RECOVERY/'shards'/str(shard);w.BACKUPS=m.BACKUP/'image-recovery'/str(shard);prep.r=w
    original=w.date
    def date(entity):
        result=original(entity);result['eligible']=result['first'] is not None and result['last']<=1955;return result
    w.date=date;prep.main(original_byte_limit=0 if shard>=3 else 1_000_000,original_pixel_limit=0 if shard>=3 else 4_000_000)

def replace_preserved(path,raw,backup):
    if path.read_bytes()==raw:return
    u.save(backup,path.read_bytes())
    temporary=path.with_name(path.name+'.recovery-tmp');temporary.write_bytes(raw);os.replace(temporary,path)

def apply():
    assert (RECOVERY/'prepared.json').exists()
    plan={v['qid']:v for v in read(RECOVERY/'plan.json')['selected']};successes=[]
    for path in sorted((RECOVERY/'extra-plans').glob('*.json')):
        for item in read(path)['selected']:
            assert item['qid'] not in plan;plan[item['qid']]=item
    assert set(plan)=={p.stem for p in (RECOVERY/'shards').glob('*/ready/*.json')},'Recovery preparation is incomplete'
    for target in ('local','cloud'):
        delivered={p.stem for folder in ('museum-applied','museum-held') for p in (RUN/folder/target).glob('*.json')}
        assert set(plan)<=delivered,'Recovery must wait for its original object decisions'
    for path in sorted((RECOVERY/'shards').glob('*/ready/*.json')):
        prepared=read(path);qid=prepared['record']['qid']
        if prepared['image']:successes.append(prepared)
        for kind,destination in [('canonical',RUN/'museum-images/ready'/path.name),('shard',Path(plan[qid]['original_ready']))]:
            old=read(destination)
            assert not old['image'] or (prepared['image'] and old['image']['sha256']==prepared['image']['sha256'])
            replace_preserved(destination,path.read_bytes(),m.BACKUP/'image-recovery/previous-ready'/kind/path.name)
    # Upload only: the ongoing main stream owns its still-pending objects.
    # Recovery changes only the already-delivered objects checked above.
    u.museum_apply(incremental=True,upload_only=True)
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    def target_apply(target,dsn):
        candidates=[v for v in successes if (RUN/'museum-applied'/target/(v['record']['qid']+'.json')).exists() and not (RECOVERY/'applied'/target/(v['record']['qid']+'.json')).exists()]
        total=0
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=u.source(db)
            for start in range(0,len(candidates),40):
                items=candidates[start:start+40]
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='15s'");db.execute("SET LOCAL statement_timeout='90s'")
                    collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    chunk,held=u.museum_target_chunk(db,items);assert not held,held
                    ids=[v['artwork_id'] for v in chunk]
                    locked={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) FOR UPDATE',(ids,)).fetchall()}
                    prior={};write=[]
                    for entry in chunk:
                        qid=entry['item']['record']['qid'];receipt=read(RUN/'museum-applied'/target/(qid+'.json'));prior[qid]=receipt
                        assert entry['before'] and locked[entry['artwork_id']]==entry['before']
                        if entry['before']!=receipt['after']:
                            # Recover a commit that completed before its filesystem
                            # receipt was replaced. Only our exact image and the
                            # writer's revision/timestamp fields may differ.
                            expected_mid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/image/'+qid+'/'+entry['item']['image']['sha256']))
                            assert entry['before']['primary_media_id']==expected_mid
                            assert all(entry['before'][k]==v for k,v in receipt['after'].items() if k not in ('primary_media_id','revision','updated_at','updated_by')),'Artwork changed outside its recorded delivery'
                            media=db.execute('SELECT storage_path,checksum_sha256 FROM media_assets WHERE id=%s',(expected_mid,)).fetchone()
                            assert media and media['storage_path']==entry['item']['image']['path'] and media['checksum_sha256']==entry['item']['image']['sha256']
                            entry['recovered_committed_media_id']=expected_mid
                        if entry['media_id']:write.append(entry)
                    key=m.core.sha(m.core.encode([v['item']['record']['qid'] for v in chunk]))[:20]
                    backup=m.BACKUP/'image-recovery/database'/target/(key+'.json')
                    if not backup.exists():u.save(backup,{'at':m.core.now(),'kind':'selected_image_gap_recovery','selected':chunk,'prior_receipts':prior,'collection':collection})
                    else:assert {v['artwork_id'] for v in read(backup)['selected']}==set(ids)
                    if write:u.museum_write_chunk(db,write,sid,collection_id)
                    after={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
                    for entry in chunk:
                        old=entry['before'];new=after[entry['artwork_id']]
                        assert all(new[k]==v for k,v in old.items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
                        if entry['media_id']:assert new['primary_media_id']==entry['media_id']
                for entry in chunk:
                    qid=entry['item']['record']['qid'];old=prior[qid];receipt_path=RUN/'museum-applied'/target/(qid+'.json')
                    media_id=entry['media_id'] or entry.get('recovered_committed_media_id')
                    if media_id:
                        archived=m.BACKUP/'image-recovery/previous-receipts'/target/(qid+'.json');u.save(archived,receipt_path.read_bytes())
                        updated=dict(old,after=after[entry['artwork_id']],image_attached=True,media_id=media_id,backup=str(backup),backup_sha256=m.core.sha(backup.read_bytes()),previous_receipt=str(archived),previous_receipt_sha256=m.core.sha(archived.read_bytes()),recovery_at=m.core.now())
                        replace_preserved(receipt_path,m.core.encode(updated),archived);total+=1
                    u.save(RECOVERY/'applied'/target/(qid+'.json'),{'qid':qid,'image_attached':bool(media_id),'at':m.core.now(),'backup':str(backup)})
                print('Recovered selected images',target,total,flush=True)
        return target,total
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(target_apply,target,dsn) for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]]
        results=[f.result() for f in futures]
    u.save(RECOVERY/'finished.json',{'at':m.core.now(),'prepared_images':len(successes),'targets':results});print('Image recovery finished',results,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','child','apply']);parser.add_argument('--shard',type=int);args=parser.parse_args()
    if args.phase=='child':child(args.shard)
    else:globals()[args.phase]()
