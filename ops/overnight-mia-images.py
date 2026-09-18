#!/usr/bin/env python3
"""Select existing Mia paintings using current factual records and exact PDM media."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,re,time,uuid
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('mia_helpers',ROOT/'ops/overnight-fsg-images.py');helpers=importlib.util.module_from_spec(s);s.loader.exec_module(helpers)
core=helpers.core;core.VERSION='overnight-mia-explicit-pdm-v1';core.PROVIDERS['night-mia']='Minneapolis Institute of Art'
core.HOSTS.update({'search.artsmia.org','img.artsmia.org','new.artsmia.org','collections.artsmia.org'})
norm=helpers.norm;ro=helpers.ro
CC0=helpers.CC0;PDM='https://creativecommons.org/publicdomain/mark/1.0/'
NAME='Minneapolis Institute of Art';SLUG='minneapolis-institute-of-art';WEBSITE='https://new.artsmia.org/'
INSTITUTION_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,WEBSITE));PLACE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/place/minneapolis-us'))
POLICY='https://new.artsmia.org/copyright-and-image-access';VISIT='https://new.artsmia.org/visit'
SOURCE='overnight-mia-primary-images-20260915'
QUERY=helpers.QUERY.replace("e.scheme='fsg-object'","e.scheme='mia-object'")

def creator_name(value,work_type):
    parts=[p.strip() for p in (value or '').split(';')]
    if len(parts)>1:
        if work_type!='print' or any(not re.fullmatch(r'(?:Publisher|Printer|Author):\s*\S.*',p) for p in parts[1:]):raise ValueError('Multiple or unclear visual creator roles require review')
    name=re.sub(r'^(?:Artist|Painter):\s*','',parts[0]).strip()
    if work_type=='print':name=re.sub(r'\s*\(self-published\)$','',name)
    if not name or ':' in name:raise ValueError('Primary visual creator role is not established')
    return name

def source_match(c,o):
    if str(o.get('id'))!=c['external_id']:raise ValueError('Museum object ID differs')
    if norm(o.get('title'))!=norm(c['title']):raise ValueError('Museum title differs')
    if o.get('classification','').strip()!={'painting':'Paintings','drawing':'Drawings','print':'Prints'}.get(c['work_type']):raise ValueError('Museum classification differs')
    if o.get('accession_number')!=c['accession_number'] or not c['accession_number']:raise ValueError('Accession identity differs')
    if re.match(r'^L',c['accession_number'],re.I) or re.search(r'\b(loan|lent by|private collection|deaccession)\b',o.get('creditline') or '',re.I):raise ValueError('Loan or collection holding requires separate review')
    primary=creator_name(o.get('artist'),c['work_type'])
    names={norm(re.sub(r'^(?:Artist|Painter):\s*','',x)) for x in [c['artist']]+c['aliases']}
    if c['roles']!=['primary'] or norm(primary) not in names:raise ValueError('Unique exact existing creator differs')
    if re.search(r'\b(attributed|after|workshop|school|follower|circle|possibly|probably|anonymous)\b',o.get('artist') or '',re.I):raise ValueError('Qualified source attribution needs review')
    lo,hi,precision=helpers.date_parts(o.get('dated') or '')
    if (lo,hi,precision)!=(c['creation_year_start'],c['creation_year_end'],c['date_precision']):raise ValueError('Museum date normalization differs')
    if lo!=hi and re.search(r'\b'+str(lo)+r'\s*[-–—]\s*'+str(hi)+r'\b',o.get('life_date') or ''):raise ValueError('Creator lifespan cannot establish artwork date')
    if o.get('rights_type')!='Public Domain' or o.get('restricted') not in (None,0) or o.get('image_copyright'):raise ValueError('Exact image rights are missing, conflicting, or outside PDM')
    if o.get('image')!='valid' or o.get('public_access')!=1 or o.get('Rights_Image_Display')!='Full':raise ValueError('Public full image access is not established')
    location=(o.get('Cache_Location') or '').replace('\\','/');rendition=o.get('Primary_RenditionNumber') or ''
    if not re.fullmatch(r'\d+(?:/\d+)*',location) or location.split('/')[-1]!=c['external_id'] or not re.fullmatch(r'[A-Za-z0-9_-]+\.jpg',rendition):raise ValueError('Exact image resource mapping is unavailable')
    url='https://img.artsmia.org/web_objects_cache/'+location+'/'+rendition[:-4]+'_800.jpg'
    return url,{'source_year_start':lo,'source_year_end':hi,'source_date_text':o['dated'],'source_creator':o['artist'],'metadata_license':CC0}

def capture_policy(run):
    records=json.loads((run/'reviewed-public-policy-evidence.json').read_text())
    client=json.loads((run/'client-resource-evidence.json').read_text())
    assert client['official_client_url']=='https://collections.artsmia.org/bundle.js'
    assert PDM in client['public_domain_mapping'] and 'Public Domain' in client['public_domain_mapping']
    assert 'https://img.artsmia.org/web_objects_cache/' in client['public_image_url_construction']
    assert records['rights']['url']==POLICY and records['rights']['facts']['exact_license_uri']==PDM
    assert records['institution']['url']==VISIT and records['institution']['facts']['name']==NAME
    assert records['metadata']['facts']['metadata_license']==CC0
    return records

def research(run,limit,deadline):
    policy=capture_policy(run)
    with ro('postgres://localhost/artline') as db:rows=db.execute(QUERY+" AND a.work_type='painting' AND a.primary_media_id IS NULL ORDER BY popular DESC,a.id").fetchall()
    def stripe(items):
        f=core.Fetcher(run/'metadata/night-mia');counts=collections.Counter()
        for c in items:
            if time.time()>=deadline:break
            path=run/'verified'/(c['external_id']+'.json');held=run/'held'/(c['external_id']+'.json')
            if path.exists() or held.exists():continue
            try:
                api='https://search.artsmia.org/id/'+c['external_id'];o=f.metadata(api);image,facts=source_match(c,o)
                page='https://collections.artsmia.org/art/'+c['external_id'];checked=core.now();credit=c['artist']+'; '+NAME+'; '+(o.get('creditline') or '')
                # Only source facts needed for identity, scope, rights, and provenance.
                keys=('id','title','classification','object_name','accession_number','artist','dated','life_date','medium','country','nationality','creditline','rights_type','restricted','image_copyright','image','public_access','Rights_Image_Display','Cache_Location','Primary_RenditionNumber','image_width','image_height')
                raw={'object':{k:o[k] for k in keys if k in o},'metadata_capture':json.loads((f.cache/(core.sha(api.encode())+'.receipt.json')).read_text()),'policy_captures':policy,'image_mapping_evidence':json.loads((run/'client-resource-evidence.json').read_text())}
                im=dict(c,provider='night-mia',scheme='mia-object',target_ids={'local':c['artwork_id']},institution_ids={'local':INSTITUTION_ID},source_image_url=image,page=page,raw=raw,scope_evidence=facts,policy_url=PDM,rights_status='public_domain',license_label='Public Domain Mark 1.0',checked_at=checked,creator_credit=credit,
                  attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. Public Domain Mark 1.0 ('+PDM+'). Full-frame proportional resize and JPEG compression.',
                  source_name=NAME,source_record_url=page,image_url=image,image_license='Public Domain Mark 1.0',image_license_url=PDM,rights_statement='Public Domain',creator=c['artist'],creation_date=o['dated'],source_object_id=c['external_id'],rights_verified_at=checked,metadata_license=CC0)
                core.save_new(path,im);counts['verified']+=1
            except ValueError as exc:core.save_new(held,{'at':core.now(),'source_object_id':c['external_id'],'reason':str(exc)});counts['held']+=1
            except Exception as exc:
                with core.LOCK:
                    with (run/'research-errors.jsonl').open('a') as out:out.write(json.dumps({'at':core.now(),'source_object_id':c['external_id'],'error':str(exc)[:240]})+'\n')
                counts['retryable_error']+=1
            if sum(counts.values())%25==0:print(core.now(),'Mia source review',dict(counts),flush=True)
        return counts
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=[j.result() for j in [pool.submit(stripe,rows[:limit][n::3]) for n in range(3)]]
    print(core.now(),'Mia research complete',dict(sum(results,collections.Counter())),flush=True)

def institution(run):
    receipts=capture_policy(run);backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/mia';results=[]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                before=db.execute("SELECT to_jsonb(i) institution FROM institutions i WHERE slug=%s OR website_url=%s OR name ILIKE '%%Minneapolis%%'",(SLUG,WEBSITE)).fetchall()
                path=backup/(target+'-institution-before.json')
                if not path.exists():core.save_new(path,before)
                assert not before or (len(before)==1 and before[0]['institution']['id']==INSTITUTION_ID),'Museum identity needs reconciliation'
                places=db.execute("SELECT id::text FROM places WHERE normalized_name='minneapolis' AND country_code='US'").fetchall()
                assert len(places)<=1
                pid=places[0]['id'] if places else PLACE_ID
                if not places:db.execute("INSERT INTO places(id,name,normalized_name,country_code) VALUES(%s,'Minneapolis','minneapolis','US')",(pid,))
                db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Minneapolis Institute of Art: current public object records and PDM images','museum_api','https://search.artsmia.org/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,POLICY));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
                db.execute("INSERT INTO institutions(id,slug,name,normalized_name,kind,status,website_url,place_id) VALUES(%s,%s,%s,'minneapolis institute of art','museum','review',%s,%s) ON CONFLICT(id) DO NOTHING",(INSTITUTION_ID,SLUG,NAME,WEBSITE,pid))
                check=db.execute('SELECT name,slug,website_url,place_id::text FROM institutions WHERE id=%s',(INSTITUTION_ID,)).fetchone();assert check=={'name':NAME,'slug':SLUG,'website_url':WEBSITE,'place_id':pid}
                if not db.execute("SELECT 1 FROM citations WHERE entity_type='institution' AND entity_id=%s AND source_id=%s",(INSTITUTION_ID,sid)).fetchone():db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at) VALUES('institution',%s,%s,'identity_and_location',%s,%s,%s)",(INSTITUTION_ID,sid,VISIT,json.dumps({'address':'2400 Third Avenue South, Minneapolis, Minnesota 55404, United States','source_capture':receipts['institution'],'note':'Holding institution geography; no inference about painter nationality or display.'}),core.now()))
            results.append({'target':target,'institution_id':INSTITUTION_ID});print(target,'Mia institution verified',flush=True)
    path=run/'institution-verified.json'
    if not path.exists():core.save_new(path,results)

original_attach=helpers.original_attach

def attach(db,im,target):
    url,_=source_match(im,im['raw']['object']);assert url==im['source_image_url']
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('Mia target identity changed')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','artist_slugs','roles')):raise ValueError('Mia target facts changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        iid=im['institution_ids'][target]
        if iid!=INSTITUTION_ID or row['current_institution_id'] not in (None,iid):raise ValueError('Holding institution differs')
        current=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(row['artwork_id'],)).fetchall()
        if current and (len(current)!=1 or current[0]['institution_id']!=iid):raise ValueError('Holding assertion conflicts')
        if not current:
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted') ON CONFLICT(id) DO NOTHING",(str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/verified-mia-holding/'+im['external_id'])),row['artwork_id'],iid,sid,im['page'],'Current public Mia catalogue explicitly identifies this object, accession, creator, title and creation date; collection holding only, not currently on view.',im['checked_at']))
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def prepare(run,limit,deadline):
    assert (run/'institution-verified.json').exists()
    candidate_path=run/'candidates.json'
    rows=json.loads(candidate_path.read_text())['candidates'] if candidate_path.exists() else [json.loads(p.read_text()) for p in (run/'verified').glob('*.json')]
    rows.sort(key=lambda c:(not c['popular'],c['work_type']!='painting',c['artwork_id']))
    for c in rows:
        source_match(c,c['raw']['object']);core.save_new(run/'selected/night-mia'/(c['artwork_id']+'.json'),c)
    path=run/'candidates.json'
    if not path.exists():core.save_new(path,{'created_at':core.now(),'candidates':rows})
    done={k for k,v in core.latest_events(run).items() if v['outcome'] in ('complete','prepared','failed')};todo=[c for c in rows if c['artwork_id'] not in done][:limit]
    for start in range(0,len(todo),50):
        if time.time()>=deadline:break
        group=todo[start:start+50]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for job in [pool.submit(core.worker,'night-mia',group[n::3],SimpleNamespace(run=run,prepare_only=True),None) for n in range(3)]:job.result()
        print(core.now(),'Mia image preparation',dict(core.COUNTS),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','institution','prepare']);p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=1000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    assert (a.run.parent/'backups.json').exists();lock=(a.run/(a.phase+'.lock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if a.phase=='research':research(a.run,a.limit,a.deadline)
    elif a.phase=='institution':institution(a.run)
    else:prepare(a.run,a.limit,a.deadline)
