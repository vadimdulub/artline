#!/usr/bin/env python3
"""Selected native NGA CC0 reproductions, inspected before production attachment."""
import argparse,base64,collections,concurrent.futures,hashlib,importlib.util,io,json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('cesi-delivery-20261010.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
s=importlib.util.spec_from_file_location('capture',Path(__file__).with_name('million-sources-20261010.py'));cap=importlib.util.module_from_spec(s);s.loader.exec_module(cap)
m=n.m;RUN=n.RUN/'images-001';ORIG=Path.home()/'Library/Application Support/Artline/source-images'/m.OP/'nga-001';POLICY='https://www.nga.gov/terms-and-notices'
def select():
    path=RUN/'selection.json.gz'
    if path.exists():return m.load(path)
    # The web tool exposed this official policy before a direct HTTP request was
    # denied. Preserve that observation explicitly; never represent it as HTML.
    policy=dict(source_url=POLICY,observed_at='2026-10-10T19:41:00Z',capture_method='Official NGA policy exposed by web search tool; direct HTTP subsequently returned 403 and remains held',facts='The NGA Open Access policy releases designated images under CC0 for commercial and non-commercial reuse. The separate published_images CSV identifies designation using openaccess=1.',source_quote='Images of these works are available free of charge for any use',supporting_url='https://www.nga.gov/artworks/free-images-and-open-access')
    policy['sha256']=m.sha(json.dumps(policy,sort_keys=True).encode());m.save(m.RUN/'sources/nga/image-policy-observation.json',policy)
    p=m.load(n.RUN/n.PLAN);rows=[];seen=collections.Counter()
    candidates=[r for r in p['new_artworks'] if r['images'] and r['last']<=1955 and r['work_type'] in ['painting','drawing','print','photograph','sculpture']]
    # Illustrate a broad set of artists, preferring paintings, then drawing and print.
    rank={'painting':0,'drawing':1,'print':2,'sculpture':3,'photograph':4}
    candidates.sort(key=lambda r:(rank[r['work_type']],r['first'],int(r['native_id'])))
    for r in candidates:
        label=r['creator_label']
        if seen[label]>=2:continue
        valid=[im for im in r['images'] if im['openaccess']=='1' and im['viewtype']=='primary' and im['depictstmsobjectid']==r['native_id']]
        if not valid:continue
        valid.sort(key=lambda im:(int(im['sequence']),im['uuid']));r=dict(r,image=valid[0]);rows.append(r);seen[label]+=1
        if len(rows)==240:break
    out=dict(at=m.now(),plan_sha256=m.load(n.RUN/n.PIN)['sha256'],rows=rows,selection_basis='240 selected pre-1956 museum objects; up to two images per creator label, paintings first. Native primary-image ID match and explicit NGA openaccess=1. No exhaustive image downloading.')
    m.save(path,out);print('Selected images',len(rows),flush=True);return out
def prepare():
    p=select();ORIG.mkdir(parents=True,exist_ok=True)
    def one(r):
        aid=r['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
        if dest.exists():return m.load(dest)['state']
        imd=r['image'];url=imd['iiifurl']+'/full/!1600,1600/0/default.jpg';out=dict(artwork_id=aid,title=r['title'],artist=r['creator_label'],source_url=r['source_url'],source_image_url=url,native_image=imd)
        try:
            assert url.startswith('https://api.nga.gov/iiif/');hold=RUN/'access-hold.json';assert not hold.exists(),'Source access held'
            original=ORIG/(aid+'.source');receipt=ORIG/(aid+'.receipt.json')
            if receipt.exists():rc=m.load(receipt);raw=original.read_bytes();assert m.sha(raw)==rc['sha256']
            else:
                d.core.provider_rate_slot('api.nga.gov');response=requests.get(url,timeout=(15,60));rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=m.sha(response.content),bytes=len(response.content),content_type=response.headers.get('Content-Type'))
                if response.status_code in (401,403,429):m.save(hold,rc)
                response.raise_for_status();raw=response.content;assert rc['content_type'].startswith('image/') and len(raw)<15000000;original.write_bytes(raw);m.save(receipt,rc)
            with Image.open(io.BytesIO(raw)) as opened:
                assert opened.width*opened.height<40000000;opened.load();im=ImageOps.exif_transpose(opened).convert('RGB');output=None
                for edge in [1200,1000,850,700,600,500]:
                    im.thumbnail((edge,edge),Image.Resampling.LANCZOS)
                    for quality in [90,85,80,75,70,65,60]:
                        buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                        if buf.tell()<=100000:output=buf.getvalue();break
                    if output:break
                assert output and min(im.size)>=40
                digest=m.sha(output);sp='/assets/artworks/imported/'+m.OP+'/'+aid+'-'+digest[:16]+'.jpg';local=m.ROOT/'apps/web/public'/sp.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
                if local.exists():assert local.read_bytes()==output
                else:local.write_bytes(output)
                out.update(state='prepared',path=str(local),storage_path=sp,sha256=digest,bytes=len(output),width=im.width,height=im.height,media_id=m.uid('media/nga/'+aid+'/'+digest),download=rc,original_path=str(original))
        except Exception as e:out.update(state='held',reason=type(e).__name__+': '+str(e)[:400])
        m.save(dest,out);return out['state']
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,state in enumerate(pool.map(one,p['rows']),1):
            counts[state]+=1
            if i%40==0:print('Prepared',i,dict(counts),flush=True)
    print(dict(counts),flush=True)
def sheets():
    p=select();rows=[m.load(RUN/'prepared'/(r['artwork_id']+'.json')) for r in p['rows']];rows=[r for r in rows if r['state']=='prepared'];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for i,group in enumerate(m.chunks(rows,40)):
        canvas=Image.new('RGB',(2400,1900),'#eeeeee');draw=ImageDraw.Draw(canvas)
        for j,r in enumerate(group):
            x=j%8*300;y=j//8*380
            with Image.open(r['path']) as im:
                im.thumbnail((290,310));canvas.paste(im,(x+(300-im.width)//2,y+(310-im.height)//2))
            draw.text((x+4,y+315),str(j+1)+'. '+r['title'][:36],font=font,fill='black');draw.text((x+4,y+337),r['artist'][:35],font=font,fill='black')
        path=ORIG/('sheet-'+str(i).zfill(2)+'.jpg');canvas.save(path,quality=94);m.save(RUN/'sheets'/(str(i).zfill(2)+'.json'),dict(path=str(path),sha256=m.sha(path.read_bytes()),items=[dict(artwork_id=r['artwork_id'],sha256=r['sha256'],title=r['title']) for r in group]))
    print('Sheets',len(list((RUN/'sheets').glob('*.json'))),flush=True)
def deliver():
    p=select();reviews=m.load(RUN/'visual-review.json');rows=[r for r in p['rows'] if reviews.get(r['artwork_id'],{}).get('decision')=='accept'];bucket=storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
    canonical=m.load(n.RUN/'duplicate-reconciliation.json')['canonical_map']
    def upload(r):
        im=m.load(RUN/'prepared'/(r['artwork_id']+'.json'));assert im['sha256']==reviews[r['artwork_id']]['sha256'];raw=Path(im['path']).read_bytes();assert m.sha(raw)==im['sha256'];dest=RUN/'uploads'/(r['artwork_id']+'.json')
        if dest.exists():return
        blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':m.OP};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
        except PreconditionFailed:pass
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert m.sha(response.content)==im['sha256'];m.save(dest,dict(at=m.now(),sha256=im['sha256'],generation=blob.generation,public_verified=True))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(upload,rows))
    for i,group in enumerate(m.chunks(rows,40)):
        rp=RUN/'applied'/(str(i).zfill(3)+'.json')
        if rp.exists():continue
        ids=[canonical.get(r['artwork_id'],r['artwork_id']) for r in group]
        with m.m.connect(write=True) as db:
            db.execute("SET LOCAL lock_timeout='120s'")
            db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
            before={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))};assert len(before)==len(ids)
            m.save(m.BACKUP/'nga/images-001'/('before-'+str(i).zfill(3)+'.json.gz'),before)
            for r in group:
                im=m.load(RUN/'prepared'/(r['artwork_id']+'.json'));target=canonical.get(r['artwork_id'],r['artwork_id']);a=before[target];assert a['status']!='archived' and a['title']==r['title']
                if target==r['artwork_id']:assert a['primary_media_id'] is None and a['status']=='review' and a['creation_year_end']==r['last']
                credit=(r['creator_label']+'. ' if r['creator_label'] else '')+r['raw']['creditline']+'. Courtesy National Gallery of Art, Washington.'
                n.copy_rows(db,'media_assets',[dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=r['source_url'],provider_name='National Gallery of Art',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['creator_label'],rights_status='cc0',license_label='NGA Open Access — CC0',license_url=POLICY,creator_credit=credit,attribution_text=credit+' Full source frame preserved; proportionally resized and JPEG compressed.',retrieved_at=im['download']['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR)])
                evidence=dict(plan_sha256=p['plan_sha256'],native_image=r['image'],download=im['download'],visual_review=reviews[r['artwork_id']],identity_basis='Exact NGA object ID in published_images.depictstmsobjectid; primary open-access image.',policy_observation=m.load(m.RUN/'sources/nga/image-policy-observation.json'),image_metadata_receipt=m.load(m.RUN/'sources/nga/published_images.csv.receipt.json'))
                n.copy_rows(db,'media_rights_evidence',[dict(media_id=im['media_id'],source_id=n.SID,source_record_id=r['native_id'],source_checksum=evidence['image_metadata_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=POLICY,rights_basis='NGA published_images openaccess=1 and official Open Access policy CC0. Native object and image IDs captured; source frame visually checked.',adapter_version=m.OP,checked_at=m.now(),evidence_json=json.dumps(evidence,ensure_ascii=False))])
                order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(target,)).fetchone()['n']
                n.copy_rows(db,'artwork_media',[dict(artwork_id=target,media_id=im['media_id'],sort_order=order,view_label='NGA open-access reproduction')])
                if a['primary_media_id'] is None:db.execute('UPDATE artworks SET primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(im['media_id'],m.ACTOR,target))
            after={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
            for aid,a in after.items():assert {k:v for k,v in a.items() if k not in ['primary_media_id','updated_by','updated_at','revision']}=={k:v for k,v in before[aid].items() if k not in ['primary_media_id','updated_by','updated_at','revision']}
            db.commit()
        m.save(rp,dict(at=m.now(),images=len(group),artwork_ids=ids));print('Attached',len(group),'batch',i,flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['select','prepare','sheets','deliver']);a=ap.parse_args();globals()[a.action]()
