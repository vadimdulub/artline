#!/usr/bin/env python3
"""Exact-object Russian icon image research; audit and selection precede downloads."""
import argparse, collections, concurrent.futures, hashlib, importlib.util, io, json, os, re, time, uuid
from pathlib import Path
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image, ImageOps, ImageDraw, ImageFont
from urllib.robotparser import RobotFileParser

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/russian-icon-images-20260921'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
DSN='postgres://localhost/artline'
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
NAMES={'russian-museum':'State Russian Museum','rublev-museum':'Andrei Rublev Museum','icon-museum':'The Icon Museum and Study Center'}
ACTOR='local-european-research'
spec=importlib.util.spec_from_file_location('base',ROOT/'ops/byzantine-russian-expansion.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
save=b.save
read=lambda p:json.loads(Path(p).read_text())
os.environ.setdefault('CLOUDSDK_CORE_ACCOUNT','vadim@alingva.com')
b.RUN=RUN
b.HOSTS.update({'commons.wikimedia.org','www.rublev-museum.ru','www.iconmuseum.org'})

def core():
    spec=importlib.util.spec_from_file_location('image_core',ROOT/'ops/enrich-artwork-images.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def cloud_audit():
    c=core();slugs=[w['slug'] for w in read(RUN/'baseline.json')['works']]
    with psycopg.connect(c.cloud_dsn(),options='-c default_transaction_read_only=on -c statement_timeout=30000',row_factory=dict_row) as db:
        found=[]
        for start in range(0,len(slugs),100):
            found+=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE slug=ANY(%s)',(slugs[start:start+100],)).fetchall()
    save(RUN/'cloud-baseline.json',{'at':b.now(),'records':[r['record'] for r in found],'queried_slugs':len(slugs)})
    save(BACKUP/'cloud-baseline.json',{'at':b.now(),'records':[r['record'] for r in found]})
    candidates=read(RUN/'museum-image-candidates.json')['records'];ids={r['record']['id'] for r in found}
    print('Production counterparts',len(found),'of',len(slugs),'museum image candidates present',sum(x['artwork_id'] in ids for x in candidates),flush=True)

def commons_search():
    cap=b.Capture();selected=read(RUN/'museum-selection.json')['records'];pages={}
    for start in range(0,len(selected),15):
        group=selected[start:start+15]
        query=' OR '.join('"'+w['accession']+'"' for w in group)
        url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':50,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5})
        try:
            raw,receipt=cap.get(url);d=json.loads(raw);assert 'error' not in d,d.get('error')
            batch=d.get('query',{}).get('pages',{});pages.update(batch)
            path=RUN/'commons-batches'/(str(start)+'.json')
            if not path.exists():save(path,{'query':query,'targets':[w['artwork_id'] for w in group],'pages':batch,'capture':receipt,'truncated':bool(d.get('continue'))})
            print('Commons accession research',min(start+15,len(selected)),'files',len(pages),flush=True)
        except Exception as e:
            save(RUN/'commons-search-hold.json',{'at':b.now(),'url':url,'reason':str(e)});break
    save(RUN/'commons-files.json',pages)

def policies():
    cap=b.Capture();out=[]
    for url in ['https://rusmuseumvrm.ru/terms/index.php?lang=en','https://www.rublev-museum.ru/collection/icons/','https://www.iconmuseum.org/collection/the-archangel-gabriel/']:
        try:
            raw,receipt=cap.get(url);soup=BeautifulSoup(raw,'html.parser')
            lines=[s for s in soup.stripped_strings if re.search('copyright|©|прав|reproduc|permission',s,re.I)]
            out.append({'url':url,'capture':receipt,'rights_text':lines})
        except Exception as e:out.append({'url':url,'error':str(e)})
    save(RUN/'museum-rights-research.json',out)
    print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)

def prepare():
    """User explicitly extended the collection policy on 21 September 2026."""
    selected=read(RUN/'museum-selection.json')['records']
    def provider_run(provider):
        cap=b.Capture();host={'russian-museum':'rusmuseumvrm.ru','rublev-museum':'www.rublev-museum.ru','icon-museum':'www.iconmuseum.org'}[provider]
        raw,receipt=cap.get('https://'+host+'/robots.txt',robot=True);policy=RobotFileParser();policy.parse(raw.decode(errors='replace').splitlines())
        stopped=None
        for w in [x for x in selected if x['provider']==provider]:
            destination=RUN/'prepared'/(w['artwork_id']+'.json')
            if destination.exists():continue
            url=w['image_urls'][0]
            try:
                if stopped:raise ValueError(stopped)
                assert policy.can_fetch(b.AGENT,url),'Robots disallows source image'
                path=ORIGINALS/'originals'/(w['artwork_id']+'.source');path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists():raw=path.read_bytes()
                else:
                    time.sleep(max(1.2,policy.crawl_delay(b.AGENT) or policy.crawl_delay('*') or 0))
                    response=cap.session.get(url,timeout=(15,60),allow_redirects=False,stream=True)
                    if response.status_code in (403,429,503):stopped='Source host paused after HTTP '+str(response.status_code)
                    assert response.status_code==200,'Source image HTTP '+str(response.status_code)
                    assert response.headers.get('Content-Type','').startswith('image/'),'Not an image response'
                    chunks=[];total=0
                    for part in response.iter_content(65536):
                        total+=len(part);assert total<=20_000_000,'Source image exceeds bound';chunks.append(part)
                    raw=b''.join(chunks);path.write_bytes(raw)
                with Image.open(io.BytesIO(raw)) as source:
                    source.load();im=ImageOps.exif_transpose(source).convert('RGB')
                original_dimensions=im.size;assert min(im.size)>=200,'Insufficient image dimensions'
                im.thumbnail((1280,1280));encoded=None
                while encoded is None:
                    for quality in [88,82,76,70,64,58,50,42]:
                        out=io.BytesIO();im.save(out,format='JPEG',quality=quality,optimize=True,progressive=True)
                        if len(out.getvalue())<=100000:encoded=out.getvalue();break
                    if encoded is None:im.thumbnail((int(im.width*.85),int(im.height*.85)))
                relative='/assets/artworks/imported/'+RUN.name+'/'+w['artwork_id']+'.jpg'
                asset=ROOT/'apps/web/public'/relative.lstrip('/');asset.parent.mkdir(parents=True,exist_ok=True)
                if asset.exists():assert asset.read_bytes()==encoded
                else:asset.write_bytes(encoded)
                media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/'+RUN.name+'/'+w['artwork_id']+'/'+b.sha(encoded)))
                entry={'work':w,'media_id':media_id,'path':relative,'bytes':len(encoded),'sha256':b.sha(encoded),'width':im.width,'height':im.height,'original_path':str(path),'original_bytes':len(raw),'original_sha256':b.sha(raw),'original_dimensions':original_dimensions,'source_image_url':url,'retrieved_at':b.now(),'rights_status':'restricted','license_label':'© '+NAMES[provider]+'; no independent reproduction permission established','license_url':'https://rusmuseumvrm.ru/terms/index.php?lang=en' if provider=='russian-museum' else w['source_url'],'creator_credit':NAMES[provider]+' (source reproduction; individual photographer not credited)','transformation':'Complete supplied frame; proportional resize, EXIF orientation and JPEG compression; no cropping','authorization':'User explicitly extended the Cyprus/Greek collection workflow to Russian museum sources on 21 September 2026; actual restrictions retained, no rights verification claimed.'}
                save(destination,entry)
                print('Prepared',provider,w['accession'],len(encoded),'bytes',flush=True)
            except Exception as e:
                held=RUN/'download-held'/(w['artwork_id']+'.json')
                if not held.exists():save(held,{'artwork_id':w['artwork_id'],'title':w['title'],'url':url,'reason':str(e),'at':b.now()})
                print('Held',provider,w['accession'],str(e),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for f in [pool.submit(provider_run,p) for p in NAMES]:f.result()

def contact():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    images.sort(key=lambda x:(x['work']['provider'],x['work']['date_end'],x['work']['source_object_id']))
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    sheets=[]
    for start in range(0,len(images),20):
        sheet=Image.new('RGB',(1200,1650),'#efefea');draw=ImageDraw.Draw(sheet)
        for index,entry in enumerate(images[start:start+20]):
            with Image.open(ROOT/'apps/web/public'/entry['path'].lstrip('/')) as source:
                im=source.copy();im.thumbnail((284,270));x=index%4*300;y=index//4*330
                sheet.paste(im,(x+(300-im.width)//2,y+(270-im.height)//2))
                w=entry['work'];draw.text((x+5,y+273),str(start+index+1)+'. '+w['accession'],font=font,fill='black')
                draw.text((x+5,y+294),w['title'][:33],font=font,fill='black')
                draw.text((x+5,y+312),w['date_display'][:37],font=font,fill='black')
        path=Path('/private/tmp')/(RUN.name+'-contact-'+str(start//20+1)+'.jpg');sheet.save(path)
        sheets.append(str(path))
    save(RUN/'contact-index.json',{'images':images,'sheets':sheets})
    duplicates=collections.defaultdict(list)
    for im in images:duplicates[im['original_sha256']].append(im['work']['artwork_id'])
    save(RUN/'exact-image-duplicates.json',[v for v in duplicates.values() if len(v)>1])
    print('Contact sheets',len(sheets),'images',len(images),flush=True)

def state(db, key):
    artwork=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(key,)).fetchone()['record']
    result={'artwork':artwork}
    for table,where in [('artwork_artists','artwork_id=%s'),('citations',"entity_type='artwork' AND entity_id=%s"),('external_identifiers',"entity_type='artwork' AND entity_id=%s"),('artwork_location_assertions','artwork_id=%s'),('curated_collection_items','artwork_id=%s')]:
        result[table]=db.execute('SELECT to_jsonb(t) record FROM '+table+' t WHERE '+where+' ORDER BY to_jsonb(t)::text',(key,)).fetchall()
    return result

def attach():
    review=read(RUN/'visual-review.json');approved=review['approved']
    for path in sorted((RUN/'prepared').glob('*.json')):
        im=read(path);w=im['work'];key=w['artwork_id']
        if key not in approved:continue
        assert approved[key]==im['sha256'];raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert b.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        receipt=RUN/'attached'/(key+'.json')
        if receipt.exists():continue
        with psycopg.connect(DSN,row_factory=dict_row) as db:
            db.execute("SET LOCAL lock_timeout='5s'")
            db.execute('SELECT pg_advisory_xact_lock(559220260915)')
            db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(key,))
            before=state(db,key);assert before['artwork']==w['before'],'Artwork changed since audit'
            assert before['artwork']['primary_media_id'] is None and before['artwork']['status']=='review' and before['artwork']['published_at'] is None
            backup=BACKUP/'preimages'/(key+'.json')
            if backup.exists():assert read(backup)==before
            else:save(backup,before)
            sid=db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,%s,'collection_page',%s) ON CONFLICT(slug) DO UPDATE SET slug=excluded.slug RETURNING id",(RUN.name+'-'+w['provider'],NAMES[w['provider']]+' selected icon image evidence',w['source_url'].split('/collection')[0])).fetchone()['id']
            credit=im['creator_credit']+'. '+im['license_label']+'. '+im['transformation']+'.'
            db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
              VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,'restricted',%s,%s,%s,%s,%s,NULL,NULL)''',
              (im['media_id'],im['path'],w['source_url'],NAMES[w['provider']],im['width'],im['height'],im['bytes'],im['sha256'],im.get('alt_text') or w['title']+' ('+w['accession']+')',im['license_label'],im['license_url'],im['creator_credit'],credit,im['retrieved_at']))
            db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
              VALUES(%s,%s,%s,%s,%s,%s,%s,'russian-icons-selected-v1',%s,%s)''',
              (im['media_id'],sid,w['source_object_id'],w['source_capture']['sha256'],im['source_image_url'],im['license_url'],im['authorization'],im['retrieved_at'],Jsonb(im)))
            db.execute('''INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES('artwork',%s,%s,'image_rights_and_identity',%s,%s,%s,%s,%s)''',
              (key,sid,w['source_object_id'],w['source_url'],json.dumps({'identity':w['identity_basis'],'media_id':im['media_id'],'image_url':im['source_image_url'],'source_capture':w['source_capture'],'authorization':im['authorization']},ensure_ascii=False),im['retrieved_at'],ACTOR))
            db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(im['media_id'],ACTOR,key))
            after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(key,)).fetchone()['record']
        save(receipt,{'at':b.now(),'artwork_id':key,'media_id':im['media_id'],'path':im['path'],'sha256':im['sha256'],'backup':str(backup),'backup_sha256':b.sha(backup.read_bytes()),'after':after,'local_only':True})
    print('Attached',len(list((RUN/'attached').glob('*.json'))),'review images',flush=True)

def verify():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json')) if p.stem in read(RUN/'visual-review.json')['approved']]
    results=[]
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on -c statement_timeout=30000',row_factory=dict_row) as db:
        for im in images:
            key=im['work']['artwork_id'];before=read(BACKUP/'preimages'/(key+'.json'));after=state(db,key)
            expected={**before['artwork'],'primary_media_id':im['media_id'],'revision':before['artwork']['revision']+1,'updated_at':after['artwork']['updated_at'],'updated_by':ACTOR}
            assert after['artwork']==expected,'Unexpected artwork metadata change'
            for k in ('artwork_artists','external_identifiers','artwork_location_assertions','curated_collection_items'):assert before[k]==after[k],(key,k)
            assert len(after['citations'])==len(before['citations'])+1
            m=db.execute('SELECT to_jsonb(m) record FROM media_assets m WHERE id=%s',(im['media_id'],)).fetchone()['record']
            assert m['rights_status']=='restricted' and m['verified_at'] is None and m['verified_by'] is None
            assert m['source_page_url']==im['work']['source_url'] and m['storage_path']==im['path'] and m['checksum_sha256'].strip()==im['sha256']
            evidence=db.execute('SELECT evidence_json FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchall()
            assert len(evidence)==1 and evidence[0]['evidence_json']==im
            raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert b.sha(raw)==im['sha256'] and len(raw)==m['byte_size']<=100000
            with Image.open(io.BytesIO(raw)) as check:assert check.size==(m['width'],m['height'])
            assert b.sha(Path(im['original_path']).read_bytes())==im['original_sha256']
            results.append({'artwork_id':key,'media_id':im['media_id'],'bytes':len(raw),'sha256':im['sha256'],'passed':True})
        counts=db.execute("SELECT count(*) total,count(primary_media_id) illustrated FROM artworks WHERE object_form='icon' AND status<>'archived'").fetchone()
    report={'at':b.now(),'passed':True,'records':results,'icon_counts':counts,'local_only':True,'maximum_bytes':max(i['bytes'] for i in images)}
    save(RUN/'verification.json',report);print({k:v for k,v in report.items() if k!='records'},flush=True)

def verify_http():
    import requests
    approved=read(RUN/'visual-review.json')['approved']
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json')) if p.stem in approved]
    def check(im):
        key=im['work']['artwork_id'];url='http://127.0.0.1:3000/api/backend/v1/atlas/artworks/'+key
        response=requests.get(url,timeout=30);assert response.status_code==200,(key,response.status_code)
        data=response.json()
        assert data['id']==key and data['media_url']==im['path'] and data['rights_status']=='restricted'
        assert data['source_page_url']==im['work']['source_url'] and data['license_label']==im['license_label']
        assert data['status']=='review' and data['object_form']=='icon' and data['display'] is None
        if im.get('alt_text'):assert data['alt_text']==im['alt_text']
        image_response=requests.get('http://127.0.0.1:3000'+im['path'],timeout=30)
        assert image_response.status_code==200 and b.sha(image_response.content)==im['sha256']
        return {'artwork_id':key,'api_status':response.status_code,'image_status':image_response.status_code,'image_sha256':im['sha256'],'rights_and_source_visible':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,images))
    save(RUN/'http-verification.json',{'at':b.now(),'passed':True,'base_url':'http://127.0.0.1:3000','records':results})
    print('Verified local application detail and image responses',len(results),flush=True)

def audit():
    if (RUN/'baseline.json').exists():return
    with psycopg.connect(DSN,options='-c default_transaction_read_only=on -c statement_timeout=60000',row_factory=dict_row) as db:
        works=db.execute("SELECT to_jsonb(a) record FROM artworks a WHERE object_form='icon' AND status<>'archived' ORDER BY id").fetchall()
        ids=[w['record']['id'] for w in works]
        identifiers=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
        creators=db.execute('SELECT * FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
        institutions=db.execute('SELECT id,slug,name FROM institutions WHERE id=ANY(%s::uuid[])',([w['record']['current_institution_id'] for w in works if w['record']['current_institution_id']],)).fetchall()
    result={'at':b.now(),'works':[w['record'] for w in works],'identifiers':identifiers,'creators':creators,'institutions':institutions}
    save(RUN/'baseline.json',result);save(BACKUP/'baseline.json',result)
    print('All icon records',len(works),'missing images',sum(not w['record']['primary_media_id'] for w in works),flush=True)

def discover():
    baseline=read(RUN/'baseline.json'); current={w['id']:w for w in baseline['works']}
    out=[];held=[]
    for campaign in ['byzantine-russian-icons-frescoes-20260920','byzantine-russian-more-20260920']:
        pin=read(ROOT/'docs/research'/campaign/'latest-selection.json')
        for w in read(ROOT/pin['path'])['records']:
            a=current.get(w['id'])
            if not a or a['primary_media_id'] or w['provider'] not in ('russian-museum','rublev-museum','icon-museum','vam'):continue
            if w['provider']=='icon-museum' and w['source_fields']['fields'].get('Country of Origin')!='Russia':continue
            raw=(ROOT/w['source_capture']['path']).read_bytes();assert b.sha(raw)==w['source_capture']['sha256']
            soup=BeautifulSoup(raw,'html.parser'); candidates=[]
            if w['provider']=='russian-museum':
                if re.search('Визант|Грец|Крит|Греч',w['date_display'],re.I):continue
                candidates=[urljoin(w['source_url'],i['src']) for i in soup.select('.work__card--left img.rsImg[src]')]
            elif w['provider']=='rublev-museum':
                if re.search('Визант|Грец|Крит|Греч',w['date_display'],re.I):continue
                card=soup.select_one('.permanent-exhibition-floors-item[data-id="'+w['source_object_id']+'"]')
                assert card and card.select_one('.NUMBER').get_text(' ',strip=True)==w['accession_number']
                candidates=[urljoin(w['source_url'],i['src']) for i in card.select('.permanent-exhibition-floors-item-img img[src]')]
            elif w['provider']=='icon-museum':
                candidates=[urljoin(w['source_url'],i['src']) for i in soup.select('article img.wp-post-image[src]')]
            else:
                held.append({'artwork_id':w['id'],'provider':w['provider'],'title':w['title'],'reason':'V&A origin and image rights require separate object-level review'});continue
            candidates=list(dict.fromkeys(candidates))
            reason=None
            if not a['creation_year_start'] or not a['creation_year_end'] or a['creation_year_end']>1955:reason='Creation date unresolved or outside established image cutoff'
            elif len(candidates)!=1:reason='Missing or multiple primary image candidates; component review required'
            elif re.search('двусторон|двухсторон|оборот|оборотн|double.sided|reverse|verso',w['title'],re.I):reason='Double-sided or reverse-specific object requires view matching'
            item={'artwork_id':w['id'],'provider':w['provider'],'title':w['title'],'accession':w['accession_number'],'source_url':w['source_url'],'source_object_id':w['source_object_id'],'image_urls':candidates,'date_display':a['date_display'],'date_start':a['creation_year_start'],'date_end':a['creation_year_end'],'source_capture':w['source_capture'],'source_fields':w['source_fields'],'before':a,'identity_basis':'Exact museum accession and native object/card identifier from the source used to create this existing catalogue record; shared Rublev pages are matched by data-id and accession, never page URL alone.'}
            if reason:held.append({**item,'reason':reason})
            else:out.append(item)
    # Research all metadata; download only a bounded selection of early collection highlights.
    selected=[]
    for provider,limit in [('russian-museum',100),('rublev-museum',80),('icon-museum',40)]:
        group=sorted([x for x in out if x['provider']==provider],key=lambda x:(x['date_end'],x['date_start'],x['source_object_id']))
        selected+=group[:limit]
    save(RUN/'museum-image-candidates.json',{'at':b.now(),'records':out,'held':held,'selection_rule':'Earliest securely dated exact museum objects: at most 100 Russian Museum, 80 Rublev Museum and 40 Icon Museum records. Museum connection is documented; this selection is an owner/editorial choice, not a museum masterpiece designation.'})
    save(RUN/'museum-selection.json',{'at':b.now(),'records':selected,'requires_policy_extension':True})
    print('Exact eligible candidates',len(out),dict(collections.Counter(x['provider'] for x in out)),'held',len(held),'bounded selection',len(selected),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['audit','discover','cloud_audit','commons_search','policies','prepare','contact','attach','verify','verify_http']);args=p.parse_args();globals()[args.stage]()
