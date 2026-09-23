#!/usr/bin/env python3
"""Bounded, source-led French Revolution selection; local review only."""
import argparse, hashlib, importlib.util, io, json, re, time, uuid
from pathlib import Path
from urllib.parse import urlparse
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests
from PIL import Image
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
core=module('revolution','revolution-discovery-20260921.py')
RUN=core.RUN;ACTOR='local-european-research';CC0='https://creativecommons.org/publicdomain/zero/1.0/'
PD='https://creativecommons.org/publicdomain/mark/1.0/'
SOURCE_IMAGES=Path.home()/'Library/Application Support/Artline/source-images/revolution-discovery-20260921'

def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/revolution-discovery-20260921/'+key))
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(url):
 path,receipt=core.capture(url);return json.loads(path.read_text()),receipt

def prepare():
 records=[]
 for oid in ['341739','384288']:
  obj,proof=load('https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid)
  assert str(obj['objectID'])==oid and obj['isPublicDomain'] and not obj['rightsAndReproduction']
  assert 1700<=obj['objectBeginDate']<=obj['objectEndDate']<=1970 and obj['objectName']=='Print'
  records.append(dict(key='met-'+oid,id=uid('met-'+oid),existing=False,scheme='european-met-the-met-object',external_id=oid,
   title=obj['title'],creator=obj['artistDisplayName'],artist_id=None,first=obj['objectBeginDate'],last=obj['objectEndDate'],date=obj['objectDate'],
   precision='exact' if obj['objectBeginDate']==obj['objectEndDate'] else 'circa_range',work_type='print',medium=obj['medium'],dimensions=obj['dimensions'] or None,
   accession=obj['accessionNumber'],institution='The Metropolitan Museum of Art',url=obj['objectURL'],image=obj['primaryImage'],image_page=obj['objectURL'],rights='cc0',license=CC0,credit='The Metropolitan Museum of Art — Open Access (CC0)',proofs=[proof],rights_proof=proof))
 for oid,first,last,kind in [('320039051',1794,1794,'drawing'),('320038878',1793,1794,'drawing'),('320027171',1794,1794,'painting')]:
  obj,proof=load('https://apicollections.parismusees.paris.fr/iiif/'+oid+'/manifest')
  meta={m['label']:m['value'] for m in obj['metadata']};canvas=obj['sequences'][0]['canvases'][0]
  rights={m['label']:m['value'] for m in canvas['metadata']};assert rights['Copyright']==CC0 and 'CC0' in rights['Droits']
  date=BeautifulSoup(meta['Date de production'],'html.parser').get_text(' ',strip=True);assert str(first) in date and str(last) in date
  records.append(dict(key='paris-'+oid,id='44ce1484-a49a-48f5-8135-5bb8d309027f' if oid=='320027171' else uid('paris-'+oid),existing=oid=='320027171',scheme='paris-musees-object',external_id=oid,
   title=obj['label'],creator='; '.join(meta['Auteur']),artist_id=None,first=first,last=last,date=str(first) if first==last else f'{first}–{last}',precision='exact' if first==last else 'range',
   work_type=kind,medium='; '.join(meta.get('Matériaux et techniques',[])) or None,dimensions='; '.join(meta.get('Dimensions',[])) or None,
   accession=meta['Numéro d’inventaire'],institution=meta['Institution'],url=meta['Catalogue des œuvres de Paris Musées'],
   image=canvas['images'][0]['resource']['@id'],image_page=meta['Catalogue des œuvres de Paris Musées'],rights='cc0',license=CC0,credit=rights['Droits'],proofs=[proof],rights_proof=proof))
 museum='https://fine-arts-museum.be/nl/de-collectie/jacques-louis-david-de-moord-op-marat'
 path,museumproof=core.capture(museum);assert '3260' in path.read_text() and '1793' in path.read_text()
 api='https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url%7Cextmetadata&titles=File%3ADeath%20of%20Marat%20by%20David.jpg'
 obj,proof=load(api);page=list(obj['query']['pages'].values())[0];info=page['imageinfo'][0];metadata=info['extmetadata']
 assert metadata['LicenseShortName']['value']=='Public domain' and metadata['Copyrighted']['value']=='False'
 assert 'Q636537' in metadata['ObjectName']['value'] and '1793' in metadata['DateTimeOriginal']['value']
 records.append(dict(key='david-marat',id=uid('david-marat'),existing=False,scheme='wikidata',external_id='Q636537',title='The Death of Marat',creator='Jacques-Louis David',artist_id='be6ed84d-46df-47eb-ac44-fa0208f090c6',first=1793,last=1793,date='1793',precision='exact',work_type='painting',medium='Oil on canvas',dimensions='165 × 128 cm',accession='3260',institution='Royal Museums of Fine Arts of Belgium',url=museum,image=info['url'],image_page=info['descriptionurl'],rights='public_domain',license=PD,credit='Jacques-Louis David. The Death of Marat, 1793. Wikimedia Commons; Google Arts & Culture / Web Gallery of Art reproduction, public domain.',proofs=[museumproof,proof],rights_proof=proof))
 # Relevant works already illustrated in the catalogue. No title-substring auto-selection.
 existing_ids=['4e0247a8-4087-420e-a0e5-04ce4c8c1c60','a975485f-196a-5e95-af19-581948b7ee60','a768ec07-fd0f-568c-823b-6d42a37830b6','338beaf0-2ce4-4b5b-bf54-14df2c6ec388','f2771312-d43a-5d38-84ae-71251471ed4d','a53799d5-5bb5-5f18-b603-05ed9bfd96bc','0e50dff4-0b77-5b7a-bc71-c41b86ae0290','c1568c10-fb73-5f41-b6e5-ad1603d75c8a','e9a90044-67fc-4839-997f-b55b993c437d','5167d716-c900-40e5-af70-006c539a668f','c20303cf-a281-446a-a74a-fb3f005cd291','e3e2a291-fda1-509a-9d49-739e21396ec8']
 with psycopg.connect(core.DSN,options='-c default_transaction_read_only=on',row_factory=dict_row) as db:
  owner=db.execute("select id::text from curated_collections where institution_id is null and curator_kind='owner' and status='review'").fetchone();assert owner
  prior=[]
  for r in records:
   found=db.execute("select entity_id::text from external_identifiers where entity_type='artwork' and (canonical_url=%s or external_id=%s)",(r['url'],r['external_id'])).fetchall()
   assert not found,'Source object already exists; reconcile before import: '+str(found)
   same=db.execute('select * from artworks where lower(title)=lower(%s) or id=%s',(r['title'],r['id'])).fetchall()
   if r['existing']:
    assert len(same)==1 and str(same[0]['id'])==r['id'] and same[0]['status']=='review' and not same[0]['primary_media_id']
    assert 'jeaurat' in same[0]['unlinked_creator_label'].lower();r['expected_revision']=same[0]['revision'];prior.extend(same)
   else:assert not same,'Title collision requires review: '+r['title']
  existing=db.execute("select a.id::text,a.title,a.date_display,a.creation_year_end,a.primary_media_id::text,a.status,(select c.source_url from citations c where c.entity_type='artwork' and c.entity_id=a.id and c.source_url like 'https://%%' order by (c.source_url like '%%storage.googleapis.com%%'),c.retrieved_at desc limit 1) source_url from artworks a where a.id=any(%s::uuid[])",(existing_ids,)).fetchall()
  assert len(existing)==len(existing_ids) and all(x['primary_media_id'] and x['creation_year_end']<=1970 and x['source_url'] for x in existing)
 core.save(core.BACKUP/'french-art-preimages.json',prior)
 plan={'at':core.now(),'records':records,'existing_selection':existing,'collection_id':owner['id'],'policy':'Personal editorial selection. Fresh object-level museum metadata; six selected CC0/public-domain reproductions. Existing artwork revised only after matching creator, title and source date. No accepted holdings, on-view claims or publication.'}
 core.save(RUN/'french-art-plan-v2.json',plan);print('Selected',len(records),'image candidates and',len(existing),'existing illustrated works')

def download():
 images=module('images','enrich-artwork-images.py')
 plan=json.loads((RUN/'french-art-plan-v2.json').read_text());out=[]
 for r in plan['records']:
  receipt=RUN/'image-receipts'/(r['key']+'.json')
  if receipt.exists():out.append(json.loads(receipt.read_text()));continue
  assert urlparse(r['image']).hostname in ['images.metmuseum.org','apicollections.parismusees.paris.fr','upload.wikimedia.org']
  response=requests.get(r['image'],timeout=(15,60),headers={'User-Agent':'Artline selected public-domain art review/1.0'});response.raise_for_status()
  raw=response.content;assert len(raw)<=20_000_000
  derivative,width,height,quality=images.compress(raw)
  source=SOURCE_IMAGES/(r['key']+'-'+digest(raw)[:16]+'.jpg');core.save(source,raw)
  relative='/assets/artworks/revolution-20260921-'+r['key']+'-'+digest(derivative)[:12]+'.jpg'
  target=ROOT/'apps/web/public'/relative.lstrip('/');core.save(target,derivative)
  info={'key':r['key'],'media_id':uid('image:'+r['key']),'source_file':str(source),'source_sha256':digest(raw),'path':relative,'sha256':digest(derivative),'bytes':len(derivative),'width':width,'height':height,'quality':quality,'retrieved_at':core.now()}
  core.save(receipt,info);out.append(info);print(r['key'],len(derivative),'bytes',flush=True);time.sleep(1)
 core.save(RUN/'french-images.json',out)

def insert(db,table,fields):
 columns=list(fields);db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder() for _ in columns)),[Jsonb(fields[k]) if isinstance(fields[k],dict) else fields[k] for k in columns])

def apply():
 assert not (RUN/'french-art-applied.json').exists(),'Already applied; verify instead'
 backup=json.loads((RUN/'local-backup.json').read_text());assert Path(backup['path']).stat().st_size==backup['bytes']
 plan=json.loads((RUN/'french-art-plan-v2.json').read_text());images={x['key']:x for x in json.loads((RUN/'french-images.json').read_text())}
 assert len(images)==len(plan['records'])==6
 for r in plan['records']:
  for proof in r['proofs']:assert digest((ROOT/proof['path']).read_bytes())==proof['sha256']
  im=images[r['key']];assert digest((ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes())==im['sha256'] and im['bytes']<=100000
 sid=uid('source');collection=plan['collection_id']
 with psycopg.connect(core.DSN,row_factory=dict_row) as db,db.transaction():
  db.execute('SELECT pg_advisory_xact_lock(559220260915)')
  db.execute("SET LOCAL lock_timeout='5s'")
  insert(db,'sources',dict(id=sid,slug='revolution-discovery-20260921',name='French Revolution — museum catalogue and image review',source_type='collection_page',base_url='https://www.parismuseescollections.paris.fr/',priority=20,is_active=True))
  owner=db.execute('select * from curated_collections where id=%s for update',(collection,)).fetchone()
  assert owner['institution_id'] is None and owner['curator_kind']=='owner' and owner['status']=='review'
  position=db.execute('select coalesce(max(position),0) n from curated_collection_items where collection_id=%s',(collection,)).fetchone()['n']
  added=[]
  for n,r in enumerate(plan['records'],1):
   im=images[r['key']]
   assert not db.execute("select entity_id from external_identifiers where entity_type='artwork' and (canonical_url=%s or external_id=%s)",(r['url'],r['external_id'])).fetchone()
   fields=dict(date_display=r['date'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=r['work_type'],medium_text=r['medium'],dimensions_text=r['dimensions'],accession_number=r['accession'])
   if r['existing']:
    old=db.execute('select * from artworks where id=%s for update',(r['id'],)).fetchone();assert old['revision']==r['expected_revision'] and old['primary_media_id'] is None and old['status']=='review'
    db.execute(sql.SQL('UPDATE artworks SET {} WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields)),[*fields.values(),r['id']])
   else:
    assert not db.execute('select id from artworks where id=%s or lower(title)=lower(%s)',(r['id'],r['title'])).fetchone()
    insert(db,'artworks',dict(id=r['id'],slug='revolution-'+r['key'],title=r['title'],normalized_title=r['title'].lower(),**fields,unlinked_creator_label=r['creator'] if not r['artist_id'] else None,status='review',research_candidate=True,description_md=f"Selected for the French Revolution reading and art collection. The {r['institution']} catalogue documents this object. Holding and display status remain subject to editorial review.\n\n[Object source]({r['url']}).",created_by=ACTOR,updated_by=ACTOR))
    if r['artist_id']:insert(db,'artwork_artists',dict(artwork_id=r['id'],artist_id=r['artist_id'],attribution_role='primary',attribution_note='Object-specific museum attribution, confirmed by the source reproduction.'))
   insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=r['id'],scheme=r['scheme'],external_id=r['external_id'],canonical_url=r['url'],source_id=sid,retrieved_at=core.now()))
   insert(db,'citations',dict(entity_type='artwork',entity_id=r['id'],field_name='revolution_object_review',source_id=sid,source_url=r['url'],source_record_id=r['external_id'],evidence_note=json.dumps(r,ensure_ascii=False),retrieved_at=core.now(),created_by=ACTOR))
   insert(db,'media_assets',dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=r['image_page'],provider_name='Wikimedia Commons' if r['rights']=='public_domain' else r['institution'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['creator'],rights_status=r['rights'],license_label='Public domain' if r['rights']=='public_domain' else 'CC0',license_url=r['license'],creator_credit=r['creator'],attribution_text=r['credit']+' Proportionally resized full-frame reproduction.',retrieved_at=im['retrieved_at'],verified_at=core.now(),verified_by=ACTOR))
   insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=sid,source_record_id=r['external_id'],source_checksum=r['rights_proof']['sha256'],source_image_url=r['image'],policy_url=r['license'],rights_basis='Exact selected museum object; explicit per-image CC0 designation or a documented public-domain faithful reproduction of the 1793 painting. No rights inferred merely from a search match.',adapter_version='revolution-review-v1',checked_at=core.now(),evidence_json={'record':r,'image':im}))
   db.execute('update artworks set primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() where id=%s',(im['media_id'],ACTOR,r['id']))
   position+=1;added.append(r['id'])
   insert(db,'curated_collection_items',dict(collection_id=collection,artwork_id=r['id'],position=position,reason='Personal editorial selection about the French Revolution. Separate from museum masterpiece designation, holdings acceptance and publication.',source_id=sid,source_url=r['url'],checked_at=core.now()))
  for n,r in enumerate(plan['existing_selection'],len(plan['records'])+1):
   assert db.execute("select id from artworks where id=%s and status<>'archived' and primary_media_id=%s",(r['id'],r['primary_media_id'])).fetchone()
   if db.execute('select 1 from curated_collection_items where collection_id=%s and artwork_id=%s',(collection,r['id'])).fetchone():continue
   position+=1;added.append(r['id'])
   insert(db,'curated_collection_items',dict(collection_id=collection,artwork_id=r['id'],position=position,reason='Personal editorial selection: contemporary depiction of Revolutionary France, a participant or a directly related event. Existing image and source evidence retained.',source_id=sid,source_url=r['source_url'],checked_at=core.now()))
  db.execute('update curated_collections set revision=revision+1,updated_at=now() where id=%s',(collection,))
 core.save(RUN/'french-art-applied.json',{'at':core.now(),'newWorks':sum(not r['existing'] for r in plan['records']),'reconciledWorks':sum(r['existing'] for r in plan['records']),'newImages':len(images),'selectedWorks':len(plan['records'])+len(plan['existing_selection']),'newPersonalSelections':len(added),'collectionId':collection,'artworkIds':[r['id'] for r in plan['records']],'planSha256':digest((RUN/'french-art-plan-v2.json').read_bytes()),'localOnly':True,'publication':'review'})
 print((RUN/'french-art-applied.json').read_text())

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','download','apply']);a=parser.parse_args();globals()[a.phase]()
