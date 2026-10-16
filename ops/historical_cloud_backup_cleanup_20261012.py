from pathlib import Path
import sys,json,subprocess,requests,time,concurrent.futures,threading
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'
PROJECT='artline-508319';INSTANCE='artline-postgres';BASE=f'https://sqladmin.googleapis.com/sql/v1beta4/projects/{PROJECT}'
lock=threading.Lock();done=0;token=None;token_at=0

def headers():
 global token,token_at
 with lock:
  if not token or time.monotonic()-token_at>2700:
   token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip();token_at=time.monotonic()
  return {'Authorization':'Bearer '+token}
def request(method,url):
 assert url.startswith(BASE+'/')
 for n in range(90):
  r=requests.request(method,url,headers=headers(),timeout=(15,45))
  if r.status_code in [409,429,500,502,503,504]:time.sleep(min(20,2+n));continue
  if r.status_code not in [200,204]:raise RuntimeError(f'Cloud SQL {method} HTTP {r.status_code}: '+r.text[:300])
  return r.json()if r.content else{}
 raise RuntimeError('Cloud SQL retry limit')
def one(b):
 global done
 id=b['id'];receipt=OUT/'cloud-backup-deletions'/(id+'.json')
 if receipt.exists():return c.load(receipt)
 assert b['instance']==INSTANCE and b['status']=='SUCCESSFUL'
 opath=OUT/'cloud-backup-delete-operations'/(id+'.json')
 if opath.exists():op=c.load(opath)
 else:
  op=request('DELETE',BASE+f'/instances/{INSTANCE}/backupRuns/{id}');c.save(opath,op)
 operation_id=op['name']
 while op['status']!='DONE':
  time.sleep(3);op=request('GET',BASE+'/operations/'+operation_id)
 assert not op.get('error'),op.get('error')
 receiptdata=dict(backupID=id,instance=INSTANCE,project=PROJECT,operation=op,completedAt=c.now())
 c.save(receipt,receiptdata)
 with lock:
  done+=1
  if done%10==0:print('Cloud SQL backups deleted',done,flush=True)
 return receiptdata
if __name__=='__main__':
 for f in ['date-removal-delivered.json','main-removal-delivered.json','medium-removal-delivered.json']:assert(OUT/f).exists(),f
 backups=c.load(OUT/'cloud-backup-inventory.json');assert len(backups)==170
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:receipts=list(pool.map(one,backups))
 remaining=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--project='+PROJECT,'--instance='+INSTANCE,'--format=json'],text=True))
 c.save(OUT/'cloud-backups-after.json',remaining)
 active=[b for b in remaining if b['status']not in ['DELETED','FAILED','SKIPPED']]
 assert not active,[(b['id'],b['status'])for b in active]
 c.save(OUT/'cloud-backup-deletion-delivered.json',dict(at=c.now(),deleted=len(receipts),activeBackupsRemaining=0,project=PROJECT,instance=INSTANCE,localBackupsDeleted=False,automaticBackupSettingsChanged=False))
 print('Verified all 170 Cloud SQL backups deleted; zero active backups remain.',flush=True)
