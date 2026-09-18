#!/usr/bin/env python3
"""Plan and apply bounded Wikimedia batches to local and production.

Only missing catalogue rows/images and evidence are added. Existing titles,
attributions, dates, biographies and publication decisions are preserved.
"""
import argparse, base64, importlib.util, json, re, uuid
from pathlib import Path
from urllib.parse import quote
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-wikimedia-catalogues.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
core=r.core
ACTOR='local-european-research'
VERSION='wikimedia-catalogue-scan-v1'
SOURCE_SLUG='wikimedia-catalogue-scan-20260913'
SOURCE_NAME='Wikimedia catalogue research — documented museum connections'
IMAGE_SOURCE_SLUG='wikimedia-catalogue-images-20260913'

def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/'+key))
def accession_key(text):return re.sub(r'\s+','',(text or '').upper().translate(str.maketrans('ΒΧΜ','BXM')))
def work_titles(record):return {r.norm(t) for t in record['titles']}
def title_lookup_variants(titles):
    # Local PostgreSQL uses C ctype (ASCII-only lower); production uses UTF-8.
    # Retain source spelling and both lowercase forms when selecting candidates.
    # The subsequent Python Unicode normalization decides identity/holds.
    ascii_lower=str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')
    punctuation=set()
    for title in titles:
        straight=title.translate(str.maketrans({'’':"'",'‘':"'",'ʼ':"'"}))
        punctuation.update((title,straight,straight.replace("'",'’')))
    return sorted({variant for title in punctuation for variant in (title,title.lower(),title.translate(ascii_lower))})

def choose_existing(record,rows):
    accessions={accession_key(x) for x in r.values(record['entity'],'P217') if isinstance(x,str)}
    if (record.get('primary_museum_review') or record.get('primary_metadata_review',{}).get('override',{}).get('accession')) and record.get('accession'):accessions.add(accession_key(record['accession']))
    exact=[row for row in rows if row['accession_number'] and accession_key(row['accession_number']) in accessions]
    if len(exact)>1:return None,'ambiguous_existing_accession'
    def same_creator(row):
        return bool(record['creator_qid'] and record['creator_qid'] in row['creator_qids']) or bool({r.norm(n) for n in row['creator_names']} & {r.norm(n) for n in r.labels(record['creator_entity'])})
    if exact:
        row=exact[0]
        same_title=bool(work_titles(record)&{r.norm(row['title']),r.norm(row['alternate_title'] or '')})
        if not same_title and not same_creator(row):return None,'accession_has_conflicting_title_and_creator'
        if row['creator_qids'] and record['creator_qid'] and record['creator_qid'] not in row['creator_qids']:return None,'accession_has_conflicting_creator'
        return row,None
    titles=[row for row in rows if work_titles(record)&{r.norm(row['title']),r.norm(row['alternate_title'] or '')} and same_creator(row)]
    if len(titles)>1:return None,'ambiguous_title_and_creator'
    expected=record.get('existing_local')
    if expected:
        known=[row for row in rows if row['slug']==expected['slug']]
        if len(known)==1:return known[0],None
    return (titles[0],None) if titles else (None,None)

def plan(number,limit):
    path=r.RUN/'batches'/f'batch-{number:03d}.json'
    if path.exists():print('Existing immutable plan',path);return
    prior=set()
    for old in (r.RUN/'batches').glob('batch-*.json'):
        if not re.fullmatch(r'batch-\d{3}\.json',old.name):continue
        prior.update(x['record']['qid'] for x in json.loads(old.read_text())['entries'])
    input_path=r.RUN/'batches'/f'batch-{number:03d}.inputs.json'
    if input_path.exists():candidates=json.loads(input_path.read_text())
    else:
        candidates=[json.loads(p.read_text()) for p in sorted((r.RUN/'ready').glob('Q*.json')) if p.stem not in prior][:limit]
        core.save_new(input_path,candidates)
    assert candidates,'No unplanned prepared candidates'
    output={'version':VERSION,'at':core.now(),'batch':number,'entries':candidates,'targets':{}}
    for target in ('local','production'):
        statuses=[];snapshots=[];inventory_cache={}
        with r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
            for item in candidates:
                record=item['record'];qid=record['qid']
                if record['date']['first'] is not None and not record['date']['eligible']:
                    statuses.append({'qid':qid,'action':'deferred','reason':'known_date_outside_scope'});continue
                slugs=record['collection'].get('related_institution_slugs',[record['collection']['institution']['slug']])
                institutions=db.execute('SELECT id::text,slug FROM institutions WHERE slug=ANY(%s)',(slugs,)).fetchall()
                new_institution=None
                if not institutions and record['collection']['institution'].get('new_institution'):
                    new_institution=record['collection']['institution']
                    collision=db.execute('SELECT id FROM institutions WHERE wikidata_id=%s OR lower(name)=%s',(new_institution['wikidata_id'],new_institution['name'].lower())).fetchone()
                    assert not collision,'New institution has an existing identity requiring reconciliation'
                    institutions=[{'id':new_institution['id'],'slug':new_institution['slug']}]
                assert institutions,'Missing target institution'
                iid=next(x['id'] for x in institutions if x['slug']==record['collection']['institution']['slug'])
                cachekey=tuple(sorted(x['id'] for x in institutions))
                if cachekey not in inventory_cache:
                    peers=[x['record'] for x in candidates if x['record']['collection']['qid']==record['collection']['qid']]
                    keys=list({accession_key(x) for peer in peers for x in r.values(peer['entity'],'P217') if isinstance(x,str)})
                    keys=list(set(keys)|{accession_key(peer['accession']) for peer in peers if (peer.get('primary_museum_review') or peer.get('primary_metadata_review',{}).get('override',{}).get('accession')) and peer.get('accession')})
                    titles=title_lookup_variants(t for peer in peers for t in peer['titles'])
                    expected=list({(peer.get('existing_local') or {}).get('slug','') for peer in peers})
                    inventory_cache[cachekey]=db.execute('''WITH selected AS MATERIALIZED (
                      SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND
                       (slug=ANY(%s) OR lower(title)=ANY(%s) OR lower(alternate_title)=ANY(%s) OR
                        regexp_replace(translate(upper(coalesce(accession_number,'')),'ΒΧΜ','BXM'),'\\s+','','g')=ANY(%s)))
                      SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.primary_media_id::text,a.status,a.revision,
                  a.creation_year_start,a.creation_year_end,a.date_precision,
                  COALESCE((SELECT jsonb_agg(e.external_id) FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata' WHERE aa.artwork_id=a.id),'[]') creator_qids,
                  COALESCE((SELECT jsonb_agg(p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creator_names
                      FROM selected s JOIN artworks a ON a.id=s.id''',(list(cachekey),expected,titles,titles,keys)).fetchall()
                rows=inventory_cache[cachekey]
                existing,reason=choose_existing(record,rows)
                authority=db.execute("SELECT entity_type,entity_id::text FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(qid,)).fetchone()
                if authority and (not existing or authority['entity_id']!=existing['id']):reason='global_identity_already_present'
                if existing and existing['status']=='archived':reason='archived_record_preserved'
                if reason:
                    statuses.append({'qid':qid,'action':'deferred','reason':reason,'matches':rows});continue
                artist=None;new_artist=None
                if not existing and record['creator_qid']:
                    cq=record['creator_qid'];ce=record['creator_entity']
                    row=db.execute("SELECT a.id::text,a.slug FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE e.external_id=%s AND a.status<>'archived'",(cq,)).fetchone()
                    if row:artist=row['id']
                    else:
                        names=r.labels(ce)
                        collision=db.execute('SELECT id FROM artists WHERE lower(display_name)=ANY(%s) OR normalized_name=ANY(%s) LIMIT 1',([n.lower() for n in names],[r.norm(n) for n in names])).fetchone()
                        birth,death=r.year(ce,'P569'),r.year(ce,'P570')
                        activity=record['date']
                        if not collision and ((birth is not None and death is not None and 1100<=birth<=death) or activity['eligible']):
                            basis='life' if birth is not None and death is not None and birth<=death else 'activity'
                            first,last=(birth,death) if basis=='life' else (activity['first'],activity['last'])
                            if first>=1100:
                                artist=uid('artist/'+cq)
                                new_artist={'id':artist,'qid':cq,'name':record['creator_label'],'birth':birth,'death':death,'first':first,'last':last,'basis':basis,'description':ce.get('descriptions',{}).get('en',{}).get('value',''),'entity':ce}
                if existing:
                    before=db.execute('SELECT to_jsonb(a) AS row FROM artworks a WHERE id=%s',(existing['id'],)).fetchone()['row'];snapshots.append(before)
                statuses.append({'qid':qid,'action':'existing' if existing else 'new','institution_id':iid,'new_institution':new_institution,'artwork_id':existing['id'] if existing else uid('artwork/'+qid),'existing':existing,'artist_id':artist,'new_artist':new_artist})
        output['targets'][target]=statuses
        core.save_new(r.BACKUPS/f'batch-{number:03d}-{target}-preimages.json',snapshots)
        print(target,'planned',len(statuses),'new',sum(x['action']=='new' for x in statuses),'existing',sum(x['action']=='existing' for x in statuses),'deferred',sum(x['action']=='deferred' for x in statuses),flush=True)
    core.save_new(path,output)
    print('Plan SHA-256',core.sha(path.read_bytes()),flush=True)

def source(db,slug,name,kind,url):
    db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(slug) DO NOTHING',(uid('source/'+slug),slug,name,kind,url))
    return db.execute('SELECT id FROM sources WHERE slug=%s AND is_active',(slug,)).fetchone()['id']

def artist_insert(db,author,record,sid):
    cq=author['qid']
    existing=db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s AND entity_type='artist'",(cq,)).fetchone()
    if existing:return existing['entity_id'],False
    if 'Q5' not in {v.get('id') for v in r.values(author['entity'],'P31') if isinstance(v,dict)}:return None,False
    names=r.labels(author['entity'])
    collision=db.execute('SELECT id FROM artists WHERE lower(display_name)=ANY(%s) OR normalized_name=ANY(%s) LIMIT 1',([n.lower() for n in names],[r.norm(n) for n in names])).fetchone()
    if collision:return None,False
    # The batch's earlier record may already have created this same painter.
    first,last=author['first'],author['last'];basis=author['basis']
    biography=(author['description']+'.\n\n' if author['description'] else '')+f'Source: [Wikidata](https://www.wikidata.org/wiki/{cq}) (CC0). Short authority description; full biography awaits editorial review.'
    fields=dict(id=author['id'],slug='wikimedia-painter-'+cq.lower(),display_name=author['name'],sort_name=author['name'],normalized_name=r.norm(author['name']),entity_type='person',birth_year=author['birth'],death_year=author['death'],timeline_start_year=first,timeline_end_year=last,timeline_display=f'{first}–{last}' if basis=='life' else f'Documented work: {first}–{last}',timeline_basis=basis,biography_md=biography,status='review',created_by=ACTOR,updated_by=ACTOR)
    if basis=='activity':fields.update(active_start_year=first,active_end_year=last,activity_display=f'Documented work: {first}–{last}')
    r.base.insert(db,'artists',fields)
    r.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=author['id'],scheme='wikidata',external_id=cq,canonical_url='https://www.wikidata.org/wiki/'+cq,source_id=sid,retrieved_at=record['creator_receipt']['retrieved_at']))
    for language,text in author['entity'].get('labels',{}).items():
        db.execute('INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,\'alternate\') ON CONFLICT DO NOTHING',(author['id'],text['value'],r.norm(text['value']),language))
    for word,code in [('Greek','GR'),('Russian','RU'),('French','FR'),('Italian','IT'),('Dutch','NL'),('Spanish','ES'),('German','DE'),('British','GB'),('American','US'),('Swedish','SE'),('Danish','DK'),('Norwegian','NO'),('Portuguese','PT')]:
        explicitly_reviewed=record.get('country_evidence') and record.get('country_code')==code
        role_wording=re.search(r'\b'+word+r'(?![- ]born)\b(?:[- /][A-Za-z]+)?(?: [\w-]+){0,4} (?:painter|artist|iconographer|printmaker|engraver|illustrator|draughtsman|sculptor)\b',author['description'],re.I)
        if explicitly_reviewed or (not record.get('country_evidence') and role_wording):
            db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) SELECT %s,%s,'cultural_affiliation',false,%s WHERE EXISTS(SELECT 1 FROM countries WHERE code=%s) ON CONFLICT DO NOTHING",(author['id'],code,'Source explicitly describes '+word+' affiliation: '+author['description']+'. This is not a modern citizenship assertion.',code))
    r.base.insert(db,'citations',dict(entity_type='artist',entity_id=author['id'],field_name='authority_identity_and_dates',source_id=sid,source_record_id=cq,source_url='https://www.wikidata.org/wiki/'+cq,evidence_note='Wikidata CC0 identity and source-labelled description. Timeline follows '+basis+' evidence; no invented birth/death dates. Full entity capture SHA-256: '+record['creator_receipt']['sha256'],retrieved_at=record['creator_receipt']['retrieved_at'],created_by=ACTOR))
    return author['id'],True

def apply(number,target,pin):
    path=r.RUN/'batches'/f'batch-{number:03d}.json';raw=path.read_bytes();assert core.sha(raw)==pin,'Plan changed'
    plan_data=json.loads(raw);items={x['record']['qid']:x for x in plan_data['entries']}
    assert (r.BACKUPS/'local-before.dump').stat().st_size>0
    assert json.loads((r.BACKUPS/'production-managed-backup.json').read_text())['status']=='SUCCESSFUL'
    assert (r.RUN/'quality-review.json').exists(),'Review preparation and sample images before application'
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    # Conditional image uploads complete before database references are committed.
    for state in plan_data['targets'][target]:
        im=items[state['qid']]['image']
        if state['action']=='deferred' or not im:continue
        data=(r.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(data)==im['sha256'] and len(data)<=100000
        blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata={'sha256':im['sha256'],'license':im['license_label'],'wikidata':state['qid']};blob.cache_control='public,max-age=31536000,immutable'
            blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0)
        blob.reload();assert blob.size==len(data) and blob.md5_hash==base64.b64encode(__import__('hashlib').md5(data).digest()).decode()
    counts={'new_artworks':0,'new_artists':0,'images_attached':0,'existing_enriched':0,'deferred':0,'already_applied':0}
    with r.base.connect(target=='production') as db:
        with db.transaction():
            sid=source(db,SOURCE_SLUG,SOURCE_NAME,'authority_data','https://www.wikidata.org/')
            commons=source(db,IMAGE_SOURCE_SLUG,'Wikimedia Commons — selected catalogue images','collection_page','https://commons.wikimedia.org/')
        for state in plan_data['targets'][target]:
            qid=state['qid'];receiptpath=r.RUN/'applied'/target/(qid+'.json')
            if receiptpath.exists():counts['already_applied']+=1;continue
            if state['action']=='deferred':counts['deferred']+=1;continue
            item=items[qid];record=item['record'];im=item['image'];aid=state['artwork_id'];new_artist=False;attached=False
            with db.transaction(), db.pipeline():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='45s'")
                db.execute('SELECT pg_advisory_xact_lock(%s)',(559220260914,))
                authority=db.execute("SELECT entity_id::text,entity_type FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(qid,)).fetchone()
                if authority:
                    assert authority['entity_id']==aid and authority['entity_type']=='artwork','Concurrent identity conflict'
                    current=db.execute("SELECT primary_media_id::text,status FROM artworks WHERE id=%s AND EXISTS(SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='wikimedia_catalogue_research')",(aid,aid,sid)).fetchone()
                    assert current,'Existing authority is not a committed record from this research'
                    recovered={'at':core.now(),'batch':number,'plan_sha256':pin,'target':target,'qid':qid,'artwork_id':aid,'action':state['action'],'new_artist':False,'artist_id':state['artist_id'],'image_attached':bool(im and current['primary_media_id']==uid('image/'+qid+'/'+im['sha256'])),'media_id':current['primary_media_id'],'status':current['status'],'receipt_recovered_after_commit':True}
                    core.save_new(receiptpath,recovered)
                    counts['already_applied']+=1
                    continue
                if state.get('new_institution'):
                    inst=state['new_institution']
                    db.execute("INSERT INTO institutions(id,slug,name,normalized_name,website_url,wikidata_id,kind,status,description) VALUES(%s,%s,%s,%s,%s,%s,'museum','review','Museum identity documented by Wikipedia and Wikidata. Current display and visitor access are not asserted.') ON CONFLICT(slug) DO NOTHING",(inst['id'],inst['slug'],inst['name'],r.norm(inst['name']),inst['website_url'],inst['wikidata_id']))
                    actual=db.execute('SELECT id::text FROM institutions WHERE slug=%s',(inst['slug'],)).fetchone();assert actual['id']==state['institution_id']
                db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,state['institution_id']))
                existing=None
                if state['action']=='existing':
                    existing=db.execute('SELECT id::text,slug,revision,primary_media_id::text,status,creation_year_start,creation_year_end FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone()
                    planned=state['existing'];assert existing and existing['slug']==planned['slug'] and existing['status']==planned['status'] and existing['revision']==planned['revision'] and existing['primary_media_id']==planned['primary_media_id'],'Existing record changed since review'
                artist=state['artist_id']
                if state['new_artist']:artist,new_artist=artist_insert(db,state['new_artist'],record,sid)
                media=None
                if im and (not existing or not existing['primary_media_id']):
                    eligible=not existing or (existing['creation_year_start'] is not None and existing['creation_year_end'] is not None and existing['creation_year_end']<=1970)
                    if eligible:
                        media=uid('image/'+qid+'/'+im['sha256'])
                        r.base.insert(db,'media_assets',dict(id=media,storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=record['title']+' — '+record['creator_label'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR))
                        r.base.insert(db,'media_rights_evidence',dict(media_id=media,source_id=commons,source_record_id=im['commons_page']['title'],source_checksum=im['commons_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis='Explicit per-file Commons licence; Wikidata P18 plus independent Commons artwork identity; original or source-thumbnail checksum; attribution retained.',adapter_version=VERSION,checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                        attached=True
                if state['action']=='new':
                    d=record['date'];collection=record['collection']['institution']['name']
                    catalogue='the reviewed primary museum catalogue' if record.get('primary_creator_review') else 'Wikidata'
                    description=f"{record['title']}, recorded by {catalogue} as a work by {record['creator_label']} connected with {collection}. Metadata remains in review."
                    work_type=record.get('work_type') or ('fresco' if 'Q22669139' in {v.get('id') for v in r.values(record['entity'],'P31') if isinstance(v,dict)} else 'painting')
                    assert work_type in ('painting','fresco','drawing','unknown'),'Source artwork type requires a dedicated adapter'
                    if work_type=='drawing':
                        assert record.get('primary_metadata_review',{}).get('override',{}).get('work_type')=='drawing','Drawing requires an explicitly reviewed primary type correction'
                    r.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+qid.lower(),title=record['title'],normalized_title=r.norm(record['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=work_type,object_form=record.get('source_form'),medium_text=record.get('primary_medium_text'),dimensions_text=record.get('primary_dimensions_text'),description_md=description,current_institution_id=state['institution_id'],current_location_text=collection,location_checked_at=record['entity_receipt']['retrieved_at'],accession_number=record['accession'],primary_media_id=media,status='review',created_by=ACTOR,updated_by=ACTOR,unlinked_creator_label=None if artist else record['creator_label'],research_candidate=d['precision']=='unknown'))
                    if artist:r.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist,attribution_role='primary',attribution_note='Individually reviewed primary museum object and creator identity; superseded secondary creator assertion retained in citation evidence.' if record.get('primary_creator_review') else 'Unqualified Wikidata P170 creator statement; source evidence retained for editorial review.'))
                    r.base.insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=state['institution_id'],context='collection',source_id=sid,source_url='https://www.wikidata.org/wiki/'+qid,evidence_note='Wikidata best-ranked, non-expired P195 collection statement. Institution identity matched through official website or Muséofile ID. This records the documented museum connection, not present display, ownership or visitor access.',checked_at=record['entity_receipt']['retrieved_at'],review_state='accepted'))
                elif media:db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(media,ACTOR,aid))
                if media:r.base.insert(db,'artwork_media',dict(artwork_id=aid,media_id=media,sort_order=0,view_label='Selected reproduction'))
                r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=qid,canonical_url='https://www.wikidata.org/wiki/'+qid,source_id=sid,retrieved_at=record['entity_receipt']['retrieved_at']))
                r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='wikimedia_catalogue_research',source_id=sid,source_record_id=qid,source_url='https://www.wikidata.org/wiki/'+qid,evidence_note=('Original Wikidata CC0 object identity, collection and source assertions preserved. Secondary creator superseded by separately cited primary museum review. Entity capture SHA-256: ' if record.get('primary_creator_review') else 'Wikidata CC0 identity, unqualified creator, collection and source date evidence. Existing catalogue titles, attribution and dating preserved. Entity capture SHA-256: ')+record['entity_receipt']['sha256'],retrieved_at=record['entity_receipt']['retrieved_at'],created_by=ACTOR))
                if record.get('primary_creator_review'):
                    ev=record['primary_creator_review'];primary=ev['source'];primary_sid=source(db,SOURCE_SLUG+'-primary-creators','Individually reviewed primary museum creator corrections','collection_page',primary['receipt']['url'])
                    r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='primary_creator_review',source_id=primary_sid,source_record_id=qid,source_url=primary['receipt']['url'],evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=primary['receipt']['retrieved_at'],created_by=ACTOR))
                if record.get('primary_metadata_review'):
                    ev=record['primary_metadata_review'];primary=ev['source'];primary_sid=source(db,SOURCE_SLUG+'-primary-metadata','Selected museum primary metadata corrections','collection_page',primary['receipt']['url'])
                    r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='primary_metadata_review',source_id=primary_sid,source_record_id=qid,source_url=primary['receipt']['url'],evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=primary['receipt']['retrieved_at'],created_by=ACTOR))
                if record.get('primary_museum_review'):
                    ev=record['primary_museum_review'];primary_sid=source(db,'overnight-gulbenkian-primary-20260913','Gulbenkian CAM: exact primary object metadata','collection_page','https://gulbenkian.pt/cam/')
                    r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='primary_object_metadata_review',source_id=primary_sid,source_record_id=record['accession'],source_url=ev['receipt']['final_url'],retrieved_at=ev['receipt']['retrieved_at'],created_by=ACTOR,evidence_note=json.dumps(dict(primary_review=ev,application='Primary dates/materials/inventory apply to new records only. Existing nonempty catalogue fields retain their prior assertions.',review_status='review'),ensure_ascii=False)))
                article=record['entity'].get('sitelinks',{}).get('enwiki',{}).get('title')
                if article:r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='wikipedia_reference',source_id=sid,source_record_id=article,source_url='https://en.wikipedia.org/wiki/'+quote(article.replace(' ','_')),evidence_note='Wikidata links this artwork identity to this Wikipedia article. Article prose was not copied.',retrieved_at=record['entity_receipt']['retrieved_at'],created_by=ACTOR))
            outcome={'at':core.now(),'batch':number,'plan_sha256':pin,'target':target,'qid':qid,'artwork_id':aid,'action':state['action'],'new_artist':new_artist,'artist_id':artist,'image_attached':attached,'media_id':media,'status':'review' if state['action']=='new' else state['existing']['status']}
            core.save_new(receiptpath,outcome)
            counts['new_artworks' if state['action']=='new' else 'existing_enriched']+=1;counts['new_artists']+=int(new_artist);counts['images_attached']+=int(attached)
            print(target,qid,state['action'],'image',attached,flush=True)
    core.save_new(r.RUN/'batch-results'/f'{number:03d}-{target}.json',{'at':core.now(),'counts':counts,'plan_sha256':pin})
    print(target,counts,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--batch',type=int,required=True);p.add_argument('--limit',type=int,default=100);p.add_argument('--target',choices=['local','production']);p.add_argument('--sha256');a=p.parse_args()
    plan(a.batch,a.limit) if a.phase=='plan' else apply(a.batch,a.target,a.sha256)
