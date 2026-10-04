#!/usr/bin/env python3
"""Publish the pinned Women’s rights selection; preserve all source payloads.

Book/event status columns are authoritative; their original imported JSON and
source checksums stay intact, including book discovery checksum relationships.
No artist profiles, unrelated works, or research leads are published.
"""
import argparse, base64, copy, importlib.util, json, subprocess
from pathlib import Path
from urllib.parse import quote
import requests
from psycopg import sql

spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('publish-japan-20260925.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
ROOT=c.ROOT
RUN=ROOT/'docs/research/womens-rights-publication-20260927'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/womens-rights-publication-20260927')
ACTOR='local-european-research'
ORDER=['sources','places','institutions','media_assets','media_rights_evidence','artworks','artwork_artists','artwork_places','artwork_media','artwork_location_assertions','external_identifiers','citations','book_creators','book_records','book_creator_links','book_discovery_terms','book_discovery','event_records']
KEYS={'book_discovery':['book_id'],'book_creator_links':['book_id','creator_id'],'book_discovery_terms':['kind','key'],'artwork_artists':['artwork_id','artist_id','attribution_role'],'artwork_media':['artwork_id','media_id']}
KEYS['media_rights_evidence']=['media_id']
PUBFIELDS=['status','published_at','research_candidate','updated_at','updated_by','revision']

def rows(db,t,col,ids,typ='uuid'):
 return c.getrows(db,t,col+'=ANY(%s::'+typ+'[])',(list(set(x for x in ids if x)),))

def checks(db,ids,published=False):
 art=db.execute("""SELECT a.id::text,a.title,a.status,a.research_candidate,a.published_at,
 artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
 artline_has_selection_evidence(a.id) selected,a.work_type,m.id::text media_id,m.rights_status,m.storage_path,m.checksum_sha256,
 (SELECT count(*) FROM citations ci JOIN sources s ON s.id=ci.source_id WHERE ci.entity_type='artwork' AND ci.entity_id=a.id AND s.is_active AND ci.source_url LIKE 'https://%%') citations,
 (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=m.id) rights_evidence,m.verified_by
 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",(ids['artworks'],)).fetchall()
 assert len(art)==50 and sum(bool(a['media_id']) for a in art)==44
 for a in art:
  assert a['scope']=='eligible' and a['selected'] and a['citations']>0,a
  assert a['status'] in ('review','published')
  if a['media_id']:assert a['rights_status'] in ('cc0','public_domain') and a['rights_evidence']>0 and a['verified_by'] and a['checksum_sha256'],a
  if published and a['work_type']!='unknown':assert a['status']=='published' and a['published_at'] and not a['research_candidate'],a
  if a['work_type']=='unknown':assert a['status']=='review',a
 result={'artworks':art}
 for t,n in [('book_records',34),('event_records',32)]:
  rs=rows(db,t,'id',ids[t],'text');assert len(rs)==n
  for r in rs:
   assert r['start_year'] and r['end_year'] and r['start_year']<=r['end_year']<=2000 and r['record']['dateBasis'] and r['record']['selectionBasis'],r['id']
   assert r['status'] in ('published','review')
   if published:assert r['status']=='published'
  result[t]=[{'id':r['id'],'status':r['status'],'start_year':r['start_year'],'end_year':r['end_year']} for r in rs]
 assert db.execute('SELECT count(*) n FROM book_records b JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.id=ANY(%s)',(ids['book_records'],)).fetchone()['n']==34
 return result

def plan():
 audit=json.loads((RUN/'audit-reconciled.json').read_text());preset=json.loads((ROOT/'docs/research/womens-rights-20260926/preset.json').read_text())
 ids={table:preset['focus']['related'].get(kind,[])+preset['focus'].get('context',{}).get(kind,[]) for table,kind in [('artworks','artwork'),('book_records','book'),('event_records','event')]}
 production_ids=copy.deepcopy(ids);production_ids['artworks']=[audit['artwork_id_map'].get(i,i) for i in ids['artworks']]
 with c.connection('local') as src,c.connection('production') as dst:
  for t in ids:
   for db,target in [(src,'local'),(dst,'production')]:assert rows(db,t,'id',(production_ids if target=='production' else ids)[t],'uuid' if t=='artworks' else 'text')==audit[t][target],'Audit changed: '+t+' '+target
  checks(src,ids)
  export={t:[r for r in audit[t]['local'] if (audit['artwork_id_map'].get(r['id'],r['id']) if t=='artworks' else r['id']) not in {x['id'] for x in audit[t]['production']}] for t in ids}
  aids=[r['id'] for r in export['artworks']];bids=[r['id'] for r in export['book_records']]
  assert [len(export[t]) for t in ids]==[9,1,26]
  for t,col in [('artwork_artists','artwork_id'),('artwork_places','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id'),('citations','entity_id'),('external_identifiers','entity_id')]:export[t]=rows(src,t,col,aids)
  artids=[r['artist_id'] for r in export['artwork_artists']]
  creators=rows(src,'artists','id',artids);assert len(creators)==len(set(artids))
  creator_maps={}
  for r in creators:
   other=c.getrows(dst,'artists','id=%s OR slug=%s',(r['id'],r['slug']));assert len(other)==1 and other[0]['status']!='archived'
   for k in ['display_name','birth_year','death_year']:assert other[0][k]==r[k],('Creator conflict',r['id'],k)
   creator_maps[r['id']]=other[0]['id']
  for r in export['artwork_artists']:r['artist_id']=creator_maps[r['artist_id']]
  export['institutions']=rows(src,'institutions','id',[r['current_institution_id'] for r in export['artworks']]+[r['institution_id'] for r in export['artwork_location_assertions']])
  export['places']=rows(src,'places','id',[r['place_id'] for r in export['institutions']]+[r['place_id'] for r in export['artwork_places']])
  mediaids=[r['primary_media_id'] for r in export['artworks']]+[r['media_id'] for r in export['artwork_media']]
  export['media_assets']=rows(src,'media_assets','id',mediaids)
  export['media_rights_evidence']=rows(src,'media_rights_evidence','media_id',mediaids)
  sourceids=[r['source_id'] for t in ['citations','external_identifiers','artwork_location_assertions','media_rights_evidence'] for r in export[t]]
  export['sources']=rows(src,'sources','id',sourceids)
  source_maps={}
  for r in export['sources']:
   matches=c.getrows(dst,'sources','id=%s OR slug=%s',(r['id'],r['slug']))
   if matches:
    assert len(matches)==1 and matches[0]['slug']==r['slug']
    for k in ['name','base_url']:assert matches[0].get(k)==r.get(k),('Source identity conflict',r['slug'],k)
    source_maps[r['id']]=matches[0]['id']
  for t in ['citations','external_identifiers','artwork_location_assertions','media_rights_evidence']:
   for r in export[t]:r['source_id']=source_maps.get(r['source_id'],r['source_id'])
  for r in export['sources']:r['id']=source_maps.get(r['id'],r['id'])
  export['book_creator_links']=rows(src,'book_creator_links','book_id',bids,'text')
  export['book_creators']=rows(src,'book_creators','id',[r['creator_id'] for r in export['book_creator_links']],'text')
  export['book_discovery']=rows(src,'book_discovery','book_id',bids,'text')
  terms=[v for r in export['book_discovery'] for k in ['languages','countries','regions'] for v in r[k]]
  export['book_discovery_terms']=rows(src,'book_discovery_terms','key',terms,'text')
  preserved={}
  for t in ORDER:
   preserved[t]=[];new=[]
   for r in export[t]:
    keys=KEYS.get(t,['id']);where=' AND '.join(k+'=%s' for k in keys)
    old=c.getrows(dst,t,where,tuple(r[k] for k in keys))
    if old:
     assert len(old)==1
     if t in ['institutions','sources']:assert old[0]['slug']==r['slug']
     elif t=='places':assert old[0]['name']==r['name'] and old[0]['country_code']==r['country_code']
     elif t=='media_assets':assert old[0]['checksum_sha256']==r['checksum_sha256'] and old[0]['storage_path']==r['storage_path']
     elif t=='book_creators':assert old[0]['name']==r['name']
     else:assert old[0]==r,('Dependency differs',t,r.get('id'))
     preserved[t].extend(old)
    else:
     if t in ['institutions','sources','artworks']:assert not c.getrows(dst,t,'slug=%s',(r['slug'],)),('Slug duplicate',t,r['slug'])
     if t=='artworks' and r['current_institution_id'] and r['accession_number']:assert not c.getrows(dst,t,'current_institution_id=%s AND accession_number=%s',(r['current_institution_id'],r['accession_number']))
     if t=='external_identifiers':assert not c.getrows(dst,t,'canonical_url=%s OR (scheme=%s AND external_id=%s)',(r['canonical_url'],r['scheme'],r['external_id']))
     new.append(r)
   export[t]=new
  for r in export['artwork_location_assertions']:assert r['venue_id'] is None and r['superseded_by'] is None and r['claim_type']=='holding'
  for r in export['places']:assert c.getrows(dst,'countries','code=%s',(r['country_code'],))
  actors={r[k] for rs in export.values() for r in rs for k in ['created_by','updated_by','verified_by'] if r.get(k)}|{ACTOR}
  for actor in actors:assert c.getrows(dst,'editor_accounts','user_id=%s',(actor,)),'Missing actor'
  selected_media=rows(src,'media_assets','id',[r['primary_media_id'] for r in audit['artworks']['local']])
  preserved['artists']=rows(dst,'artists','id',list(creator_maps.values()))
  incomplete=[r['id'] for r in audit['artworks']['local'] if r['work_type']=='unknown']
  assert len(incomplete)==15
  plan={'at':c.now(),'ids':ids,'production_ids':production_ids,'rows':export,'preimages':audit,'preserved_dependencies':preserved,'selected_media':selected_media,'incomplete_artworks_retained_in_review':incomplete,'note':__doc__+' Fifteen existing artwork records with unknown work type remain in review, visible in the public research preview without status labels, under AGENTS.md incomplete-data policy.'}
 c.save(RUN/'plan.json',plan);c.save(RUN/'plan-pin.json',{'sha256':c.sha(c.raw(plan))});c.save(BACKUP/'plan.json',plan)
 print(json.dumps({t:len(v) for t,v in export.items()}))

def pinned():
 p=json.loads((RUN/'plan.json').read_text());assert c.sha((RUN/'plan.json').read_bytes())==json.loads((RUN/'plan-pin.json').read_text())['sha256'];return p

def backup():
 pinned();BACKUP.mkdir(parents=True,exist_ok=True)
 for service in ['artline-api','artline-web']:
  dest=BACKUP/(service+'-before.json')
  if not dest.exists():
   data=subprocess.check_output(['gcloud','run','services','describe',service,'--project='+c.PROJECT,'--region=europe-west1','--format=json']);dest.write_bytes(data);dest.chmod(0o600)
 dump=BACKUP/'local-before-publication.dump'
 if not dump.exists():
  tmp=dump.with_suffix('.incomplete');subprocess.run(['pg_dump','-h','localhost','-d','artline','-Fc','-f',str(tmp)],check=True);subprocess.run(['pg_restore','--list',str(tmp)],check=True,stdout=subprocess.DEVNULL);tmp.rename(dump)
 description='Before Women rights publication 20260927'
 result=BACKUP/'production-backup.json'
 if not result.exists():c.save(result,subprocess.check_output(['gcloud','sql','backups','create','--instance='+c.INSTANCE,'--project='+c.PROJECT,'--description='+description,'--format=json']))
 backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance='+c.INSTANCE,'--project='+c.PROJECT,'--limit=20','--format=json']))
 cloud=next(b for b in backups if b.get('description')==description);assert cloud['status']=='SUCCESSFUL'
 c.save(RUN/'backups.json',{'at':c.now(),'local':{'path':str(dump),'sha256':c.sha(dump.read_bytes()),'bytes':dump.stat().st_size},'production':cloud});print('Verified recovery backups',cloud['id'])

def upload():
 p=pinned();assert json.loads((RUN/'backups.json').read_text())['production']['status']=='SUCCESSFUL'
 token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip();session=requests.Session();session.headers['Authorization']='Bearer '+token
 checks=[]
 for m in p['selected_media']:
  data=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes();assert len(data)==m['byte_size'] and c.sha(data)==m['checksum_sha256']
  assert m['rights_status'] in ('cc0','public_domain') and m['verified_by']
  name=m['storage_path'].lstrip('/');url=f'https://storage.googleapis.com/storage/v1/b/{c.BUCKET}/o/'+quote(name,safe='')
  response=session.get(url,timeout=40);created=response.status_code==404
  if created:
   response=session.post(f'https://storage.googleapis.com/upload/storage/v1/b/{c.BUCKET}/o',params={'uploadType':'media','name':name,'ifGenerationMatch':0},data=data,headers={'Content-Type':m['mime_type']},timeout=60);response.raise_for_status();response=session.get(url,timeout=40)
  response.raise_for_status();obj=response.json();assert int(obj['size'])==len(data) and obj['md5Hash']==base64.b64encode(__import__('hashlib').md5(data).digest()).decode()
  checks.append({'media_id':m['id'],'path':m['storage_path'],'sha256':c.sha(data),'generation':obj['generation'],'created':created})
 c.save(RUN/'storage.json',{'at':c.now(),'checks':checks});print('Verified',len(checks),'selected images;',sum(r['created'] for r in checks),'uploaded')

def insert(db,t,r):
 cols={r['column_name'] for r in db.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND is_generated='NEVER'",(t,))}
 return c.insert(db,t,{k:v for k,v in r.items() if k in cols})

def apply():
 p=pinned();assert json.loads((RUN/'backups.json').read_text())['production']['status']=='SUCCESSFUL';assert len(json.loads((RUN/'storage.json').read_text())['checks'])==44
 for target in ['production','local']:
  receipt=RUN/(target+'-applied.json')
  if receipt.exists():continue
  target_ids=p['production_ids'] if target=='production' else p['ids']
  with c.connection(target,False) as db,db.transaction():
   db.execute("SET LOCAL lock_timeout='10s'");db.execute('SELECT pg_advisory_xact_lock(559220260915)')
   db.execute('LOCK TABLE artworks,book_records,event_records IN SHARE ROW EXCLUSIVE MODE')
   for t,ids in target_ids.items():assert rows(db,t,'id',ids,'uuid' if t=='artworks' else 'text')==p['preimages'][t][target],('Preimage changed',target,t)
   if target=='production':
    for t,rs in p['preserved_dependencies'].items():
     for r in rs:
      keys=KEYS.get(t,['id']);assert c.getrows(db,t,' AND '.join(k+'=%s' for k in keys),tuple(r[k] for k in keys))==[r],('Dependency changed',t)
    for t in ORDER:
     for r in p['rows'][t]:insert(db,t,r)
   checks(db,target_ids)
   db.execute("UPDATE artworks SET status='published',research_candidate=false,published_at=COALESCE(published_at,%s::timestamptz),updated_at=%s::timestamptz,updated_by=%s,revision=revision+1 WHERE id=ANY(%s::uuid[]) AND status<>'published' AND work_type<>'unknown'",(p['at'],p['at'],ACTOR,target_ids['artworks']))
   for t in ['book_records','event_records']:db.execute(sql.SQL("UPDATE {} SET status='published' WHERE id=ANY(%s::text[]) AND status<>'published'").format(sql.Identifier(t)),(target_ids[t],))
   verified=checks(db,target_ids,True)
   for t in p['ids']:
    after=rows(db,t,'id',target_ids[t],'uuid' if t=='artworks' else 'text');before={r['id']:r for r in p['preimages'][t][target]}
    if target=='production':before.update({r['id']:r for r in p['rows'][t]})
    allowed=PUBFIELDS if t=='artworks' else ['status']
    for r in after:assert {k:v for k,v in r.items() if k not in allowed}=={k:v for k,v in before[r['id']].items() if k not in allowed},('Unexpected change',t,r['id'])
  c.save(receipt,{'at':c.now(),'target':target,'checks':verified});print('Published',target,'35 artworks, 34 books, 32 events; 15 incomplete artworks remain visible in review',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','backup','upload','apply']);globals()[p.parse_args().phase]()
