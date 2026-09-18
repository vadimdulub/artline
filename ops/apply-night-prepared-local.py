#!/usr/bin/env python3
"""Attach prepared, rights-verified campaign images locally; cloud stays queued."""
import argparse,collections,fcntl,importlib.util,json,time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
ADAPTERS={'met':'overnight-image-campaign.py','chicago':'overnight-image-campaign.py','cleveland':'overnight-image-campaign.py','smk':'overnight-image-campaign.py',
 'night-fng':'overnight-fng-images.py','night-rijks':'overnight-rijks-images.py','night-saam':'overnight-saam-images.py','night-fsg':'overnight-fsg-images.py','night-mia':'overnight-mia-images.py','night-smk':'overnight-smk-selected-images.py','night-cleveland':'overnight-cleveland-selected-images.py','night-met-commons':'overnight-met-commons-images.py','night-commons':'overnight-commons-images.py','night-nga-commons':'overnight-nga-commons.py','night-joconde':'overnight-joconde-images.py','night-walters':'overnight-walters-images.py'}

ADAPTERS['followup-nga']='followup-nga-direct-images.py'
ADAPTERS['followup-nationalmuseum']='followup-nationalmuseum-images.py'
ADAPTERS['followup-nationalmuseum-commons']='followup-nationalmuseum-commons.py'
ADAPTERS['austria-wien']='austrian-collection-images.py'
ADAPTERS['austria-commons']='austrian-collection-images.py'
ADAPTERS['popular-commons-depicts']='popular-commons-depicts.py'
ADAPTERS['popular-staedel']='popular-staedel-images.py'
ADAPTERS['popular-native-photo']='popular-native-photo-images.py'
ADAPTERS['popular-reims']='popular-reims-images.py'
ADAPTERS['popular-reims-donation']='popular-reims-donations.py'

def reviewed_image_allowed(image,reviewed):
    if reviewed is None:return True
    expected=reviewed.get(image['artwork_id'])
    if expected is None:return False
    if expected!=image['sha256']:raise ValueError('Reviewed image checksum differs; preserve the unreviewed candidate')
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);p.add_argument('--once',action='store_true');p.add_argument('--reviewed-images',type=Path);a=p.parse_args()
    reviewed=None
    if a.reviewed_images:
        rows=json.loads(a.reviewed_images.read_text())['records'];reviewed={r['artwork_id']:r['image_sha256'] for r in rows}
        assert len(reviewed)==len(rows),'Duplicate reviewed artwork identities'
    lock=(a.run/'local-attachment-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run/'backups.json').exists():raise SystemExit('Backup manifest required')
    journal=a.run/'local-attachments.jsonl';seen=set()
    if journal.exists():
        for l in journal.read_text().splitlines():
            x=json.loads(l)
            if x['outcome'] in ('attached','already_attached','existing_media_preserved','manual_review','withdrawn'):seen.add(x['receipt'])
    adapters={};totals=collections.Counter()
    with psycopg.connect('postgres://localhost/artline',autocommit=True,row_factory=dict_row) as db:
        while time.time()<a.deadline:
            exclusion=a.run/'withdrawn-images.json'
            blocked={r['artwork_id'] for r in json.loads(exclusion.read_text())['records'] if r['status']=='withdrawn'} if exclusion.exists() else set()
            paths=sorted(a.run.glob('*/images/*/*.json'))+sorted(a.run.glob('images/*/*.json'))
            for path in paths:
                if str(path) in seen:continue
                im=json.loads(path.read_text());provider=im['provider']
                if im['artwork_id'] in blocked:continue
                if not reviewed_image_allowed(im,reviewed):continue
                if provider not in ADAPTERS:continue
                if ADAPTERS[provider] not in adapters:
                    sp=importlib.util.spec_from_file_location('local_'+provider.replace('-','_'),ROOT/'ops'/ADAPTERS[provider]);module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module);adapters[ADAPTERS[provider]]=module
                module=adapters[ADAPTERS[provider]];core=module.core
                result={'at':core.now(),'provider':provider,'artwork_id':im['artwork_id'],'media_id':im['media_id'],'receipt':str(path)}
                try:
                    current=db.execute('SELECT primary_media_id::text FROM artworks WHERE id=%s',(im['artwork_id'],)).fetchone()
                    if not current:raise ValueError('Local artwork not present; metadata import pending')
                    if current['primary_media_id']==im['media_id']:outcome='already_attached'
                    elif current['primary_media_id']:outcome='existing_media_preserved'
                    else:
                        local_path=ROOT/'apps/web/public'/im['path'].lstrip('/')
                        if not str(local_path.resolve()).startswith(str(ROOT/'apps/web/public/assets/artworks')+'/'):raise ValueError('Unexpected media storage path')
                        data=local_path.read_bytes()
                        if core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Prepared file checksum or size mismatch')
                        if not im.get('source_image_url') or not im.get('creator_credit') or im['rights_status'] not in ('cc0','public_domain','cc_by','cc_by_sa'):raise ValueError('Missing required media provenance')
                        outcome=module.attach(db,im,'local')
                        if outcome=='attached':
                            checked=db.execute('SELECT a.primary_media_id::text,m.checksum_sha256,r.policy_url FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence r ON r.media_id=m.id WHERE a.id=%s',(im['artwork_id'],)).fetchone()
                            if not checked or checked['primary_media_id']!=im['media_id'] or checked['checksum_sha256']!=im['sha256'] or checked['policy_url']!=im['policy_url']:raise ValueError('Local attachment postcondition failed')
                    result['outcome']=outcome
                except Exception as exc:result.update(outcome='manual_review',error=str(exc)[:350])
                with journal.open('a') as f:f.write(json.dumps(result,ensure_ascii=False)+'\n')
                seen.add(str(path));totals[result['outcome']]+=1
            print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'local campaign attachments',dict(totals),flush=True)
            if a.once:break
            time.sleep(25)
if __name__=='__main__':main()
