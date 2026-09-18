#!/usr/bin/env python3
"""Read-only audit of actual local attachments, source evidence and image files."""
import argparse,base64,collections,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
MODULES={'met':'overnight-image-campaign.py','chicago':'overnight-image-campaign.py','cleveland':'overnight-image-campaign.py','smk':'overnight-image-campaign.py','night-fng':'overnight-fng-images.py','night-rijks':'overnight-rijks-images.py','night-saam':'overnight-saam-images.py','night-fsg':'overnight-fsg-images.py','night-mia':'overnight-mia-images.py','night-smk':'overnight-smk-selected-images.py','night-cleveland':'overnight-cleveland-selected-images.py','night-met-commons':'overnight-met-commons-images.py','night-commons':'overnight-commons-images.py','night-joconde':'overnight-joconde-images.py','night-nga-commons':'overnight-nga-commons.py','night-walters':'overnight-walters-images.py'}
MODULES['followup-nga']='followup-nga-direct-images.py'
MODULES['followup-nationalmuseum']='followup-nationalmuseum-images.py'
MODULES['followup-nationalmuseum-commons']='followup-nationalmuseum-commons.py'
MODULES['austria-wien']='austrian-collection-images.py'
MODULES['austria-commons']='austrian-collection-images.py'
MODULES['popular-commons-depicts']='popular-commons-depicts.py'
MODULES['popular-staedel']='popular-staedel-images.py'
MODULES['popular-native-photo']='popular-native-photo-images.py'
MODULES['popular-reims']='popular-reims-images.py'
MODULES['popular-reims-donation']='popular-reims-donations.py'
def allowed(uri):
    # Preserve the actual ported licence; it is not interchangeable with 2.0 generic.
    return uri in ('https://creativecommons.org/licenses/by/2.0/fr/', 'https://creativecommons.org/licenses/by-sa/2.0/fr/') or bool(re.fullmatch(r'https://creativecommons.org/(?:publicdomain/(?:mark|zero)/1\.0|licenses/(?:by|by-sa)/(?:1\.0|2\.0|2\.5|3\.0|4\.0))/',uri or ''))
def completed_ids(run):
    done=set()
    for path in run.glob('**/events.jsonl'):
        for line in path.read_text().splitlines():
            try:row=json.loads(line)
            except ValueError:continue
            if row.get('outcome')=='complete' and row.get('local')=='attached' and row.get('cloud')=='attached':done.add(row['artwork_id'])
    path=run/'withdrawn-images.json'
    if path.exists():done-={row['artwork_id'] for row in json.loads(path.read_text())['records'] if row['status']=='withdrawn'}
    return done
def verify_blob(blob,expected):
    assert blob.size==expected['bytes'],'Storage byte size differs'
    assert blob.md5_hash==expected['md5'],'Storage MD5 differs'
    assert blob.content_type=='image/jpeg','Storage content type differs'
    assert blob.metadata and blob.metadata.get('sha256')==expected['sha256'],'Storage SHA256 metadata differs'
    assert blob.metadata.get('artwork-id')==expected['local_artwork_id'],'Storage artwork identity differs'
    assert blob.metadata.get('source-record-id')==expected['external_id'],'Storage source record differs'
    assert blob.metadata.get('license')==expected['license_label'],'Storage licence metadata differs'
def validate_source(module,im):
    module.core.validate_source_image_identity(im)
    p=im['provider'];raw=im['raw']
    if p in ('followup-nga','followup-nationalmuseum','followup-nationalmuseum-commons','austria-wien','austria-commons','popular-commons-depicts','popular-staedel','popular-native-photo','popular-reims','popular-reims-donation'):module.verify(im)
    elif p in ('met','chicago','cleveland','smk'):module.fresh_scope(p,raw,im)
    elif p=='night-fng':module.source_match(im,raw['object'])
    elif p=='night-rijks':
        module.source_match(im,raw['object']);assert module.core.rijks_edm(raw['edm']['edm_document'],im['external_id'],im['accession_number'])
        module.verify_image(im)
    elif p in ('night-saam','night-fsg'):module.source_match(im,raw['object'])
    elif p in ('night-mia','night-smk','night-cleveland'):
        url,_=module.source_match(im,raw['object']);assert url==im['source_image_url']
    elif p=='night-met-commons':module.verify(im)
    elif p in ('night-commons','night-joconde'):
        common=module if p=='night-commons' else module.common
        common.entity_match(im,raw['wikidata'],require_primary_image=False);common.rights_and_identity(im,raw['wikidata'],raw['commons'],raw['structured_data'],im.get('rendered_licence_evidence'))
        if raw.get('independent_photo_discovery',{}).get('independent_photographers_only'):
            spec=importlib.util.spec_from_file_location('photo_audit',ROOT/'ops/research-popular-painting-photos.py')
            photo=importlib.util.module_from_spec(spec);spec.loader.exec_module(photo)
            photo.verify_original_photograph(im,raw['commons'])
        if p=='night-joconde':assert im['external_id'] in common.values(raw['wikidata'],'P347')
    elif p=='night-nga-commons':module.object_match(im,raw['nga_object']);module.verify_file(im,raw['commons_file'])
    elif p=='night-walters':module.source_match(im,raw['walters_object']);module.verify_file(im,raw['commons_file'],im.get('rendered_licence_evidence'))
    else:raise ValueError('Unreviewed image provider')

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],default='local');p.add_argument('--verify-gcs',action='store_true');a=p.parse_args();started=time.time();journal={};modules={};expected={};errors=[];counts=collections.Counter();types=collections.Counter();licenses=collections.Counter();museum=collections.Counter();country=collections.Counter();popular=0;checksums=collections.defaultdict(list)
    for line in (a.run/'local-attachments.jsonl').read_text().splitlines():
        try:x=json.loads(line)
        except ValueError:continue
        if x['outcome'] in ('attached','already_attached'):journal[x['artwork_id']]=x
        elif x['outcome']=='withdrawn':journal.pop(x['artwork_id'],None)
    if a.target=='cloud':
        done=completed_ids(a.run);journal={aid:j for aid,j in journal.items() if aid in done}
    for n,(aid,j) in enumerate(journal.items(),1):
        try:
            path=Path(j['receipt']);path=path if path.is_absolute() else ROOT/path;im=json.loads(path.read_text());provider=im['provider'];name=MODULES[provider]
            if name not in modules:
                s=importlib.util.spec_from_file_location('audit_'+provider.replace('-','_'),ROOT/'ops'/name);module=importlib.util.module_from_spec(s);s.loader.exec_module(module);modules[name]=module
            module=modules[name];core=module.core
            assert im['artwork_id']==aid and im['media_id']==j['media_id'],'Receipt identity differs'
            assert allowed(im['policy_url']) and im.get('creator_credit') and im.get('attribution_text'),'Missing required rights or credit'
            assert urlparse(im['source_image_url']).scheme=='https' and urlparse(im['source_image_url']).hostname in core.HOSTS,'Unapproved image host'
            assert im.get('source_record_url') and im.get('rights_verified_at'),'Required provenance fields missing'
            validate_source(module,im)
            local_path=(ROOT/'apps/web/public'/im['path'].lstrip('/')).resolve();assert local_path.is_relative_to(ROOT/'apps/web/public/assets/artworks'),'Image storage path outside expected assets'
            image_bytes=local_path.read_bytes();assert len(image_bytes)==im['bytes']<=100000 and core.sha(image_bytes)==im['sha256'],'Image file size/hash differs'
            assert im['transform']=='Full-frame proportional resize and JPEG compression; no crop or generated content','Unexpected image transformation'
            expected[aid]={k:im[k] for k in ('media_id','path','sha256','bytes','policy_url','page','source_image_url','license_label','rights_status','creator_credit','attribution_text','title','creation_year_start','creation_year_end','work_type','provider')}
            expected[aid]['source_checksum']=core.sha(core.encode(im['raw']));checksums[im['sha256']].append(aid);counts[provider]+=1;licenses[im['policy_url']]+=1;types[im['work_type']]+=1
            expected[aid].update(local_artwork_id=aid,scheme=im['scheme'],external_id=im['external_id'],md5=base64.b64encode(hashlib.md5(image_bytes).digest()).decode())
        except Exception as e:errors.append({'artwork_id':aid,'phase':'source_or_file','error':str(e)[:300]})
        if n%1000==0:print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'audited source/files',n,'of',len(journal),'errors',len(errors),flush=True)
    ids=list(expected);db_checked=0
    dsn='postgres://localhost/artline' if a.target=='local' else core.cloud_dsn()
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=True,options='-c default_transaction_read_only=on') as db:
        if a.target=='cloud':
            mapped={}
            for start in range(0,len(ids),500):
                group=ids[start:start+500]
                requests=[{'local_id':aid,'scheme':expected[aid]['scheme'],'external_id':expected[aid]['external_id']} for aid in group]
                rows=db.execute("""WITH requested AS (SELECT * FROM jsonb_to_recordset(%s) AS x(local_id text,scheme text,external_id text))
                  SELECT r.local_id,e.entity_id::text id FROM requested r JOIN external_identifiers e
                  ON e.entity_type='artwork' AND e.scheme=r.scheme AND e.external_id=r.external_id""",(Jsonb(requests),)).fetchall()
                by_local=collections.defaultdict(list)
                for row in rows:by_local[row['local_id']].append(row['id'])
                for aid in group:
                    hits=by_local[aid]
                    if len(hits)!=1 or hits[0] in mapped:errors.append({'artwork_id':aid,'phase':'production_identity','error':'Native source identity absent, ambiguous or shared'});continue
                    mapped[hits[0]]=expected[aid]
            expected=mapped;ids=list(expected)
        for start in range(0,len(ids),500):
            group=ids[start:start+500]
            rows=db.execute("""SELECT a.id::text,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.status,a.published_at,a.primary_media_id::text,
              artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) selected,
              m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,m.license_label,m.license_url,m.source_page_url,m.creator_credit,m.attribution_text,
              r.source_checksum,r.source_image_url,r.policy_url,
              i.name museum,coalesce(p.country_code,vc.country_code) institution_country,
              EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
              FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence r ON r.media_id=m.id
              LEFT JOIN institutions i ON i.id=coalesce(a.current_institution_id,(SELECT la.institution_id FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='holding' AND la.review_state='accepted' AND la.superseded_by IS NULL ORDER BY la.checked_at DESC LIMIT 1))
              LEFT JOIN places p ON p.id=i.place_id
              LEFT JOIN LATERAL (SELECT min(vp.country_code) country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id HAVING count(DISTINCT vp.country_code)=1 AND bool_and(vp.country_code IS NOT NULL)) vc ON true
              WHERE a.id=ANY(%s::uuid[])""",(group,)).fetchall();found=set()
            for row in rows:
                aid=row['id'];found.add(aid);e=expected[aid]
                mapping={'primary_media_id':'media_id','storage_path':'path','checksum_sha256':'sha256','byte_size':'bytes','source_page_url':'page','license_url':'policy_url'}
                try:
                    for dest,source in mapping.items():assert row[dest]==e[source],dest+' differs'
                    for key in ('title','creation_year_start','creation_year_end','work_type','policy_url','source_image_url','source_checksum','rights_status','license_label','creator_credit','attribution_text'):assert row[key]==e[key],key+' differs'
                    assert row['status']=='review' and row['published_at'] is None and row['selected'] and row['scope']=='eligible','Scope/selection/editorial state differs'
                    db_checked+=1;museum[row['museum'] or 'Unresolved institution']+=1;country[row['institution_country'] or 'Not mapped']+=1;popular+=int(row['popular'])
                except Exception as exc:errors.append({'artwork_id':aid,'phase':'database','error':str(exc)[:300]})
            for aid in set(group)-found:errors.append({'artwork_id':aid,'phase':'database','error':'Attached artwork/media/rights row absent'})
    duplicate_hashes=[{'sha256':key,'artwork_ids':value} for key,value in checksums.items() if len(value)>1]
    gcs_checked=0
    if a.verify_gcs:
        wanted={e['path'].lstrip('/'):e for e in expected.values()};found=set()
        client=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials())
        for provider in sorted(counts):
            for blob in client.list_blobs(core.BUCKET,prefix='assets/artworks/open-museums/'+provider+'/',page_size=1000,timeout=60):
                if blob.name not in wanted:continue
                found.add(blob.name)
                try:verify_blob(blob,wanted[blob.name]);gcs_checked+=1
                except AssertionError as exc:errors.append({'artwork_id':wanted[blob.name]['local_artwork_id'],'phase':'google_storage','error':str(exc)})
            print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'Storage audited',provider,'verified total',gcs_checked,flush=True)
        for path in wanted.keys()-found:errors.append({'artwork_id':wanted[path]['local_artwork_id'],'phase':'google_storage','error':'Expected image object absent'})
    report={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_seconds':round(time.time()-started,2),'journal_snapshot_artworks':len(journal),'source_and_file_verified':sum(counts.values()),'db_verified':db_checked,'popular_painter_images':popular,'by_provider':counts,'by_work_type':types,'by_image_license':licenses,'by_holding_museum':museum,'by_holding_country':country,'identical_approved_image_hash_groups':duplicate_hashes,'errors':errors,'production_verified_in_this_audit':False,'notes':'Read-only local audit. All actual attached image bytes, approved licence URI, credit, identity/scope evidence and database references were checked. Country is institution location, not inferred artist nationality. Matching image hashes are review leads, not proof of duplicate physical artworks.'}
    report.update(target=a.target,google_storage_verified=gcs_checked,production_verified_in_this_audit=a.target=='cloud',notes='Read-only '+a.target+' audit. Source evidence, actual local bytes and database references checked; production IDs mapped by exact native source identifiers. Google Storage sizes, MD5 and provenance metadata freshly checked when requested. Institution country is not artist nationality. Identical image hashes require physical-object review, not automatic merging.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print('LOCAL AUDIT',json.dumps({k:report[k] for k in ('journal_snapshot_artworks','source_and_file_verified','db_verified','popular_painter_images','elapsed_seconds')}),'errors',len(errors),'identical_image_groups',len(duplicate_hashes),flush=True)
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
