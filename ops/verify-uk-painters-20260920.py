#!/usr/bin/env python3
"""Read-only UK collection delivery verification and human-readable index."""
import argparse,collections,concurrent.futures,importlib.util,json,time,uuid
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('uk',Path(__file__).with_name('uk-painters-20260920.py'))
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
ROOT,RUN,m=u.ROOT,u.RUN,u.m
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'

def public_get(url):
    for attempt in range(3):
        try:
            response=m.requests.get(url,timeout=(15,45))
            if response.status_code not in (429,502,503,504) or attempt==2:return response
            delay=m.core.retry_delay(response.headers.get('Retry-After'),default=2**attempt)
        except m.requests.RequestException:
            if attempt==2:raise
            delay=2**attempt
        time.sleep(delay)

def read(path):return json.loads(path.read_bytes())
def records(path):return [read(p) for p in sorted(path.glob('*.json'))]
def iter_records(path):
    for p in sorted(path.glob('*.json')):yield read(p)
def directory_plan():
    path=RUN/'wikiart-directory-resolved-plan.json'
    return read(path if path.exists() else RUN/'wikiart-directory-final-plan.json')

def verify(partial=False):
    from PIL import Image
    errors=[];targets={};snapshots={};backup_hashes={};api=[]
    selected=read(RUN/'selected-museum/catalogue.json');selection_held=selected['held']
    source={r['qid']:{k:r[k] for k in ('qid','creator_qid','creator_label','date','accession','title')} for r in selected['selected']}
    del selected
    prepared={r['record']['qid']:{'image':r['image']} for r in iter_records(RUN/'museum-images/ready')}
    if not partial:assert set(source)<=set(prepared)
    wiki=[];wiki_images=[]
    for folder in (RUN,RUN/'wikiart-supplement'):
        receipts=records(folder/'delivery')
        if not receipts:continue
        check=read(sorted(folder.glob('verification-'+str(len(receipts))+'-*.json'))[-1]);assert not check['errors']
        wiki.append(check);wiki_images.extend(records(folder/'images'))
    def check_backup(receipt):
        path=receipt['backup']
        if path not in backup_hashes:backup_hashes[path]=m.core.sha(Path(path).read_bytes())
        if backup_hashes[path]!=receipt['backup_sha256']:errors.append({'error':'Recovery checksum differs','path':path})
        if receipt.get('previous_receipt'):
            prior=Path(receipt['previous_receipt'])
            if m.core.sha(prior.read_bytes())!=receipt['previous_receipt_sha256']:errors.append({'error':'Prior delivery receipt checksum differs','path':str(prior)})
            check_backup(read(prior))
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        artists=records(RUN/'authorities-applied'/target)+records(RUN/'directory-final-applied'/target)
        receipts=[v for v in records(RUN/'museum-applied'/target) if not partial or v['qid'] in prepared]
        held=[v for v in records(RUN/'museum-held'/target) if not partial or v['qid'] in prepared]
        if not partial and {v['qid'] for v in receipts+held}!=set(source):errors.append({'target':target,'error':'Museum selection lacks complete applied/held receipts'})
        artist_ids=list({v['artist_id'] for v in artists});ids=[v['artwork_id'] for v in receipts]
        with m.read_only(dsn) as db:
            for correction in records(RUN/'identity-corrections/applied'/target):
                old=correction['old_artist_id'];new=correction['new_artist_id'];check_backup(correction)
                actual=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(old,)).fetchone()
                if actual!=correction['old_after']['artist']:errors.append({'target':target,'artist_id':old,'error':'Preserved namesake artist metadata changed'})
                native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s",(correction['qid'],)).fetchall()
                if native!=[{'entity_id':new}]:errors.append({'target':target,'qid':correction['qid'],'error':'Corrected namesake identity differs'})
                for key,table,where in [('artwork_links','artwork_artists','artist_id=%s'),('countries','artist_countries','artist_id=%s')]:
                    actual=[v['record'] for v in db.execute('SELECT to_jsonb(t) record FROM '+table+' t WHERE '+where,(old,)).fetchall()]
                    if sorted(actual,key=lambda v:json.dumps(v,sort_keys=True))!=sorted(correction['old_after'][key],key=lambda v:json.dumps(v,sort_keys=True)):errors.append({'target':target,'artist_id':old,'error':'Preserved namesake '+key+' differs'})
            current={v['record']['id']:v['record'] for v in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()}
            qmap={v['external_id']:v['entity_id'] for v in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND entity_id=ANY(%s::uuid[])",(artist_ids,)).fetchall()}
            gb={v['artist_id'] for v in db.execute("SELECT artist_id::text FROM artist_countries WHERE artist_id=ANY(%s::uuid[]) AND country_code='GB'",(artist_ids,)).fetchall()}
            for receipt in artists:
                aid=receipt['artist_id'];check_backup(receipt)
                if current.get(aid)!=receipt['after']:errors.append({'target':target,'artist_id':aid,'error':'Artist metadata differs from delivery receipt'})
                if receipt.get('qid') and qmap.get(receipt['qid'])!=aid:errors.append({'target':target,'artist_id':aid,'error':'Artist source identity differs'})
                if aid not in gb:errors.append({'target':target,'artist_id':aid,'error':'UK source affiliation absent'})
                if receipt['created'] and receipt['after']['status']!='review':errors.append({'target':target,'artist_id':aid,'error':'New artist review state differs'})
            works={v['record']['id']:v for v in db.execute('SELECT to_jsonb(a) record,to_jsonb(ma) media FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()}
            workqids={v['external_id']:v['entity_id'] for v in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(list(source),)).fetchall()}
            links=collections.defaultdict(list)
            for v in db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall():links[v['artwork_id']].append((v['artist_id'],v['attribution_role']))
            members={v['artwork_id'] for v in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection_id,ids)).fetchall()}
            new_ids=[v['artwork_id'] for v in receipts if v['created']]
            claims=db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND (review_state='accepted' OR claim_type='display')",(new_ids,)).fetchone()['n']
            if claims:errors.append({'target':target,'error':'Unexpected accepted holding/current-display claims','count':claims})
            for receipt in receipts:
                q=receipt['qid'];aid=receipt['artwork_id'];rec=source[q];actual=works.get(aid);check_backup(receipt)
                if not actual or actual['record']!=receipt['after']:errors.append({'target':target,'qid':q,'error':'Artwork differs from delivery receipt'});continue
                a=actual['record']
                if workqids.get(q)!=aid:errors.append({'target':target,'qid':q,'error':'Artwork source identity differs'})
                expected=[(receipt['artist_id'],'primary')] if receipt['artist_id'] else []
                if links[aid]!=expected or (not expected and a['unlinked_creator_label']!=rec['creator_label']):errors.append({'target':target,'qid':q,'error':'Creator identity differs'})
                if rec['creator_qid'] in qmap and receipt['artist_id']!=qmap[rec['creator_qid']]:errors.append({'target':target,'qid':q,'error':'Creator differs from source authority'})
                if rec['accession'] and a['accession_number'] and rec['accession']!=a['accession_number']:errors.append({'target':target,'qid':q,'error':'Source accession differs'})
                if aid not in members:errors.append({'target':target,'qid':q,'error':'Personal selection membership absent'})
                if receipt['created']:
                    if a['status']!='review' or not a['research_candidate'] or a['current_institution_id']:errors.append({'target':target,'qid':q,'error':'New artwork review state differs'})
                    if (a['creation_year_start'],a['creation_year_end'])!=(rec['date']['first'],rec['date']['last']):errors.append({'target':target,'qid':q,'error':'Source date differs'})
                if receipt['image_attached']:
                    im=prepared[q]['image'];media=actual['media']
                    if not im or not media or any(media[k]!=im[v] for k,v in [('storage_path','path'),('checksum_sha256','sha256'),('byte_size','bytes'),('rights_status','rights_status')]) or not a['creation_year_end'] or a['creation_year_end']>1955:errors.append({'target':target,'qid':q,'error':'Attached image metadata or eligible date differs'})
            catalogue=db.execute("""SELECT to_jsonb(a) artist,
                coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers
                FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code='GB') ORDER BY a.sort_name,a.id""").fetchall()
            all_ids=[v['artist']['id'] for v in catalogue]
            artwork_rows=db.execute("""SELECT aa.artist_id::text,a.id::text,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.status,a.primary_media_id::text,ma.storage_path,
                coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers
                FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
                WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ORDER BY aa.artist_id,a.title,a.id""",(all_ids,)).fetchall()
            size_audit=db.execute("SELECT count(*) total,count(*) FILTER(WHERE byte_size>100000) oversized,count(*) FILTER(WHERE byte_size IS NULL) unknown,max(byte_size) max_bytes FROM media_assets WHERE mime_type LIKE 'image/%%'").fetchone()
            if size_audit['oversized'] or size_audit['unknown']:errors.append({'target':target,'error':'Catalogue image size metadata audit failed','audit':size_audit})
            targets[target]={'new_artist_profiles':len({v['artist_id'] for v in artists if v['created']}),'active_uk_profiles':len(catalogue),'museum_records':len(receipts),'museum_held':len(held),'new_museum_artworks':sum(v['created'] for v in receipts),'existing_museum_artworks':sum(not v['created'] for v in receipts),'museum_images':sum(v['image_attached'] for v in receipts),'new_wikiart_artworks':sum(v['databases'][target]['new_artworks'] for v in wiki),'wikiart_images':sum(v['databases'][target]['attached'] for v in wiki),'new_artworks':sum(v['created'] for v in receipts)+sum(v['databases'][target]['new_artworks'] for v in wiki),'image_attachments':sum(v['image_attached'] for v in receipts)+sum(v['databases'][target]['attached'] for v in wiki),'catalogue_image_sizes':size_audit,'uk_artworks':len({v['id'] for v in artwork_rows}),'uk_artworks_with_images':len({v['id'] for v in artwork_rows if v['primary_media_id']})}
            snapshots[target]={'artists':catalogue,'artworks':artwork_rows}
        print('Verified database',target,targets[target],flush=True)
    images=[dict(v['image'],qid=q) for q,v in prepared.items() if v['image'] and (not partial or (RUN/'museum-uploads'/(q+'.json')).exists())]
    source_files=collections.defaultdict(list)
    for im in images:source_files[im['identity_basis']['wikidata_P18']].append(im['qid'])
    shared_source_files=[{'file':name,'qids':qids} for name,qids in source_files.items() if len(qids)>1]
    for im in images:
        receipt=im['commons_receipt']
        if receipt.get('capture_kind')=='selected_page_from_batch':
            parent_path=receipt['parent_capture']
            if parent_path not in backup_hashes:backup_hashes[parent_path]=m.core.sha(Path(parent_path).read_bytes())
            if backup_hashes[parent_path]!=receipt['parent_receipt']['sha256']:errors.append({'qid':im['qid'],'error':'Commons parent response checksum differs'})
            page=im['commons_page'];member=m.core.encode({'query':{'pages':{str(page['pageid']):page}}})
            if m.core.sha(member)!=receipt['sha256'] or len(member)!=receipt['bytes']:errors.append({'qid':im['qid'],'error':'Derived Commons member receipt differs'})
    def check_image(im):
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();result={'path':im['path'],'bytes':len(raw),'sha256':im['sha256'],'checked_at':m.core.now(),'local_verified':len(raw)<=100000 and len(raw)==im['bytes'] and m.core.sha(raw)==im['sha256']}
        with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')) as picture:
            result['local_verified']=result['local_verified'] and picture.format=='JPEG' and picture.size==(im['width'],im['height'])
        cache=RUN/'public-file-checks'/(im['qid']+'-'+im['sha256'][:16]+'.json')
        if cache.exists():
            previous=read(cache)
            if result['local_verified'] and previous.get('public_verified') and previous['path']==im['path'] and previous['sha256']==im['sha256']:return dict(previous,cache_reused=True)
        try:
            response=public_get(BASE+im['path'])
            result.update(http_status=response.status_code,public_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
        except m.requests.RequestException as exc:result.update(public_verified=False,error=str(exc)[:150])
        if result['local_verified'] and result['public_verified']:u.save(cache,result)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check_image,images))
    errors.extend(v for v in checks if not v['local_verified'] or not v['public_verified'])
    applied=[v for v in receipts if v['image_attached']]
    def check_api(receipt):
        q=receipt['qid'];im=prepared[q]['image'];response=public_get(BASE+'/api/backend/v1/atlas/artworks/'+receipt['artwork_id']);body=response.json() if response.status_code==200 else {}
        return {'qid':q,'http_status':response.status_code,'verified':response.status_code==200 and body.get('media_url')==im['path']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:api=list(pool.map(check_api,applied[::max(1,len(applied)//100)][:100]))
    errors.extend(dict(v,error='Public artwork API differs') for v in api if not v['verified'])
    started=time.monotonic();response=public_get(BASE+'/api/backend/v1/timeline?country=GB&popular=false');timeline={'http_status':response.status_code,'elapsed_seconds':round(time.monotonic()-started,3),'body':response.json()}
    if response.status_code!=200:errors.append({'error':'Public UK timeline failed','http_status':response.status_code})
    directory=directory_plan()
    result={'at':m.core.now(),'partial':partial,'databases':targets,'wikiart_directory_profiles':len(read(RUN/'wikiart-uk-directory.json')['artists']),'wikiart_directory_resolved':len(directory['matched']),'public_uploaded_files':len(wiki_images)+len(images),'max_uploaded_bytes':max(v['bytes'] for v in wiki_images+images),'new_museum_unknown_dates':sum(v['created'] and v['after']['creation_year_start'] is None for v in receipts),'museum_selection_held':selection_held,'file_checks':checks,'wikiart_verifications':wiki,'api_checks':api,'public_timeline':timeline,'snapshots':snapshots,'errors':errors}
    result['shared_source_files']=shared_source_files
    output=RUN/(('prefix' if partial else 'final')+'-verification-'+str(int(time.time()))+'.json');u.save(output,result);print('Verification',output,'errors',len(errors),flush=True)
    for error in errors:print(json.dumps(error),flush=True)
    if errors:raise SystemExit(1)


def report():
    path=sorted(RUN.glob('final-verification-*.json'))[-1];result=read(path);assert not result['errors']
    cloud=result['databases']['cloud'];snapshot=result['snapshots']['cloud'];works=collections.defaultdict(list)
    def md(value):return str(value if value is not None else 'Unknown').replace('|','\\|').replace('\n',' ')
    for work in snapshot['artworks']:works[work['artist_id']].append(work)
    artist_rows=['# UK painter catalogue — 20–21 September 2026','','Active UK-linked catalogue profiles, including source affiliations beyond current citizenship. Counts include earlier works and unknown dates. This is source coverage, not a claim that every historical painter is known.','','| Painter | Supplied life/activity dates | Artworks | With image | Source |','| --- | --- | ---: | ---: | --- |']
    artwork_rows=['# UK painter artworks — 20–21 September 2026','','Existing and new review records grouped by painter. Source collection statements do not establish accepted holdings or current display.','','| Painter | Artwork | Supplied date | Image | Source |','| --- | --- | --- | --- | --- |']
    for row in snapshot['artists']:
        artist=row['artist'];group=works[artist['id']];url=BASE+'/?'+urlencode({'country':'GB','popular':'false','artist':artist['slug']})
        identity=next((v for v in row['identifiers'] if v['scheme']=='wikidata'),next(iter(row['identifiers']),None))
        link='['+md(identity['id'])+']('+identity['url']+')' if identity and identity['url'] else 'Source retained in catalogue'
        artist_rows.append('| ['+md(artist['display_name'])+']('+url+') | '+md(artist['timeline_display'])+' | '+str(len(group))+' | '+str(sum(bool(w['primary_media_id']) for w in group))+' | '+link+' |')
        for work in group:
            identity=next(iter(work['identifiers']),None);link='['+md(identity['id'])+']('+identity['url']+')' if identity and identity['url'] else 'Source retained in catalogue'
            image='[View image]('+BASE+work['storage_path']+')' if work['storage_path'] else 'No image'
            artwork_rows.append('| '+md(artist['display_name'])+' | '+md(work['title'])+' | '+md(work['date_display'])+' | '+image+' | '+link+' |')
    indexed_ids={v['id'] for v in snapshot['artworks']}
    applied_museum={v['qid']:v for v in iter_records(RUN/'museum-applied/cloud')}
    held_museum={v['qid']:v for v in iter_records(RUN/'museum-held/cloud')}
    selected_qids={v['qid'] for v in read(RUN/'selected-museum/catalogue-index.json')['selected']}
    additional=[];commons_alternates=[];reasons=collections.Counter()
    for prepared in iter_records(RUN/'museum-images/ready'):
        rec=prepared['record'];qid=rec['qid'];im=prepared['image'];applied=applied_museum.get(qid)
        if applied and applied['artwork_id'] not in indexed_ids:
            after=applied['after'];image='[View image]('+BASE+im['path']+')' if im and applied['image_attached'] else 'No new image'
            additional.append('| '+md(rec['creator_label'])+' | '+md(after['title'])+' | '+md(after['date_display'])+' | '+image+' | ['+qid+'](https://www.wikidata.org/wiki/'+qid+') |')
            indexed_ids.add(applied['artwork_id'])
        if im and not (applied and applied['image_attached']):
            reason=held_museum.get(qid,{}).get('reason','Existing primary image preserved' if applied else 'Captured prefix selection not retained in the final object selection')
            commons_alternates.append('- ['+md(rec['creator_label']+' — '+rec['title'])+'](https://www.wikidata.org/wiki/'+qid+'): [public image]('+BASE+im['path']+'). '+md(reason)+'.')
        if not im and qid in selected_qids:reasons[prepared.get('image_reason') or prepared['image_outcome']]+=1
    for folder in (RUN,RUN/'wikiart-supplement'):
        for receipt in iter_records(folder/'delivery'):
            target=receipt['targets']['cloud'];after=target.get('after')
            if after and after['id'] not in indexed_ids:
                im=read(folder/'images'/(receipt['artwork_id']+'.json'))
                additional.append('| '+md(after.get('unlinked_creator_label') or after.get('cultural_context') or im['artist'])+' | '+md(after['title'])+' | '+md(after['date_display'])+' | [View image]('+BASE+im['path']+') | [WikiArt]('+im['page']+') |')
                indexed_ids.add(after['id'])
    if additional:
        artwork_rows.extend(['','## Other retained records from this source pass','','These review records have unresolved creator links, source affiliations outside the active UK filter, or a cultural context rather than a named painter. They are included for a complete delivery index.','','| Supplied creator or context | Artwork | Supplied date | Image | Source |','| --- | --- | --- | --- | --- |']+additional)
    (RUN/'ARTISTS.md').write_text('\n'.join(artist_rows)+'\n');(RUN/'ARTWORKS.md').write_text('\n'.join(artwork_rows)+'\n')
    authority=read(RUN/'authority-plan.json');directory=directory_plan();research=read(RUN/'work-candidate-selection.json')
    review=['# UK source records requiring review','','## Artist identity, affiliation or date uncertainty','','| Source | Name | Reason |','| --- | --- | --- |']
    applied={p.stem for p in (RUN/'authorities-applied/cloud').glob('*.json')}
    for row in authority['held']:
        if row['qid'] not in applied:review.append('| ['+row['qid']+'](https://www.wikidata.org/wiki/'+row['qid']+') | '+md(row['name'])+' | '+md(row['reason'])+' |')
    review.extend(['','## WikiArt directory reconciliation','','| Profile | Reason |','| --- | --- |'])
    for row in directory['held']:review.append('| ['+md(row['source']['name'])+']('+row['source']['url']+') | '+md(row['reason'])+' |')
    review.extend(['','Jacob Epstein already has separate WikiArt and NGA/Wikidata catalogue identities. The explicit WikiArt profile was retained for this directory; both existing profiles and their artworks remain preserved for duplicate review.'])
    review.extend(['','Eight newly added works from WikiArt’s “Viking art” category retain that cultural context and no named-artist attribution. Their images and review records remain available. The pre-existing category profile and its older works are preserved for separate reconciliation; the category is excluded from the 327 named-person directory matches.'])
    review.extend(['','## Corrected same-name identities','','Six new authorities were separated from older namesakes after reviewing native NGA/Tate records and supplied source chronology. Eight artworks created by this pass were reassigned with their images intact. Older artwork links and artist metadata were preserved. William Jones of Bath uses documented activity dates, with unknown life dates. The older Tate profile contains an inherited activity-as-lifespan issue retained for separate review. The original authority plan remains archived evidence; canonical delivery receipts incorporate these corrections.','','| Source identity | Correct profile | Earlier namesake preserved |','| --- | --- | --- |'])
    for row in records(RUN/'identity-corrections/applied/cloud'):
        review.append('| ['+row['qid']+'](https://www.wikidata.org/wiki/'+row['qid']+') | '+md(row['new_after']['artist']['record']['slug'])+' | '+md(row['old_after']['artist']['record']['slug'])+' |')
    name_review=read(RUN/'identity-corrections/name-match-review.json')
    review.extend(['','Five additional existing name matches have compatible chronology but no shared exact life year. They remain in review for manual confirmation:'])
    for row in name_review['reviewed_matches']:
        if row['qid'] in name_review['remaining_manual_review']:review.append('- ['+md(row['name'])+'](https://www.wikidata.org/wiki/'+row['qid']+').')
    review.extend(['','## Artwork records requiring object review','','| Source | Reason |','| --- | --- |'])
    for row in result['museum_selection_held']+records(RUN/'museum-held/cloud'):review.append('| ['+row['qid']+'](https://www.wikidata.org/wiki/'+row['qid']+') | '+md(row['reason'])+' |')
    if result.get('shared_source_files'):
        review.extend(['','## Shared source images','','Distinct source object IDs below reference the same source file. Records remain separate for identity review.'])
        for row in result['shared_source_files']:review.append('- '+md(row['file'])+': '+', '.join('['+qid+'](https://www.wikidata.org/wiki/'+qid+')' for qid in row['qids']))
    review.extend(['','## Public alternate images','','These additional files remain public. The individual reasons distinguish unresolved object matches, preserved existing primary images and captured prefix selections.'])
    for folder in (RUN,RUN/'wikiart-supplement'):
        for p in sorted((folder/'delivery').glob('*.json')):
            receipt=read(p)
            if receipt['targets']['cloud']['outcome']=='held':
                im=read(folder/'images'/p.name);review.append('\n- ['+md(im['artist']+' — '+im['title'])+']('+im['page']+'): [public image]('+BASE+im['path']+'). '+md(receipt['targets']['cloud']['reason'])+'.')
    review.extend(['']+commons_alternates)
    review.extend(['','## Collection-source image decisions','','Metadata remains in review when a selected file has no eligible date, image, source identity confirmation or resolved licence. Per-file evidence is retained under `museum-images/ready/`.','','| Reason | Records |','| --- | ---: |'])
    review.extend('| '+md(reason)+' | '+str(n)+' |' for reason,n in reasons.most_common())
    (RUN/'REVIEW.md').write_text('\n'.join(review)+'\n')
    rows=[]
    for key,title in [('new_artist_profiles','New artist profiles'),('active_uk_profiles','Active UK-linked profiles'),('new_artworks','New artwork records'),('image_attachments','New image attachments'),('uk_artworks','Total UK-linked artwork records'),('uk_artworks_with_images','Total UK-linked artworks with images')]:rows.append('| '+title+' | '+f"{result['databases']['local'][key]:,}"+' | '+f"{cloud[key]:,}"+' |')
    content=f'''# UK painters and selected artworks — 20–21 September 2026

Delivered to both the real local catalogue and live Artline collection.

[Open UK painters]({BASE}/?country=GB&popular=false) · [Full painter list](ARTISTS.md) · [Artwork and image index](ARTWORKS.md) · [Review queue and public alternates](REVIEW.md)

| Verified result | Local | Live |
| --- | ---: | ---: |
'''+ '\n'.join(rows)+f'''

## Coverage and selection

Surveyed all {authority['roster_count']:,} identities returned by the uncapped Wikidata painter census across the UK, constituent countries and historical states. Historical polity alone was insufficient to infer present-day UK cultural affiliation. Other national relationships and existing biographies were preserved. {result['wikiart_directory_resolved']} of {result['wikiart_directory_profiles']} profiles in [WikiArt’s British directory](https://www.wikiart.org/en/artists-by-nation/british/text-list) were reconciled; remaining identities are documented in the review queue. These are source inventories, not an exhaustive list of every UK painter in history.

Of the {len(snapshot['artists']):,} active UK-linked profiles in the live catalogue, {sum(bool(works[row['artist']['id']]) for row in snapshot['artists']):,} have artwork records and {sum(any(work['primary_media_id'] for work in works[row['artist']['id']]) for row in snapshot['artists']):,} have illustrated works. Profiles with no resolved artworks remain in the full painter index.

The collection-source search covered {research['artists_surveyed']:,} painter identities and captured {research['source_rows']:,} source rows. Selected up to four further collection-linked records per painter and up to eight further featured historical WikiArt works per matched profile. Artwork creation dates determine image eligibility. Painter birth or death dates are not used as artwork dates.

Added {cloud['new_museum_artworks']:,} collection-source artwork records and {cloud['new_wikiart_artworks']:,} WikiArt records. Source-pass totals include unresolved affiliations and eight works retained with a Viking cultural context rather than a named painter; the UK-filter totals are reported separately. {result['new_museum_unknown_dates']:,} new collection-source records have unknown dates and remain in review. Unresolved named creators remain object-level labels. Wikidata collection statements can identify museums, galleries or other collections; they were retained as citations without inventing accepted holdings or current display claims. Owner selections remain distinct from museum designations.

## Public images and verification

Uploaded {result['public_uploaded_files']:,} public files. Every derivative is at most 100,000 bytes; the largest is {result['max_uploaded_bytes']:,} bytes. Selected image creation dates end by 1955. Source licences, restricted/unknown rights labels and credits are preserved. Public alternate links remain available for unresolved object matches.

Final verification `{path.name}` recorded zero errors. Checks cover exact database receipts, authority IDs, creator links, date fields, review states, collection membership, recovery hashes, all uploaded public image hashes and bounded artwork API checks. The UK timeline returned HTTP {result['public_timeline']['http_status']} in {result['public_timeline']['elapsed_seconds']} seconds. Whole-catalogue image-size metadata audits found no oversized or unknown-size images in either database. No test fixtures or test databases were created. No code was deployed or committed. This validates the actual collection operation; it is not a 10-million-row load test.

Forty-seven offline tests passed for source-image review, WikiArt selection/delivery, request pacing and same-name identity matching. Six confirmed namesake errors were corrected in both catalogues, preserving older artist records and artworks. Five remaining name matches are explicitly listed for manual confirmation in the review queue. Public file checksum receipts retain their actual check timestamps; successful immutable-file checks from the earlier delivery are reused alongside fresh checks for the final batch.

## Research and recovery locations

- Source captures, per-record decisions and verification receipts: this research directory.
- Artist/artwork preimages, correction snapshots, receipt chains and selected Commons originals: `/Users/vadimdulub/Library/Application Support/Artline/backups/uk-painters-20260920/`. Earlier artist baselines preserve alias text rather than complete alias-table row IDs.
- Original WikiArt downloads: `/Users/vadimdulub/Library/Application Support/Artline/source-images/uk-painters-20260920/`.
- Operation runners: `ops/uk-painters-20260920.py` and `ops/verify-uk-painters-20260920.py`.

The query service used Wikimedia’s documented main-graph endpoint with paced, bounded requests and service backoff. Resumed media requests use a shared two-connection gate and 16 Mbps client bandwidth ceiling; Action API calls use one shared connection and a pause after slow responses, following the [Wikimedia robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy). Larger final-selection originals use the API-provided 1280-pixel version, one of the [standard thumbnail sizes](https://www.mediawiki.org/wiki/Common_thumbnail_sizes). Server retry delays are retained and extended after repeated failures. Artist records preserve explicit life-date precision or supplied activity periods without inventing missing years.
'''
    (RUN/'README.md').write_text(content)
    scripts=[]
    for name in ['uk-painters-20260920.py','verify-uk-painters-20260920.py','uk-source-downloads-20260920.py','uk-image-recovery-20260920.py','uk-identity-corrections-20260921.py','test_uk_identity.py','test_uk_source_downloads.py','test_image_source_review.py','wikiart-artist-coverage.py','wikiart-selected-images.py','research-wikimedia-catalogues.py','prepare-wikimedia-catalogue-images.py']:
        raw=(ROOT/'ops'/name).read_bytes();digest=m.core.sha(raw);archive=m.BACKUP/'operation-scripts'/(name+'.'+digest[:16]);u.save(archive,raw);scripts.append({'name':name,'sha256':digest,'archive':str(archive)})
    u.save(RUN/'final-operation-script-archive.json',scripts);print(json.dumps({'report':str(RUN/'README.md'),'counts':cloud,'public_files':result['public_uploaded_files']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['verify','report']);parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    if args.phase=='verify':verify(args.partial)
    else:report()
