#!/usr/bin/env python3
"""Evidence-pinned images for already linked historical exhibition image gaps.

No database writes in discovery. Only the frozen missing-image object IDs are
requested, at two requests per second. An access denial stops the source.
Selection and preparation require per-object CC0 evidence and visual review.
Explicit upload/apply commands deliver bounded, pinned production batches;
verify checks their media, source relationships and preserved catalogue fields.
The real local database is never written.
"""
from pathlib import Path
import concurrent.futures
import json
import sys
import threading
import time
import requests
import exhibitions_common as c
import base64
import hashlib
import importlib.util
import io
import re
from urllib.parse import unquote,urlsplit
from PIL import Image,ImageOps,ImageStat,ImageDraw,ImageFont
from psycopg.types.json import Jsonb
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/cleveland-image-gaps'
HOST='https://openaccess-api.clevelandart.org/api/artworks/'
lock=threading.Lock()
stop=threading.Event()
next_request=0.0
OP='historical-exhibitions-cma-images-20261012'
ACTOR='local-european-research'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
IID='729385eb-92b0-4cc8-9229-1ac3a46aee1f'
SID=c.uid('source/'+OP)


def batchdir(batch):
    return OUT/'batches'/f'{int(batch):03d}'


def validate_object(a,o,native):
    assert str(o['id'])==native,'Native object mismatch'
    assert a['accession_number']==o['accession_number'],'Accession mismatch'
    assert c.norm(a['title'])==c.norm(o['title']),'Title mismatch'
    assert {'Painting':'painting','Drawing':'drawing','Print':'print'}.get(o['type'])==a['work_type'],'Medium mismatch'
    assert a['current_institution_id']==IID,'Current institution differs'
    assert o['share_license_status']=='CC0' and not o.get('copyright') and not o.get('rights_and_reproductions'),'No explicit unconflicted CC0 image'
    assert isinstance(o.get('creation_date_latest'),int) and o['creation_date_latest']<=1970,'Source creation date outside selected scope or unknown'
    assert isinstance(a['creation_year_end'],int) and a['creation_year_end']<=1970,'Existing creation interval outside scope'
    assert o.get('legal_status')=='accessioned' and o.get('on_loan') is False,'Source ownership differs'
    assert o.get('record_type')in ('object','cover','component','part'),'Unknown object structure'
    url=o.get('url')or''
    assert urlsplit(url).hostname in ('clevelandart.org','www.clevelandart.org')
    assert unquote(urlsplit(url).path).rstrip('/')=='/art/'+a['accession_number']
    im=(o.get('images')or{}).get('web')or{}
    assert im.get('url'),'No source primary image'
    # Prefer a manageable print-size primary image for unusually long scrolls.
    # No alternate views, guessed URLs, or huge full TIFF downloads.
    if min(int(im.get('width') or 0),int(im.get('height') or 0))<150:
        larger=(o.get('images')or{}).get('print')or{}
        if larger.get('url') and int(larger.get('filesize') or 99999999)<=12000000:im=larger
    u=urlsplit(im['url']);filename=im.get('filename')
    assert u.scheme=='https' and u.hostname=='openaccess-cdn.clevelandart.org'
    assert filename in (a['accession_number']+'_web.jpg',a['accession_number']+'_print.jpg')
    assert unquote(u.path)=='/'+a['accession_number']+'/'+filename,'Native primary-image resource mismatch'
    return im


def select(batch):
    dest=batchdir(batch);pins=c.load(OUT/'catalogue-pins.json')
    artwork={r['id']:r for r in pins['artworks']};byartist={r['id']:r['display_name']for r in pins['artists']}
    prior=set()
    for f in (OUT/'batches').glob('*/selection.json'):
        prior.update(r['id']for r in c.load(f)['records'])
    rows=c.load(OUT/'missing-images-scoped.json')['rows'];records=[];held=[];pending=0
    for row in rows:
        if row['id']in prior:continue
        if row['work_type']not in ('painting','drawing','print','icon')or not isinstance(row['creation_year_end'],int)or row['creation_year_end']>1970:
            held.append(dict(id=row['id'],nativeID=row['source_artwork_id'],reason='Outside the frozen metadata-discovery medium/date selection'))
            continue
        f=OUT/'metadata'/f"{row['source_artwork_id']}.json"
        if not f.exists():pending+=1;continue
        a=artwork[row['id']];o=c.load(f)['data']
        try:
            im=validate_object(a,o,row['source_artwork_id'])
            if len(records)>=100:continue
            rc=c.load(f.with_suffix('.json.receipt.json'));assert c.sha(f.read_bytes())==rc['sha256']
            native=[x for x in pins['identifiers']if x['entity_id']==row['id'] and 'cleveland' in x['scheme'] and x['external_id']==row['source_artwork_id']]
            assert native,'No matching native identifier remains'
            links=[x for x in pins['artistLinks']if x['artwork_id']==row['id']]
            records.append(dict(id=row['id'],nativeID=row['source_artwork_id'],title=a['title'],type=a['work_type'],
                creators='; '.join(byartist.get(x['artist_id'],'')for x in links)or'Unknown artist',
                sourceCreators=o.get('creators'),sourceDate=o.get('creation_date'),sourceDateStart=o.get('creation_date_earliest'),sourceDateEnd=o.get('creation_date_latest'),
                events=row['events'],object=o,metadataReceipt=rc,image=im,before=a,artistLinks=links,identifiers=native,
                objectStructure=o['record_type'],parentAccession=o.get('cover_accession_number'),visualReviewRequired=True))
        except (AssertionError,ValueError,KeyError,TypeError)as error:
            held.append(dict(id=row['id'],nativeID=row['source_artwork_id'],reason=str(error)))
    assert records
    records.sort(key=lambda r:(r['parentAccession']or r['object']['accession_number'],r['objectStructure']!='cover',r['object']['accession_number']))
    c.save(dest/'selection.json',dict(at=c.now(),batch=int(batch),records=records,metadataHolds=held,pendingMetadata=pending,
        note='A bounded delivery batch of existing native-ID-matched works. All multipart and anonymous objects require visual review; no catalogue facts or statuses will change.',
        pinsSHA256=c.sha((OUT/'catalogue-pins.json').read_bytes())))
    print('Selected',len(records),'image candidates; metadata pending',pending,flush=True)


def prepare_one(row,dest):
    native=row['nativeID'];result=dest/'prepared'/f'{native}.json'
    if result.exists():return c.load(result)
    im=row['image'];source=dest/'originals'/f'{native}.jpg';rcpath=source.with_suffix('.receipt.json')
    out=dict(id=row['id'],nativeID=native,title=row['title'])
    try:
        assert not (OUT/'image-access-hold.json').exists(),'Image host access held'
        if source.exists():
            raw=source.read_bytes();rc=c.load(rcpath);assert c.sha(raw)==rc['sha256']
        else:
            slot()
            with requests.get(im['url'],headers={'User-Agent':c.UA},stream=True,allow_redirects=False,timeout=(15,45))as response:
                if response.status_code in (401,403,429):
                    stop.set()
                    with lock:
                        if not (OUT/'image-access-hold.json').exists():c.save(OUT/'image-access-hold.json',dict(at=c.now(),url=im['url'],status=response.status_code))
                response.raise_for_status();assert response.status_code==200
                assert response.headers.get('Content-Type','').startswith('image/')
                raw=bytearray()
                for chunk in response.iter_content(65536):
                    raw.extend(chunk);assert len(raw)<=12000000,'Source size exceeds selected derivative limit'
                raw=bytes(raw)
            rc=dict(url=im['url'],status=200,retrievedAt=c.now(),bytes=len(raw),sha256=c.sha(raw))
            source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw);c.save(rcpath,rc)
        with Image.open(io.BytesIO(raw))as opened:
            assert opened.width*opened.height<=16000000
            opened.load();image=ImageOps.exif_transpose(opened).convert('RGB')
        original=image.size
        declared=(int(im['width']),int(im['height']))
        if original!=declared:
            # A frozen, per-file editorial exception may resolve stale API
            # dimensions. It never changes the source metadata or native URL.
            review=row.get('dimensionReview')or{}
            assert review.get('decision')=='accept'and review.get('sourceSHA256')==rc['sha256'],'Image dimensions disagree with native metadata'
            assert review.get('observedDimensions')==list(original)and review.get('declaredDimensions')==list(declared)
            assert review.get('originalVisuallyReviewed')is True
            assert abs(original[0]/original[1]-declared[0]/declared[1])<.015
        encoded=None
        # Long horizontal/vertical scrolls retain a larger long edge and the
        # whole composition. The byte ceiling remains the same.
        edges=[3400,2800,2200,1800,1400,1100]if max(original)/min(original)>5 else [1200,1050,900,800,700,600]
        for edge in edges:
            resized=image.copy();resized.thumbnail((edge,edge),Image.Resampling.LANCZOS)
            for quality in [90,85,80,75,70,65,60,55]:
                buf=io.BytesIO();resized.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                if buf.tell()<=100000:encoded=buf.getvalue();break
            if encoded:break
        assert encoded and min(resized.size)>=40 and max(resized.size)>=200
        assert abs(resized.width/resized.height-original[0]/original[1])<max(.03,2/resized.height)
        digest=c.sha(encoded);path=dest/'derivatives'/f'{native}.jpg';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded)
        gray=resized.convert('L');flags=[]
        if row['objectStructure']!='object':flags.append('multipart_'+row['objectStructure'])
        if max(original)/min(original)>5:flags.append('long_scroll')
        if gray.entropy()<3 or ImageStat.Stat(gray).stddev[0]<8:flags.append('low_information')
        out.update(state='prepared',path=str(path),originalPath=str(source),sourceReceipt=rc,sourceSHA256=rc['sha256'],
            sha256=digest,width=resized.width,height=resized.height,bytes=len(encoded),quality=quality,originalDimensions=original,flags=flags,
            mediaID=c.uid(OP+'/media/'+row['id']+'/'+digest),imagePath='/assets/artworks/'+OP+'/'+row['id']+'-'+digest[:16]+'.jpg')
    except Exception as error:out.update(state='held',reason=type(error).__name__+': '+str(error))
    c.save(result,out);return out


def prepare(batch):
    dest=batchdir(batch);selection=c.load(dest/'selection.json');rows=selection['records']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        results=list(pool.map(lambda r:prepare_one(r,dest),rows))
    c.save(dest/'prepared.json',dict(at=c.now(),rows=results,selectionSHA256=c.sha((dest/'selection.json').read_bytes())))
    # Every prepared image is included in the review sheets, with exact native
    # inventory and parent labels. These sheets are review aids, not app assets.
    ready=[r for r in results if r['state']=='prepared'];byid={r['id']:r for r in rows}
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for start in range(0,len(ready),12):
        sheet=Image.new('RGB',(1600,1140),'#eee9e1');draw=ImageDraw.Draw(sheet)
        for n,r in enumerate(ready[start:start+12]):
            row=byid[r['id']];x=(n%4)*400;y=(n//4)*380
            image=Image.open(r['path']);image.thumbnail((390,290));sheet.paste(image,(x+(400-image.width)//2,y+(290-image.height)//2))
            lines=[f"{start+n+1}. {r['nativeID']} | {row['object']['accession_number']}",row['title'][:49],row['creators'][:48],row['objectStructure']+'; parent '+str(row['parentAccession']or'—')]
            for j,line in enumerate(lines):draw.text((x+5,y+298+j*19),line,font=font,fill='#151515')
        sheet.save(dest/f'review-sheet-{start//12+1:02d}.jpg',quality=90)
    print('Prepared',len(ready),'images; all included in',(len(ready)+11)//12,'review sheets',flush=True)


def accepted(batch):
    dest=batchdir(batch);selection=c.load(dest/'selection.json');prepared=c.load(dest/'prepared.json');review=c.load(dest/'visual-review.json')
    assert review['selectionSHA256']==c.sha((dest/'selection.json').read_bytes())
    byid={r['id']:r for r in selection['records']};decisions={r['nativeID']:r for r in review['decisions']}
    ready=[r for r in prepared['rows']if r['state']=='prepared']
    assert {r['nativeID']for r in ready}==set(decisions),'Every prepared image requires a visual decision'
    chosen=[r for r in ready if decisions[r['nativeID']]['decision']=='accept']
    assert len({r['sha256']for r in chosen})==len(chosen),'Duplicate derivative images need object identity reconciliation'
    return dest,byid,chosen,decisions


def upload(batch):
    dest,_,chosen,_=accepted(batch)
    spec=importlib.util.spec_from_file_location('historical_cma_image_core',Path(__file__).with_name('enrich-artwork-images.py'))
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    credentials=core.GcloudCredentials();credentials.refresh(None)
    bucket=storage.Client(project='artline-508319',credentials=credentials).bucket('artline-508319-images')
    def one(r):
        receipt=dest/'uploaded'/f"{r['nativeID']}.json"
        if receipt.exists():return c.load(receipt)
        raw=Path(r['path']).read_bytes();assert c.sha(raw)==r['sha256']and len(raw)<=100000
        blob=bucket.blob(r['imagePath'].lstrip('/'));blob.metadata={'sha256':r['sha256'],'operation':OP,'artwork-id':r['id'],'native-id':r['nativeID']};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
        except PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+r['imagePath'],timeout=(15,45));response.raise_for_status();assert c.sha(response.content)==r['sha256']
        rc=dict(at=c.now(),id=r['id'],nativeID=r['nativeID'],sha256=r['sha256'],bytes=len(raw),generation=blob.generation,publicBytesVerified=True)
        c.save(receipt,rc);return rc
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:receipts=list(pool.map(one,chosen))
    c.save(dest/'uploaded.json',dict(at=c.now(),images=len(receipts),visualReviewSHA256=c.sha((dest/'visual-review.json').read_bytes()),receipts=receipts))
    print('Uploaded and public-hash verified',len(receipts),'images',flush=True)


def apply(batch):
    dest,byid,chosen,decisions=accepted(batch);reviewsha=c.sha((dest/'visual-review.json').read_bytes())
    uploaded=c.load(dest/'uploaded.json')
    assert uploaded['visualReviewSHA256']==reviewsha
    receipts={r['id']:r for r in uploaded['receipts']}
    assert set(receipts)=={r['id']for r in chosen}
    assert all(receipts[r['id']]['sha256']==r['sha256']and receipts[r['id']]['publicBytesVerified']for r in chosen)
    ids=[r['id']for r in chosen];assert 0<len(ids)<=100
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        current=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall()
        for a in current:assert json.loads(json.dumps(a,default=str))==byid[str(a['id'])]['before'],'Artwork changed since selection'
        assert len(current)==len(ids)
        conflicts=db.execute('SELECT id,checksum_sha256 FROM media_assets WHERE checksum_sha256=ANY(%s)',([r['sha256']for r in chosen],)).fetchall()
        assert not conflicts,'Existing identical media needs separate identity review'
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url)VALUES(%s,%s,'Cleveland Museum of Art — historical exhibition image evidence','museum_api',%s,%s) ON CONFLICT(id)DO NOTHING",(SID,OP,HOST,CC0))
        for im in chosen:
            r=byid[im['id']];o=r['object'];validate_object(r['before'],o,r['nativeID'])
            for native in r['identifiers']:
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork'AND entity_id=%s AND scheme=%s AND external_id=%s",(im['id'],native['scheme'],native['external_id'])).fetchone()
            links=db.execute('SELECT artwork_id,artist_id,attribution_role,attribution_note FROM artwork_artists WHERE artwork_id=%s ORDER BY artwork_id,artist_id',(im['id'],)).fetchall()
            assert json.loads(json.dumps(links,default=str))==r['artistLinks'],'Creator links changed'
            credit=(o.get('tombstone')or(o.get('title')+'; The Cleveland Museum of Art'))
            db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'The Cleveland Museum of Art','image/jpeg',%s,%s,%s,%s,%s,'public_domain','CC0',%s,%s,%s,%s,now(),%s)",
                (im['mediaID'],im['imagePath'],o['url'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creators'],CC0,credit,credit+' Full source frame preserved; proportional resizing and JPEG compression.',im['sourceReceipt']['retrievedAt'],ACTOR))
            db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)",
                (im['mediaID'],SID,r['nativeID'],r['metadataReceipt']['sha256'],r['image']['url'],CC0,'The exact object API designates its primary image CC0; no conflicting copyright or reproduction-rights label. Native object, inventory, title and medium match the existing catalogue.',OP,Jsonb(dict(metadataReceipt=r['metadataReceipt'],sourceObject=o,download=im['sourceReceipt'],sourceObjectStructure=r['objectStructure'],parentAccession=r['parentAccession'],dimensionReview=r.get('dimensionReview'),visualReview=decisions[r['nativeID']],visualReviewSHA256=reviewsha,sourceDatesPreservedWithoutCatalogueMutation=[r['sourceDate'],r['sourceDateStart'],r['sourceDateEnd']],scope='Existing historical exhibition connections; no new ownership/current-display claim or publication change.'))))
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,%s)',(im['id'],im['mediaID'],decisions[r['nativeID']].get('viewLabel','Full artwork reproduction')))
            db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['mediaID'],im['id']))
        affected=db.execute("SELECT count(*) connections,count(distinct x.exhibition_id)events FROM exhibition_entries x JOIN exhibitions e ON e.id=x.exhibition_id WHERE x.artwork_id=ANY(%s::uuid[])AND e.status<>'archived'AND e.start_year BETWEEN 1600 AND 1989 AND e.end_year<=1989",(ids,)).fetchone()
    c.save(dest/'delivered.json',dict(at=c.now(),batch=int(batch),newImages=len(chosen),newArtworks=0,newExhibitions=0,newConnections=0,existingConnectionsIllustrated=affected,ids=ids,visualReviewSHA256=reviewsha,realLocalDatabaseWrites=False))
    print('Committed',len(chosen),'primary images;',affected,flush=True)


def verify(batch):
    dest,byid,chosen,_=accepted(batch);ids=[r['id']for r in chosen];expected={r['id']:r for r in chosen}
    with c.connect()as db:
        rows=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall();assert len(rows)==len(ids)
        for r in rows:
            a=json.loads(json.dumps(r,default=str));aid=a['id'];before=byid[aid]['before']
            assert a['primary_media_id']==expected[aid]['mediaID']
            for key in before:
                if key not in ('primary_media_id','updated_at','revision'):assert a[key]==before[key],(aid,key)
        assets=db.execute('SELECT a.id,a.primary_media_id,m.checksum_sha256,m.byte_size,m.width,m.height,m.storage_path,m.license_label FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN artwork_media am ON am.artwork_id=a.id AND am.media_id=m.id JOIN media_rights_evidence re ON re.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall();assert len(assets)==len(ids)
        for a in assets:
            im=expected[str(a['id'])];assert a['checksum_sha256']==im['sha256']and a['byte_size']==im['bytes']<=100000 and a['license_label']=='CC0'
            assert (a['width'],a['height'],a['storage_path'])==(im['width'],im['height'],im['imagePath'])
        links=db.execute('SELECT artwork_id,artist_id,attribution_role,attribution_note FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])ORDER BY artwork_id,artist_id',(ids,)).fetchall()
        links=json.loads(json.dumps(links,default=str))
        wanted=sorted([link for aid in ids for link in byid[aid]['artistLinks']],key=lambda r:(r['artwork_id'],r['artist_id']))
        assert links==wanted,'Creator attribution links differ'
    c.save(dest/'verified.json',dict(at=c.now(),images=len(chosen),allPrimaryAndJunctionAndRightsRelations=True,allChecksumsAndBytesMatch=True,allCatalogueMetadataAndStatusesPreserved=True,allCreatorAttributionLinksPreserved=True,realLocalDatabaseWrites=False))
    print('Verified',len(chosen),'images; all catalogue fields and statuses preserved',flush=True)


def slot():
    global next_request
    with lock:
        delay=max(0,next_request-time.monotonic())
        next_request=max(next_request,time.monotonic())+.5
    if delay:stop.wait(delay)
    if stop.is_set():raise RuntimeError('Source stopped after denial')


def metadata(row):
    native=row['source_artwork_id'];path=OUT/'metadata'/f'{native}.json'
    receipt=path.with_suffix('.json.receipt.json')
    if path.exists():
        rc=c.load(receipt);raw=path.read_bytes()
        assert rc['status']==200 and c.sha(raw)==rc['sha256']
        obj=json.loads(raw)['data'];assert str(obj['id'])==native
        return native,True
    for attempt in range(3):
        slot()
        try:r=requests.get(HOST+native,headers={'User-Agent':c.UA},timeout=(15,35))
        except (requests.Timeout,requests.ConnectionError):
            if attempt==2:raise
            stop.wait(2+attempt);continue
        if r.status_code in (401,403,429):
            stop.set()
            with lock:
                if not (OUT/'metadata-access-hold.json').exists():
                    c.save(OUT/'metadata-access-hold.json',dict(at=c.now(),url=r.url,status=r.status_code,sha256=c.sha(r.content)))
            raise RuntimeError(f'Source access held: HTTP {r.status_code}')
        if r.status_code>=500 and attempt<2:stop.wait(2+attempt);continue
        r.raise_for_status();obj=r.json()['data'];assert str(obj['id'])==native
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.content)
        c.save(receipt,dict(url=HOST+native,finalURL=r.url,status=200,retrievedAt=c.now(),sha256=c.sha(r.content),path=str(path)))
        return native,False


def discover():
    assert not (OUT/'metadata-access-hold.json').exists(),'Metadata source is held'
    rows=c.load(OUT/'missing-images-scoped.json')['rows']
    selected=[r for r in rows if r['work_type']in ('painting','drawing','print','icon')
              and isinstance(r['creation_year_end'],int) and r['creation_year_end']<=1970]
    assert len({r['source_artwork_id']for r in selected})==len(selected)
    results=[];failed=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        pending={pool.submit(metadata,r):r for r in selected}
        for future in concurrent.futures.as_completed(pending):
            row=pending[future]
            try:results.append(future.result())
            except Exception as error:failed.append(dict(nativeID=row['source_artwork_id'],reason=str(error)))
            if (len(results)+len(failed))%50==0:print('Metadata reviewed',len(results),'failed',len(failed),'of',len(selected),flush=True)
            if stop.is_set():
                for f in pending:f.cancel()
                break
    c.save(OUT/'metadata-discovery-result.json',dict(at=c.now(),scopedMissing=len(rows),selected=len(selected),completed=len(results),failed=failed,sourceHeld=stop.is_set(),databaseWrites=False))
    print('Metadata discovery finished',len(results),'of',len(selected),'failed',len(failed),flush=True)


if __name__=='__main__':
    if sys.argv[1:]==['discover']:discover()
    elif len(sys.argv)==3 and sys.argv[1]in ('select','prepare','upload','apply','verify'):
        globals()[sys.argv[1]](sys.argv[2])
    else:raise SystemExit('Use discover or select/prepare/upload/apply/verify BATCH')
