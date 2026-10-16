from pathlib import Path
import sys,requests,json,re,time,concurrent.futures,threading,gzip
from bs4 import BeautifulSoup
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/royal-academy'
lock=threading.Lock();done=0

def capture(url,path):
 receipt=path.with_suffix(path.suffix+'.receipt.json')
 if path.exists():
  raw=path.read_bytes();rc=c.load(receipt);assert c.sha(raw)==rc['sha256'];assert rc['status']==200;return raw,rc
 for n in range(3):
  r=requests.get(url,headers={'User-Agent':c.UA},timeout=(15,45))
  if r.status_code>=500 and n<2:time.sleep(2+n);continue
  break
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.content)
 rc=dict(url=url,finalURL=r.url,status=r.status_code,retrievedAt=c.now(),sha256=c.sha(r.content),path=str(path));c.save(receipt,rc)
 if r.status_code!=200:raise RuntimeError(f'Access held HTTP {r.status_code} {url}')
 time.sleep(.25)
 return r.content,rc

def one(year):
 global done
 raw,rc=capture('https://chronicle250.com/'+str(year),OUT/str(year)/'page.html');soup=BeautifulSoup(raw,'html.parser')
 els=soup.select('[data-manifest]');manifests=[]
 for el in els:
  url=el['data-manifest']
  if any(m['url']==url for m in manifests):continue
  blob,receipt=capture(url,OUT/str(year)/('manifest-'+str(len(manifests))+'.json'));d=json.loads(blob)
  metadata=d.get('metadata',[]);title=' '.join(str(m['value'])for m in metadata if m.get('label')=='Title');date=' '.join(str(m['value'])for m in metadata if m.get('label')=='Date')
  assert str(year)in title or date==str(year),(year,title,date)
  manifests.append(dict(url=url,title=title,date=date,license=d.get('license'),canvasCount=sum(len(s.get('canvases',[]))for s in d.get('sequences',[])),receipt=receipt))
 assert manifests,year
 record=dict(year=year,title=f'Royal Academy Summer Exhibition {year}',sourceURL=rc['url'],pageReceipt=rc,catalogues=manifests,datePrecision='year',startDate=None,endDate=None,city='London',country='United Kingdom',institution='Royal Academy of Arts',reviewNote='Annual event and catalogue identities verified individually. Catalogue navDate is not an opening date. Mixed-media exhibition: selected painting/drawing/print entries must be checked against catalogue pages; no sculpture or photography entries are imported.')
 c.save(OUT/str(year)/'record.json',record)
 with lock:
  done+=1
  if done%20==0:print('Royal Academy years documented',done,flush=True)
 return record
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(one,range(1769,1990)))
 c.save(OUT/'records.json',rows);print('Documented historical Royal Academy exhibitions',len(rows),flush=True)
