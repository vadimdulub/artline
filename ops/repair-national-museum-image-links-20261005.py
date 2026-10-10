#!/usr/bin/env python3
"""Reconnect a pinned set of reviewed existing reproductions, without new works.

Plan is read-only. Apply locks and compares source/target/media/rights preimages,
backs up the complete affected rows outside Documents, and changes only image
attachments and a readable identity citation. No dates, holdings or publication.
"""
import argparse,concurrent.futures,hashlib,importlib.util,json,uuid
from pathlib import Path
import requests

s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
BACKUP=Path.home()/'Library/Application Support/Artline/backups/national-museum-image-links-20261005'
EDITOR='local-european-research'
OP='national-museum-image-links-20261005'

def snapshots(db,ids):
 rows=db.execute('''SELECT to_jsonb(a) artwork,
 COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
 COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY am.media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments,
 (SELECT to_jsonb(m) FROM media_assets m WHERE m.id=a.primary_media_id) media,
 (SELECT to_jsonb(e) FROM media_rights_evidence e WHERE e.media_id=a.primary_media_id) rights
 FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
 return {x['artwork']['id']:x for x in rows}

def cid(c):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+c['target_id']))

def plan():
 claims=r.load(r.RUN/'national-reviewed-image-links.json.gz')['ready'];ids=sorted({c[k]for c in claims for k in ['source_id','target_id']});targets={}
 with r.connect()as db:local=snapshots(db,ids)
 slugs=[v['artwork']['slug']for v in local.values()]
 for target in ['local','production']:
  with r.connect(target)as db:
   found={x['slug']:x['id']for x in db.execute('SELECT id::text id,slug FROM artworks WHERE slug=ANY(%s)',(slugs,)).fetchall()}
   assert len(found)==len(ids), 'Missing artwork slugs'
   mapping={aid:found[v['artwork']['slug']]for aid,v in local.items()}
   snap=snapshots(db,list(mapping.values()));assert len(snap)==len(ids)
   source=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/source'))
   for c in claims:
    src=snap[mapping[c['source_id']]];dst=snap[mapping[c['target_id']]]
    keys=['title','creation_year_start','creation_year_end','date_precision','unlinked_creator_label']
    for key in ['source_id','target_id']:
     assert all(snap[mapping[c[key]]]['artwork'][k]==local[c[key]]['artwork'][k]for k in keys), 'Cross-environment identity metadata differs'
    assert src['artwork']['primary_media_id']==c['media_id'] and not dst['artwork']['primary_media_id']
    assert dst['artwork']['current_institution_id'] and dst['artwork']['title']==local[c['target_id']]['artwork']['title']
    assert src['media']['rights_status']=='public_domain' and src['media']['byte_size']<=100000 and src['rights']
    assert src['artwork']['status']=='review' and dst['artwork']['status']=='review'
   targets[target]={'preimages':snap,'catalogue_source_id':source,'id_map':mapping}
 # Probe only the selected files already in production. Never upload substitutes.
 def probe(c):
  media=targets['production']['preimages'][targets['production']['id_map'][c['source_id']]]['media']
  response=requests.get('https://artlines.org'+media['storage_path'],timeout=30);response.raise_for_status();body=response.content
  assert response.headers['content-type'].startswith('image/') and len(body)==media['byte_size'] and hashlib.sha256(body).hexdigest()==media['checksum_sha256']
  return {'media_id':media['id'],'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'status':response.status_code}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:probes=list(pool.map(probe,claims))
 data={'operation':OP,'claims':claims,'targets':targets,'asset_probes':probes};r.save_gz(r.RUN/'national-image-repair-plan.json.gz',data)
 print(json.dumps({'ready':len(claims),'verified_live_files':len(probes),'targets':list(targets)}))

def apply(target):
 path=r.RUN/'national-image-repair-plan.json.gz';data=r.load(path);digest=hashlib.sha256(path.read_bytes()).hexdigest();mapping=data['targets'][target]['id_map'];claims=[{**c,'source_id':mapping[c['source_id']],'target_id':mapping[c['target_id']]}for c in data['claims']];before=data['targets'][target]['preimages'];ids=sorted(before)
 BACKUP.mkdir(parents=True,exist_ok=True);r.save_gz(BACKUP/(target+'-preimages.json.gz'),{'plan_sha256':digest,**data['targets'][target]})
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute('SELECT pg_advisory_xact_lock(202610052)')
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  db.execute('SELECT id FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',([c['media_id']for c in claims],)).fetchall()
  current=snapshots(db,ids)
  if all(current[c['target_id']]['artwork']['primary_media_id']==c['media_id']for c in claims):
   assert all(db.execute('SELECT 1 FROM citations WHERE id=%s',(cid(c),)).fetchone()for c in claims)
   print(target,'already repaired',len(claims));return
  assert current==before,'Catalogue changed after pinned preflight; nothing applied'
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,%s,'collection_page',%s)ON CONFLICT(id)DO NOTHING",(data['targets'][target]['catalogue_source_id'],OP,'Reviewed museum image identities from Joconde','https://pop.culture.gouv.fr/'))
  for c in claims:
   db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(c['target_id'],c['media_id'],'Full composition'))
   db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(c['media_id'],EDITOR,c['target_id']))
   note=f"Existing reproduction matched to national museum object {c['object_id']} using its Joconde identifier, named creator, creation interval, subject and composition dimensions. Image reused from Artline record {c['source_id']} ({c['source_title']}); original image credit and rights evidence retained. Image reconciliation only; no holding or current-display change. Research: docs/research/museum-gaps-20261005/national-image-repair-plan.json.gz; plan SHA-256 {digest}."
   db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    VALUES(%s,'artwork',%s,'image_identity',%s,%s,%s,%s,%s,%s)''',(cid(c),c['target_id'],data['targets'][target]['catalogue_source_id'],c['object_id'],c['source_url'],note,c['source_receipt']['retrieved_at'],EDITOR))
  after=snapshots(db,ids)
  for c in claims:
   assert after[c['source_id']]==before[c['source_id']], 'Source record changed'
   old=before[c['target_id']]['artwork'];new=after[c['target_id']]['artwork'];allowed={'primary_media_id','revision','updated_at','updated_by'}
   assert {k:v for k,v in old.items()if k not in allowed}=={k:v for k,v in new.items()if k not in allowed},'Unrelated metadata changed'
   assert new['primary_media_id']==c['media_id'] and new['revision']==old['revision']+1
 r.save_gz(BACKUP/(target+'-after.json.gz'),{'plan_sha256':digest,'records':after})
 print(json.dumps({'target':target,'reconnected':len(claims),'publication_changed':False,'new_artworks':0}))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='plan':plan()
 else:assert args.target;apply(args.target)
