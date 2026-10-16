#!/usr/bin/env python3
"""One bounded WikiArt image batch for exact Moralis 1988 objects."""
import base64, csv, fcntl, gzip, hashlib, importlib.util, io, json, os, shutil, subprocess, sys
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('image151_base',ROOT/'ops/continuous-exhibitions-image-000147.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
b.E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000151'
b.R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000151'
b.OP='continuous-exhibitions-20261013-batch-000151-images'
b.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/b.OP
b.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/b.OP
for p in (b.E,b.R,b.BACKUP,b.ORIG):p.mkdir(parents=True,exist_ok=True)
b.BACKUP.chmod(0o700)
E,R,OP,B=b.E,b.R,b.OP,b.BACKUP
c,d,save,load,sha=b.c,b.d,b.save,b.load,b.sha
PREV=E.parent/'000150'

def prepare():
    old=load(PREV/'immutable-plan.json');assert sha((PREV/'immutable-plan.json').read_bytes())==load(PREV/'plan-pin.json')['sha256']
    save(E/'production-target-reconciliation.json',b.target())
    registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
    docs=[ROOT/'AGENTS.md',ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',ROOT/'ops/exhibitions_common.py',ROOT/'ops/cesi-top100-20261010.py']
    save(E/'required-input-verification.json',dict(at=c.now(),registry_sha256=sha(registry.read_bytes()),registry_rows=111,files=[dict(path=str(p),sha256=sha(p.read_bytes())) for p in docs],wikiart_authorization='User-approved source policy 6 October 2026; actual rights retained separately.',scope='Historical exhibitions 1600–1989; main works through1970',free_bytes=shutil.disk_usage(R).free,passed=True))
    ids=[x['artwork_id'] for x in old['objects']]
    with c.connect() as db:
        own=db.execute('select media_id::text,evidence_json from media_rights_evidence where adapter_version=%s',(OP,)).fetchall();assert not own
        allbefore=d.snapshot(db,ids)
        prior=db.execute('select id::text,artwork_id::text,catalogue_number from exhibition_entries where exhibition_id=%s and id=any(%s::uuid[]) order by id',(old['event_id'],[x['id'] for x in old['objects']])).fetchall();assert len(prior)==6
        citations=db.execute("select to_jsonb(x) r from citations x where entity_type='artwork' and entity_id=any(%s::uuid[]) order by id",(ids,)).fetchall()
        links=b.entries(db,ids)
    selected=[x for x in old['objects'] if not allbefore[x['artwork_id']]['artwork']['primary_media_id'] and not allbefore[x['artwork_id']]['attachments']]
    assert len(selected)<=10
    save(E/'exact-operation-recovery-verification.json',dict(at=c.now(),own_operation=OP,own_existing_rows=own,prior_batch_links=prior,other_job_rows_in_broad_batch_number_search=load(E/'startup-recovery-verification.json')['own_prior_writes'],correction='Initial broad batch-number query also matched independent Smithsonian batch151; these three assets are not this programme and are excluded. Exact operation has zero rows.',existing_images_excluded=[x for x in ids if x not in [r['artwork_id'] for r in selected]],passed=True))
    images={x['artwork_id']:x for x in load(PREV/'identity-image-retrieval-verification.json')['images']}
    prior_review=load(PREV/'visual-object-identity-verification.json')
    for f in prior_review['files']:assert sha(Path(f['path']).read_bytes())==f['sha256']
    assert sha(Path(old['source']['body_path']).read_bytes())==old['source']['sha256']
    chosen=[];captures=[]
    for x in selected:
        aid=x['artwork_id'];native=x['wikiart_native_id'];im=images[aid]
        url=x['existing_source_page_url']
        if im['updated_source_page']:
            rc=im['updated_source_page'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert sha(raw)==rc['sha256']
            dest=R/'source-captures'/f'{native}.html';dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
            meta=dict(rc,path=str(dest),reused_prior_capture=True)
        else:raw,meta=b.capture(url,R/'source-captures'/f'{native}.html')
        soup=BeautifulSoup(raw,'html.parser');txt=soup.get_text(' ',strip=True)
        assert 'Yiannis Moralis' in txt and 'Fair Use' in txt
        imageurl=soup.find('meta',property='og:image')['content']
        assert imageurl.split('!')[0]==im['receipt']['url'].split('!')[0],(native,imageurl)
        rawim=Path(im['path']).read_bytes();assert sha(rawim)==im['receipt']['sha256']
        original=b.ORIG/(native+'.jpg');original.write_bytes(rawim)
        # Already-small source JPEGs require no resizing or recompression.
        with Image.open(io.BytesIO(rawim)) as pic:pic.load();dimensions=pic.size;assert pic.format=='JPEG'
        assert len(rawim)<=100000
        prepared=R/'prepared'/(native+'.jpg');prepared.parent.mkdir(exist_ok=True);prepared.write_bytes(rawim)
        citation=next(q['r'] for q in citations if q['r']['entity_id']==aid and q['r']['source_url']==url)
        mid=b.uid('media/'+aid+'/'+sha(rawim))
        selected_links=[z for z in links if z['entry']['artwork_id']==aid]
        assert any(z['entry']['id']==x['id'] and z['entry']['participation']=='exhibited' for z in selected_links)
        chosen.append(dict(artwork_id=aid,native_id=native,title=allbefore[aid]['artwork']['title'],source_url=url,source_image_url=im['receipt']['url'],source_checksum=sha(raw),source_id=citation['source_id'],source_citation_id=citation['id'],original_path=str(original),original_sha256=sha(rawim),source_dimensions=list(dimensions),prepared_path=str(prepared),sha256=sha(rawim),bytes=len(rawim),width=dimensions[0],height=dimensions[1],media_id=mid,storage_path='/assets/artworks/imported/'+OP+'/'+aid+'-'+sha(rawim)[:16]+'.jpg',accession=x['accession'],catalogue_number=x['number'],identity_basis=x['visual_basis'],exact_existing_entry_ids=[z['entry']['id'] for z in selected_links],source_rights_label='© Yiannis Moralis; Fair Use',rights_status='restricted',prior_identity_review_sha256=sha((PREV/'visual-object-identity-verification.json').read_bytes()),dimension_discrepancy=native=='268589',catalogue_dimensions=x['dimensions'],full_source_frame=True,transform='None; original supplied JPEG already at most100000 bytes.'))
        captures.append(dict(native_id=native,metadata=meta,image_receipt=im['receipt'],original_copy=str(original),rights_excerpt=txt[max(0,txt.find('Fair Use')-160):txt.find('Fair Use')+170],image_url_from_page=imageurl))
    save(E/'source-capture-verification.json',dict(at=c.now(),rows=captures,prior_identity_evidence=str(PREV/'visual-object-identity-verification.json'),prior_identity_review_sha256=sha((PREV/'visual-object-identity-verification.json').read_bytes()),museum_catalogue=old['source'],original_catalogue_not_uploaded=True,passed=True))
    ids=[x['artwork_id'] for x in chosen]
    pre=dict(at=c.now(),before={k:v for k,v in allbefore.items() if k in ids},exact_links=[z for z in links if z['entry']['artwork_id'] in ids],citations=[x for x in citations if x['r']['entity_id'] in ids])
    save(E/'transaction-preimage.json',pre);save(B/'selection-preimage.json',pre)
    p=dict(at=c.now(),operation=OP,rows=chosen,preimage_sha256=sha((E/'transaction-preimage.json').read_bytes()),source_capture_sha256=sha((E/'source-capture-verification.json').read_bytes()))
    save(E/'immutable-plan.json',p);save(E/'plan-pin.json',dict(sha256=sha((E/'immutable-plan.json').read_bytes())))
    save(E/'technical-verification.json',dict(at=c.now(),rows=[dict(native_id=x['native_id'],bytes=x['bytes'],dimensions=x['source_dimensions'],sha256=x['sha256'],full_decode=True,source_bytes_unchanged=True,at_most100000=True) for x in chosen],passed=True))
    print(json.dumps([dict(native_id=x['native_id'],path=x['prepared_path'],title=x['title']) for x in chosen],indent=2))

def deliver():
    p=b.plan();pin=load(E/'plan-pin.json')['sha256'];review=load(E/'visual-review.json');assert review['plan_sha256']==pin
    assert sha((E/'visual-review.json').read_bytes())==load(E/'visual-review-pin.json')['sha256']
    reviews={x['native_id']:x for x in review['rows']};assert len(reviews)==len(p['rows'])
    assert load(E/'backup-verification.json')['passed']
    pre=load(E/'transaction-preimage.json');assert sha((E/'transaction-preimage.json').read_bytes())==p['preimage_sha256']
    ids=[r['artwork_id'] for r in p['rows']]
    save(E/'production-target-before-database-write.json',b.target())
    with c.connect(write=True) as db:
        db.execute("set local lock_timeout='55s'");db.execute("select set_config('artline.actor_user_id',%s,true)",(b.ACTOR,));db.execute("select set_config('artline.request_id',%s,true)",(OP,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        db.execute('select id from artworks where id=any(%s::uuid[]) order by id for update',(ids,)).fetchall()
        own=db.execute('select media_id::text,evidence_json from media_rights_evidence where adapter_version=%s',(OP,)).fetchall()
        if own:
            assert len(own)==len(ids) and all(r['evidence_json']['selection_sha256']==pin for r in own);print('Own pinned delivery already exists; verify only');return
        before=d.snapshot(db,ids);assert before==pre['before'],'Concurrent image delivery: stop and reselect without overwriting'
        assert json.loads(json.dumps(b.entries(db,ids),default=str))==pre['exact_links']
        assert all(x['artwork']['primary_media_id'] is None and not x['attachments'] for x in before.values())
        save(B/'transaction-preimage.json',dict(plan_sha256=pin,before=before,exact_links=pre['exact_links']))
        credentials=b.core.GcloudCredentials();credentials.refresh(None);client=storage.Client(project='artline-508319',credentials=credentials)
        receipts=[]
        for r in p['rows']:
            rv=reviews[r['native_id']];assert rv['actually_viewed'] and rv['decision']=='accept' and rv['sha256']==r['sha256'] and rv['editorial_confidence']>=.90
            assert db.execute('select 1 from citations where id=%s and entity_id=%s and source_record_id=%s',(r['source_citation_id'],r['artwork_id'],r['native_id'])).fetchone()
            assert not db.execute('select id from media_assets where id=%s or checksum_sha256=%s',(r['media_id'],r['sha256'])).fetchone(),'Preexisting media elsewhere; do not duplicate or recount'
            raw=Path(r['prepared_path']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)<=100000
            save(E/f"targets/storage-{r['native_id']}.json",b.target())
            blob=client.bucket(b.core.BUCKET).blob(r['storage_path'].lstrip('/'));blob.metadata={'sha256':r['sha256'],'operation':OP,'plan_sha256':pin};blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
            except PreconditionFailed:pass
            blob.reload();assert blob.size==len(raw) and blob.metadata=={'sha256':r['sha256'],'operation':OP,'plan_sha256':pin}
            assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
            response=requests.get('https://artlines.org'+r['storage_path'],timeout=(15,45));response.raise_for_status();assert sha(response.content)==r['sha256']
            receipts.append(dict(native_id=r['native_id'],generation=blob.generation,sha256=r['sha256'],bytes=len(raw),operation=OP,plan_sha256=pin,public_status=response.status_code,public_sha256=sha(response.content)))
            credit='© Yiannis Moralis; image supplied by WikiArt. Source label: Fair Use.'
            d.batch(db,'media_assets',[dict(id=r['media_id'],storage_kind='local',storage_path=r['storage_path'],source_page_url=r['source_url'],provider_name='WikiArt',mime_type='image/jpeg',width=r['width'],height=r['height'],byte_size=r['bytes'],checksum_sha256=r['sha256'],alt_text=r['title']+' — Yiannis Moralis',rights_status='restricted',license_label=r['source_rights_label'],license_url=r['source_url'],creator_credit=credit,attribution_text=credit+' Complete supplied frame preserved; image bytes unchanged. User source approval is separate from a rights-holder licence.',retrieved_at=c.now(),verified_at=c.now(),verified_by=b.ACTOR)])
            evidence=dict(selection_sha256=pin,preimage_sha256=p['preimage_sha256'],native_source_checksum=r['source_checksum'],download_sha256=r['original_sha256'],visual_review=rv,visual_review_sha256=sha((E/'visual-review.json').read_bytes()),native_id=r['native_id'],accession=r['accession'],catalogue_number=r['catalogue_number'],source_citation_id=r['source_citation_id'],prior_identity_review_sha256=r['prior_identity_review_sha256'],exact_existing_entry_ids=r['exact_existing_entry_ids'],source_rights_label=r['source_rights_label'],complete_source_frame=True,actual_source_dimensions=r['source_dimensions'],catalogue_dimensions=r['catalogue_dimensions'],dimension_discrepancy=r['dimension_discrepancy'],user_authorization='WikiArt source policy approved 6 October2026; continuous exhibition images authorized.',independent_rights_holder_licence_claimed=False)
            d.batch(db,'media_rights_evidence',[dict(media_id=r['media_id'],source_id=r['source_id'],source_record_id=r['native_id'],source_checksum=r['source_checksum'],source_image_url=r['source_image_url'],policy_url=r['source_url'],rights_basis='Explicit WikiArt source approval; actual copyright and Fair Use label retained as restricted, not an independent licence.',adapter_version=OP,checked_at=c.now(),evidence_json=evidence)])
            d.batch(db,'artwork_media',[dict(artwork_id=r['artwork_id'],media_id=r['media_id'],sort_order=0,view_label='WikiArt exact artwork reproduction; complete supplied frame')])
            db.execute('update artworks set primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 where id=%s and primary_media_id is null',(r['media_id'],b.ACTOR,r['artwork_id']))
        save(E/'storage-upload-verification.json',dict(at=c.now(),rows=receipts,passed=True))
        after=d.snapshot(db,ids)
        for aid in ids:
            assert all(v==after[aid]['artwork'][k] for k,v in before[aid]['artwork'].items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
            assert before[aid]['creators']==after[aid]['creators'] and before[aid]['holdings']==after[aid]['holdings']
        save(B/'transaction-postimage.json',dict(plan_sha256=pin,after=after));db.commit()
    save(E/'applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,new_images=len(ids),artwork_ids=ids))
    print('Selected images committed; independent verification required')

if __name__=='__main__':
    {'prepare':prepare,'backup':b.backup,'deliver':deliver,'verify':b.verify}[sys.argv[1]]()
