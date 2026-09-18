#!/usr/bin/env python3
"""Attach individually CC0 Smithsonian images to exact existing painting records."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,re,time,unicodedata,uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse,parse_qs
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('saam_core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.VERSION='overnight-saam-explicit-cc0-v1';core.PROVIDERS['night-saam']='Smithsonian American Art Museum';core.HOSTS.add('ids.si.edu')
CC0='https://creativecommons.org/publicdomain/zero/1.0/';INSTITUTION_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://americanart.si.edu/'))
def norm(v):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',str(v).casefold())))
def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')
QUERY="""SELECT a.id::text artwork_id,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,
 a.work_type,a.status,a.research_candidate,a.accession_number,a.primary_media_id::text,a.current_institution_id::text,e.external_id,e.source_id::text,
 COALESCE((SELECT jsonb_agg(aa.attribution_role ORDER BY aa.attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') roles,
 (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
 COALESCE((SELECT jsonb_agg(al.alias) FROM artwork_artists aa JOIN artist_aliases al ON al.artist_id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') aliases,
 (SELECT jsonb_agg(p.slug ORDER BY p.slug) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist_slugs,
 EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
 WHERE e.entity_type='artwork' AND e.scheme='saam-object' AND a.status='review' AND a.work_type IN ('painting','drawing','print')
 AND a.creation_year_start>=1000 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' """
def fields(ft,name,label=None):return [x['content'] for x in ft.get(name,[]) if x.get('content') and (label is None or x.get('label')==label)]
def source_match(c,o):
    d=o.get('content',{});dnr=d.get('descriptiveNonRepeating',{});ft=d.get('freetext',{});url=dnr.get('record_link','')
    if o.get('unitCode')!='SAAM' or dnr.get('data_source')!='Smithsonian American Art Museum':raise ValueError('Holding institution unverified')
    if not url.startswith('https://americanart.si.edu/') or parse_qs(urlparse(url).query).get('id')!=[c['external_id']]:raise ValueError('Museum object ID differs')
    if dnr.get('metadata_usage',{}).get('access')!='CC0':raise ValueError('Metadata terms not CC0')
    allowed={'painting':(['Painting'],['Painting-Miniature']),'drawing':(['Drawing'],),'print':(['Graphic Arts-Print'],)}
    if fields(ft,'objectType','Type') not in allowed.get(c.get('work_type','painting'),()):raise ValueError('Source classification differs')
    if norm(dnr.get('title',{}).get('content'))!=norm(c['title']):raise ValueError('Source title differs')
    if not c['accession_number'] or fields(ft,'identifier','Object number')!=[c['accession_number']]:raise ValueError('Source accession differs')
    names=fields(ft,'name','Artist')
    if len(names)!=1 or c['roles']!=['primary']:raise ValueError('Single primary maker not verified')
    name=re.split(r', (?:born|died|active|ca\.)',names[0],maxsplit=1)[0]
    if norm(name) not in {norm(x) for x in [c['artist']]+c['aliases']}:raise ValueError('Current museum artist differs')
    if re.search(r'\b(attributed|after|workshop|school|follower|circle|possibly|probably|anonymous)\b',name,re.I):raise ValueError('Qualified attribution requires review')
    dates=fields(ft,'date','Date')
    if len(dates)!=1:raise ValueError('Creation date not unique')
    match=re.fullmatch(r'\s*(?P<approx>(?:ca\.|c\.|circa|about)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}|\d{2}))?\s*',dates[0],re.I)
    if not match:raise ValueError('Date wording requires review')
    lo=int(match['lo']);end=match['hi'] or match['lo'];hi=int(str(lo)[:2]+end) if len(end)==2 else int(end)
    precision=('circa' if lo==hi else 'circa_range') if match['approx'] else ('exact' if lo==hi else 'range')
    if not 1000<=lo<=hi<=1970 or (lo,hi,precision)!=(c['creation_year_start'],c['creation_year_end'],c['date_precision']):raise ValueError('Date normalization differs')
    if re.search(r'\b'+str(lo)+r'\s*[-–—]\s*(?:died\s+[^0-9]*)?'+str(hi)+r'\b',names[0]) and lo!=hi:raise ValueError('Possible creator-lifespan date needs review')
    if fields(ft,'objectRights','Restrictions & Rights')!=['CC0']:raise ValueError('Object rights not explicitly CC0')
    if not any('Smithsonian American Art Museum Collection'==x for x in fields(ft,'setName','See more items in')):raise ValueError('Collection membership missing')
    media=dnr.get('online_media',{}).get('media',[])
    if len(media)!=1:raise ValueError('Multiple or absent source images require view selection')
    im=media[0]
    if im.get('type')!='Images' or im.get('usage',{}).get('access')!='CC0':raise ValueError('Exact image is not explicitly CC0')
    image=im.get('content','');parts=urlparse(image)
    if parts.scheme!='https' or parts.hostname!='ids.si.edu' or parts.path!='/ids/deliveryService' or parse_qs(parts.query).get('id')!=[im.get('idsId')] or not im.get('idsId','').startswith('SAAM-'):raise ValueError('Unverified image delivery identity')
    return im,image,{'source_year_start':lo,'source_year_end':hi,'source_date_text':dates[0],'source_creator':names[0]}

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    urls=(run/'index.txt').read_text().splitlines();objects={};receipts={}
    if len(urls)!=256:raise ValueError('Incomplete museum metadata directory index')
    for u in urls:
        p=run/'metadata'/u.rsplit('/',1)[-1];raw=p.read_bytes();receipt=json.loads(p.with_suffix('.receipt.json').read_text())
        if core.sha(raw)!=receipt['sha256'] or receipt['url']!=u:raise ValueError('Museum shard checksum mismatch')
        for line in raw.splitlines():
            o=json.loads(line);url=o.get('content',{}).get('descriptiveNonRepeating',{}).get('record_link','');oid=parse_qs(urlparse(url).query).get('id',[None])[0]
            if not oid:continue
            if oid in objects:raise ValueError('Duplicate museum object ID in current export')
            objects[oid]=o;receipts[oid]=receipt
    with ro('postgres://localhost/artline') as db:rows=db.execute(QUERY+' AND a.primary_media_id IS NULL ORDER BY popular DESC,a.id').fetchall()
    prepared=[];held=[]
    for c in rows:
        o=objects.get(c['external_id'])
        if not o:held.append({'id':c['artwork_id'],'reason':'Museum object absent from public export'});continue
        try:im,url,facts=source_match(c,o)
        except ValueError as e:held.append({'id':c['artwork_id'],'reason':str(e)});continue
        dnr=o['content']['descriptiveNonRepeating'];ft=o['content']['freetext'];page=dnr['record_link'];credit='; '.join(fields(ft,'creditLine'))
        if not credit:credit='Smithsonian American Art Museum'
        credit=c['artist']+'; '+credit;checked=core.now()
        prepared.append(dict(c,provider='night-saam',scheme='saam-object',target_ids={'local':c['artwork_id']},source_image_url=url,page=page,raw={'object':o,'metadata_capture':receipts[c['external_id']]},scope_evidence=facts,
          policy_url=CC0,rights_status='cc0',license_label='CC0 1.0',checked_at=checked,creator_credit=credit,
          attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. CC0 1.0 ('+CC0+'). Full-frame proportional resize and JPEG compression.',
          source_name='Smithsonian American Art Museum',source_record_url=page,image_url=url,image_license='CC0 1.0',image_license_url=CC0,rights_statement='CC0',creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=checked,metadata_license=CC0))
    with ro(dsn) as db:remote=db.execute(QUERY+' AND e.external_id=ANY(%s)',([c['external_id'] for c in prepared],)).fetchall()
    index=collections.defaultdict(list)
    for r in remote:index[r['external_id']].append(r)
    valid=[]
    for c in prepared:
        hits=index[c['external_id']]
        if len(hits)!=1 or any(hits[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','date_precision','artist_slugs','roles')):held.append({'id':c['artwork_id'],'reason':'Production identity differs'});continue
        if hits[0]['primary_media_id']:continue
        c['target_ids']['cloud']=hits[0]['artwork_id'];valid.append(c)
    for target,d in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(d) as db:
            existing=db.execute("SELECT id::text FROM institutions WHERE slug='smithsonian-american-art-museum' OR website_url='https://americanart.si.edu/'").fetchall()
            if len(existing)>1:raise ValueError('Institution identity ambiguous')
            place=db.execute("SELECT id::text FROM places WHERE name='Washington, DC' AND country_code='US'").fetchall()
            if len(place)!=1:raise ValueError('Verified museum place missing')
            for c in valid:c.setdefault('institution_ids',{})[target]=existing[0]['id'] if existing else INSTITUTION_ID;c.setdefault('place_ids',{})[target]=place[0]['id']
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.id=ANY(%s::uuid[])',([c['target_ids'][target] for c in valid],)).fetchall();core.save_new(run/(target+'-before.json'),before)
    for c in valid:core.save_new(run/'selected/night-saam'/(c['artwork_id']+'.json'),c)
    core.save_new(path,{'created_at':core.now(),'candidates':valid});core.save_new(run/'held.json',held)
    print('SAAM selected',len(valid),'held',len(held),'reasons',dict(collections.Counter(x['reason'] for x in held)),flush=True);return valid

original_attach=core.attach
def attach(db,im,target):
    source_match(im,im['raw']['object'])
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('SAAM target identity changed')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','creation_year_start','creation_year_end','date_precision','artist_slugs','roles')):raise ValueError('SAAM target facts changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        iid=im['institution_ids'][target]
        if row['current_institution_id'] not in (None,iid):raise ValueError('Existing holding differs')
        current=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(row['artwork_id'],)).fetchall()
        if current and (len(current)!=1 or current[0]['institution_id']!=iid):raise ValueError('Existing holding assertion conflicts')
        if not current:
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('overnight-saam-primary-images-20260915','Smithsonian American Art Museum: current public CC0 records and media','museum_api','https://americanart.si.edu/',%s) ON CONFLICT(slug) DO NOTHING",(CC0,))
            sid=db.execute("SELECT id FROM sources WHERE slug='overnight-saam-primary-images-20260915'").fetchone()['id']
            db.execute("INSERT INTO institutions(id,slug,name,normalized_name,kind,status,website_url,place_id) VALUES(%s,'smithsonian-american-art-museum','Smithsonian American Art Museum','smithsonian american art museum','museum','review','https://americanart.si.edu/',%s) ON CONFLICT(id) DO NOTHING",(iid,im['place_ids'][target]))
            institution=db.execute('SELECT name,website_url,place_id::text FROM institutions WHERE id=%s',(iid,)).fetchone()
            if institution['name']!='Smithsonian American Art Museum' or institution['website_url']!='https://americanart.si.edu/' or institution['place_id']!=im['place_ids'][target]:raise ValueError('SAAM institution identity conflict')
            if not db.execute("SELECT 1 FROM citations WHERE entity_type='institution' AND entity_id=%s AND source_id=%s",(iid,sid)).fetchone():
                db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at) VALUES('institution',%s,%s,'location','https://americanart.si.edu/visit/saam','Official visitor page: Smithsonian American Art Museum, 8th and G Streets NW, Washington DC 20004, United States. Museum geography does not establish artist nationality.',%s)",(iid,sid,im['checked_at']))
            oid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/verified-saam-holding/'+im['external_id']))
            db.execute("""INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
               VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted') ON CONFLICT(id) DO NOTHING""",
               (oid,row['artwork_id'],iid,sid,im['page'],'Current Smithsonian SAAM CC0 catalogue states collection membership, exact object ID '+im['external_id']+', inventory '+im['accession_number']+', creator, title and creation date agree. Holding only; current display not asserted.',im['checked_at']))
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists() or not (a.run/'institution.receipt.json').exists():raise SystemExit('Recovery backups and museum institution evidence required')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=select(a.run,dsn);done=set()
    done={key for key,r in core.latest_events(a.run).items() if r.get('outcome') in (('complete','failed','prepared') if a.prepare_only else ('complete','failed'))}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    for start in range(0,len(rows),100):
        if time.time()>=a.deadline:break
        group=rows[start:start+100]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-saam',group[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if group[n::3]]
            for job in jobs:job.result()
        print(core.now(),'SAAM',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
