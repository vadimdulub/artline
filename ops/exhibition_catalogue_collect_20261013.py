#!/usr/bin/env python3
"""Capture bounded official metadata for the frozen exhibition linking cohort.
No database writes, image downloads, translation services, or inferred works.
"""
import collections,json,sys,time
import exhibitions_common as c
OUT=c.DATA.parent/'exhibition-catalogue-links-20261013'
FIELDS='id,accession_number,title,url,type,technique,creation_date,creation_date_earliest,creation_date_latest,creators,dimensions,creditline,legal_status,on_loan,record_type,cover_accession_number,culture'
ARTIST_FIELDS='id name{ja en} displayName{ja en} alternateNames{attribute name} birthDate deathDate fields{ja en} gender authority{wikiID ulanID viafID}'
def cleveland():
 baseline=c.load(OUT/'baseline.json.gz');selected={e['source_artwork_id']for e in baseline['entries']if e['source_key']=='cleveland' and not e['artwork_id']};found={}
 for kind in ['Painting','Drawing','Print']:
  skip=0
  while True:
   path=OUT/'cma-pages'/f'{kind.lower()}-{skip:06d}.json.gz'
   if path.exists():p=c.load(path)
   else:
    raw,rc=c.capture('https://openaccess-api.clevelandart.org/api/artworks/',{'type':kind,'limit':1000,'skip':skip,'fields':FIELDS});p=dict(receipt=rc,data=json.loads(raw));c.save(path,p)
   rows=p['data']['data'];assert isinstance(rows,list)
   for obj in rows:
    if str(obj['id'])in selected:
     if str(obj['id'])in found:assert found[str(obj['id'])]['data']==obj
     found[str(obj['id'])]=dict(data=obj,receipt=p['receipt'])
   print('Cleveland',kind,skip+len(rows),'/',p['data']['info']['total'],'selected',len(found),flush=True)
   if skip+len(rows)>=p['data']['info']['total']:break
   assert rows;skip+=len(rows);time.sleep(.2)
 c.save(OUT/'cma-selected.json.gz',dict(objects=found,missing=sorted(selected-set(found)),counts=dict(selected=len(selected),captured=len(found))))
def apj():
 baseline=c.load(OUT/'baseline.json.gz');ids=sorted({e['source_person_id']for e in baseline['participants']if e['source_key']=='apj_full'and e['source_person_id']});found={};missing=[]
 for offset in range(0,len(ids),10):
  batch=ids[offset:offset+10];path=OUT/'apj-pages'/f'{offset:05d}.json.gz'
  if path.exists():p=c.load(path)
  else:
   query='query ArtlineExhibitionCreatorIdentity { '+' '.join(f'a{i}: getArtist(id:{json.dumps(nid)}) {{ {ARTIST_FIELDS} }}' for i,nid in enumerate(batch))+' }'
   raw,rc=c.capture('https://api.artplatform.go.jp/graphql',{'query':query});d=json.loads(raw);assert not d.get('errors'),d.get('errors');p=dict(receipt=rc,data=d);c.save(path,p)
  for i,nid in enumerate(batch):
   obj=p['data']['data'].get(f'a{i}')
   if obj:assert obj['id']==nid;found[nid]=dict(data=obj,receipt=p['receipt'])
   else:missing.append(nid)
  print('APJ identities',offset+len(batch),'/',len(ids),'captured',len(found),flush=True);time.sleep(.25)
 c.save(OUT/'apj-selected.json.gz',dict(artists=found,missing=missing))
if __name__=='__main__':globals()[sys.argv[1]]()
