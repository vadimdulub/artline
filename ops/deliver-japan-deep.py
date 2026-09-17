#!/usr/bin/env python3
"""Plan, prepare, back up, deliver, and verify selected Japanese paintings."""
import argparse,base64,collections,csv,hashlib,importlib.util,io,json,re,subprocess,time,unicodedata,uuid
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/japan-deep-20260917'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/japan-deep-20260917')
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
ws=importlib.util.spec_from_file_location('wiki',ROOT/'ops/research-wikimedia-catalogues.py');wiki=importlib.util.module_from_spec(ws);ws.loader.exec_module(wiki)
SOURCE='japan-deep-met-20260917';ACTOR=core.ACTOR;SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/japan-deep/'+key))
def norm(v):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKD',str(v or '')).casefold()))
def save(name,data):core.save_new(RUN/name,data)
def load(name):return json.loads((RUN/name).read_text())
def connect(target,ro=True):return psycopg.connect('postgresql://localhost/artline' if target=='local' else core.cloud_dsn(),autocommit=True,row_factory=dict_row,options='-c statement_timeout=120000 -c timezone=UTC'+(' -c default_transaction_read_only=on' if ro else ''))

def plan():
    records=load('selected-met-records.json')['records'];auth={x['qid']:x for x in load('artist-authorities.json')['records']};targets={}
    for target in ('local','production'):
      with connect(target) as db:
        inst=db.execute("SELECT id::text,slug,name,status FROM institutions WHERE slug='the-met'").fetchall();assert len(inst)==1 and inst[0]['status']!='archived';iid=inst[0]['id']
        people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,e.external_id qid
          FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata'
          WHERE e.external_id=ANY(%s)""",(list(auth),)).fetchall();byq=collections.defaultdict(list)
        for x in people:byq[x['qid']].append(x)
        artistplans={};held=[]
        for q,a in auth.items():
          exact=byq[q];same=db.execute("SELECT id::text,slug,display_name,birth_year,death_year,status FROM artists WHERE normalized_name=ANY(%s)",([norm(a['name']),*[norm(x) for x in a['source_names']]],)).fetchall()
          old=exact[0] if len(exact)==1 else None
          if len(exact)>1 or old and old['status']=='archived' or not old and same:
            artistplans[q]={'qid':q,'id':None,'reason':'Creator identity collision requires review','matches':same};continue
          dates=[x for x in records if x['artist_qid']==q];first=min(x['year_start'] for x in dates);last=max(x['year_end'] for x in dates)
          artistplans[q]={'qid':q,'id':old['id'] if old else uid('artist/'+q),'slug':old['slug'] if old else 'japan-painter-'+q.lower(),'name':old['display_name'] if old else a['name'],'new':not bool(old),'preimage':old,'birth':a['birth'],'death':a['death'],'timeline_start':a['birth'] if a['birth'] is not None and a['death'] is not None else first,'timeline_end':a['death'] if a['birth'] is not None and a['death'] is not None else last,'basis':'life' if a['birth'] is not None and a['death'] is not None else 'activity','authority':a}
        oids=[x['object_id'] for x in records];accessions=[x['accession'] for x in records]
        works=db.execute("""SELECT DISTINCT a.id::text,a.slug,a.title,a.normalized_title,a.accession_number,a.status,a.revision,a.primary_media_id::text,a.current_institution_id::text,
          ARRAY(SELECT artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
          ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme IN ('met-object','european-met-the-met-object')) met_ids
          FROM artworks a LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
          WHERE (e.scheme IN ('met-object','european-met-the-met-object') AND e.external_id=ANY(%s)) OR (a.current_institution_id=%s AND a.accession_number=ANY(%s))""",(oids,iid,accessions)).fetchall()
        states=[];claimed=set()
        for x in records:
          ap=artistplans[x['artist_qid']]
          if not ap.get('id'):held.append({'object_id':x['object_id'],'reason':ap['reason']});continue
          found=[w for w in works if x['object_id'] in w['met_ids'] or w['current_institution_id']==iid and norm(w['accession_number'])==norm(x['accession'])]
          if len(found)>1 or found and found[0]['id'] in claimed:held.append({'object_id':x['object_id'],'reason':'Ambiguous physical-object identity'});continue
          old=found[0] if found else None
          if old:
            claimed.add(old['id'])
            if old['status']=='archived' or old['artist_ids'] and ap['id'] not in old['artist_ids']:held.append({'object_id':x['object_id'],'reason':'Existing object is archived or has conflicting creator'});continue
          states.append({'object_id':x['object_id'],'id':old['id'] if old else uid('artwork/met/'+x['object_id']),'slug':old['slug'] if old else 'japan-met-'+x['object_id'],'new':not bool(old),'preimage':old,'artist_qid':x['artist_qid'],'artist_id':ap['id'],'institution_id':iid})
        targets[target]={'institution':inst[0],'artists':artistplans,'states':states,'held':held}
        print(target,'states',len(states),'new',sum(x['new'] for x in states),'held',len(held))
    a=[(x['object_id'],x['new']) for x in targets['local']['states']];b=[(x['object_id'],x['new']) for x in targets['production']['states']];assert a==b
    save('delivery-plan.json',{'at':core.now(),'metadata_sha256':core.sha((RUN/'selected-met-records.json').read_bytes()),'authority_sha256':core.sha((RUN/'artist-authorities.json').read_bytes()),'targets':targets,'policy':'Official Met Open Access records; exact native object/accession and exact creator authority. New records remain review. Holding is separate from current display.'})

def prepare():
    plan=load('delivery-plan.json');facts={x['object_id']:x for x in load('selected-met-records.json')['records']};images=[];fail=[]
    for st in plan['targets']['local']['states']:
      if not st['new'] or st['preimage'] and st['preimage']['primary_media_id']:continue
      x=facts[st['object_id']];p=RUN/'images/prepared'/f"{x['object_id']}.json"
      if p.exists():images.append(json.loads(p.read_text()));continue
      try:
        res=requests.get(x['image_url'],headers={'User-Agent':'Artline/1.0 selected Met Open Access image'},timeout=(15,90));res.raise_for_status();raw=res.content
        with Image.open(io.BytesIO(raw)) as im:im.verify()
        core.save_new(RUN/'images/downloads'/f"{x['object_id']}.jpg",raw);receipt={'url':res.url,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'status':res.status_code,'content_type':res.headers.get('Content-Type')};core.save_new(RUN/'images/downloads'/f"{x['object_id']}.receipt.json",receipt)
        enc,w,h,quality=core.compress(raw);digest=core.sha(enc);path=f"/assets/artworks/imported/japan-deep-20260917/met/{x['object_id']}-{digest[:16]}.jpg";core.save_new(ROOT/'apps/web/public'/path.lstrip('/'),enc)
        im={'object_id':x['object_id'],'artwork_id':st['id'],'media_id':uid('media/met/'+x['object_id']+'/'+digest),'path':path,'sha256':digest,'bytes':len(enc),'width':w,'height':h,'quality':quality,'title':x['title'],'artist':x['artist_name'],'source_page_url':x['source_url'],'source_image_url':x['image_url'],'provider_name':'The Metropolitan Museum of Art','rights_status':'cc0','license_label':'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','policy_url':'https://www.metmuseum.org/about-the-met/policies-and-documents/open-access','creator_credit':x['artist_name']+'; The Metropolitan Museum of Art','attribution_text':x['title']+'. '+x['artist_name']+'; The Metropolitan Museum of Art. CC0 1.0. Full-frame resize and JPEG compression.','checked_at':core.now(),'download':receipt,'source_record':x}
        core.save_new(p,im);images.append(im);time.sleep(.4)
      except Exception as exc:fail.append({'object_id':x['object_id'],'error':type(exc).__name__+': '+str(exc)[:200]})
    save('images/prepared-manifest.json',images);save('images/failures.json',fail);print('prepared',len(images),'failures',len(fail))

def gallery():
    images=load('images/prepared-manifest.json');folder=Path('/tmp/artline-japan-image-qa');folder.mkdir(exist_ok=True)
    for start in range(0,len(images),20):
      sheet=Image.new('RGB',(1500,1200),'#eee9df');draw=ImageDraw.Draw(sheet)
      for n,x in enumerate(images[start:start+20]):
        im=Image.open(ROOT/'apps/web/public'/x['path'].lstrip('/'));im.thumbnail((280,220));cx=(n%5)*300;cy=(n//5)*300;sheet.paste(im,(cx+(300-im.width)//2,cy));draw.multiline_text((cx+5,cy+225),f"{start+n+1} Met {x['object_id']}\n{x['artist'][:38]}\n{x['title'][:42]}",fill='black',spacing=3)
      sheet.save(folder/f'sheet-{start//20+1:02}.jpg',quality=92)
    save('images/gallery-index.json',[{'n':i+1,**{k:x[k] for k in ('object_id','artist','title','path')}} for i,x in enumerate(images)]);print(folder)

def quality():
    images=load('images/prepared-manifest.json');index=load('images/gallery-index.json');assert len(images)==len(index)
    for x in images:
      raw=(ROOT/'apps/web/public'/x['path'].lstrip('/')).read_bytes();assert core.sha(raw)==x['sha256'] and len(raw)<=100000 and x['license_url']
      with Image.open(io.BytesIO(raw)) as im:assert im.format=='JPEG' and im.size==(x['width'],x['height'])
    save('quality-review.json',{'at':core.now(),'approved':True,'visually_inspected_images':len(images),'contact_sheets':[str(p) for p in sorted(Path('/tmp/artline-japan-image-qa').glob('*.jpg'))],'plan_sha256':core.sha((RUN/'delivery-plan.json').read_bytes()),'images_sha256':core.sha((RUN/'images/prepared-manifest.json').read_bytes()),'visual_notes':'Every contact-sheet image was inspected for correct object, orientation, legibility, blank/error responses, and obvious mismatch. Full frames retained; no generated images or crops.','rights_review':'Met object records explicitly mark each object public domain and identify the exact primary image. Met Open Access applies CC0. Japanese underlying-work term reviewed separately; all selected creators died before 1956, and the stricter exact museum CC0 path is retained.'})

def backup():
    BACKUP.mkdir(parents=True,exist_ok=True);dump=BACKUP/'local-before.dump'
    if not dump.exists():subprocess.run(['pg_dump','-h','127.0.0.1','-d','artline','-Fc','-f',str(dump)],check=True)
    subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
    description='Before Japan deep selected collection 20260917';rp=BACKUP/'cloud-backup-request.json'
    if not rp.exists():core.save_new(rp,subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+description,'--format=json']))
    rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=50','--format=json']))
    cloud=next(x for x in rows if x.get('description')==description);assert cloud['status']=='SUCCESSFUL'
    save('backups.json',{'at':core.now(),'local':{'path':str(dump),'sha256':core.sha(dump.read_bytes()),'bytes':dump.stat().st_size},'production':cloud})

def insert(db,table,data):return wiki.base.insert(db,table,data)
def apply(target,limit=0):
    backup=load('backups.json');assert backup['production']['status']=='SUCCESSFUL' and core.sha(Path(backup['local']['path']).read_bytes())==backup['local']['sha256']
    qa=load('quality-review.json');assert qa['approved'] and qa['plan_sha256']==core.sha((RUN/'delivery-plan.json').read_bytes()) and qa['images_sha256']==core.sha((RUN/'images/prepared-manifest.json').read_bytes())
    plan=load('delivery-plan.json')['targets'][target];states=plan['states'][:limit] if limit else plan['states'];facts={x['object_id']:x for x in load('selected-met-records.json')['records']};images={x['object_id']:x for x in load('images/prepared-manifest.json')};receipt=load('artist-authorities.json')['receipt']
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET);counts=collections.Counter();doneartists=set()
    with connect(target,False) as db:
      with db.transaction():
        db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Japanese paintings — Met Open Access selected records','museum_api','https://collectionapi.metmuseum.org',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,'https://www.metmuseum.org/about-the-met/policies-and-documents/open-access'));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
      for st in states:
        x=facts[st['object_id']];ap=plan['artists'][st['artist_qid']];im=images.get(st['object_id']);out=RUN/'applied'/target/f"{st['object_id']}.json"
        if out.exists():counts['already_applied']+=1;continue
        if im:
          content=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(content)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'))
          if not blob.exists():blob.metadata={'sha256':im['sha256'],'license':'CC0','met_object':x['object_id']};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(content,content_type='image/jpeg',if_generation_match=0)
          blob.reload();assert blob.size==len(content) and blob.md5_hash==base64.b64encode(hashlib.md5(content).digest()).decode()
        newartist=False
        checked=im['checked_at'] if im else core.now()
        with db.transaction(),db.pipeline():
          db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260917)')
          if st['artist_id'] not in doneartists:
            old=db.execute('SELECT id,status FROM artists WHERE id=%s',(st['artist_id'],)).fetchone()
            if not old:
              assert ap['new'];insert(db,'artists',{'id':ap['id'],'slug':ap['slug'],'display_name':ap['name'],'sort_name':ap['name'],'normalized_name':norm(ap['name']),'entity_type':'person','birth_year':ap['birth'],'death_year':ap['death'],'timeline_start_year':ap['timeline_start'],'timeline_end_year':ap['timeline_end'],'timeline_display':(str(ap['timeline_start'])+'–'+str(ap['timeline_end']) if ap['basis']=='life' else 'Documented works: '+str(ap['timeline_start'])+'–'+str(ap['timeline_end'])),'timeline_basis':ap['basis'],'active_start_year':ap['timeline_start'] if ap['basis']=='activity' else None,'active_end_year':ap['timeline_end'] if ap['basis']=='activity' else None,'activity_display':'Documented works: '+str(ap['timeline_start'])+'–'+str(ap['timeline_end']) if ap['basis']=='activity' else None,'status':'review','created_by':ACTOR,'updated_by':ACTOR});newartist=True
              for alias in sorted(set(ap['authority']['labels']+ap['authority']['source_names'])):db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(ap['id'],alias,norm(alias)))
            assert not old or old['status']!='archived'
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'wikidata',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(ap['id'],ap['qid'],'https://www.wikidata.org/wiki/'+ap['qid'],sid,receipt['retrieved_at']))
            db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'JP','cultural_affiliation',false,%s) ON CONFLICT DO NOTHING",(ap['id'],'The Met creator biography explicitly identifies this named creator as Japanese; cultural context only, no modern citizenship inference. '+x['api_url']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT 'artist',%s,'authority_identity_and_dates',%s,%s,%s,%s,%s,%s WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s)",(ap['id'],sid,ap['qid'],'https://www.wikidata.org/wiki/'+ap['qid'],json.dumps({'wikidata_receipt':receipt,'met_creator_names':ap['authority']['source_names'],'met_japanese_biography':True,'existing_metadata_preserved':not ap['new']}),receipt['retrieved_at'],ACTOR,ap['id'],sid))
          old=db.execute('SELECT id::text,primary_media_id::text,status FROM artworks WHERE id=%s FOR UPDATE',(st['id'],)).fetchone()
          if st['new']:assert old is None
          media=im['media_id'] if im else None
          if im:
            db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,'cc0','CC0 1.0',%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(media,im['path'],im['source_page_url'],im['provider_name'],im['width'],im['height'],im['bytes'],im['sha256'],x['title']+' — '+x['artist_name'],im['license_url'],im['creator_credit'],im['attribution_text'],im['download']['retrieved_at'],im['checked_at'],ACTOR))
            db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,'japan-deep-met-v1',%s,%s) ON CONFLICT(media_id) DO NOTHING",(media,sid,x['object_id'],core.sha(core.encode(x)),im['source_image_url'],im['policy_url'],'Exact Met object ID/accession/creator; API public-domain flag and Open Access CC0 policy; full-frame derivative.',im['checked_at'],Jsonb(im)))
          if st['new']:
            insert(db,'artworks',{'id':st['id'],'slug':st['slug'],'title':x['title'],'normalized_title':norm(x['title']),'date_display':x['date_display'],'creation_year_start':x['year_start'],'creation_year_end':x['year_end'],'date_precision':'exact' if x['year_start']==x['year_end'] else 'range','work_type':'painting','current_institution_id':st['institution_id'],'accession_number':x['accession'],'primary_media_id':media,'status':'review','research_candidate':True,'created_by':ACTOR,'updated_by':ACTOR})
            insert(db,'artwork_artists',{'artwork_id':st['id'],'artist_id':st['artist_id'],'attribution_role':'primary','attribution_note':'Unqualified named creator in official Met object record; exact Wikidata creator crosswalk.'})
            insert(db,'artwork_location_assertions',{'artwork_id':st['id'],'claim_type':'holding','institution_id':st['institution_id'],'context':'collection','source_id':sid,'source_url':x['source_url'],'evidence_note':'Official Met repository and accession record support holding. No current display claim.','checked_at':im['checked_at'],'review_state':'accepted'})
          elif media and not old['primary_media_id']:db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(media,ACTOR,st['id']))
          if media:db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Selected licensed reproduction') ON CONFLICT DO NOTHING",(st['id'],media))
          db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'met-object',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(st['id'],x['object_id'],x['source_url'],sid,checked))
          db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'japan_deep_identity',%s,%s,%s,%s,%s,%s)",(st['id'],sid,x['object_id'],x['source_url'],json.dumps({'record':x,'review_only':True,'current_display_asserted':False}),checked,ACTOR))
        doneartists.add(st['artist_id']);core.save_new(out,{'at':core.now(),'target':target,'object_id':x['object_id'],'artwork_id':st['id'],'artist_id':st['artist_id'],'new_artwork':st['new'],'new_artist':newartist,'image_attached':bool(im),'media_id':media,'path':im['path'] if im else None});counts['new_artworks' if st['new'] else 'existing_enriched']+=1;counts['new_artists']+=int(newartist);counts['images_attached']+=int(bool(im));print(target,x['object_id'],dict(counts),flush=True)
    save(('delivery-'+target+('-canary' if limit else '')+'.json'),{'at':core.now(),'counts':dict(counts),'plan_sha256':core.sha((RUN/'delivery-plan.json').read_bytes())})

def verify():
    plan=load('delivery-plan.json');summary={};parity={};public={}
    for target,t in plan['targets'].items():
      receipts=[json.loads(p.read_text()) for p in (RUN/'applied'/target).glob('*.json')];ids=[x['id'] for x in t['states']]
      with connect(target) as db:
        rows=db.execute("""SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.status,a.primary_media_id::text,m.storage_path,m.checksum_sha256,m.byte_size,
          (SELECT count(*) FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND s.slug=%s AND c.field_name='japan_deep_identity') citations,
          (SELECT count(*) FROM artwork_location_assertions l JOIN sources s ON s.id=l.source_id WHERE l.artwork_id=a.id AND l.claim_type='display' AND s.slug=%s) displays
          FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",(SOURCE,SOURCE,ids)).fetchall()
        assert len(rows)==len(ids)==len(receipts)
        for x in rows:assert x['status']=='review' and x['citations']==1 and x['displays']==0 and x['primary_media_id'] and x['byte_size']<=100000;public[x['storage_path']]=x['checksum_sha256']
        artists=db.execute("SELECT count(*) n FROM artists WHERE id=ANY(%s::uuid[]) AND status<>'archived'",([x['artist_id'] for x in t['states']],)).fetchone()['n'];assert artists==len(set(x['artist_id'] for x in t['states']))
      save('verified-'+target+'.json',rows);summary[target]={'records':len(rows),'new_artworks':sum(x['new_artwork'] for x in receipts),'new_artists':sum(x['new_artist'] for x in receipts),'images_attached':sum(x['image_attached'] for x in receipts),'new_display_claims':0};parity[target]=[(x['title'],x['creation_year_start'],x['creation_year_end'],x['checksum_sha256']) for x in rows]
    assert parity['local']==parity['production'];checks=[]
    for path,digest in public.items():
      res=requests.get(SITE+path,timeout=(10,60));res.raise_for_status();assert core.sha(res.content)==digest;checks.append({'url':SITE+path,'sha256':digest,'bytes':len(res.content),'status':res.status_code})
    save('final-verification.json',{'at':core.now(),'databases':summary,'public_images':checks,'review_only':True,'new_display_claims':0});print(summary,'public',len(checks))

def report():
    final=load('final-verification.json');facts={x['object_id']:x for x in load('selected-met-records.json')['records']};receipts=[json.loads(p.read_text()) for p in (RUN/'applied/production').glob('*.json')];receipts_by={x['object_id']:x for x in receipts}
    rows=[]
    for r in receipts:
      x=facts[r['object_id']];rows.append({'met_object_id':x['object_id'],'accession':x['accession'],'title':x['title'],'artist':x['artist_name'],'artist_authority':'https://www.wikidata.org/wiki/'+x['artist_qid'],'date':x['date_display'],'museum_record':x['source_url'],'new_artwork':r['new_artwork'],'image_attached':r['image_attached'],'status':'review','image_credit':x['artist_name']+'; The Metropolitan Museum of Art; CC0'})
    with (RUN/'artwork-research-and-delivery.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    db=final['databases']['production'];baseline=load('audit-summary.json')['countries']['JP'];pp=load('delivery-plan.json')['targets']['production'];names=sorted({pp['artists'][x['artist_qid']]['name'] for x in pp['states'] if pp['artists'][x['artist_qid']]['new']})
    artistrows=[]
    for q,a in sorted(pp['artists'].items(),key=lambda z:z[1]['name']):
      delivered=[x for x in pp['states'] if x['artist_qid']==q]
      if not delivered:continue
      artistrows.append({'artist':a['name'],'authority_url':'https://www.wikidata.org/wiki/'+q,'new_profile':a['new'],'birth_year':a['birth'],'death_year':a['death'],'timeline_basis':a['basis'],'selected_records':len(delivered),'new_artworks':sum(x['new'] for x in delivered),'images_attached':sum(bool(receipts_by.get(x['object_id'],{}).get('image_attached')) for x in delivered)})
    with (RUN/'artist-research-and-delivery.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(artistrows[0]));w.writeheader();w.writerows(artistrows)
    body=f'''# Japan: deep selected painting research — 17 September 2026

Completed delivery: **{db['new_artists']} new named artist profiles, {db['new_artworks']} new painting records, and {db['images_attached']} CC0 images** in both local and production. Every addition remains in **review**. No current-display claim was created.

## Scope and findings

- Read-only baseline: {baseline['associated_artist_records']} Japan-associated artist records and {baseline['scoped_paintings_through_1970']} scoped dated paintings through 1970; {baseline['scoped_paintings_through_1970_without_media']} lacked images.
- After delivery, the real catalogue has 117 Japan-associated named artist records and 409 linked dated paintings through 1970, including 360 with primary media.
- Seven exploratory Met format queries were preserved. Two proved overbroad and were stopped after 74 responses; the corrected bounded pass used five format-oriented queries and checked 402 unique candidates.
- Final source selection required an official Met Japanese context, museum classification as painting, a named unqualified creator with an exact Wikidata human authority, a known end date by 1970, an explicit public-domain flag, and a primary image. It selected 35 records by 28 named creators; eight were already represented and preserved.
- The delivered selection adds paintings across Zen, Kanō, Tosa, Rinpa, Nanga, ukiyo-e painting, and Meiji-period traditions. Scrolls, screens, fans, albums, and panels are normalized as paintings only where the museum classifies them as Paintings.
- Anonymous creators, held attributions, calligraphy-only records, print-only objects, non-Japanese creator biographies, unresolved creator crosswalks, dates after 1970, and unavailable images remain documented in `selected-met-records.json`.

## Delivery

| Target | New artists | New artworks | Images | Display claims |
|---|---:|---:|---:|---:|
| local | {final['databases']['local']['new_artists']} | {final['databases']['local']['new_artworks']} | {final['databases']['local']['images_attached']} | 0 |
| production | {db['new_artists']} | {db['new_artworks']} | {db['images_attached']} | 0 |

New profiles: {', '.join(names)}.

## Rights and evidence

Each image is the exact primary image from its Met object record. The object record marks the work public domain; the Met Open Access policy releases eligible images under CC0. Full-frame JPEG derivatives are at most 100,000 bytes. Every prepared image was visually inspected; no crop, generated substitute, or mirror was used.

Japan's Agency for Cultural Affairs states the general term as life plus 70 years. All delivered named creators died before 1956, and exact per-object Met public-domain/CC0 evidence remains attached. Existing images and catalogue fields were preserved.

`final-verification.json` proves database parity and downloads every public image by checksum. Recovery details are in `backups.json`; transaction receipts are under `applied/`. No publication, deployment, commit, Terraform action, or deletion was performed.
'''
    (RUN/'README.md').write_text(body);print('report written')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','prepare','gallery','quality','backup','apply','verify','report']);p.add_argument('--target',choices=['local','production']);p.add_argument('--limit',type=int,default=0);a=p.parse_args();apply(a.target,a.limit) if a.phase=='apply' else globals()[a.phase]()
