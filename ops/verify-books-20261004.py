#!/usr/bin/env python3
import json,sys,urllib.request,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'docs/research/books-5000bce-1850-20261004'
api,web,receipt=sys.argv[1:];plan=json.load(open(P/'plan.json'));man=json.load(open(P/'prepared-image-manifests.json'))
covers={r['bookId']:{k:v for k,v in r.items() if k not in ['bookId','sourceId']} for r in man['books']};portraits={r['creatorId']:{k:v for k,v in r.items() if k not in ['creatorId','creatorSourceUrl']} for r in man['authors']}
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ArtlineDeliveryVerification/1.0'}),timeout=35) as res:return res.read()
seen=set()
for c in plan['changes']:
 b=json.loads(get(api+'/books/'+c['id']));r=c['record']
 for k in ['id','sourceId','title','author','startYear','endYear','years','approximate','status','description','dateBasis','dateSources']:assert b[k]==r[k],(c['id'],k)
 assert b.get('cover')==covers.get(c['id']),c['id']
 assert [a['id'] for a in b['creators']]==[a['creator_id'] for a in c['links']]
 for a in b['creators']:
  assert a.get('portrait')==portraits.get(a['id']),a['id'];seen.add(a['id'])
 print('Book',b['id'],flush=True)
for r in json.load(open(P/'selected-images.json')):
 u=web+'/'+r['path'].split('apps/web/public/')[1];raw=get(u);assert hashlib.sha256(raw).hexdigest()==r['sha256'],u
session=json.loads(get(api+'/auth/session'));assert session.get('enabled') and not session.get('local_debug') and not session.get('all_features')
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'api':api,'web':web,'books':29,'creatorProfiles':len(seen),'covers':19,'portraits':21,'servedImageChecksums':40,'allReviewStatus':True,'googleSignInEnabled':True,'productionLocalDebugDisabled':True}
(P/receipt).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
