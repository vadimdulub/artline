#!/usr/bin/env python3
"""Selected authentic museum images: source checks, visual review and guarded delivery."""
import argparse, base64, collections, concurrent.futures, hashlib, importlib.util, io, json, re, subprocess, time
from pathlib import Path
from urllib.parse import quote, urlparse, unquote
from PIL import Image, ImageOps, ImageDraw, ImageFont
import requests
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
RUN,ROOT,ORIGINALS,BACKUP=d.RUN,d.ROOT,d.ORIGINALS,d.BACKUP
save,load,sha,uid,now=d.save,d.load,d.sha,d.uid,d.now
POLICY='User-approved Greek museum/artist image workflow, 20 September 2026, continued by the explicit all-Greek-museums request on 8 October 2026. Selected works dated by 1955; authentic complete source frame; original source rights retained separately from user approval. No independent copyright-holder licence asserted.'
GOU_CANDIDATES='goulandris-image-candidates-v4.json'
CANDIDATES='greek-image-candidates-v3.json'
CONTACT='greek-contact-index-v2.json'
IMAGE_BATCH='greek'


def compress(raw):
    # Same complete-frame and byte-limit strategy as enrich-artwork-images.py.
    with Image.open(io.BytesIO(raw))as opened:
        assert opened.width*opened.height<=40_000_000
        im=ImageOps.exif_transpose(opened).convert('RGB')
        for edge in [1200,1000,843,700,600,500,400]:
            im.thumbnail((edge,edge),Image.Resampling.LANCZOS)
            for quality in [90,85,80,75,70,65,60,55]:
                out=io.BytesIO();im.save(out,'JPEG',quality=quality,optimize=True,progressive=True)
                if out.tell()<=100000:return out.getvalue(),im.width,im.height,quality
    raise ValueError('Cannot meet image byte limit')


def goulandris():
    spec=importlib.util.spec_from_file_location('goulandris',ROOT/'ops/museum-expansion-goulandris-20261006.py')
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    mu=next(x['institution']for x in load(RUN/'production-baseline.json')['institutions']if x['institution']['slug']=='basil-elise-goulandris-athens')
    existing=[x for x in load(RUN/'production-scoped-artworks.json.gz')if x['artwork']['current_institution_id']==mu['id']]
    selected=[];held=[]
    for item in existing:
        w=item['artwork']
        if w['primary_media_id']or not w['creation_year_end']or w['creation_year_end']>1955:continue
        urls=sorted({e['canonical_url']for e in item['identifiers']if parser.source_id(e['canonical_url'])})
        if len(urls)!=1:held.append(dict(id=w['id'],reason='exact_native_identifier_unavailable'));continue
        try:
            raw,rc=d.m.capture(urls[0],timeout=30);assert rc['status']==200
            parsed=parser.fields(raw);soup=d.g.BeautifulSoup(raw,'html.parser')
            title=parsed['translated_title']or parsed['title'];assert w['normalized_title']in{d.norm(title),d.norm(parsed['title'])},'Original/translated title conflict'
            physical=parser.PRINT_CREATION.get(parser.source_id(urls[0]))
            if physical:
                assert physical[0]in parsed['medium_notes'];years=parser.creation_date(physical[1])
            else:years=parser.creation_date(parsed['date'])
            assert years and years[:2]==(w['creation_year_start'],w['creation_year_end']),'Physical creation date conflict'
            images=[a for a in soup.select('a.artwork__display-image[href]')if not re.search(r'detail|verso|reverse|-BACK-',a['href'],re.I)]
            if w['id']in ['7d195eae-ac2f-5bdd-ae9f-83be61f92d01','af35131b-221a-4265-bbb6-91eee5a1779a']:
                # Reviewed native gallery: named title/creator file precedes
                # short, unlabelled detail files. Visual full-frame QA follows.
                assert len(images)>1 and '-'in images[0]['href'].rsplit('/',1)[1]
                images=images[:1]
            assert len(images)==1,'Ambiguous complete gallery image'
            image_url=images[0]['href'];assert '/works/images/'in image_url and '_carousel'not in image_url
            selected.append(dict(artwork_id=w['id'],title=w['title'],creator=parsed['creator'],source_url=urls[0],source_id=parser.source_id(urls[0]),receipt=rc,
                museum=mu,policy=POLICY,identity_confidence=0.99,holding_confidence=0.98,
                identity_basis='Exact existing native Goulandris object identifier; fresh original/translated title, physical print edition and creation date match; sole complete gallery image after explicitly labelled DETAIL/verso/reverse files excluded. Existing catalogue values preserved.',
                image_url=image_url,rights_label='Copyright © 2026 Basil & Elise Goulandris Foundation; '+('; '.join(parsed['rights'])or'No object-specific reuse licence stated'),
                rights_status='restricted',license_url=urls[0],creator_credit=parsed['creator']+'; Basil & Elise Goulandris Foundation',
                provider_name='Basil & Elise Goulandris Foundation',rights_evidence=parsed['rights'],source_metadata=parsed))
        except Exception as e:held.append(dict(id=w['id'],reason=type(e).__name__+': '+str(e)))
        if len(selected)%10==0:print('Goulandris',len(selected),'selected',len(held),'held',flush=True)
    save(RUN/GOU_CANDIDATES,dict(at=now(),records=selected,held=held))
    print('Goulandris complete',len(selected),'selected',len(held),'held',flush=True)


def candidates():
    p=load(RUN/d.PLAN);selected=[];held=[]
    supplement=RUN/'supplement-delivery-plan.json.gz'
    if supplement.exists():p['records']+=load(supplement)['records']
    for f in p['records']:
        if f['last'] is None or f['last']>1955:
            held.append(dict(artwork_id=f['artwork_id'],reason='creation_date_unknown_or_outside_existing_museum_image_approval'));continue
        if f['before'] and f['before']['artwork']['primary_media_id']:continue
        x=dict(artwork_id=f['artwork_id'],title=f['title'],creator=f['creator_label']or'Creator not recorded',
            source_url=f['source_url'],source_id=f['source_id'],receipt=f['receipt'],museum=f['museum'],policy=POLICY,
            holding_confidence=f['holding_confidence'],identity_confidence=0.99,
            identity_basis='Image explicitly attached to the exact provider object identifier; selected full primary view. Visual review required before attachment.')
        if f['source']=='acropolis':
            x.update(image_url=f['image_url'],rights_label='Acropolis Museum; image provision by request; no open reuse licence stated',rights_status='restricted',license_url=f['source_url'],
                creator_credit='Acropolis Museum',provider_name='Acropolis Museum',rights_evidence='Official object page includes Provision of image link.')
        elif f['source']=='searchculture':
            licenses=f['raw']['license_links'];label='; '.join(a['title']for a in licenses) or 'No reuse licence stated'
            status='cc_by_sa'if label=='CC BY-SA 4.0'else'cc_by'if label in ['CC BY 4.0','CC BY 3.0']else'cc0'if label=='CC0'else'restricted'
            x.update(image_url=f['raw']['thumbnail'],rights_label=label,rights_status=status,
                license_url=licenses[0]['url']if licenses else f['source_url'],creator_credit=f['museum']['name']+'; SearchCulture / National Documentation Centre',
                provider_name=f['museum']['name']+' via SearchCulture',native_url=f['native_url'],rights_evidence=f['raw'].get('fields',{}).get('Rights'))
        else:
            raw,rc=d.m.capture('https://nationalarchive.culture.gr/image-api/getImages/'+str(f['raw']['recordId']),timeout=30)
            images=json.loads(raw)
            media=[im for im in(f['raw']['media']or[])if im and im.get('master')]
            primary=[im for im in media if im.get('primaryForPublication')]
            if not primary:primary=media
            if not primary:held.append(dict(artwork_id=f['artwork_id'],reason='no_supplied_object_image'));continue
            # Some object pages designate several publishable views; retain the
            # first in native object order, subject to full-frame visual review.
            primary=primary[:1]
            def stem(filename):
                return re.sub(r'(?:\.(?:jpg|jpeg|png|tif|tiff))+$','',re.sub(r'_(?:thumb|high)\.jpg$','',unquote(filename).lower()))
            master=stem(primary[0]['master'])
            matches=[im for im in images.get('images',[])if stem(im['fullsize'].rsplit('/',1)[-1])==master]
            if len(matches)!=1:held.append(dict(artwork_id=f['artwork_id'],reason='primary_image_file_not_returned'));continue
            path=matches[0]['fullsize'];assert path.startswith('/deamImages/')
            x.update(image_url='https://nationalarchive-a5b9g0gbh9e0ducr.a01.azurefd.net/image-api'+path.replace('/deamImages/','/deamImagesRaw/'),
                image_endpoint_receipt=rc,rights_label=primary[0]['rightsValue']or'No reuse licence stated',rights_status='restricted',
                license_url=primary[0].get('rightsUri')or f['source_url'],creator_credit='Hellenic Ministry of Culture; '+f['museum']['name'],
                provider_name='Hellenic Ministry of Culture / National Archive of Monuments',rights_evidence=primary[0],
                identity_basis='Exact object image endpoint and matching native media filename stem. Documented _thumb/_high and extension-only filename variants reconciled within this object only. First designated view, or first native media view when no designation; full-frame visual review required.')
        selected.append(x)
    extra=RUN/GOU_CANDIDATES
    if extra.exists():selected+=load(extra)['records']
    save(RUN/CANDIDATES,dict(at=now(),records=selected,held=held))
    print('Image candidates',len(selected),'held',len(held),flush=True)


def prepare():
    allowed={f['artwork_id']for f in load(RUN/d.PLAN)['records']}
    if (RUN/'supplement-delivery-plan.json.gz').exists():allowed|={f['artwork_id']for f in load(RUN/'supplement-delivery-plan.json.gz')['records']}
    if (RUN/'native-delivery-plan-v2.json.gz').exists():allowed|={f['artwork_id']for f in load(RUN/'native-delivery-plan-v2.json.gz')['records']}
    if (RUN/GOU_CANDIDATES).exists():allowed|={x['artwork_id']for x in load(RUN/GOU_CANDIDATES)['records']}
    selected=[x for x in load(RUN/CANDIDATES)['records']if x['artwork_id']in allowed];ORIGINALS.mkdir(parents=True,exist_ok=True)
    blocked_hosts=set()
    def one(x):
        dest=RUN/'prepared/greek'/(x['artwork_id']+'.json')
        if dest.exists():return 'preserved'
        original=ORIGINALS/(sha(x['image_url'].encode())+'.body');receipt=RUN/'image-downloads'/(sha(x['image_url'].encode())+'.json')
        try:
            if receipt.exists():rc=load(receipt);raw=original.read_bytes();assert sha(raw)==rc['sha256']
            else:
                host=urlparse(x['image_url']).netloc
                with d.m.LOCKS[host]:
                    assert host not in blocked_hosts,'Source access restriction encountered; further host requests paused'
                    time.sleep(max(0,d.m.LAST.get(host,0)+1.1-time.monotonic()));d.m.LAST[host]=time.monotonic()
                    with requests.get(x['image_url'],headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum object)'},timeout=(15,45),stream=True)as resp:
                        if resp.status_code in [403,429]:blocked_hosts.add(host)
                        resp.raise_for_status();assert resp.headers.get('Content-Type','').startswith('image/')
                        raw=b''
                        for chunk in resp.iter_content(65536):raw+=chunk;assert len(raw)<=20_000_000
                        rc=dict(url=x['image_url'],final_url=resp.url,status=resp.status_code,sha256=sha(raw),bytes=len(raw),retrieved_at=now(),path=str(original))
                original.write_bytes(raw);save(receipt,rc)
            content,width,height,quality=compress(raw);assert min(width,height)>=80
            with Image.open(original)as original_im:
                original_size=ImageOps.exif_transpose(original_im).size
            assert abs(width/height-original_size[0]/original_size[1])<0.03
            digest=sha(content);path='/assets/artworks/imported/'+RUN.name+'/'+x['artwork_id']+'-'+digest[:16]+'.jpg'
            visual=ROOT/'apps/web/public'/path.lstrip('/');visual.parent.mkdir(parents=True,exist_ok=True)
            if visual.exists():assert visual.read_bytes()==content
            else:visual.write_bytes(content)
            im=dict(**x,media_id=uid('media/'+x['artwork_id']+'/'+digest),path=path,sha256=digest,bytes=len(content),width=width,height=height,
                quality=quality,download=rc,visual_path=str(visual),original_size=original_size)
            save(dest,im);return 'prepared'
        except Exception as e:
            save(RUN/'image-errors'/(x['artwork_id']+'-'+str(time.time_ns())+'.json'),dict(artwork_id=x['artwork_id'],image_url=x['image_url'],error=type(e).__name__+': '+str(e)))
            return 'held'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        counts=collections.Counter()
        for n,status in enumerate(pool.map(one,selected),1):
            counts[status]+=1
            if n%25==0:print('PREPARED',n,'/',len(selected),dict(counts),flush=True)
    print('PREPARED',dict(counts),flush=True)
    contact()


def contact():
    records=[load(p)for p in sorted((RUN/'prepared/greek').glob('*.json'))];index=[]
    folder=ORIGINALS/'contact-sheets/greek-v2';folder.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    for start in range(0,len(records),24):
        sheet=Image.new('RGB',(1600,1380),'#eee9df');draw=ImageDraw.Draw(sheet)
        for n,im in enumerate(records[start:start+24]):
            with Image.open(im['visual_path'])as src:thumb=ImageOps.contain(src.convert('RGB'),(258,266))
            left=n%6*266;top=n//6*345;sheet.paste(thumb,(left+(266-thumb.width)//2,top))
            draw.multiline_text((left+4,top+268),f"{start+n+1}. {im['title'][:32]}\n{im['museum']['name'][:32]}\n{im['width']} x {im['height']}",fill='black',font=font,spacing=3)
            index.append(dict(number=start+n+1,sheet=start//24+1,artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title'],museum=im['museum']['name']))
        sheet.save(folder/f'{start//24+1:03}.jpg',quality=90)
    save(RUN/CONTACT,index)
    print('Contact sheets',len(records),'images',str(folder),flush=True)


def plan():
    review=load(RUN/(IMAGE_BATCH+'-visual-review.json'));assert review['contact_index_sha256']==sha((RUN/CONTACT).read_bytes())
    selected=[]
    for aid in review['approved_artwork_ids']:
        im=load(RUN/review.get('prepared_overrides',{}).get(aid,'prepared/greek/'+aid+'.json'))
        im.update(review.get('metadata_overrides',{}).get(aid,{}))
        assert im['artwork_id']==aid
        selected.append(im)
    with d.connect()as db:
        rows=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',([im['artwork_id']for im in selected],)).fetchall()
        before={r['row']['id']:r['row']for r in rows}
        existing={r['checksum_sha256']:r['id']for r in db.execute('SELECT id::text,checksum_sha256 FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256']for im in selected],))}
    counts=collections.Counter(im['sha256']for im in selected);ready=[];held=[]
    for im in selected:
        w=before.get(im['artwork_id']);reason=None
        if not w:reason='artwork_not_delivered'
        elif w['primary_media_id']:reason='existing_image_preserved'
        elif w['status']!='review' or w['published_at']:reason='publication_state_preserved'
        elif counts[im['sha256']]>1 or im['sha256']in existing:reason='duplicate_pixels_need_reconciliation'
        if reason:held.append(dict(artwork_id=im['artwork_id'],reason=reason));continue
        assert sha(Path(im['visual_path']).read_bytes())==im['sha256'] and im['bytes']<=100000
        ready.append(dict(image=im,before=w))
    value=dict(at=now(),records=ready,held=held,visual_review=review)
    save(RUN/(IMAGE_BATCH+'-image-plan.json.gz'),value);save(BACKUP/(IMAGE_BATCH+'-image-preimages.json.gz'),value)
    print('Image plan',len(ready),'ready',len(held),'held',flush=True)


def upload():
    p=load(RUN/(IMAGE_BATCH+'-image-plan.json.gz'));bucket='artline-508319-images'
    token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip()
    def one(item):
        im=item['image'];data=Path(im['visual_path']).read_bytes();assert sha(data)==im['sha256'] and len(data)<=100000
        dest=RUN/'storage'/IMAGE_BATCH/(im['artwork_id']+'.json')
        if dest.exists():return load(dest)
        name=im['path'].lstrip('/');url='https://storage.googleapis.com/storage/v1/b/'+bucket+'/o/'+quote(name,safe='')
        with requests.Session()as session:
            session.headers['Authorization']='Bearer '+token
            for attempt in range(5):
                try:
                    r=session.get(url,timeout=(15,30));created=False
                    if r.status_code==404:
                        r=session.post('https://storage.googleapis.com/upload/storage/v1/b/'+bucket+'/o',params=dict(uploadType='media',name=name,ifGenerationMatch=0),data=data,headers={'Content-Type':'image/jpeg'},timeout=(15,45));created=True
                    if r.status_code in [408,412,429,500,502,503,504]and attempt<4:
                        time.sleep(2**attempt);continue
                    r.raise_for_status();obj=r.json()
                    assert int(obj['size'])==len(data)and obj['md5Hash']==base64.b64encode(hashlib.md5(data).digest()).decode()
                    check=dict(artwork_id=im['artwork_id'],path=im['path'],sha256=im['sha256'],generation=obj['generation'],created=created)
                    save(dest,check);return check
                except (requests.Timeout,requests.ConnectionError):
                    if attempt==4:raise
                    time.sleep(2**attempt)
    checks=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for check in pool.map(one,p['records']):
            checks.append(check)
            if len(checks)%25==0:print('Uploaded',len(checks),'/',len(p['records']),flush=True)
    save(RUN/(IMAGE_BATCH+'-storage.json'),dict(at=now(),checks=checks));print('UPLOADED',len(checks),'verified objects',flush=True)


def attach():
    p=load(RUN/(IMAGE_BATCH+'-image-plan.json.gz'));digest=sha((RUN/(IMAGE_BATCH+'-image-plan.json.gz')).read_bytes())
    storage=load(RUN/(IMAGE_BATCH+'-storage.json'));assert len(storage['checks'])==len(p['records']);after=[]
    with d.connect(readonly=False)as db:
        for start in range(0,len(p['records']),20):
            path=RUN/'image-applied'/IMAGE_BATCH/(str(start//20+1).zfill(3)+'.json')
            if path.exists():after+=load(path)['after'];continue
            current=[]
            with db.transaction():
                for item in p['records'][start:start+20]:
                    im=item['image'];aid=im['artwork_id'];w=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']
                    assert w==item['before'],'Artwork changed before image attachment: '+aid
                    row=dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_url'],provider_name=im['provider_name'],
                        mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+' — '+im['creator'],
                        rights_status=im['rights_status'],license_label=im['rights_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['creator_credit'],
                        retrieved_at=im['download']['retrieved_at'],verified_at=None,verified_by=None)
                    d.m.insert(db,'media_assets',row);d.m.audit_entry(db,'media_asset',im['media_id'],None,row,'insert')
                    d.m.insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=uid('source'),source_record_id=im['source_id'],source_checksum=im['receipt']['sha256'],
                        source_image_url=im['image_url'],policy_url=im['source_url'],rights_basis=im['policy'],adapter_version=RUN.name,checked_at=im['receipt']['retrieved_at'],evidence_json=Jsonb(im)))
                    link=dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label='Complete supplied primary image; source marks retained')
                    d.m.insert(db,'artwork_media',link);d.m.audit_entry(db,'artwork_media',aid,None,link,'insert')
                    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],d.ACTOR,aid))
                    d.m.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='verified_image_identity_20261008',source_id=uid('source'),source_record_id=im['source_id'],
                        source_url=im['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,identity=im['identity_basis'],confidence=im['identity_confidence'],visual_review=p['visual_review']),ensure_ascii=False),
                        retrieved_at=im['receipt']['retrieved_at'],created_by=d.ACTOR))
                    result=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
                    assert all(result[k]==w[k]for k in w if k not in {'primary_media_id','revision','updated_at','updated_by'})
                    d.m.audit_entry(db,'artwork',aid,w,result,'update');current.append(result)
            save(path,dict(at=now(),plan_sha256=digest,after=current));after+=current;print('Attached',len(after),'/',len(p['records']),flush=True)
    save(RUN/(IMAGE_BATCH+'-images-applied.json'),dict(at=now(),plan_sha256=digest,images=len(after),after=after))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['goulandris','candidates','prepare','contact','plan','upload','attach']);args=parser.parse_args()
    globals()[args.action]()
