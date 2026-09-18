#!/usr/bin/env python3
"""Bounded read-only production identity crosswalk during Cloud login expiry.

Uses the explicitly enabled public research-preview API. No editor credentials,
mutations, image downloads or database authentication workaround. Records not
exposed by these routes remain unverified, never assigned guessed remote IDs.
"""
import collections,concurrent.futures,gzip,importlib.util,json,threading,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'public-production-index';API=m.SITE+'/api/backend/v1';STATE=threading.local()
def fetch(url,params):
 if not hasattr(STATE,'session'):STATE.session=requests.Session()
 for attempt in range(3):
  response=STATE.session.get(url,params=params,timeout=35,allow_redirects=False)
  if response.status_code==200:
   assert len(response.content)<12000000
   data=response.json();receipt=dict(url=response.url,at=CORE.now(),status=200,sha256=CORE.sha(response.content),bytes=len(response.content));time.sleep(.5);return data,receipt,response.content
  if response.status_code not in (429,500,502,503,504):response.raise_for_status()
  time.sleep(min(20,2**attempt*3))
 raise RuntimeError('Public read unavailable after three bounded attempts: '+str(response.status_code))
def catalogue():
 dest=RUN/'artists.json'
 if dest.exists():return json.loads(dest.read_text())['artists']
 rows=[];receipts=[];offset=0
 while True:
  file=RUN/'catalogue-pages'/f'{offset:06d}.json'
  if file.exists():stored=json.loads(file.read_text());data=stored['data'];receipt=stored['receipt']
  else:
   data,receipt,raw=fetch(API+'/catalogue/artists',dict(limit=200,offset=offset,sort='name'));CORE.save_new(file,dict(data=data,receipt=receipt))
  rows.extend(data['items']);receipts.append(receipt)
  if not data['has_more']:break
  offset+=200
 assert len({r['slug'] for r in rows})==len(rows),'Catalogue changed pagination identities; repeat under a new capture phase'
 CORE.save_new(dest,dict(at=CORE.now(),artists=rows,receipts=receipts,scope='Public active painter catalogue; archived/private profiles are not exposed. Offset pagination endpoint used at bounded200, with duplicate identity check.'));print('Public production painters',len(rows),flush=True);return rows
def artist(a):
 slug=a['slug'];dest=RUN/'artist-works'/(slug+'.json')
 if dest.exists():return json.loads(dest.read_text())
 cursor='';page=0;items=[];seen=set();receipts=[];expected=None
 try:
  while True:
   file=RUN/'artwork-pages'/slug/f'{page:04d}.json.gz';rp=file.with_suffix('.receipt.json')
   if file.exists():raw=gzip.decompress(file.read_bytes());data=json.loads(raw);receipt=json.loads(rp.read_text());assert CORE.sha(raw)==receipt['sha256']
   else:
    data,receipt,raw=fetch(API+'/artists/'+slug+'/works',dict(limit=60,**({'cursor':cursor} if cursor else {})));CORE.save_new(file,gzip.compress(raw,mtime=0));CORE.save_new(rp,receipt)
   if expected is None:expected=data['matching_total']
   assert data['matching_total']==expected,'Painter catalogue changed during capture'
   for w in data['items']:
    assert w['id'] not in seen,'Repeated keyset page identity';seen.add(w['id']);items.append({k:w.get(k) for k in ('id','slug','title','status','creation_year_start','creation_year_end','date_precision','date_display','work_type','accession_number','media_url','rights_status','attribution_role')})
   receipts.append(receipt);cursor=data.get('next_cursor');page+=1
   if not cursor:break
   assert page<2000,'Unexpected unbounded painter scope'
  assert len(items)==expected,(slug,len(items),expected)
  out=dict(at=CORE.now(),artist_slug=slug,artist_id=a['id'],items=items,pages=page,receipts=receipts,complete=True)
 except Exception as e:out=dict(at=CORE.now(),artist_slug=slug,artist_id=a['id'],items=items,pages=page,receipts=receipts,complete=False,error=type(e).__name__+': '+str(e)[:250])
 CORE.save_new(dest,out);return out
def main():
 artists=catalogue()
 # Scope work-page reads to painters actually linked to catalogue works. Local
 # absence does not prove production absence, so this restriction is explicit.
 with m.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');linked={r['slug'] for r in db.execute("SELECT a.slug FROM artists a WHERE EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived')")}
 selected=[a for a in artists if a['slug'] in linked];results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for n,result in enumerate(pool.map(artist,selected),1):
   results.append(result)
   if n%100==0:print('Production public identity scopes',n,'/',len(selected),'works',sum(len(r['items']) for r in results),'incomplete',sum(not r['complete'] for r in results),flush=True)
 works={};conflicts=[]
 for result in results:
  for w in result['items']:
   if w['slug'] in works and works[w['slug']]['id']!=w['id']:conflicts.append(w['slug'])
   works[w['slug']]=dict(id=w['id'],slug=w['slug'],status=w['status'])
 assert not conflicts
 CORE.save_new(RUN/'crosswalk.json',dict(at=CORE.now(),artists={a['slug']:a['id'] for a in artists},artworks={s:w['id'] for s,w in works.items()},incomplete_artists=[r['artist_slug'] for r in results if not r['complete']],not_queried_artists=[a['slug'] for a in artists if a['slug'] not in linked],policy='Observed production IDs only. Read-only public API is not a database foreign-key audit or a transactionally consistent backup. No archived/private/unlinked artwork identity is inferred.'))
 print('Public production crosswalk complete',len(artists),len(works),'unresolved scopes',sum(not r['complete'] for r in results),flush=True)
if __name__=='__main__':main()
