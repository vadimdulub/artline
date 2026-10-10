#!/usr/bin/env python3
"""User-approved Prado reproductions, preserved as restricted; bounded batches."""
import argparse,base64,collections,concurrent.futures,gzip,hashlib,importlib.util,json,math,re,threading,time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from PIL import Image,ImageDraw,ImageOps
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('expansion','ops/expand-prado-catalogue-20261006.py');r=m.r
cm=module('commons','ops/overnight-commons-images.py');core=cm.core
RUN=m.RUN/'museum-image-delivery';OP='prado-museum-images-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
POLICY='https://www.museodelprado.es/en/legal-information'
gate=threading.Lock();request_gates=collections.defaultdict(threading.Lock);next_requests=collections.defaultdict(float);paused_hosts=set()

def identities():
    authorization=r.load(m.RUN/'prado-image-authorization.json');assert authorization['user_instruction']=='Extend the WikiArt policy to Prado images'
    leads=r.load(m.RUN/'images/prado-origin-permission-review.json');plan=r.load(m.RUN/'production-plan.json.gz');by={x['artwork_id']:x for x in plan['records']}
    originals={x['artwork']['id']for x in r.load(m.RUN/'production-baseline.json.gz')['records']if not x['artwork']['primary_media_id']}
    pages={}
    for f in sorted((m.RUN/'images/commons-batches').glob('*.json')):
        for p in r.load(f)['response'].get('query',{}).get('pages',{}).values():pages[p['title'].removeprefix('File:').replace('_',' ')]=p
    source=[];held=[]
    for lead in leads:
        p=pages[lead['filename'].replace('_',' ')];x=by[lead['artwork_id']]
        source.append((lead,p,x))
    fetch=core.Fetcher(RUN/'identity-captures');fetch.defer_long_cooldowns=True;sdc={}
    mids=list(dict.fromkeys('M'+str(p['pageid'])for _,p,_ in source))
    for start in range(0,len(mids),40):
        dest=RUN/'structured-batches'/f'{start:05}.json'
        if dest.exists():data=r.load(dest)
        else:
            data=cm.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(mids[start:start+40]),'props':'claims'});r.save(dest,data)
        sdc.update(data['entities'])
        if start%400==0:print('Prado file identities',min(start+40,len(mids)),'/',len(mids),flush=True)
    selected=[]
    for lead,p,x in source:
        try:
            assert len(lead['qid'])==1,'Multiple artwork authorities require individual resolution'
            qid=lead['qid'][0];sd=sdc['M'+str(p['pageid'])];targets=cm.ids(sd,'P6243')
            assert not targets or targets=={qid},'Conflicting Commons physical-object identity'
            text=p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','');info=p['imageinfo'][0];meta=info.get('extmetadata',{})
            credit=' '.join(meta.get(k,{}).get('value','')for k in ('Credit','Attribution'));filetext=text+' '+json.dumps(meta,ensure_ascii=False)
            native_ids=set(re.findall(r'(?:obra-de-arte|art-work)/[^\s<>\"]*?/([0-9a-f-]{36})',credit,re.I))
            assert not native_ids or x['source_id']in native_ids,'Museum object link differs from selected native ID'
            exact=bool(re.search(r'\b'+qid+r'\b',filetext))or targets=={qid}or x['source_id']in native_ids
            if not exact:
                match=re.search(r'(?:accession(?: number)?|inventory)\s*=\s*([^\n|]+)',text,re.I)
                exact=bool(match and m.inventory(x['accession'])in {m.inventory(z)for z in re.split(r'[;,]',match[1])})
            assert exact,'Exact file-to-object correspondence not established'
            assert not re.search(r'\b(?:detail|detalle|verso|reverse|infrared|radiograph|collage|montage)\b',lead['filename'],re.I),'Detail, reverse or technical image requires separate review'
            assert x['date']['last']and x['date']['last']<=1955 and not x['date']['review']
            assert info.get('mime','').startswith('image/')and info['width']>=100 and info['height']>=100
            assert urlsplit(lead['source_image_url']).hostname in ('upload.wikimedia.org','thumb.wikimedia.org')
            h=re.search(r'Alto\s*:\s*([\d.,]+)',x['object']['Dimensión']);w=re.search(r'Ancho\s*:\s*([\d.,]+)',x['object']['Dimensión'])
            ratio=(info['width']/info['height'])/(float(w[1].replace(',','.'))/float(h[1].replace(',','.')))if h and w and float(h[1].replace(',','.'))and float(w[1].replace(',','.'))else None
            selected.append({'artwork_id':lead['artwork_id'],'lead':lead,'object':x['object'],'source_id':x['source_id'],'page':p,'structured_data':sd,
              'source_image_url':lead['source_image_url'],'source_page_url':lead['commons_page'],'museum_page_url':x['object']['url'],
              'rights_status':'restricted','license_label':'Prado reproduction terms; user-approved collection/display','policy_url':POLICY,
              'commons_rights_label':lead['commons_rights_label'],'creator_credit':'; '.join(z for z in [x['creator_label'],cm.plain(meta.get('Artist',{}).get('value','')),cm.plain(credit),'© Madrid, Museo Nacional del Prado']if z),
              'original_gap':lead['artwork_id']in originals,'physical_ratio_comparison':ratio,'identity_basis':'Exact Prado-native catalogue object, collection/inventory crosswalk and Commons file/object correspondence; visual review required.','at':r.now()})
        except Exception as e:held.append({'lead':lead,'reason':type(e).__name__+': '+str(e)})
    groups=collections.defaultdict(list)
    for x in selected:groups[x['artwork_id']].append(x)
    chosen=[];alternates=[]
    for aid,items in groups.items():
        items.sort(key=lambda x:(abs(math.log(x['physical_ratio_comparison']))if x['physical_ratio_comparison']else .1,-x['page']['imageinfo'][0]['width']))
        chosen.append(items[0]);alternates.extend(items[1:])
    wiki=r.load(m.RUN/'wikiart-delivery/visual-decisions.json')['approved_ids']
    ids=[x['artwork_id']for x in chosen]
    with r.connect('production')as db:current={x['id']:x['primary_media_id']for x in db.execute('SELECT id::text,primary_media_id::text FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))}
    ready=[];preserved=[]
    for x in chosen:
        if current[x['artwork_id']]or x['artwork_id']in wiki:preserved.append({'artwork_id':x['artwork_id'],'reason':'existing image or already reviewed WikiArt delivery preserved'})
        else:ready.append(x)
    ready.sort(key=lambda x:(not x['original_gap'],abs(math.log(x['physical_ratio_comparison']))<.18 if x['physical_ratio_comparison']else True,x['lead']['accession']))
    r.save_gz(RUN/'selection.json.gz',{'at':r.now(),'authorization':authorization,'ready':ready,'held':held,'alternate_files':alternates,'preserved':preserved})
    print('Prado selected',len(ready),'original gaps',sum(x['original_gap']for x in ready),'identity holds',len(held),'preserved',len(preserved),'alternate files',len(alternates),flush=True)

def request_slot(host):
    while True:
        if host in paused_hosts:raise RuntimeError('Provider paused after response; resumable selection preserved')
        wait=core.provider_cooldown_seconds(host)
        if wait>0:time.sleep(min(wait,30));continue
        # Share the established 1.1-second host gate with other catalogue jobs.
        # A source Retry-After extends this same persisted gate.
        with request_gates[host]:
            time.sleep(max(0,next_requests[host]-time.monotonic()))
            core.provider_rate_slot(host)
            next_requests[host]=time.monotonic()+(2 if host=='upload.wikimedia.org'else 1.1)
        return

def selections():
    records={x['artwork_id']:x for x in r.load(RUN/'selection.json.gz')['ready']}
    for path in sorted(RUN.glob('selection-addendum-*.json.gz')):
        records.update({x['artwork_id']:x for x in r.load(path)['ready']})
    return list(records.values())

def prepare(limit=0,selected=None):
    selected=selections()if selected is None else selected;pending=[x for x in selected if not(RUN/'prepared'/(x['artwork_id']+'.json')).exists()]
    if limit:pending=pending[:limit]
    def one(x):
        aid=x['artwork_id'];url=x['source_image_url'];host=urlsplit(url).hostname;original=ORIGINALS/(r.sha(url.encode())+'.body');receipt=RUN/'downloads'/(aid+'.json')
        try:
            if receipt.exists():rc=r.load(receipt);raw=original.read_bytes();assert r.sha(raw)==rc['sha256']
            else:
                for attempt in range(3):
                    request_slot(host)
                    response=requests.get(url,headers={'User-Agent':r.UA},timeout=(15,45),stream=True,allow_redirects=False)
                    if response.status_code!=429:break
                    bounded=next(response.iter_content(512),b'').decode('utf-8','replace')
                    r.save(RUN/'download-errors'/(aid+'-'+str(time.time_ns())+'.json'),{'at':r.now(),'method':'GET','url':url,'status':429,'retry_after':response.headers.get('Retry-After'),'content_type':response.headers.get('Content-Type'),'bounded_body':bounded,'attempt':attempt+1})
                    core.provider_rate_slot(host,cooldown=max(core.retry_delay(response.headers.get('Retry-After')),15*2**attempt))
                    response.close()
                    if attempt==2:
                        paused_hosts.add(host);raise RuntimeError('Provider paused after three rate-limit responses for one selected file')
                with response:
                    if response.status_code!=200:
                        bounded=next(response.iter_content(512),b'').decode('utf-8','replace')
                        r.save(RUN/'download-errors'/(aid+'-'+str(time.time_ns())+'.json'),{'at':r.now(),'method':'GET','url':url,'status':response.status_code,'retry_after':response.headers.get('Retry-After'),'content_type':response.headers.get('Content-Type'),'bounded_body':bounded})
                    response.raise_for_status();assert response.status_code==200 and response.headers.get('Content-Type','').startswith('image/')
                    chunks=[];size=0
                    for chunk in response.iter_content(65536):
                        size+=len(chunk)
                        if size>15_000_000:raise ValueError('Source rendition exceeds selected byte limit')
                        chunks.append(chunk)
                    raw=b''.join(chunks);rc={'at':r.now(),'url':url,'status':response.status_code,'bytes':len(raw),'sha256':r.sha(raw),'content_type':response.headers.get('Content-Type')}
                r.save(original,raw);r.save(receipt,rc)
            data,w,h,quality=core.compress(raw);digest=r.sha(data);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
            assert min(w,h)>=50 and max(w,h)>=200
            r.save(ROOT/'apps/web/public'/path.lstrip('/'),data)
            im={**x,'media_id':m.uid('media/'+OP+'/'+digest),'path':path,'sha256':digest,'bytes':len(data),'width':w,'height':h,'jpeg_quality':quality,'download':rc,'visual_path':str(ROOT/'apps/web/public'/path.lstrip('/'))}
            r.save(RUN/'prepared'/(aid+'.json'),im);return 'prepared'
        except Exception as e:
            dest=RUN/'preparation-events.jsonl';event={'at':r.now(),'artwork_id':aid,'outcome':'transient_or_source_error','error':type(e).__name__+': '+str(e)[:220]}
            with gate:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('a')as out:out.write(json.dumps(event)+'\n')
            return 'held'
    counts=collections.Counter();groups=collections.defaultdict(list)
    for x in pending:groups[urlsplit(x['source_image_url']).hostname].append(x)
    def provider(host,rows):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1 if host=='upload.wikimedia.org'else 3)as pool:
            for n,outcome in enumerate(pool.map(one,rows),1):
                with gate:
                    counts[outcome]+=1
                    if n%100==0:print('Prado image preparation',host,n,'/',len(rows),dict(counts),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(groups)or 1)as pool:
        list(pool.map(lambda pair:provider(*pair),groups.items()))
    print('Prado prepared',dict(counts),flush=True)

def sheets():
    selected=selections();records=[r.load(RUN/'prepared'/(x['artwork_id']+'.json'))for x in selected if(RUN/'prepared'/(x['artwork_id']+'.json')).exists()]
    folder=ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True);index=[]
    for start in range(0,len(records),24):
        sheet=Image.new('RGB',(1440,1280),'#eee9df');draw=ImageDraw.Draw(sheet)
        for n,x in enumerate(records[start:start+24]):
            with Image.open(x['visual_path'])as src:im=ImageOps.contain(src.convert('RGB'),(232,250))
            left=(n%6)*240;top=(n//6)*320;sheet.paste(im,(left+(240-im.width)//2,top))
            ratio=x['physical_ratio_comparison'];label=f"{start+n+1} {x['lead']['accession']}"+(' ORIGINAL GAP'if x['original_gap']else'')+f"\n{x['lead']['title'][:36]}\n{(x['lead']['creator']or'Unknown')[:34]}"+(f"\nRatio {ratio:.2f}"if ratio and abs(math.log(ratio))>.18 else'')
            draw.multiline_text((left+4,top+254),label,fill='black',spacing=3)
            index.append({'number':start+n+1,'sheet':start//24+1,'artwork_id':x['artwork_id'],'sha256':x['sha256'],'accession':x['lead']['accession'],'title':x['lead']['title'],'original_gap':x['original_gap'],'physical_ratio_comparison':ratio})
        sheet.save(folder/f'{start//24+1:03}.jpg',quality=90)
    version=len(index);r.save(RUN/f'contact-sheet-index-{version}.json',index);print('Prado sheets',folder,'images',version,'sheets',(version+23)//24,flush=True)

def batch_plan(batch):
    prefix=f'batch-{batch:03}';decisions=r.load(RUN/(prefix+'-visual.json'));prepared={}
    for decision in decisions['approved']:
        aid=decision['artwork_id'];im=r.load(RUN/'prepared'/(aid+'.json'));raw=Path(im['visual_path']).read_bytes()
        assert im['sha256']==decision['sha256']==r.sha(raw)and len(raw)==im['bytes']<=100000
        with Image.open(im['visual_path'])as src:src.load();assert src.size==(im['width'],im['height'])
        im['visual_review']=decision.get('note','Full composition and source-object identity reviewed in the labelled contact sheet.')
        im['view_label']=decision.get('view_label','Full supplied composition');prepared[aid]=im
    ids=list(prepared)
    assert len({im['sha256']for im in prepared.values()})==len(ids),'Repeated pixels need an individual object decision'
    with r.connect('production')as db:
        preimages={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
        assert len(preimages)==len(ids)
        assert all(a['current_institution_id']==m.MUSEUM and a['status']=='review'and a['primary_media_id']is None for a in preimages.values())
    plan={'operation':OP,'batch':batch,'at':r.now(),'prepared':prepared,'preimages':preimages,'source_id':m.uid('source/'+OP),
      'visual_decisions':decisions,'authorization_sha256':r.sha((m.RUN/'prado-image-authorization.json').read_bytes())}
    path=RUN/(prefix+'-plan.json.gz');r.save_gz(path,plan);digest=r.sha(path.read_bytes());r.save(RUN/(prefix+'-pin.json'),{'sha256':digest,'count':len(ids)})
    r.save_gz(BACKUP/(prefix+'-plan.json.gz'),plan);print('Pinned',prefix,len(ids),'original gaps',sum(im['original_gap']for im in prepared.values()),digest,flush=True)

def pinned(batch):
    prefix=f'batch-{batch:03}';raw=(RUN/(prefix+'-plan.json.gz')).read_bytes();pin=r.load(RUN/(prefix+'-pin.json'));assert r.sha(raw)==pin['sha256'];return json.loads(gzip.decompress(raw)),pin

def upload(batch):
    plan,pin=pinned(batch);bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(im):
        aid=im['artwork_id'];dest=RUN/'uploads'/(aid+'.json')
        if dest.exists():assert r.load(dest)['plan_sha256']==pin['sha256'];return
        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'))
        blob.metadata={'sha256':im['sha256'],'artwork-id':aid,'operation':OP,'rights-status':'restricted'};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except core.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert r.sha(response.content)==im['sha256']
        r.save(dest,{'at':r.now(),'artwork_id':aid,'plan_sha256':pin['sha256'],'sha256':im['sha256'],'bytes':len(raw),'public_bytes_verified':True})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for n,_ in enumerate(pool.map(one,plan['prepared'].values()),1):
            if n%100==0:print('Prado uploaded and verified',n,'/',len(plan['prepared']),flush=True)
    print('Upload complete',len(plan['prepared']),flush=True)

def apply(batch):
    plan,pin=pinned(batch);ids=list(plan['prepared']);sid=plan['source_id'];assert r.load(m.BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    for aid in ids:
        receipt=r.load(RUN/'uploads'/(aid+'.json'));assert receipt['plan_sha256']==pin['sha256']and receipt['public_bytes_verified']
    with r.connect('production',readonly=False)as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='10s'");db.execute('SELECT pg_advisory_xact_lock(202610066)')
        before={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
        if all(before[aid]['primary_media_id']==plan['prepared'][aid]['media_id']for aid in ids):print('Already attached',len(ids),'zero writes',flush=True);return
        assert before==plan['preimages'],'Catalogue changed after pinned plan'
        source=db.execute('SELECT id,slug FROM sources WHERE id=%s',(sid,)).fetchone()
        if source:assert source['slug']==OP
        else:m.insert(db,'sources',{'id':sid,'slug':OP,'name':'Museo Nacional del Prado reproductions via Commons — user-approved restricted image collection','source_type':'collection_page','base_url':'https://www.museodelprado.es/','terms_url':POLICY})
        with db.pipeline():
            for aid,im in plan['prepared'].items():
                title=im['lead']['title'];credit=im['creator_credit'];mid=im['media_id'];label='Prado reproduction terms; Commons label: '+im['commons_rights_label']
                m.insert(db,'media_assets',{'id':mid,'storage_kind':'local','storage_path':im['path'],'source_page_url':im['source_page_url'],'provider_name':'Museo Nacional del Prado via Wikimedia Commons','mime_type':'image/jpeg','width':im['width'],'height':im['height'],'byte_size':im['bytes'],'checksum_sha256':im['sha256'],'alt_text':title+' — '+(im['lead']['creator']or'Unidentified creator'),'rights_status':'restricted','license_label':label,'license_url':POLICY,'creator_credit':credit,'attribution_text':title+'. '+credit+'. Source terms: '+POLICY+'. Commons asserts: '+im['commons_rights_label']+'. Proportional resize and JPEG compression; full supplied composition.','retrieved_at':im['download']['at'],'verified_at':im['at'],'verified_by':m.ACTOR})
                evidence={k:v for k,v in im.items()if k not in ('visual_path',)};evidence.update(user_authorization=r.load(m.RUN/'prado-image-authorization.json'),plan_sha256=pin['sha256'])
                m.insert(db,'media_rights_evidence',{'media_id':mid,'source_id':sid,'source_record_id':str(im['page']['pageid']),'source_checksum':r.sha(json.dumps(im['page'],ensure_ascii=False,sort_keys=True).encode()),'source_image_url':im['source_image_url'],'policy_url':POLICY,'rights_basis':'User explicitly extended the WikiArt collection and public-display policy to selected Prado-origin images. Museum terms and the separate Commons label are retained; no independently obtained licence or museum permission is asserted. '+im['identity_basis'],'adapter_version':OP,'checked_at':im['at'],'evidence_json':Jsonb(evidence)})
                m.insert(db,'artwork_media',{'artwork_id':aid,'media_id':mid,'sort_order':0,'view_label':im.get('view_label','Full supplied composition')})
                db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,m.ACTOR,aid))
                m.insert(db,'citations',{'entity_type':'artwork','entity_id':aid,'field_name':'image_identity','source_id':sid,'source_record_id':im['source_id'],'source_url':im['museum_page_url'],'evidence_note':json.dumps({'plan_sha256':pin['sha256'],'batch':batch,'museum_accession':im['lead']['accession'],'file_url':im['source_page_url'],'identity_basis':im['identity_basis'],'visual_review':im['visual_review'],'scope':'Image only; preserve metadata, holdings and publication.'},ensure_ascii=False),'retrieved_at':im['at'],'created_by':m.ACTOR})
        after={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,))}
        for aid,a in after.items():
            allowed={'primary_media_id','revision','updated_at','updated_by'};assert {k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in before[aid].items()if k not in allowed};assert a['primary_media_id']==plan['prepared'][aid]['media_id']and a['revision']==before[aid]['revision']+1
    result={'at':r.now(),'batch':batch,'plan_sha256':pin['sha256'],'attached':len(ids),'original_gaps_filled':sum(im['original_gap']for im in plan['prepared'].values()),'artwork_ids':ids,'rights_status':'restricted','metadata_preserved':True,'publication_changed':False,'local_database_changed':False}
    r.save(RUN/f'batch-{batch:03}-applied.json',result);r.save_gz(BACKUP/f'batch-{batch:03}-after.json.gz',after);print(json.dumps({k:v for k,v in result.items()if k!='artwork_ids'}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['identities','prepare','sheets','batch_plan','upload','apply']);parser.add_argument('--limit',type=int,default=0);parser.add_argument('--batch',type=int,default=1);args=parser.parse_args()
    if args.command=='prepare':prepare(args.limit)
    elif args.command in ('batch_plan','upload','apply'):globals()[args.command](args.batch)
    else:globals()[args.command]()
