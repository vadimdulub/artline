#!/usr/bin/env python3
"""Image-only delivery of selected, independently licensed Prado reproductions."""
import argparse,base64,collections,concurrent.futures,gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageOps
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('images','ops/research-prado-expansion-images-20261006.py');r=m.r;cm=m.cm;core=cm.core
RUN=m.RUN/'delivery';OP='prado-expansion-commons-20261006';BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP

def prepare():
    selected=r.load(m.RUN/'commons-reviewed-selection.json.gz')['approved'];fetch=core.Fetcher(RUN/'downloads');fetch.defer_long_cooldowns=True
    for n,x in enumerate(selected,1):
        aid=x['lead']['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
        if dest.exists():continue
        try:
            raw,headers=fetch.get(x['source_image_url'],15_000_000)
            original=ORIGINALS/(aid+'-'+r.sha(raw)[:16]+'.original');core.save_new(original,raw)
            data,w,h,quality=core.compress(raw);digest=r.sha(data);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
            core.save_new(ROOT/'apps/web/public'/path.lstrip('/'),data)
            prepared={**x,'artwork_id':aid,'media_id':m.m.uid('media/'+digest),'path':path,'sha256':digest,'bytes':len(data),'width':w,'height':h,'jpeg_quality':quality,
              'downloaded_at':r.now(),'source_sha256':r.sha(raw),'source_bytes':len(raw),'response_headers':headers,'original_path':str(original),'visual_path':str(ROOT/'apps/web/public'/path.lstrip('/'))}
            r.save(dest,prepared)
        except Exception as e:r.save(RUN/'preparation-held'/(aid+'.json'),{'artwork_id':aid,'reason':type(e).__name__+': '+str(e)[:300]})
        if n%10==0:print('Prepared image decisions',n,'/',len(selected),flush=True)

def sheets():
    records=[r.load(f)for f in sorted((RUN/'prepared').glob('*.json'))];index=[];dest=Path('/private/tmp/artline-prado-expansion-commons-qa');dest.mkdir(exist_ok=True)
    for start in range(0,len(records),24):
        sheet=Image.new('RGB',(1440,1280),'#eee9df');draw=ImageDraw.Draw(sheet)
        for j,x in enumerate(records[start:start+24]):
            with Image.open(x['visual_path'])as original:im=ImageOps.contain(original.convert('RGB'),(230,255))
            col=j%6;row=j//6;sheet.paste(im,(col*240+(240-im.width)//2,row*320))
            draw.multiline_text((col*240+4,row*320+258),f"{start+j+1} {x['lead']['accession']}\n{x['lead']['title'][:35]}\n{(x['lead']['creator']or'Unknown')[:35]}",fill='black',spacing=3)
            index.append({'number':start+j+1,'artwork_id':x['artwork_id'],'sha256':x['sha256'],'accession':x['lead']['accession'],'title':x['lead']['title'],'path':x['visual_path']})
        sheet.save(dest/f'sheet-{start//24+1:02}.jpg')
    r.save(RUN/'contact-sheet-index.json',index);print('Sheets',dest,'images',len(index),flush=True)

def plan():
    decision=r.load(RUN/'visual-decisions.json');index=r.load(RUN/'contact-sheet-index.json');ids=decision['approved_ids']
    assert set(ids)|set(decision['held'])=={x['artwork_id']for x in index};assert not set(ids)&set(decision['held'])
    prepared={aid:r.load(RUN/'prepared'/(aid+'.json'))for aid in ids}
    for aid,note in decision.get('object_resolutions',{}).items():
        if aid in prepared:prepared[aid]['visual_resolution']=note
    assert len({x['sha256']for x in prepared.values()})==len(prepared),'Duplicate pixels require review'
    with r.connect('production')as db:
        before={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
        assert len(before)==len(ids)
        assert all(a['current_institution_id']==m.m.MUSEUM and a['primary_media_id']is None for a in before.values())
    for x in prepared.values():
        raw=Path(x['visual_path']).read_bytes();assert len(raw)==x['bytes']<=100000 and r.sha(raw)==x['sha256']
    plan={'operation':OP,'at':r.now(),'preimages':before,'prepared':prepared,'visual_decisions':decision,'source_id':m.m.uid('source/'+OP)}
    r.save_gz(RUN/'production-plan.json.gz',plan);digest=r.sha((RUN/'production-plan.json.gz').read_bytes());r.save(RUN/'production-plan-pin.json',{'sha256':digest,'images':len(ids)})
    r.save_gz(BACKUP/'production-plan.json.gz',plan);print('Pinned image plan',len(ids),digest,flush=True)

def pinned():
    raw=(RUN/'production-plan.json.gz').read_bytes();pin=r.load(RUN/'production-plan-pin.json');assert r.sha(raw)==pin['sha256'];return json.loads(gzip.decompress(raw)),pin

def upload():
    plan,pin=pinned();bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(x):
        dest=RUN/'uploads'/(x['artwork_id']+'.json')
        if dest.exists():return
        raw=Path(x['visual_path']).read_bytes();assert r.sha(raw)==x['sha256'];blob=bucket.blob(x['path'].lstrip('/'))
        blob.metadata={'sha256':x['sha256'],'artwork-id':x['artwork_id'],'operation':OP};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except core.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+x['path'],timeout=(15,45));response.raise_for_status();assert r.sha(response.content)==x['sha256']
        r.save(dest,{'at':r.now(),'artwork_id':x['artwork_id'],'sha256':x['sha256'],'plan_sha256':pin['sha256'],'public_bytes_verified':True})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,plan['prepared'].values()))
    print('Uploaded and publicly verified',len(plan['prepared']),flush=True)

def apply():
    plan,pin=pinned();ids=list(plan['prepared']);sid=plan['source_id'];assert r.load(m.m.BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    for aid in ids:
        receipt=r.load(RUN/'uploads'/(aid+'.json'));assert receipt['plan_sha256']==pin['sha256']and receipt['public_bytes_verified']
    with r.connect('production',readonly=False)as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='10s'");db.execute('SELECT pg_advisory_xact_lock(202610066)')
        before={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()};assert before==plan['preimages']
        m.m.insert(db,'sources',{'id':sid,'slug':OP,'name':'Wikimedia Commons — independently licensed Prado reproductions, 6 October 2026','source_type':'collection_page','base_url':'https://commons.wikimedia.org/'})
        for aid,x in plan['prepared'].items():
            artist=x['lead']['creator']or'Unknown creator';credit=x['creator_credit'];title=x['lead']['title'];mid=x['media_id']
            m.m.insert(db,'media_assets',{'id':mid,'storage_kind':'local','storage_path':x['path'],'source_page_url':x['source_page_url'],'provider_name':'Wikimedia Commons','mime_type':'image/jpeg','width':x['width'],'height':x['height'],'byte_size':x['bytes'],'checksum_sha256':x['sha256'],'alt_text':title+' — '+artist,'rights_status':x['rights_status'],'license_label':x['license_label'],'license_url':x['policy_url'],'creator_credit':credit,'attribution_text':artist+'. '+title+'. '+credit+'. '+x['license_label']+' ('+x['policy_url']+'). Full-frame proportional resize and JPEG compression; no crop.','retrieved_at':x['downloaded_at'],'verified_at':x['at'],'verified_by':m.m.ACTOR})
            evidence={k:v for k,v in x.items()if k not in ('visual_path','original_path')}
            m.m.insert(db,'media_rights_evidence',{'media_id':mid,'source_id':sid,'source_record_id':str(x['page']['pageid']),'source_checksum':r.sha(json.dumps(x['page'],ensure_ascii=False,sort_keys=True).encode()),'source_image_url':x['source_image_url'],'policy_url':x['policy_url'],'rights_basis':x['identity_basis'],'adapter_version':OP,'checked_at':x['at'],'evidence_json':Jsonb(evidence)})
            m.m.insert(db,'artwork_media',{'artwork_id':aid,'media_id':mid,'sort_order':0,'view_label':'Historical state before restoration'if x.get('visual_resolution')else'Full supplied composition'})
            db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,m.m.ACTOR,aid))
            m.m.insert(db,'citations',{'entity_type':'artwork','entity_id':aid,'field_name':'image_identity','source_id':sid,'source_record_id':str(x['page']['pageid']),'source_url':x['source_page_url'],'evidence_note':json.dumps({'plan_sha256':pin['sha256'],'identity_basis':x['identity_basis'],'origin':x['origin'],'museum_accession':x['lead']['accession'],'scope':'Image only; preserve metadata, holdings and publication.'},ensure_ascii=False),'retrieved_at':x['at'],'created_by':m.m.ACTOR})
        after={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
        for aid,a in after.items():
            allowed={'primary_media_id','revision','updated_at','updated_by'};assert {k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in before[aid].items()if k not in allowed};assert a['primary_media_id']==plan['prepared'][aid]['media_id']
    r.save(RUN/'production-applied.json',{'at':r.now(),'plan_sha256':pin['sha256'],'attached':len(ids),'artwork_ids':ids,'publication_changed':False,'local_database_changed':False});r.save_gz(BACKUP/'production-after.json.gz',after);print('Attached',len(ids),'Commons images',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','sheets','plan','upload','apply']);globals()[p.parse_args().command]()
