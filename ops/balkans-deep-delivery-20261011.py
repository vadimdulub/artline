"""Evidence-pinned selected delivery. Production only; no local DB connection."""
import os,base64,collections,concurrent.futures,hashlib,importlib.util,io,json,re,subprocess,sys,uuid
from pathlib import Path
from urllib.parse import quote
import requests,pymupdf
from PIL import Image,ImageOps,ImageDraw
from psycopg import sql
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('balkans','ops/balkans-deep-20261011.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
WAVE=os.environ.get('ARTLINE_BALKANS_WAVE','wave1');assert WAVE in {'wave1','wave2','wave3'}
OP=m.RUN.name+(''if WAVE=='wave1'else'-'+WAVE);TEMP=Path('/tmp/artline-balkans-delivery');TEMP.mkdir(exist_ok=True)
def uid(x):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+x))
def insert(db,table,row):
    ks=list(row);db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,ks)),sql.SQL(',').join(sql.Placeholder()for _ in ks)),[row[k]for k in ks])
def plan():
    selection=m.h.load(m.RUN/('selection-'+WAVE+'.json'));facts=selection['records'];rows=[];held=[];new_places={};museum_plan={}
    with m.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        all_inst=[r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i')]
        places=[r['v']for r in db.execute('SELECT to_jsonb(p)v FROM places p WHERE country_code=ANY(%s)',(['GR','BG','MK'],))]
        for mu in selection['museums']:
            if not any(f['museum_slug']==mu['slug']for f in facts):continue
            match=[i for i in all_inst if i['slug']==mu['slug']or m.h.norm(i['name'])==m.h.norm(mu['name'])]
            assert len(match)<=1,(mu,match)
            if match:row=match[0];before=row
            else:
                ps=[p for p in places if p['country_code']==mu['country_code']and m.h.norm(p['name'])==m.h.norm(mu['city'])]
                if ps:place=ps[0]
                else:
                    place=dict(id=uid('place:'+mu['country_code']+':'+mu['city']),name=mu['city'],normalized_name=m.h.norm(mu['city']),country_code=mu['country_code']);new_places[place['id']]=place
                row=dict(id=uid('institution:'+mu['slug']),slug=mu['slug'],name=mu['name'],normalized_name=m.h.norm(mu['name']),kind='museum',status='review',place_id=place['id'],website_url=mu['website_url']);before=None
            museum_plan[mu['slug']]=dict(row=row,before=before,evidence=mu)
        inst={k:v['row']for k,v in museum_plan.items()}
        ids=[v['id']for v in inst.values()]
        source_urls=list({f['source_url']for f in facts})
        existing_sources=db.execute("SELECT entity_id::text,source_url,source_record_id FROM citations WHERE entity_type='artwork'AND source_url=ANY(%s)",(source_urls,)).fetchall()
        titles=sorted({m.h.norm(t)for f in facts for t in [f['title'],f.get('alternate_title')]if t})
        candidates=[r['v']for r in db.execute("SELECT to_jsonb(a)v FROM artworks a WHERE normalized_title=ANY(%s) AND status<>'archived'",(titles,))]
        existing_ids=[f['existing_id']for f in facts if f.get('existing_id')]
        existing_ids+=list({r['entity_id']for r in existing_sources})
        old=[r['v']for r in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])OR id=ANY(%s::uuid[])',(ids,existing_ids))]
        byid={a['id']:a for a in old+candidates}
        cids=list(byid)
        creators=db.execute('SELECT aa.artwork_id::text,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(cids,)).fetchall()
        for f in facts:
            if f['work_type']=='mosaic':f=dict(f,work_type='unknown',medium=f.get('medium')or'Mosaic',classification_note='Mosaic: no matching value in the current catalogue type vocabulary; original classification retained.')
            if f['work_type']=='jewelry':f=dict(f,work_type='metalwork',classification_note='Gold jewellery; metalwork is the supported catalogue type.')
            mu=inst[f['museum_slug']];before=byid.get(f.get('existing_id'))
            matches=[a for a in old if a['current_institution_id']==mu['id']and a['status']!='archived'and(m.h.norm(a['title'])==m.h.norm(f['title'])or(f.get('accession')and f['accession']==a['accession_number']))]
            source_matches={r['entity_id']for r in existing_sources if r['source_url']==f['source_url']and r['source_record_id']==f['source_record_id']}
            # Conservative identity holds for same title plus creator, or exact title and date.
            possible=[]
            for a in candidates:
                if a['id']in f.get('identity_exclusions',[]):continue
                if m.h.norm(a['title'])not in {m.h.norm(f['title']),m.h.norm(f.get('alternate_title')or'')}:continue
                labels=[a.get('unlinked_creator_label')or'']+[c['display_name']for c in creators if c['artwork_id']==a['id']]
                creator=bool(f.get('creator'))and any(m.h.norm(n)==m.h.norm(f['creator'])for n in labels)
                same_date=f['start']is not None and a['creation_year_start']==f['start']and a['creation_year_end']==f['end']
                if creator or same_date:possible.append(a)
            if not before and(matches or source_matches or possible):held.append(dict(fact=f,reason='Possible existing object requires version reconciliation; held to prevent duplicate',ids=sorted({a['id']for a in matches+possible}|source_matches)));continue
            if before:assert before['current_institution_id']==mu['id']and before['status']!='archived'
            aid=before['id']if before else uid('artwork:'+f['key'])
            if not before:assert not db.execute('SELECT 1 FROM artworks WHERE id=%s',(aid,)).fetchone()
            if f.get('source_receipt'):
                rc=f['source_receipt'];assert m.h.sha(__import__('gzip').decompress((m.ROOT/rc['body_path']).read_bytes()))==rc['sha256']
            assert f['end']is None or f['end']<=1970
            rows.append(dict(fact=f,artwork_id=aid,before=before,museum=mu,media_id=uid('media:'+f['key'])))
        aids=[r['artwork_id']for r in rows if r['before']]
        prior_media=[r['v']for r in db.execute('SELECT to_jsonb(am)v FROM artwork_media am WHERE artwork_id=ANY(%s::uuid[])ORDER BY artwork_id,media_id',(aids,))]
        prior_artists=[r['v']for r in db.execute('SELECT to_jsonb(aa)v FROM artwork_artists aa WHERE artwork_id=ANY(%s::uuid[])ORDER BY artwork_id,artist_id',(aids,))]
    # Only create institutions and places backed by an accepted object.
    museum_plan={k:v for k,v in museum_plan.items()if any(r['fact']['museum_slug']==k for r in rows)}
    new_places={k:v for k,v in new_places.items()if any(x['row']['place_id']==k for x in museum_plan.values())}
    p=dict(at=m.h.now(),target='production',records=rows,held=held,museums=museum_plan,new_places=list(new_places.values()),selection_sha256=m.h.sha((m.RUN/('selection-'+WAVE+'.json')).read_bytes()),prior_media=prior_media,prior_artists=prior_artists,identity_candidates=list(byid.values()))
    m.h.save(m.BACKUP/(WAVE+'-plan.json.gz'),p);m.h.save(m.RUN/(WAVE+'-plan-pin.json'),dict(sha256=m.h.sha((m.BACKUP/(WAVE+'-plan.json.gz')).read_bytes()),records=len(rows),held=held));print('PLANNED',len(rows),'HELD',len(held),'NEW MUSEUMS',sum(not x['before']for x in museum_plan.values()))
def pinned():
    p=m.h.load(m.BACKUP/(WAVE+'-plan.json.gz'));assert m.h.sha((m.BACKUP/(WAVE+'-plan.json.gz')).read_bytes())==m.h.load(m.RUN/(WAVE+'-plan-pin.json'))['sha256'];assert p['selection_sha256']==m.h.sha((m.RUN/('selection-'+WAVE+'.json')).read_bytes())
    review=m.RUN/(WAVE+'-record-review.json')
    if review.exists():
        v=m.h.load(review);excluded={r['key']for r in v['excluded']}
        p['records']=[r for r in p['records']if r['fact']['key']not in excluded];p['held']+=v['excluded']
        if(m.RUN/(WAVE+'-visual-review.json')).exists():assert m.h.load(m.RUN/(WAVE+'-visual-review.json'))['record_review_sha256']==m.h.sha(review.read_bytes())
    return p
def images_path():
    reviewed=m.RUN/(WAVE+'-images-reviewed.json')
    return reviewed if reviewed.exists()else m.RUN/(WAVE+'-images.json')
def images():
    p=pinned();m.ORIGINALS.mkdir(parents=True,exist_ok=True);dest=m.ROOT/'apps/web/public/assets/artworks/imported'/OP;dest.mkdir(parents=True,exist_ok=True)
    def one(row):
        f=row['fact'];aid=row['artwork_id'];path=m.ORIGINALS/(aid+'.bin');rp=m.ORIGINALS/(aid+'.json')
        if path.exists():raw=path.read_bytes();rc=m.h.load(rp)
        elif 'pdf_xref'in f:
            d=pymupdf.open(f.get('pdf_path','/tmp/artline-cyprus-pdf/catalogue.pdf'));assert f['pdf_xref']in[x['xref']for x in d[f['pdf_page_index']].get_image_info(xrefs=True)];raw=d.extract_image(f['pdf_xref'])['image'];rc=dict(url=f['source_url']+'#page='+str(f['pdf_page_index']+1),retrieved_at=m.h.now(),sha256=m.h.sha(raw),pdf_xref=f['pdf_xref'],pdf_page=f['pdf_page_index']+1,extraction='Complete original embedded catalogue plate; object position explicitly labelled; no crop.');path.write_bytes(raw);m.h.save(rp,rc)
        else:
            r=requests.get(f['image_url'],timeout=(15,45));r.raise_for_status();raw=r.content;assert len(raw)<=30_000_000;rc=dict(url=f['image_url'],final_url=r.url,retrieved_at=m.h.now(),sha256=m.h.sha(raw),content_type=r.headers.get('Content-Type'));path.write_bytes(raw);m.h.save(rp,rc)
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB');original_size=im.size;im.thumbnail((1500,1500));quality=88
        while True:
            buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True);served=buf.getvalue()
            if len(served)<=100000:break
            if quality>60:quality-=4
            else:im.thumbnail((max(1,int(im.width*.9)),max(1,int(im.height*.9))))
        out=dest/(aid+'.jpg');out.write_bytes(served)
        return dict(artwork_id=aid,media_id=row['media_id'],key=f['key'],title=f['title'],museum_slug=f['museum_slug'],path='/assets/artworks/imported/'+OP+'/'+out.name,visual_path=str(out),sha256=m.h.sha(served),bytes=len(served),width=im.width,height=im.height,original_size=original_size,receipt=rc,source_url=f['source_url'],source_record_id=f['source_record_id'],source_checksum=f.get('source_receipt',{}).get('sha256'),image_url=f.get('image_url')or rc['url'],view_label=f['view_label'],rights_status='restricted',rights_label=f.get('rights_label','No open reuse licence stated; museum/source copyright retained'),provider_name=row['museum']['name'],creator_credit=f.get('creator_credit',row['museum']['name']),user_authorization='User requested the same deep research and selected artwork-image delivery for Greece, Bulgaria and North Macedonia on 11 October 2026; existing selected pre-1956 museum-source workflow continued. Approval is distinct from source rights and is not an independent licence.')
    selected=[r for r in p['records']if r['fact'].get('image_eligible')and(r['fact'].get('image_url')or'pdf_xref'in r['fact'])]
    ims=[];fail=[]
    for r in selected:
        try:ims.append(one(r))
        except Exception as e:fail.append(dict(artwork_id=r['artwork_id'],reason=type(e).__name__+': '+str(e)[:250]))
        if(len(ims)+len(fail))%10==0:print('PREPARED',len(ims),'failed',len(fail),flush=True)
    m.h.save(m.RUN/(WAVE+'-images.json'),ims);m.h.save(m.RUN/(WAVE+'-image-failures.json'),fail)
    for k in range(0,len(ims),20):
        subset=ims[k:k+20];sheet=Image.new('RGB',(1400,340*((len(subset)+4)//5)),'#eee');draw=ImageDraw.Draw(sheet)
        for j,x in enumerate(subset):
            im=Image.open(x['visual_path']);im.thumbnail((265,275));xx=j%5*280;yy=j//5*340;sheet.paste(im,(xx+(280-im.width)//2,yy));draw.text((xx+5,yy+277),str(k+j)+' '+x['title'][:35],fill='black');draw.text((xx+5,yy+295),x['museum_slug'][:35],fill='black')
        sheet.save(TEMP/f'{WAVE}-{k//20}.jpg')
    print('IMAGES',len(ims),'FAILURES',fail)
def backup():
    rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=10','--format=json'],text=True));r=next(x for x in rows if x['status']=='SUCCESSFUL');m.h.save(m.RUN/'recovery-backup.json',dict(at=m.h.now(),backup=r,transaction_preimages=str(m.BACKUP/(WAVE+'-plan.json.gz'))));print('RECOVERY',r['id'],r.get('endTime'))
def upload():
    p=pinned();ims=m.h.load(images_path());review=m.h.load(m.RUN/(WAVE+'-visual-review.json'));assert review['manifest_sha256']==m.h.sha((images_path()).read_bytes())and review['approved_ids']==[x['artwork_id']for x in ims]
    assert {x['artwork_id']for x in ims}<={r['artwork_id']for r in p['records']},'Reconcile prepared images against the live identity plan before delivery'
    assert len({x['sha256']for x in ims})==len(ims),'Same image across objects: review required'
    token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip();sess=requests.Session();sess.headers['Authorization']='Bearer '+token;checks=[];bucket='artline-508319-images'
    for x in ims:
        raw=Path(x['visual_path']).read_bytes();assert len(raw)==x['bytes']<=100000 and m.h.sha(raw)==x['sha256'];dest=m.RUN/'storage'/(x['artwork_id']+'.json')
        if dest.exists():checks.append(m.h.load(dest));continue
        name=x['path'].lstrip('/');u='https://storage.googleapis.com/storage/v1/b/'+bucket+'/o/'+quote(name,safe='');r=sess.get(u,timeout=(15,30));created=False
        if r.status_code==404:r=sess.post('https://storage.googleapis.com/upload/storage/v1/b/'+bucket+'/o',params=dict(uploadType='media',name=name,ifGenerationMatch=0),data=raw,headers={'Content-Type':'image/jpeg'},timeout=(15,45));created=True
        r.raise_for_status();v=r.json();assert int(v['size'])==len(raw)and v['md5Hash']==base64.b64encode(hashlib.md5(raw).digest()).decode();c=dict(artwork_id=x['artwork_id'],path=x['path'],generation=v['generation'],sha256=x['sha256'],created=created);m.h.save(dest,c);checks.append(c)
        if len(checks)%10==0:print('STORAGE',len(checks),'/',len(ims),flush=True)
    m.h.save(m.RUN/(WAVE+'-storage.json'),dict(at=m.h.now(),images_sha256=m.h.sha((images_path()).read_bytes()),checks=checks));print('UPLOADED',len(checks))
def apply():
    p=pinned();assert not(m.RUN/(WAVE+'-applied.json')).exists();assert m.h.load(m.RUN/'recovery-backup.json')['backup']['status']=='SUCCESSFUL';ims={x['artwork_id']:x for x in m.h.load(images_path())};assert m.h.load(m.RUN/(WAVE+'-storage.json'))['images_sha256']==m.h.sha((images_path()).read_bytes());sid=uid('source');stamp=m.h.now();after=[]
    assert set(ims)<={r['artwork_id']for r in p['records']},'Prepared images include an object not accepted by the live plan'
    with m.d.connect(readonly=False)as db,db.transaction():
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        aids=[r['artwork_id']for r in p['records']if r['before']];locked={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(aids,))};assert all(locked[r['artwork_id']]==r['before']for r in p['records']if r['before']),'Preimage changed'
        insert(db,'sources',dict(id=sid,slug=OP,name='Greece, Bulgaria and North Macedonia: selected museum catalogue objects',source_type='collection_page',base_url='https://nationalgallery.bg/collections/'))
        for place in p['new_places']:insert(db,'places',place)
        for mp in p['museums'].values():
            if not mp['before']:insert(db,'institutions',mp['row'])
        for iid in sorted({r['museum']['id']for r in p['records']}):insert(db,'source_institutions',dict(source_id=sid,institution_id=iid))
        for row in p['records']:
            f=row['fact'];aid=row['artwork_id'];before=row['before'];im=ims.get(aid);mu=row['museum']
            if not before:
                art=dict(id=aid,slug=OP+'-'+m.h.sha(f['key'].encode())[:20],title=f['title'],normalized_title=m.h.norm(f['title']),date_display=f['date_display'],creation_year_start=f['start'],creation_year_end=f['end'],date_precision=f['precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],current_institution_id=mu['id'],current_location_text=mu['name'],location_checked_at=stamp,accession_number=f['accession'],status='review',research_candidate=True,unlinked_creator_label=f['creator'],created_by=m.h.ACTOR,updated_by=m.h.ACTOR);insert(db,'artworks',art)
                insert(db,'artwork_location_assertions',dict(id=uid('holding:'+aid),artwork_id=aid,claim_type='holding',institution_id=mu['id'],context='collection',source_id=sid,source_url=f['source_url'],evidence_note=json.dumps(dict(operation=OP,fact=f,confidence=.96,confidence_basis='Object-level museum catalogue or officially linked museum tour; editorial assessment, not a calibrated probability.',remaining_uncertainty='Holding evidence is not a fresh current-display assertion. Supplied uncertain meanings and creator labels retained.'),ensure_ascii=False),checked_at=stamp,review_state='accepted'))
                insert(db,'external_identifiers',dict(id=uid('external:'+aid),entity_type='artwork',entity_id=aid,scheme='balkans-museum-object-20261011',external_id=f['key'],canonical_url=f['source_url'],source_id=sid,retrieved_at=stamp))
            insert(db,'citations',dict(id=uid('citation:'+aid),entity_type='artwork',entity_id=aid,field_name='source_image'if before else'catalogue_metadata_and_holding',source_id=sid,source_record_id=f['source_record_id'],source_url=f['source_url'],page_or_locator=f['locator'],evidence_note=json.dumps(dict(operation=OP,fact=f,preserved_existing_metadata=bool(before)),ensure_ascii=False),retrieved_at=stamp,created_by=m.h.ACTOR))
            if im:
                media=dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_url'],provider_name=im['provider_name'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=f['title']+' — '+im['view_label'],rights_status=im['rights_status'],license_label=im['rights_label'],license_url=f['source_url'],creator_credit=im['creator_credit'],attribution_text='Image source: '+im['provider_name']+'. '+im['rights_label'],retrieved_at=im['receipt']['retrieved_at']);insert(db,'media_assets',media)
                insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=sid,source_record_id=f['source_record_id'],source_checksum=im['source_checksum'],source_image_url=im['image_url']if im['image_url'].startswith('https://')else'https://storage.googleapis.com/artline-508319-images'+im['path'],policy_url=f['source_url']if f['source_url'].startswith('https://')else'https://storage.googleapis.com/artline-508319-images/assets/artworks/imported/cyprus-deep-20261010/source-policy.json',rights_basis=im['user_authorization'],adapter_version=OP,checked_at=stamp,evidence_json=Jsonb(dict(im,original_source_image_url=im['image_url'],source_image_url_role='original source'if im['image_url'].startswith('https://')else'HTTPS delivery copy; original HTTP retrieval URL retained in this evidence'))))
                insert(db,'artwork_media',dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label=im['view_label']))
                db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],m.h.ACTOR,aid))
            current=db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE id=%s',(aid,)).fetchone()['v'];after.append(current)
            if before:assert all(current[k]==before[k]for k in before if k not in {'primary_media_id','revision','updated_at','updated_by'})
            else:assert current['status']=='review'and current['published_at']is None
            db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,%s,'artwork',%s,%s,%s,%s)",(m.h.ACTOR,('balkans_image_added'if im else'balkans_source_added')if before else'balkans_artwork_added',aid,OP,Jsonb(before)if before else None,Jsonb(current)))
        m.h.save(m.BACKUP/(WAVE+'-after.json.gz'),dict(at=stamp,artworks=after))
    receipt=dict(at=m.h.now(),target='production',new_artworks=sum(not r['before']for r in p['records']),new_museums=sum(not mp['before']for mp in p['museums'].values()),existing_images=sum(bool(r['before'])and r['artwork_id']in ims for r in p['records']),images=len(ims),museums=len({r['museum']['id']for r in p['records']}),publication_changes=0,local_database_writes=0);m.h.save(m.RUN/(WAVE+'-applied.json'),receipt);print('COMMITTED',receipt)
def verify():
    p=pinned();expected={a['id']:a for a in m.h.load(m.BACKUP/(WAVE+'-after.json.gz'))['artworks']};ims=m.h.load(images_path());checks=[]
    with m.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');actual={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE id=ANY(%s::uuid[])',(list(expected),))};assert actual==expected
        audits=db.execute('SELECT count(*)n FROM audit_log WHERE request_id=%s AND entity_type=\'artwork\'',(OP,)).fetchone()['n'];assert audits==len(expected)
        for im in ims:
            media=db.execute('SELECT checksum_sha256,byte_size FROM media_assets WHERE id=%s',(im['media_id'],)).fetchone();assert media['checksum_sha256']==im['sha256']and media['byte_size']==im['bytes'];assert actual[im['artwork_id']]['primary_media_id'] in {im['media_id'],next((r['before']['primary_media_id']for r in p['records']if r['artwork_id']==im['artwork_id']and r['before']),None)}
        prior=[r['v']for r in db.execute('SELECT to_jsonb(aa)v FROM artwork_artists aa WHERE artwork_id=ANY(%s::uuid[])ORDER BY artwork_id,artist_id',([r['artwork_id']for r in p['records']if r['before']],))];assert prior==p['prior_artists']
    def check(im):
        u='https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'];r=requests.get(u,timeout=(15,45));r.raise_for_status();assert m.h.sha(r.content)==im['sha256'];return dict(artwork_id=im['artwork_id'],status=r.status_code,sha256=im['sha256'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:checks=list(pool.map(check,ims))
    m.h.save(m.RUN/(WAVE+'-verified.json'),dict(at=m.h.now(),artworks=len(expected),public_image_checks=checks,prior_creator_links_preserved=True,verified=True));print('VERIFIED',len(expected),'records',len(checks),'public images')
if __name__=='__main__':globals()[sys.argv[1]]()
