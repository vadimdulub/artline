#!/usr/bin/env python3
"""Selected France reproduction evidence. Image bytes are handled by Go only."""
import argparse
import importlib.util
import json
import re
import uuid
import hashlib
import base64
from urllib.parse import urlsplit, urlunsplit
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('france_image_common',ROOT/'ops/overnight-commons-images.py')
common=importlib.util.module_from_spec(s);s.loader.exec_module(common)
core=common.core
RUN=ROOT/'docs/research/france-catalogue-20260916/images-pilot001'
SPECS=[
 {'artwork_id':'3ea10ab4-2bb2-4105-88e4-a4d3c57c74ca','ref':'07200000523','file':'MuMA - Monet - Fécamp, bord de mer.jpg','artist':'Claude Monet','year':1881,'museum':'MuMa, Le Havre','website_url':'https://www.muma-lehavre.fr','accession':'994.01'},
 {'artwork_id':'14fdf454-8279-4ad0-bffd-dca3ccde2eef','ref':'07120002591','file':"Dieppe (Seine-Maritime) - Château-musée - \"Vue de l'avant-port de Dieppe, 1902\" (Camille Pissarro, 1830-1903) (35650153133).jpg",'artist':'Camille Pissarro','year':1902,'museum':'Musée de Dieppe','website_url':'https://www.dieppe.fr','accession':'902.18.1'},
 {'artwork_id':'bde58d01-8a1e-5a9b-9ad8-9175ff377b99','ref':'000PE000014','file':"75 - Musée d'Orsay - Madame de Loynes 1862 - Amaury-Duval - Joconde000PE000014.jpg",'artist':'Amaury-Duval','year':1862,'museum':"Musée d'Orsay",'website_url':'https://www.musee-orsay.fr','accession':'RF 2168'},
]


def capture():
    f=core.Fetcher(RUN/'metadata')
    response=common.api(f,'commons.wikimedia.org',{'action':'query','titles':'|'.join('File:'+x['file'] for x in SPECS),
        'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
    out=[]
    for spec in SPECS:
        try:
            page=common.page_for_filename(response,spec['file'])
            rendered=common.rendered_rights_uri(f,page)
            core.save_new(RUN/'evidence'/(spec['ref']+'.json'),{'at':core.now(),'spec':spec,'page':page,'rendered_licence':rendered})
            info=page['imageinfo'][0];m=info['extmetadata'];field=lambda k:m.get(k,{}).get('value','')
            out.append({'ref':spec['ref'],'title':page['title'],'revision':page['revisions'][0]['revid'],
                'license':field('LicenseShortName'),'license_url':field('LicenseUrl') or (rendered or {}).get('uri'),
                'artist':common.plain(field('Artist')),'credit':common.plain(field('Credit')),'restrictions':field('Restrictions'),
                'object_name':common.plain(field('ObjectName')),'image_description':common.plain(field('ImageDescription')),
                'url':info.get('thumburl'),'width':info.get('thumbwidth'),'height':info.get('thumbheight')})
        except (ValueError,KeyError) as error:
            out.append({'ref':spec['ref'],'held':str(error)})
    core.save_new(RUN/'capture-summary.json',out)
    print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)


def plan():
    output=[]
    for spec in SPECS[:2]:
        path=RUN/'evidence'/(spec['ref']+'.json');evidence=json.loads(path.read_text());page=evidence['page'];info=page['imageinfo'][0]
        meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','');wikitext=page['revisions'][0]['slots']['main']['*']
        assert not field('Restrictions') and not re.search(r'\{\{\s*(?:copyvio|no permission|delete|disputed|Not-PD-US)',wikitext,re.I)
        if spec['ref']=='07200000523':
            assert 'Q18918107' in wikitext and '|date               = 1881' in wikitext and '{{Creator:Claude Monet}}' in wikitext
            assert field('LicenseShortName')=='Public domain' and field('Copyrighted')=='False'
            assert '{{PD-Art|PD-old-auto-expired|deathyear=1926}}' in wikitext
            common.origin.verify(spec,page)
            status='public_domain';uri=common.PDM;label='Public Domain Mark 1.0';credit='Photograph by Pymouss; painting by Claude Monet'
            basis='Manually reviewed MuMa Monet Fécamp identity: title, artist, 1881 date, museum-specific filename, Commons object Q18918107; official Joconde 07200000523, inventory 994.01. Supplied catalogue review record has the same exact title, date, artist lifespan and museum label. No inferred acceptance/publication.'
        else:
            assert '{{cc-by-sa-2.0}}' in wikitext and 'FlickreviewR|status=passed' in wikitext and 'reviewlicense=cc-by-sa-2.0' in wikitext
            assert "Vue de l'avant-port de Dieppe, 1902" in wikitext and 'Camille Pissarro, 1830-1903' in wikitext
            assert field('LicenseShortName')=='CC BY-SA 2.0'
            status='cc_by_sa';uri='https://creativecommons.org/licenses/by-sa/2.0/';label='CC BY-SA 2.0';credit='Patrick Monchicourt / Morio60 (Flickr); painting by Camille Pissarro'
            basis='Manually reviewed Dieppe Pissarro object identity: exact work title, 1902 creation, creator, museum and photograph description; current immutable catalogue research link joconde:07120002591. Photographer Flickr CC BY-SA 2.0 licence verified by Commons FlickreviewR. Underlying 1902 painting by artist deceased 1903; no modern underlying-work claim.'
        uri_from_file=common.canonical_licence_uri(field('LicenseUrl')) or (evidence.get('rendered_licence') or {}).get('uri')
        assert uri_from_file==uri
        # Remove provider-supplied analytics parameters only; the original media path is unchanged.
        u=urlsplit(info['url']);assert u.hostname=='upload.wikimedia.org' and u.scheme=='https'
        image=dict(spec,external_id=spec['ref'],provider='france-commons',source_image_url=urlunsplit((u.scheme,u.netloc,u.path,'','')),
            page=info['descriptionurl'],raw=evidence,policy_url=uri,rights_status=status,license_label=label,creator_credit=credit,
            checked_at=evidence['at'],source_evidence_sha256=core.sha(path.read_bytes()),identity_basis=basis)
        image['commons_original_sha1']=info['sha1']
        image['targets']={}
        for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
            with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
                record_id={'07200000523':'f394f7cb83732706d3fad28c5fd530e29778026410415e4ac07e746b5a24dce2','07120002591':'e894d0d942a1ecad7c0da678de5593649615e77145f4058306ef872117b303fa'}[spec['ref']]
                matches=db.execute('''SELECT a.id::text,a.slug,a.title,a.status,a.research_candidate,a.creation_year_start,a.creation_year_end,
                  a.primary_media_id::text,to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
                  (SELECT jsonb_agg(to_jsonb(l)) FROM research_artwork_links l WHERE l.artwork_id=a.id) links,
                  (SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) citations
                  FROM artworks a WHERE a.id=%s OR a.id IN (SELECT artwork_id FROM research_artwork_links WHERE source_key='supplied-registry' AND record_kind='catalogue_object' AND research_record_id=%s)''',(spec['artwork_id'],record_id)).fetchall()
                assert len(matches)==1, (target,spec['ref'],'ambiguous/missing immutable research identity',len(matches))
                r=matches[0]
                assert r['status']=='review' and r['research_candidate'] and r['primary_media_id'] is None, (target,spec['ref'],r['status'],r['primary_media_id'])
                assert r['creation_year_start']==r['creation_year_end']==spec['year']
                assert spec['file'].lower().find(spec['artist'].split()[-1].lower())>=0
                image['title']=r['title'];image['slug']=r['slug']
                if spec['ref']=='07120002591':assert any(l['object_key']=='joconde:'+spec['ref'] for l in r['links'])
                else:assert any(l['research_record_id']=='f394f7cb83732706d3fad28c5fd530e29778026410415e4ac07e746b5a24dce2' for l in r['links'])
                image['targets'][target]={'id':r['id'],'metadata_sha256':core.sha(core.encode(r['metadata'])),'source_id':r['citations'][0]['source_id']}
                core.save_new(RUN/(target+'-before-'+spec['ref']+'.json'),r)
        image['attribution_text']=f"{spec['artist']}. {image['title']}. Image credit: {credit}. {image['page']}. {label} ({uri}). Full-frame resize and JPEG compression; applicable ShareAlike terms retained. Catalogue remains in review."
        output.append(image)
    core.save_new(RUN/'go-selection.json',output)
    print('Reviewed image selection SHA256:',core.sha((RUN/'go-selection.json').read_bytes()),flush=True)


def upload():
    review=json.loads((RUN/'visual-review.json').read_text())
    assert review['approved'] and len(review['images'])<=2
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    results=[]
    for reviewed in review['images']:
        receipt=RUN/'go-prepared'/(reviewed['artwork_id']+'.json')
        image=json.loads(receipt.read_text());path=ROOT/'apps/web/public'/image['path'].lstrip('/');data=path.read_bytes()
        assert core.sha(data)==image['sha256']==reviewed['sha256'] and len(data)==image['bytes']<=100000
        with Image.open(path) as im:im.load();assert im.size==(image['width'],image['height'])
        image['media_id']=str(uuid.uuid5(uuid.NAMESPACE_URL,image['path']))
        blob=bucket.blob(image['path'].lstrip('/'));blob.metadata={'sha256':image['sha256'],'artwork-id':image['artwork_id'],'provider':'france-commons','source-record-id':image['ref'],'license':image['license_label']};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=45)
        except core.PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(data) and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
        result={'at':core.now(),'ref':image['ref'],'artwork_id':image['artwork_id'],'path':image['path'],'sha256':image['sha256'],'bytes':image['bytes'],'generation':blob.generation,'targets':{}}
        for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
            with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    row=db.execute("SELECT primary_media_id::text,to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata FROM artworks a WHERE id=%s FOR UPDATE",(image['targets'][target]['id'],)).fetchone()
                    assert row and core.sha(core.encode(row['metadata']))==image['targets'][target]['metadata_sha256'],'Catalogue metadata changed; image upload retained but attachment held'
                    assert row['primary_media_id'] in (None,image['media_id']),'Existing image preserved'
                    if row['primary_media_id'] is None:
                        db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                          VALUES(%s,'local',%s,%s,'Wikimedia Commons — selected France reproductions','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                          (image['media_id'],image['path'],image['page'],image['width'],image['height'],image['bytes'],image['sha256'],image['title']+' — '+image['artist'],image['rights_status'],image['license_label'],image['policy_url'],image['creator_credit'],image['attribution_text'],image['downloaded_at'],image['checked_at'],core.ACTOR))
                        db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,'france-selected-go-images-v1',%s,%s)''',
                          (image['media_id'],image['targets'][target]['source_id'],image['ref'],image['source_evidence_sha256'],image['source_image_url'],image['policy_url'],image['identity_basis'],image['checked_at'],Jsonb(image)))
                        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(image['media_id'],core.ACTOR,image['targets'][target]['id']))
                    after=db.execute('SELECT status,research_candidate,primary_media_id::text FROM artworks WHERE id=%s',(image['targets'][target]['id'],)).fetchone()
                    assert after['status']=='review' and after['research_candidate'] and after['primary_media_id']==image['media_id']
                result['targets'][target]='attached_and_database_verified'
        # Verify actual remote bytes, not just successful upload response metadata.
        remote=blob.download_as_bytes(timeout=45);assert core.sha(remote)==image['sha256']
        result['remote_bytes_verified']=True
        core.save_new(RUN/'uploaded'/(image['ref']+'.json'),result);results.append(result);print(json.dumps(result),flush=True)
    core.save_new(RUN/'upload-summary.json',results)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['capture','plan','upload']);a=p.parse_args()
    {'capture':capture,'plan':plan,'upload':upload}[a.phase]()
