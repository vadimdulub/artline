#!/usr/bin/env python3
"""Independent approved WikiArt matches for selected historical Chicago gaps."""
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit,unquote

from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibition_chicago_aic_20261012 as links
import historical_exhibition_chicago_images_20261012 as images

OUT=links.OUT/'wikiart-images'
OP='historical-exhibition-chicago-wikiart-20261012'
SID=c.uid('source/'+OP)
POLICY='https://www.wikiart.org/en/terms-of-use'
LEADS={
    '109780':'https://www.wikiart.org/en/george-bellows/love-of-winter-1914',
    '87479':'https://www.wikiart.org/en/el-greco/assumption-of-the-virgin-1577',
    '72801':'https://www.wikiart.org/en/john-henry-twachtman/icebound',
    '28067':'https://www.wikiart.org/en/pablo-picasso/the-old-blind-guitarist-1903',
    '15401':'https://www.wikiart.org/en/william-james-glackens/chez-mouquin-1905'}
images.OUT=OUT;images.OP=OP;images.helper.OP=OP;images.helper.batchdir=lambda _:OUT


def select():
    spec=importlib.util.spec_from_file_location('wikiart_fields',Path(__file__).with_name('cesi-top100-20261010.py'))
    w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);w.capture=c.capture
    by={r['nativeID']:r for r in c.load(links.OUT/'aic-delivery-plan.json')['records']};rows=[]
    for nid,url in LEADS.items():
        r=by[nid];assert not r['before']['primary_media_id'];page=w.wiki_fields(url)
        assert 'Art Institute of Chicago' in page['fields'].get('Location','')
        assert page['date']and page['date']['last']<=1933
        display=urlsplit(page['image_url']);original=urlsplit(page['metadata']['image'])
        assert all(re.fullmatch(r'uploads\d*\.wikiart\.org',u.hostname or'')for u in [display,original])
        assert unquote(display.path).split('!')[0]==unquote(original.path).split('!')[0]
        # These five title/profile pairs were individually reviewed against the
        # exact museum IDs, current dimensions and explicit museum labels.
        notes={
            '109780':'Bellows, Love of Winter, 1914; exact distinctive title/date and explicit Chicago holding. Different Cleveland 1917 print excluded.',
            '87479':'El Greco, Assumption, 1577; explicit Chicago holding and monumental altarpiece dimensions. AIC dates 1577–79; WikiArt dates 1577 and labels support panel whereas museum says canvas. Preserve both sources without rewriting unknown catalogue date or medium.',
            '72801':'Twachtman Icebound; explicit Chicago holding and approximately 64 x 76 cm. Distinct Metcalf painting of the same title excluded.',
            '28067':'Picasso Old Blind Guitarist, 1903; explicit Chicago holding, vertical composition and approximately 121 x 82 cm. Museum dates 1903–04 and panel support; WikiArt canvas wording retained separately.',
            '15401':'Glackens At Mouquin’s / Chez Mouquin, 1905; exact title/date and explicit Chicago holding. Source dimensions and complete cafe composition checked.'}
        rows.append(dict(**r,title=r['object']['title'],creators=page['creator'],imageURL=page['metadata']['image'],wikiart=page,
            identityConfidence=.99,identityBasis=notes[nid],rightsBasis=page['rights_basis']))
    with c.connect()as db:
        reuse=db.execute('SELECT m.*,re.evidence_json FROM media_assets m LEFT JOIN media_rights_evidence re ON re.media_id=m.id WHERE m.source_page_url=ANY(%s)',(list(LEADS.values()),)).fetchall()
    p=dict(at=c.now(),records=rows,sourcePins=links.evidence_pins(),existingSourceMedia=links.normal(reuse),
        authorization='User-approved WikiArt source policy, 6 October 2026, reaffirmed by instruction to add WikiArt images. Actual source labels retained separately from approval.',
        museumImageAccessHeld=True,independentProvider=True,realLocalDatabaseWrites=False)
    c.save(OUT/'selection.json',p);c.save(links.BACKUP/'wikiart-image-preimage.json.gz',p)
    print('Selected',len(rows),'independent WikiArt matches; existing media references',len(reuse),flush=True)
    for r in rows:print(r['nativeID'],r['wikiart']['title'],r['wikiart']['rights_label'],r['imageURL'],flush=True)


def prepare():images.prepare()
def upload():images.upload()


def apply():
    _,by,chosen,decisions=images.helper.accepted(1);selection=c.load(OUT/'selection.json');uploaded=c.load(OUT/'uploaded.json');reviewsha=c.sha((OUT/'visual-review.json').read_bytes())
    assert uploaded['visualReviewSHA256']==reviewsha and len(uploaded['receipts'])==len(chosen)
    assert selection==c.load(links.BACKUP/'wikiart-image-preimage.json.gz')
    ids=[r['id']for r in chosen]
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(links.ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        current=links.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall())
        assert len(current)==len(ids)and all(r==by[r['id']]['before']for r in current)
        assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([r['sha256']for r in chosen],)).fetchall(),'Existing image needs explicit reuse reconciliation'
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url)VALUES(%s,%s,'WikiArt — selected historical Chicago exhibition images','collection_page','https://www.wikiart.org',%s)",(SID,OP,POLICY))
        for im in chosen:
            r=by[im['id']];page=r['wikiart'];credit=page['creator']+'. '+page['title']+'. WikiArt. '+page['rights_label']
            assert db.execute('SELECT 1 FROM exhibition_entries WHERE id=%s AND artwork_id=%s',(r['entryID'],r['id'])).fetchone()
            db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'WikiArt','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)",
                (im['mediaID'],im['imagePath'],page['source_url'],im['width'],im['height'],im['bytes'],im['sha256'],r['title']+' — '+r['creators'],page['rights_status'],page['rights_label'],POLICY,page['creator'],credit+' Source frame preserved; proportional resizing and JPEG compression.',im['sourceReceipt']['retrievedAt'],links.ACTOR))
            db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)',
                (im['mediaID'],SID,str(page['source_id']),page['receipt']['sha256'],r['imageURL'],POLICY,r['rightsBasis'],OP,Jsonb(dict(page=page,nativeMuseumObject=r['object'],identityBasis=r['identityBasis'],identityConfidence=r['identityConfidence'],download=im['sourceReceipt'],visualReview=decisions[r['nativeID']],visualReviewSHA256=reviewsha,userApproval=selection['authorization'],catalogueMetadataPreserved=True))))
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,%s)',(im['id'],im['mediaID'],decisions[r['nativeID']].get('viewLabel','Full artwork reproduction')))
            db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['mediaID'],im['id']))
    c.save(OUT/'delivered.json',dict(at=c.now(),newImages=len(chosen),newArtworks=0,newEvents=0,visualReviewSHA256=reviewsha,realLocalDatabaseWrites=False))
    print('Attached',len(chosen),'independently matched WikiArt images.',flush=True)


def verify():
    _,by,chosen,_=images.helper.accepted(1);expected={r['id']:r for r in chosen}
    with c.connect()as db:
        rows=links.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall())
        assert len(rows)==len(expected)
        for r in rows:
            assert r['primary_media_id']==expected[r['id']]['mediaID']
            assert all(r[k]==v for k,v in by[r['id']]['before'].items()if k not in ['primary_media_id','updated_at','revision'])
        records=db.execute('SELECT m.*,am.artwork_id FROM media_assets m JOIN artwork_media am ON am.media_id=m.id JOIN media_rights_evidence re ON re.media_id=m.id WHERE m.id=ANY(%s::uuid[])',([r['mediaID']for r in chosen],)).fetchall();assert len(records)==len(chosen)
        for m in records:
            im=expected[str(m['artwork_id'])];assert m['checksum_sha256']==im['sha256']and m['byte_size']==im['bytes']<=100000
            assert m['license_label']==by[str(m['artwork_id'])]['wikiart']['rights_label']
    c.save(OUT/'verified.json',dict(at=c.now(),images=len(chosen),allPrimaryJunctionAndRightsRelationsVerified=True,allCatalogueMetadataPreserved=True,realLocalDatabaseWrites=False))
    print('Verified',len(chosen),'WikiArt images and unchanged artwork metadata.',flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['select','prepare','upload','apply','verify']:raise SystemExit('Use select, prepare, upload, apply or verify')
    globals()[sys.argv[1]]()
