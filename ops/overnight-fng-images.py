#!/usr/bin/env python3
"""Verify FNG holdings and attach exact CC0 images to existing review artworks.

Uses the museum's documented anonymous metadata export, never an API-key bypass.
Only exact FNG object/person identities and consistent source facts are accepted.
The holding assertion is source-validated; editorial/publication state is retained.
"""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,re,time,unicodedata,uuid
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng_core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.VERSION='overnight-fng-exact-cc0-v1'
core.PROVIDERS['night-fng']='Finnish National Gallery'
core.HOSTS.add('kokoelma.kansallisgalleria.fi')
LICENCE='https://creativecommons.org/publicdomain/zero/1.0/'
ORG={'Kansallisgalleria / Ateneumin taidemuseo','Kansallisgalleria / Sinebrychoffin taidemuseo'}
def norm(v):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',str(v).casefold())))

def source_match(c,o):
    if str(o['objectId'])!=c['external_id']:raise ValueError('FNG object mismatch')
    if o.get('responsibleOrganisation') not in ORG:raise ValueError('Holding organisation not verified')
    if not (o.get('owner') or '').startswith('Suomen valtio'):raise ValueError('Loan or owner requires separate holding review')
    if o.get('category',{}).get('categoryId')!='artwork' or o.get('children') or o.get('parents'):raise ValueError('Multipart work requires individual review')
    kind=c.get('work_type','painting')
    classifications={x.get('en','').casefold() for x in o.get('classifications',[])}
    materials={x.get('en','').casefold() for x in o.get('materials',[])}
    print_media={'etching','drypoint','lithograph','lithography','woodcut','engraving','aquatint','mezzotint','monotype','linocut','screen print','serigraphy'}
    classified=kind in classifications or (kind=='print' and 'graphic arts' in classifications and bool(materials & print_media))
    if kind not in ('painting','drawing','print') or not classified:raise ValueError('Current FNG classification differs from selected work type')
    if norm(c['title']) not in {norm(v) for v in o.get('title',{}).values() if v}:raise ValueError('FNG title mismatch')
    if not c.get('accession_number') or norm(c['accession_number'])!=norm(o.get('inventoryNumber')):raise ValueError('FNG accession mismatch')
    people=[p for p in o.get('people',[]) if p.get('role',{}).get('en')=='Artist']
    if len(people)!=1 or people[0].get('attribution'):raise ValueError('Qualified or multiple source creators need review')
    p=people[0]
    if c['fng_people']!=[str(p['id'])] or c['roles']!=['primary']:raise ValueError('Exact FNG artist authority not matched')
    lo=o.get('yearFrom');hi=o.get('yearTo') or lo
    if not isinstance(lo,int) or not isinstance(hi,int) or not 1000<=lo<=hi<=1970:raise ValueError('Current date outside scope or unknown')
    if lo!=c['creation_year_start'] or hi!=c['creation_year_end']:raise ValueError('Current FNG date differs')
    prefix=(o.get('datePrefix') or {}).get('en')
    if prefix not in (None,'','circa'):raise ValueError('Open-ended source date needs review')
    precision=('circa' if lo==hi else 'circa_range') if prefix=='circa' else ('exact' if lo==hi else 'range')
    if c['date_precision']!=precision:raise ValueError('Date precision mismatch')
    if lo!=hi and lo==p.get('birthYear') and hi==p.get('deathYear'):raise ValueError('Creation interval repeats creator lifespan; requires review')
    images=[i for i in o.get('multimedia',[]) if i.get('isRiaDisplayImage') and i.get('license')=='CC0']
    if len(images)!=1:raise ValueError('No unique preferred CC0 reproduction')
    im=images[0];url=im.get('jpg',{}).get('1000')
    if not url or not re.fullmatch(r'/media-assets/\d+/jpg/1000/[\w.-]+',url):raise ValueError('Unexpected museum image path')
    return im,'https://kokoelma.kansallisgalleria.fi'+url

QUERY='''SELECT a.id::text artwork_id,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,
 a.work_type,a.status,a.research_candidate,a.accession_number,a.primary_media_id::text,a.current_institution_id::text,e.external_id,e.source_id::text,
 COALESCE((SELECT jsonb_agg(DISTINCT p.external_id ORDER BY p.external_id) FROM artwork_artists aa JOIN external_identifiers p ON p.entity_type='artist' AND p.entity_id=aa.artist_id AND p.scheme='fng-person' WHERE aa.artwork_id=a.id),'[]') fng_people,
 COALESCE((SELECT jsonb_agg(aa.attribution_role ORDER BY aa.attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') roles,
 (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
 EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
 WHERE e.entity_type='artwork' AND e.scheme='fng-object' AND a.status='review' AND a.work_type IN ('painting','drawing','print')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' '''

def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    raw=(run/'objects-current.json').read_bytes();receipt=json.loads((run/'objects-current.receipt.json').read_text())
    if core.sha(raw)!=receipt['sha256']:raise ValueError('Museum export checksum mismatch')
    objects={str(o['objectId']):o for o in json.loads(raw)};held=[];prepared=[]
    with ro('postgres://localhost/artline') as db:
        rows=db.execute(QUERY+' AND a.primary_media_id IS NULL ORDER BY popular DESC,a.id').fetchall()
    for c in rows:
        o=objects.get(c['external_id'])
        if not o:held.append({'id':c['artwork_id'],'reason':'Object absent from current public museum export'});continue
        try:im,url=source_match(c,o)
        except ValueError as error:held.append({'id':c['artwork_id'],'reason':str(error)});continue
        credit=c['artist']+'; Finnish National Gallery'
        if im.get('photographer_name'):credit+='; photograph: '+im['photographer_name']
        facts={k:o.get(k) for k in ('objectId','responsibleOrganisation','owner','title','yearFrom','yearTo','datePrefix','category','classifications','inventoryNumber','people','children','parents')}
        facts['multimedia']=[im]
        prepared.append(dict(c,provider='night-fng',scheme='fng-object',source_image_url=url,page='https://kokoelma.kansallisgalleria.fi/en/object/'+c['external_id'],
          raw={'object':facts,'metadata_capture':receipt},policy_url=LICENCE,rights_status='cc0',license_label='CC0 1.0',checked_at=core.now(),
          creator_credit=credit,attribution_text=f"{c['artist']}. {c['title']}. {credit}. CC0 ({LICENCE}). Full-frame proportional resize and JPEG compression.",
          source_name='Finnish National Gallery',image_url=url,image_license='CC0 1.0',image_license_url=LICENCE,rights_statement='CC0',creator=c['artist'],
          creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=core.now(),target_ids={'local':c['artwork_id']}))
    with ro(dsn) as db:
        remote=db.execute(QUERY+' AND e.external_id=ANY(%s)',([c['external_id'] for c in prepared],)).fetchall()
        index=collections.defaultdict(list)
        for r in remote:index[r['external_id']].append(r)
        accepted=[]
        for c in prepared:
            matches=index[c['external_id']]
            if len(matches)!=1 or any(matches[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','date_precision','fng_people','roles')):
                held.append({'id':c['artwork_id'],'reason':'Production identity needs review'});continue
            if matches[0]['primary_media_id']:continue
            c['target_ids']['cloud']=matches[0]['artwork_id'];c['source_record_url']=c['page'];accepted.append(c)
    for target,conn in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(conn) as db:
            inst=db.execute("SELECT id::text,slug,wikidata_id FROM institutions WHERE wikidata_id='Q2983474' AND status<>'archived'").fetchall()
            if len(inst)!=1:raise ValueError('Existing FNG institution missing or ambiguous')
            for c in accepted:c.setdefault('institution_ids',{})[target]=inst[0]['id']
            rows=db.execute('''SELECT to_jsonb(a) artwork,
              (SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
              (SELECT jsonb_agg(to_jsonb(la)) FROM artwork_location_assertions la WHERE la.artwork_id=a.id) assertions
              FROM artworks a WHERE a.id=ANY(%s::uuid[])''',([c['target_ids'][target] for c in accepted],)).fetchall()
            core.save_new(run/(target+'-before.json'),rows)
    for c in accepted:core.save_new(run/'selected/night-fng'/(c['artwork_id']+'.json'),c)
    core.save_new(path,{'created_at':core.now(),'candidates':accepted});core.save_new(run/'held.json',held)
    print('FNG selected',len(accepted),'held',len(held),'reasons',dict(collections.Counter(x['reason'] for x in held)),flush=True)
    return accepted

original_attach=core.attach
def attach(db,im,target):
    source_match(im,im['raw']['object'])
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('FNG target identity changed')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','creation_year_start','creation_year_end','date_precision','fng_people','roles')):raise ValueError('FNG target facts changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        iid=im['institution_ids'][target]
        if row['current_institution_id'] not in (None,iid):raise ValueError('Existing holding differs; preserve for review')
        current=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(row['artwork_id'],)).fetchall()
        if current and (len(current)!=1 or current[0]['institution_id']!=iid):raise ValueError('Existing holding assertion conflicts')
        if not current:
            db.execute('''INSERT INTO sources(slug,name,source_type,base_url,terms_url)
              VALUES('overnight-fng-primary-images-20260915','Finnish National Gallery: independently verified collection records and CC0 images','museum_api',
                'https://kokoelma.kansallisgalleria.fi/api/v1/objects',%s) ON CONFLICT(slug) DO NOTHING''',(LICENCE,))
            sid=db.execute("SELECT id FROM sources WHERE slug='overnight-fng-primary-images-20260915'").fetchone()['id']
            oid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/verified-fng-holding/'+im['external_id']))
            db.execute('''INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
              VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted') ON CONFLICT(id) DO NOTHING''',
              (oid,row['artwork_id'],iid,sid,im['page'],'Current official FNG export identifies '+im['raw']['object']['responsibleOrganisation']+
               ' as responsible collection; exact object ID '+im['external_id']+', inventory '+im['accession_number']+', source person ID, title and creation interval agree. Holding evidence only; current display is not asserted.',im['checked_at']))
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--select-only',action='store_true');p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Recovery backup manifest required')
    if a.prepare_only and not (a.run/'candidates.json').exists():raise SystemExit('Preparation requires reviewed candidate manifest')
    if not a.prepare_only and (a.run/'candidates.json').exists() and json.loads((a.run/'candidates.json').read_text()).get('production_metadata_pending'):raise SystemExit('Production metadata import and target reconciliation required before uploading this expansion')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=select(a.run,dsn)
    if a.select_only:return
    done=set()
    done={key for key,r in core.latest_events(a.run).items() if r.get('outcome') in (('complete','failed','prepared') if a.prepare_only else ('complete','failed'))}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    for start in range(0,len(rows),100):
        if time.time()>=a.deadline:break
        group=rows[start:start+100]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-fng',group[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if group[n::3]]
            for job in jobs:job.result()
        print(core.now(),'FNG',dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
