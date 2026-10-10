#!/usr/bin/env python3
"""Supplemental recovery of selected source display images; no plan rewriting."""
import argparse, importlib.util, io, json, textwrap
from pathlib import Path
from PIL import Image, ImageOps, ImageStat, ImageDraw, ImageFont
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-random-200-painters-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
r=d.r;s=d.s;m=d.m;RUN=d.RUN;BACKUP=d.BACKUP

def prepare():
    rows={row['artwork_id']:row for data,pin in d.plans() for row in data['rows'] if row.get('artwork_id')}
    recovered=[];failures=[]
    for path in sorted((RUN/'prepared-images').glob('*.json')):
        old=r.load(path)
        if old['outcome']!='preparation_held':continue
        aid=old['artwork_id'];dest=RUN/'recovered-images'/(aid+'.json')
        if dest.exists():
            x=r.load(dest)
            (recovered if x['outcome']=='prepared' else failures).append(x);continue
        row=rows[aid];page=row['page'];url=page['image_url']
        assert d.q.image_key(url)==d.q.image_key(old['source_image_url'])
        im={k:v for k,v in old.items() if k not in ['outcome','error']}
        im.update(source_image_url=url,original_image_url=old['source_image_url'],prior_failure_receipt=str(path.relative_to(ROOT)),prior_failure_sha256=r.sha(path.read_bytes()))
        try:
            original,rc=d.d.download(url);raw,width,height,quality=d.d.core.compress(original)
            assert 0<len(raw)<=100000 and min(width,height)>=50 and max(width,height)>=200,'Source image remains below resolution threshold'
            with Image.open(io.BytesIO(raw)) as image:image.verify()
            with Image.open(io.BytesIO(original)) as source:original_size=list(ImageOps.exif_transpose(source).size)
            assert abs(width/height-original_size[0]/original_size[1])<.025
            with Image.open(io.BytesIO(raw)) as image:
                stddev=ImageStat.Stat(image.convert('L')).stddev[0];assert stddev>1
            digest=r.sha(raw);target_path='/assets/artworks/imported/'+m.OP+'/'+aid+'-'+digest[:16]+'.jpg'
            target=ROOT/'apps/web/public'/target_path.lstrip('/');r.save(target,raw)
            im.update(outcome='prepared',path=target_path,visual_path=str(target),sha256=digest,
                      media_id=m.uid('image-media/'+aid+'/'+digest),bytes=len(raw),width=width,height=height,
                      original_dimensions=original_size,jpeg_quality=quality,download=rc,luminance_stddev=stddev)
            recovered.append(im)
        except Exception as exc:
            im.update(outcome='preparation_held',error=str(exc));failures.append(im)
        r.save(dest,im)
    # Explicitly review every supplemental image, not a statistical sample.
    sheet=Image.new('RGB',(1440,400),'white');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    for n,im in enumerate(recovered):
        with Image.open(im['visual_path']) as source:
            image=source.convert('RGB');image.thumbnail((230,290));sheet.paste(image,(n*240+(240-image.width)//2,(290-image.height)//2))
        for line,text in enumerate(textwrap.wrap(im['artist']+': '+im['title'],30)[:6]):draw.text((n*240+5,300+line*16),text,font=font,fill='black')
    path=m.ORIGINALS/'contact-sheets/supplemental.jpg'
    if not path.exists():sheet.save(path,quality=92)
    r.save(RUN/'supplemental-visual-batch.json',{'images':recovered,'failures':failures,'path':str(path),'sha256':r.sha(path.read_bytes())})
    print('Recovered',len(recovered),'images;',len(failures),'still held',flush=True)

def plan():
    dest=RUN/'supplemental-plan.json.gz'
    if dest.exists():return
    batch=r.load(RUN/'supplemental-visual-batch.json');review=r.load(RUN/'supplemental-visual-review.json')
    assert review['sheet_sha256']==batch['sha256']
    assert set(review['approved'])|set(review['held'])=={im['artwork_id'] for im in batch['images']}
    images=[im for im in batch['images'] if im['artwork_id'] in review['approved']]
    assert len({im['sha256'] for im in images})==len(images)
    existing_hashes={im['sha256'] for data,pin in d.pinned_deliveries() for im in data['images']}
    assert not existing_hashes & {im['sha256'] for im in images}
    selected={row['artwork_id']:row for data,pin in d.pinned_deliveries() for row in data['rows']}
    with r.connect('production') as db:
        before=s.snapshots(db,[im['artwork_id'] for im in images])
        for im in images:
            aid=im['artwork_id'];row=selected[aid];prior=before[aid]
            assert (RUN/'verified'/(im['artist_id']+'.json')).exists()
            assert prior['artwork']['status']=='review' and not prior['artwork']['primary_media_id']
            assert not prior['attachments'] and len(prior['creators'])==1 and prior['creators'][0]['artist_id']==im['artist_id']
            assert row['page']['date']['creation_year_end']<=1970 and not row.get('image_hold')
        data={'at':r.now(),'images':images,'preimages':before,'rows':[selected[im['artwork_id']] for im in images],
              'authorization_sha256':r.sha((RUN/'authorization.json').read_bytes()),'visual_review_sha256':r.sha((RUN/'supplemental-visual-review.json').read_bytes())}
        r.save_gz(dest,data);pin=r.sha(dest.read_bytes());r.save(RUN/'supplemental-pin.json',{'sha256':pin})
        r.save_gz(BACKUP/'supplemental-preimages.json.gz',{'plan_sha256':pin,'records':before})

def apply():
    done=RUN/'supplemental-applied.json'
    if done.exists():return
    path=RUN/'supplemental-plan.json.gz';data=r.load(path);pin=r.sha(path.read_bytes())
    assert pin==r.load(RUN/'supplemental-pin.json')['sha256']
    assert data['authorization_sha256']==r.sha((RUN/'authorization.json').read_bytes())
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    # Reuse immutable storage upload and public checksum verification only.
    original=d.pinned_deliveries;d.pinned_deliveries=lambda:iter([(data,pin)])
    try:d.upload()
    finally:d.pinned_deliveries=original
    images=data['images'];ids=[im['artwork_id'] for im in images];rows={row['artwork_id']:row for row in data['rows']}
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        before=s.snapshots(db,ids);assert before==data['preimages'],'Concurrent change to supplemental target'
        for im in images:
            aid=im['artwork_id'];row=rows[aid];page=row['page'];rc=r.load(RUN/'image-uploads'/(aid+'.json'))
            assert rc['plan_sha256']==pin and rc['public_bytes_verified'] and rc['sha256']==im['sha256']
            attribution=im['artist']+'. '+im['title']+'. WikiArt source label: '+im['source_rights_label']+'. Proportional resize and JPEG compression; no crop. Source: '+im['source_page_url']
            db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
              checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at)
              VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (im['media_id'],im['path'],im['source_page_url'],im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+im['artist'],
               im['rights_status'],im['source_rights_label']+' (WikiArt source label)',m.POLICY,im['artist']+'; reproduction via WikiArt',attribution,im['download']['at']))
            db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,
              rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (im['media_id'],m.uid('source/images'),im['source_id'],page['receipt']['sha256'],im['source_image_url'],m.POLICY,
               'Exact WikiArt source rights label retained under the explicitly requested image workflow; no independent licence inferred.',m.OP+'-supplemental-v1',page['receipt']['retrieved_at'],
               Jsonb({'image':im,'page':page,'authorization':r.load(RUN/'authorization.json'),'plan_sha256':pin,'visual_sampled':True,'identity_basis':row['identity_basis'],'confidence':row['confidence']})))
            db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Complete source reproduction')",(aid,im['media_id']))
            changed=db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],m.ACTOR,aid));assert changed.rowcount==1
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES(%s,'artwork',%s,%s,'random_200_image_recovery',%s,%s,%s,%s,%s)''',
              (m.uid('supplemental-image/'+aid),aid,m.uid('source/images'),im['source_id'],im['source_page_url'],json.dumps({'plan_sha256':pin,'prior_failure_receipt':im['prior_failure_receipt'],'source_image_url':im['source_image_url'],'scope':'Attach validated display-size reproduction actually supplied on the same WikiArt artwork page; preserve metadata, holdings and publication.'}),r.now(),m.ACTOR))
        after=s.snapshots(db,ids)
        for im in images:
            aid=im['artwork_id'];allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in after[aid]['artwork'].items() if k not in allowed}=={k:v for k,v in before[aid]['artwork'].items() if k not in allowed}
            assert after[aid]['creators']==before[aid]['creators'] and after[aid]['locations']==before[aid]['locations']
            assert after[aid]['artwork']['primary_media_id']==im['media_id']
    r.save_gz(BACKUP/'supplemental-after.json.gz',{'plan_sha256':pin,'records':after})
    r.save(done,{'at':r.now(),'plan_sha256':pin,'images_added':len(images),'artwork_ids':ids})
    print('Attached supplemental images',len(images),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','plan','apply']);args=parser.parse_args();globals()[args.phase]()
