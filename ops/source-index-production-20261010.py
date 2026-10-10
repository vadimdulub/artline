#!/usr/bin/env python3
"""Assistant-reviewed authentic images and source-backed production catalogue additions."""
import argparse,importlib.util,json,hashlib,re,io,base64,subprocess,time
from pathlib import Path
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import urlsplit,urljoin
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps
from psycopg.types.json import Jsonb
from psycopg import sql
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
s=importlib.util.spec_from_file_location('resolution',Path(__file__).with_name('source-index-resolve-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;n=r.n;RUN=r.RUN;OP=r.OP;ROOT=m.ROOT;uid=r.uid
s=importlib.util.spec_from_file_location('previous_delivery',Path(__file__).with_name('source-index-deliver-20261009.py'));old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
core=old.core;ACTOR=old.ACTOR
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
NAMES={'smk':'Statens Museum for Kunst','fng':'Finnish National Gallery','mia':'Minneapolis Institute of Art','cleveland':'Cleveland Museum of Art','walters':'Walters Art Museum','moma':'Museum of Modern Art','wikiart':'WikiArt'}
HOSTS={'smk':{'iip.smk.dk','api.smk.dk'},'fng':{'kokoelma.kansallisgalleria.fi'},'mia':{'img.artsmia.org'},'cleveland':{'openaccess-cdn.clevelandart.org'},'walters':{'art.thewalters.org'},'wikiart':{'uploads0.wikiart.org','uploads1.wikiart.org','uploads2.wikiart.org','uploads3.wikiart.org','uploads4.wikiart.org','uploads5.wikiart.org','uploads6.wikiart.org','uploads7.wikiart.org','uploads8.wikiart.org','uploads9.wikiart.org','www.wikiart.org'}}
NAMES.update({'getty':'J. Paul Getty Museum','russian-museum':'State Russian Museum','rijksmuseum':'Rijksmuseum','saam':'Smithsonian American Art Museum','domain:collection.pushkinmuseum.art':'Pushkin State Museum of Fine Arts','goulandris':'Basil & Elise Goulandris Foundation','benaki':'Benaki Museum','domain:ebyzantinemuseum.gr':'Byzantine and Christian Museum, Athens','leventis':'A. G. Leventis Gallery'})
HOSTS.update({'getty':{'media.getty.edu'},'russian-museum':{'rusmuseumvrm.ru'},'rijksmuseum':{'iiif.micr.io'},'saam':{'ids.si.edu'},'domain:collection.pushkinmuseum.art':{'collection.pushkinmuseum.art'},'goulandris':{'goulandris.gr','www.goulandris.gr'},'benaki':{'www.benaki.org','benaki.org'},'domain:ebyzantinemuseum.gr':{'www.ebyzantinemuseum.gr','ebyzantinemuseum.gr'},'leventis':{'www.leventisgallery.org','leventisgallery.org'}})
HOSTS['goulandris'].add('s3-eu-west-1.amazonaws.com')
NAMES.update({'krakow':'National Museum in Kraków','domain:api-zbiory.mnk.pl':'National Museum in Kraków','domain:cyfrowe-api.mnw.art.pl':'National Museum in Warsaw','nationalmuseum':'Nationalmuseum, Stockholm','domain:digitalarchive.npm.gov.tw':'National Palace Museum, Taipei'})
HOSTS.update({'krakow':{'cdn-zbiory.mnk.pl'},'domain:api-zbiory.mnk.pl':{'cdn-zbiory.mnk.pl'},'domain:cyfrowe-api.mnw.art.pl':{'cyfrowe-cdn.mnw.art.pl'},'nationalmuseum':{'collection.nationalmuseum.se'},'domain:digitalarchive.npm.gov.tw':{'digitalarchive.npm.gov.tw'}})
NAMES.update({'chicago':'Art Institute of Chicago','byzantine-thessaloniki':'Museum of Byzantine Culture, Thessaloniki'})
HOSTS.update({'chicago':{'www.artic.edu'},'byzantine-thessaloniki':{'www.mbp.gr'}})
HOSTS['domain:ebyzantinemuseum.gr'].add('www.psfiles.gr')

def extra_rows():
    paths=sorted(RUN.glob('secondary-resolution-*.json.gz'));rows=m.load(paths[-1])['rows'] if paths else [];independent=RUN/'independent-wikiart-resolution.json.gz'
    if independent.exists():
        known={x['artwork_id'] for x in rows};rows+=[x for x in m.load(independent)['rows'] if x['artwork_id'] not in known]
    return rows
def rows():
    native={x['artwork_id']:x for x in m.load(RUN/r.RESOLUTION)['rows']};native.update({x['artwork_id']:x for x in extra_rows()});return list(native.values())
def facts(row):return r.effective_facts(m.load(ROOT/row['native_file']))
def snapshot(db,ids):return old.snapshot(db,ids)

def prepare(extra=False):
    selected=[x for x in (extra_rows() if extra else rows()) if x['image_candidate']];ORIGINALS.mkdir(parents=True,exist_ok=True)
    def one(row):
        aid=row['artwork_id'];dest=RUN/'prepared-images'/(aid+'.json')
        if dest.exists():return m.load(dest)['state']
        f=facts(row);provider=row['provider'];url=f['image'];out=dict(artwork_id=aid,provider=provider,title=row['title'],source_url=f['page'],source_image_url=url)
        try:
            assert f['image_open'] and row['state'] in ('new','existing')
            assert not (RUN/('image-host-hold-'+provider+'.json')).exists(),'Image source access hold'
            original=ORIGINALS/(aid+'.source');receipt=ORIGINALS/(aid+'.receipt.json')
            if receipt.exists():rc=m.load(receipt);raw=original.read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256']
            else:
                dest_url=url
                for _ in range(4):
                    p=urlsplit(dest_url);assert p.scheme=='https' and p.netloc in HOSTS[provider],('Unexpected image host',p.netloc)
                    with requests.get(dest_url,headers={'User-Agent':n.f.UA},timeout=(15,60),stream=True,allow_redirects=False) as response:
                        if response.status_code in (301,302,303,307,308):dest_url=urljoin(dest_url,response.headers['Location']);continue
                        if response.status_code in (401,403,429):m.save(RUN/('image-host-hold-'+provider+'.json'),dict(at=m.now(),url=dest_url,status=response.status_code))
                        response.raise_for_status();ct=response.headers.get('Content-Type','');assert ct.startswith('image/') or (provider=='fng' and ct=='application/octet-stream'),'Unexpected image content type: '+ct
                        parts=[];size=0
                        for chunk in response.iter_content(65536):
                            size+=len(chunk);assert size<=30_000_000,'Selected source file exceeds 30 MB';parts.append(chunk)
                        raw=b''.join(parts);rc=dict(url=url,final_url=dest_url,at=m.now(),bytes=size,sha256=hashlib.sha256(raw).hexdigest(),content_type=response.headers.get('Content-Type'))
                        original.write_bytes(raw);m.save(receipt,rc);break
                else:raise ValueError('Too many redirects')
            with Image.open(io.BytesIO(raw)) as opened:
                if opened.width*opened.height>40_000_000:
                    assert opened.format=='JPEG' and opened.width*opened.height<=160_000_000,'Oversized source dimensions'
                    opened.draft('RGB',(2400,2400));assert opened.width*opened.height<=40_000_000
                    intermediate=io.BytesIO();ImageOps.exif_transpose(opened).convert('RGB').save(intermediate,'JPEG',quality=95);working=intermediate.getvalue()
                else:working=raw
            data,width,height,quality=core.compress(working)
            assert min(width,height)>=16 and max(width,height)>=300,'Insufficient useful reproduction dimensions'
            digest=hashlib.sha256(data).hexdigest();path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/path.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
            if local.exists():assert local.read_bytes()==data
            else:local.write_bytes(data)
            with Image.open(local) as opened:opened.verify()
            out.update(state='prepared',storage_path=path,path=str(local),sha256=digest,bytes=len(data),width=width,height=height,quality=quality,media_id=uid('media/'+aid+'/'+digest),download=rc,original_path=str(original),image_rights=f['image_rights'],image_view_note=f.get('image_view_note'))
        except Exception as e:out.update(state='held',reason=type(e).__name__+': '+str(e)[:350])
        m.save(dest,out);return out['state']
    def batch(provider):
        rr=[x for x in selected if x['provider']==provider];counts=Counter()
        for i,row in enumerate(rr,1):
            counts[one(row)]+=1
            if i%25==0:print('Image preparation',provider,i,'/',len(rr),dict(counts),flush=True)
        return provider,dict(counts)
    counts={}
    with ThreadPoolExecutor(max_workers=7) as pool:
        for p,cc in pool.map(batch,sorted({x['provider'] for x in selected})):counts[p]=cc
    suffix=('extra-' if extra else 'native-')+str(len(list(RUN.glob('image-preparation-summary-'+('extra' if extra else 'native')+'*.json')))+1)
    m.save(RUN/('image-preparation-summary-'+suffix+'.json'),dict(at=m.now(),selected=len(selected),providers=counts));print('Images prepared',counts,flush=True)

def sheets():
    batches=sorted((RUN/'contact-batches').glob('*.json'));seen={x['artwork_id'] for b in batches for sh in m.load(b)['sheets'] for x in sh['items']};batchno=len(batches)+1
    ims=[m.load(p) for p in sorted((RUN/'prepared-images').glob('*.json')) if m.load(p)['state']=='prepared' and m.load(p)['artwork_id'] not in seen];assert ims,'No new images awaiting visual review';output=ORIGINALS/'contact-sheets';output.mkdir(parents=True,exist_ok=True)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    except OSError:font=ImageFont.load_default()
    index=[]
    for offset in range(0,len(ims),40):
        subset=ims[offset:offset+40];sheet=Image.new('RGB',(2400,1750),'#eeeeee');draw=ImageDraw.Draw(sheet);items=[]
        for j,im in enumerate(subset):
            x=j%8*300;y=j//8*350
            with Image.open(im['path']) as opened:
                thumb=opened.convert('RGB');thumb.thumbnail((290,295),Image.Resampling.LANCZOS);sheet.paste(thumb,(x+(300-thumb.width)//2,y+(295-thumb.height)//2))
            draw.text((x+5,y+298),str(offset+j+1)+'. '+im['provider']+' '+im['artwork_id'][:8],font=font,fill='black')
            draw.text((x+5,y+318),im['title'][:36],font=font,fill='black');items.append(dict(number=offset+j+1,artwork_id=im['artwork_id'],image_sha256=im['sha256'],title=im['title']))
        path=output/f'batch-{batchno:03d}-sheet-{offset//40+1:03d}.jpg';sheet.save(path,quality=92);index.append(dict(path=str(path),sha256=m.m.sha(path),items=items))
    m.save(RUN/'contact-batches'/f'{batchno:03d}.json',dict(at=m.now(),sheets=index,images=len(ims)));print('Visual review batch',batchno,'sheets',len(index),'images',len(ims),flush=True)

def finish_sheets():
    sheets=[sh for p in sorted((RUN/'contact-batches').glob('*.json')) for sh in m.load(p)['sheets']];items={x['artwork_id']:x for sh in sheets for x in sh['items']};prepared={m.load(p)['artwork_id'] for p in (RUN/'prepared-images').glob('*.json') if m.load(p)['state']=='prepared'};assert set(items)==prepared
    decisions=[x for p in sorted((RUN/'visual-review-batches').glob('*.json')) for x in m.load(p)['decisions']];assert len({x['artwork_id'] for x in decisions})==len(decisions) and {x['artwork_id'] for x in decisions}==prepared
    for x in decisions:assert x['image_sha256']==items[x['artwork_id']]['image_sha256']
    m.save(RUN/'contact-sheet-index.json',dict(at=m.now(),sheets=sheets,images=len(prepared)));m.save(RUN/'visual-review.json',dict(at=m.now(),contact_index_sha256=m.m.sha(RUN/'contact-sheet-index.json'),method='Assistant inspected every contact sheet and selected individual enlargements. Decisions tied to image SHA-256 and immutable sheet-batch receipts.',decisions=decisions));print('All image decisions pinned',len(decisions),dict(Counter(x['decision'] for x in decisions)),flush=True)

def backup():
    BACKUP.mkdir(parents=True,exist_ok=True)
    def cloud(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--format=json'],text=True))
    description='Before source-index artwork and image delivery 20261010'
    matches=[x for x in cloud('sql','backups','list','--instance=artline-postgres','--limit=50') if x.get('description')==description]
    if not matches:
        result=cloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async');m.save(BACKUP/'cloud-backup-operation.json',result);print('Recovery backup requested',flush=True);return
    row=max(matches,key=lambda x:int(x['id']));print('Recovery backup',row['id'],row['status'],flush=True)
    if row['status']=='SUCCESSFUL':m.save(BACKUP/'cloud-backup.json',row);m.save(RUN/'cloud-backup.json',dict(id=row['id'],status=row['status'],description=description))

def plan():
    assert not (RUN/'delivery-plan.json.gz').exists()
    visual=m.load(RUN/'visual-review.json');index=m.load(RUN/'contact-sheet-index.json');assert visual['contact_index_sha256']==m.m.sha(RUN/'contact-sheet-index.json')
    decisions={x['artwork_id']:x for x in visual['decisions']};sheetitems={x['artwork_id']:x for sheet in index['sheets'] for x in sheet['items']};assert set(decisions)==set(sheetitems)
    for sheet in index['sheets']:assert m.m.sha(sheet['path'])==sheet['sha256']
    selected=[x for x in rows() if x['state']=='existing' and (x['field_updates'] or x['image_candidate'])]
    assert not any(x['state']=='new' for x in rows()),'New artwork delivery requires a separate reviewed insertion plan'
    baseline={a['id']:a for a in m.load(RUN/r.INVENTORY)['artworks']};baseline.update({a['id']:a for a in m.load(RUN/'inventory.json.gz')['artworks'] if a['id'] not in baseline})
    with m.m.connect() as db:before=snapshot(db,[x['artwork_id'] for x in selected])
    claims=[];held=[]
    for x in selected:
        aid=x['artwork_id'];current=before.get(aid)
        if not current or current['artwork']['status']=='archived':held.append(dict(artwork_id=aid,reason='Missing or archived'));continue
        a=current['artwork'];f=facts(x);native=m.load(ROOT/x['native_file'])
        if any(a.get(k)!=baseline[aid].get(k) for k in ['title','current_institution_id','creation_year_start','creation_year_end','date_precision','date_display','accession_number']):held.append(dict(artwork_id=aid,reason='Object identity fields changed since resolution'));continue
        fields={k:v for k,v in x['field_updates'].items() if not str(a.get(k) or '').strip()};im=None;prepared=RUN/'prepared-images'/(aid+'.json')
        image_date_hold=any(year is not None and year>1970 for year in [a.get('creation_year_end'),f.get('dates',{}).get('end')])
        if image_date_hold:held.append(dict(artwork_id=aid,reason='Image date scope crosses or follows 1970; existing record and date uncertainty retained'))
        if not a['primary_media_id'] and prepared.exists() and not image_date_hold:
            data=m.load(prepared)
            if data['state']=='prepared' and decisions[aid]['decision']=='accept':
                assert data['sha256']==decisions[aid]['image_sha256']==sheetitems[aid]['image_sha256']==m.m.sha(data['path'])
                assert data['source_url']==f['page'] and data['source_image_url']==f['image']
                im=dict(data,view_label=decisions[aid].get('view_label') or f.get('image_view_note') or 'Full source reproduction',visual_note=decisions[aid]['note'])
        if not fields and not im:continue
        claims.append(dict(artwork_id=aid,provider=x['provider'],title=a['title'],updates=fields,image=im,source_index_ids=x['source_index_ids'],source_url=f['page'],source_record_id=str(f['native_id']),source_facts=f,source_receipt=native['receipt'],native_file=x['native_file'],native_sha256=m.m.sha(ROOT/x['native_file']),identity_review=x['identity_basis']))
    assert claims
    value=dict(at=m.now(),operation=OP,index_sha256=m.m.sha(m.PREVIOUS/'sources.jsonl'),visual_review_sha256=m.m.sha(RUN/'visual-review.json'),resolution_sha256=m.m.sha(RUN/r.RESOLUTION),claims=claims,preimages={c['artwork_id']:before[c['artwork_id']] for c in claims},source_ids={p:uid('source/'+p) for p in {c['provider'] for c in claims}},concurrent_holds=held,policy='Production only. Exact object identities; preserve all existing title/date/creator/holding/status fields and image attachments. Fill only empty medium/dimensions/accession and primary image. No new display claims.')
    m.save(RUN/'delivery-plan.json.gz',value);BACKUP.mkdir(parents=True,exist_ok=True);m.save(BACKUP/'delivery-plan-and-preimages.json.gz',value)
    pin=dict(path=str((RUN/'delivery-plan.json.gz').relative_to(ROOT)),sha256=m.m.sha(RUN/'delivery-plan.json.gz'),artworks=len(claims),images=sum(bool(c['image']) for c in claims),metadata_fields=sum(len(c['updates']) for c in claims),metadata_artworks=sum(bool(c['updates']) for c in claims));m.save(RUN/'delivery-plan-pin.json',pin);print(json.dumps(pin,indent=2),flush=True)

def pinned():
    pin=m.load(RUN/'delivery-plan-pin.json');assert m.m.sha(ROOT/pin['path'])==pin['sha256'];plan=m.load(ROOT/pin['path']);assert m.m.sha(m.PREVIOUS/'sources.jsonl')==plan['index_sha256'];assert m.m.sha(RUN/'visual-review.json')==plan['visual_review_sha256'];return plan,pin

def upload():
    plan,pin=pinned();bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(c):
        im=c['image'];dest=RUN/'uploads'/(c['artwork_id']+'.json')
        if dest.exists():receipt=m.load(dest);assert receipt['plan_sha256']==pin['sha256'];return receipt
        raw=Path(im['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==im['sha256'] and len(raw)<=100000
        blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':OP};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
        except PreconditionFailed:pass
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));response.raise_for_status();assert hashlib.sha256(response.content).hexdigest()==im['sha256']
        receipt=dict(at=m.now(),artwork_id=c['artwork_id'],path=im['storage_path'],plan_sha256=pin['sha256'],sha256=im['sha256'],public_verified=True,generation=blob.generation);m.save(dest,receipt);return receipt
    ims=[c for c in plan['claims'] if c['image']]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,_ in enumerate(pool.map(one,ims),1):
            if i%50==0:print('Uploaded and publicly verified',i,'/',len(ims),flush=True)

def insert_many(db,table,records):
    if not records:return
    keys=list(records[0]);assert all(list(x)==keys for x in records)
    cols=sql.SQL(',').join(map(sql.Identifier,keys))
    query=sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(sql.Identifier(table),cols,cols,sql.Identifier(table))
    for batch in r.batches(records,200):db.execute(query,(Jsonb(batch),))

def apply():
    plan,pin=pinned()
    if (RUN/'production-applied.json').exists():assert m.load(RUN/'production-applied.json')['plan_sha256']==pin['sha256'];print('Already applied: no writes');return
    assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'
    for c in plan['claims']:
        assert m.m.sha(ROOT/c['native_file'])==c['native_sha256']
        if c['image']:
            receipt=m.load(RUN/'uploads'/(c['artwork_id']+'.json'));assert receipt['public_verified'] and receipt['plan_sha256']==pin['sha256']
    s=importlib.util.spec_from_file_location('alignment',ROOT/'ops/align-catalogues-20261008.py');dbm=importlib.util.module_from_spec(s);s.loader.exec_module(dbm)
    ids=[c['artwork_id'] for c in plan['claims']]
    with dbm.connect('production',readonly=False) as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();assert snapshot(db,ids)==plan['preimages'],'Concurrent catalogue edits: transaction stopped before writes'
        m.save(BACKUP/'locked-preimages.json.gz',dict(plan_sha256=pin['sha256'],preimages=plan['preimages']))
        insert_many(db,'sources',[dict(id=sid,slug=OP+'-'+re.sub('[^a-z0-9]+','-',p),name=NAMES[p]+' — source-index delivery, 10 October 2026',source_type='museum_api' if p in ['smk','fng','mia','cleveland','walters','moma'] else 'collection_page',base_url=next(c['source_url'] for c in plan['claims'] if c['provider']==p),priority=10) for p,sid in plan['source_ids'].items()])
        media=[];evidence=[];attachments=[];citations=[];updates=[]
        for c in plan['claims']:
            aid=c['artwork_id'];p=c['provider'];sid=plan['source_ids'][p];f=c['source_facts'];im=c['image'];fields=dict(c['updates'])
            if im:
                rights=f.get('rights_status') or ('cc0' if f.get('license_url')==n.CC0 else 'public_domain');credit='; '.join(filter(None,[NAMES[p],f.get('credit')]))
                media.append(dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=c['source_url'],provider_name=NAMES[p],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=c['title'],rights_status=rights,license_label=f['image_rights'] or 'No source label',license_url=f['license_url'],creator_credit=credit,attribution_text=c['title']+'. '+credit+'. Proportional resize and JPEG compression; complete source frame.',retrieved_at=im['download']['at'],verified_at=m.now(),verified_by=ACTOR))
                evidence.append(dict(media_id=im['media_id'],source_id=sid,source_record_id=c['source_record_id'],source_checksum=c['source_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=f['license_url'],rights_basis=f.get('rights_basis') or 'Explicit native museum per-object image reuse label; source rights retained.',adapter_version=OP,checked_at=c['source_receipt']['retrieved_at'],evidence_json=dict(source_facts=f,source_receipt=c['source_receipt'],download=im['download'],source_index_ids=c['source_index_ids'],index_sha256=plan['index_sha256'],plan_sha256=pin['sha256'],visual_note=im['visual_note'])))
                attachments.append(dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label=im['view_label']));fields['primary_media_id']=im['media_id']
            assert set(fields)<={'medium_text','dimensions_text','accession_number','primary_media_id'}
            updates.append(dict(id=aid,fields=fields))
            note=dict(operation=OP,plan_sha256=pin['sha256'],source_index_ids=c['source_index_ids'],index_sha256=plan['index_sha256'],field_updates=c['updates'],image_added=bool(im),source_facts=f,identity_review=c['identity_review'],scope='Existing work enrichment only. Dates, title, holdings, display, creators and historical status preserved.')
            citations.append(dict(id=uid('citation/'+aid),entity_type='artwork',entity_id=aid,field_name='source_index_verified_enrichment',source_id=sid,source_record_id=c['source_record_id'],source_url=c['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=c['source_receipt']['retrieved_at'],created_by=ACTOR))
        insert_many(db,'media_assets',media);insert_many(db,'media_rights_evidence',evidence);insert_many(db,'artwork_media',attachments);insert_many(db,'citations',citations)
        # A single bounded server-side update avoids thousands of network round trips.
        changed=db.execute('''WITH changes AS (SELECT * FROM jsonb_to_recordset(%s) AS x(id uuid,fields jsonb))
          UPDATE artworks a SET medium_text=CASE WHEN fields ? 'medium_text' THEN fields->>'medium_text' ELSE a.medium_text END,
          dimensions_text=CASE WHEN fields ? 'dimensions_text' THEN fields->>'dimensions_text' ELSE a.dimensions_text END,
          accession_number=CASE WHEN fields ? 'accession_number' THEN fields->>'accession_number' ELSE a.accession_number END,
          primary_media_id=CASE WHEN fields ? 'primary_media_id' THEN (fields->>'primary_media_id')::uuid ELSE a.primary_media_id END,
          revision=revision+1,updated_at=now(),updated_by=%s FROM changes c WHERE a.id=c.id''',(Jsonb(updates),ACTOR)).rowcount
        assert changed==len(ids);after=snapshot(db,ids);old.validate_after(plan,after)
        insert_many(db,'audit_log',[dict(id=uid('audit/'+aid),actor_user_id=ACTOR,action='source_index_enrichment',entity_type='artwork',entity_id=aid,request_id=OP,before_json=plan['preimages'][aid],after_json=after[aid]) for aid in ids])
        m.save(BACKUP/'transaction-after.json.gz',dict(plan_sha256=pin['sha256'],after=after))
    receipt=dict(at=m.now(),plan_sha256=pin['sha256'],index_sha256=plan['index_sha256'],artworks=len(ids),metadata_artworks=sum(bool(c['updates']) for c in plan['claims']),metadata_fields=sum(len(c['updates']) for c in plan['claims']),new_images=len(media),citations=len(citations),audit_rows=len(ids),new_artworks=0,status_changes=0,current_display_claims=0,local_catalogue_writes=0);m.save(RUN/'production-applied.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

def verify():
    plan,pin=pinned();receipt=m.load(RUN/'production-applied.json');assert receipt['plan_sha256']==pin['sha256'];ids=[c['artwork_id'] for c in plan['claims']]
    with m.m.connect() as db:
        after=snapshot(db,ids);old.validate_after(plan,after)
        for table,keys in [('citations',[uid('citation/'+aid) for aid in ids]),('audit_log',[uid('audit/'+aid) for aid in ids])]:assert db.execute(sql.SQL('SELECT count(*) n FROM {} WHERE id=ANY(%s::uuid[])').format(sql.Identifier(table)),(keys,)).fetchone()['n']==len(ids)
        media_ids=[c['image']['media_id'] for c in plan['claims'] if c['image']];actual=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(media_ids,)).fetchall();by={x['media']['id']:x for x in actual};assert len(by)==len(media_ids)
        for c in plan['claims']:
            if not c['image']:continue
            im=c['image'];got=by[im['media_id']];assert got['media']['checksum_sha256']==im['sha256'] and got['media']['byte_size']==im['bytes']<=100000;assert got['evidence']['source_checksum']==c['source_receipt']['sha256']
    result=dict(at=m.now(),plan_sha256=pin['sha256'],verified_artworks=len(ids),verified_images=len(media_ids),verified_citations=len(ids),verified_audit_rows=len(ids),original_artwork_fields_preserved=True,original_artist_links_preserved=True,original_image_attachments_preserved=True,local_catalogue_writes=0);m.save(RUN/'production-verification.json',result);print(json.dumps(result,indent=2),flush=True)

def public_verify():
    plan,pin=pinned()
    # AGENTS.md 10 October: individual artist/artwork pages are public;
    # museum browsing requires membership. Use those intended public surfaces.
    artist_ids=sorted({a['artist_id'] for item in plan['preimages'].values() for a in item['creators']})
    with m.m.connect() as db:artists={x['id']:x['slug'] for x in db.execute("SELECT id::text,slug FROM artists WHERE id=ANY(%s::uuid[]) AND status<>'archived'",(artist_ids,)).fetchall()}
    routes={}
    for c in plan['claims']:
        aid=c['artwork_id'];a=plan['preimages'][aid];choices=[x for x in a['creators'] if x['artist_id'] in artists]
        routes[aid]='artists/'+artists[choices[0]['artist_id']]+'/works/'+aid if choices else 'artworks'
    def one(c):
        aid=c['artwork_id'];dest=RUN/'public-verification'/(aid+'.json')
        if dest.exists():return m.load(dest)
        url='https://artlines.org/api/backend/v1/'+routes[aid];result=dict(artwork_id=aid,url=url,at=m.now())
        for attempt in range(3):
            try:
                if routes[aid]=='artworks':
                    cursor=None;body=None;page_count=0
                    while body is None:
                        params=dict(q=c['title'].encode('utf-8')[:180].decode('utf-8',errors='ignore'),limit=60)
                        if cursor:params['cursor']=cursor
                        response=requests.get(url,params=params,timeout=(15,45));response.raise_for_status();page=response.json();page_count+=1
                        body=next((x for x in page['items'] if x['id']==aid),None)
                        if body:break
                        next_cursor=page.get('next_cursor');assert next_cursor and next_cursor!=cursor,'Artwork absent from public directory';assert page_count<100,'Public directory page bound reached';cursor=next_cursor
                    result.update(verification_surface='public_artwork_directory',metadata_verification='All descriptive fields separately verified in production database',pages=page_count)
                else:
                    response=requests.get(url,timeout=(15,45));response.raise_for_status();body=response.json()
                    for k,v in c['updates'].items():assert body.get(k)==v,(k,'Public metadata differs')
                    result['verification_surface']='public_artist_artwork_detail'
                assert body['title']==c['title'] and body['id']==aid
                if c['image']:assert body.get('media_url')==c['image']['storage_path']
                result.update(verified=True,http_status=response.status_code,media_url=body.get('media_url'));m.save(dest,result);return result
            except Exception as e:
                m.save(RUN/'public-artwork-verification-attempts'/(aid+'-'+str(attempt)+'.json'),dict(at=m.now(),error=repr(e),url=url));time.sleep(1+attempt)
        result.update(verified=False);return result
    out=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i,x in enumerate(pool.map(one,plan['claims']),1):
            out.append(x)
            if i%100==0:print('Public API readback',i,'/',len(plan['claims']),flush=True)
    report=dict(at=m.now(),plan_sha256=pin['sha256'],checked=len(out),verified=sum(x['verified'] for x in out),surfaces=dict(Counter(x.get('verification_surface','failed') for x in out)),museum_member_access_preserved=True,rows=out);m.save(RUN/'public-api-verification.json',report);print('Public API verified',report['verified'],'/',len(out),flush=True);assert report['verified']==len(out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','prepare-extra','sheets','finish-sheets','backup','plan','upload','apply','verify','public-verify']);a=p.parse_args()
    if a.command=='prepare-extra':prepare(True)
    else:globals()[a.command.replace('-','_')]()
