#!/usr/bin/env python3
"""Verify existing Rijksmuseum paintings against current Linked Art and EDM records."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,re,time,unicodedata,uuid,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('rijks_core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.VERSION='overnight-rijks-primary-images-v1';core.PROVIDERS['night-rijks']='Rijksmuseum'
PDM='https://creativecommons.org/publicdomain/mark/1.0/';CC0='https://creativecommons.org/publicdomain/zero/1.0/'
def norm(v):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',str(v).casefold())))
def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')
QUERY="""SELECT a.id::text artwork_id,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,
 a.work_type,a.status,a.research_candidate,a.accession_number,a.primary_media_id::text,a.current_institution_id::text,e.external_id,e.source_id::text,
 COALESCE((SELECT jsonb_agg(DISTINCT p.external_id ORDER BY p.external_id) FROM artwork_artists aa JOIN external_identifiers p ON p.entity_type='artist' AND p.entity_id=aa.artist_id AND p.scheme='rijks-person' WHERE aa.artwork_id=a.id),'[]') rijks_people,
 COALESCE((SELECT jsonb_agg(aa.attribution_role ORDER BY aa.attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') roles,
 (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
 EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
 WHERE e.entity_type='artwork' AND e.scheme='rijks-object' AND a.status='review' AND a.work_type='painting'
 AND a.creation_year_start>=1000 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' """
def source_match(c,o):
    if o.get('id')!='https://id.rijksmuseum.nl/'+c['external_id'] or o.get('type')!='HumanMadeObject':raise ValueError('Source identity differs')
    if not any(x.get('id')=='http://vocab.getty.edu/aat/300033618' for k in o.get('classified_as',[]) for x in k.get('equivalent',[])):raise ValueError('Museum does not classify this as a painting')
    titles={norm(x.get('content')) for x in o.get('identified_by',[]) if x.get('type')=='Name'}
    if norm(c['title']) not in titles:raise ValueError('Museum title differs')
    accession={norm(x.get('content')) for x in o.get('identified_by',[]) if x.get('type')=='Identifier' and any(t.get('id')=='http://vocab.getty.edu/aat/300312355' for t in x.get('classified_as',[]))}
    if not c['accession_number'] or norm(c['accession_number']) not in accession:raise ValueError('Museum accession differs')
    production=o.get('produced_by',{});parts=production.get('part',[])
    if len(parts)!=1:raise ValueError('Multiple production parts require review')
    part=parts[0];people=part.get('carried_out_by',[])
    if len(people)!=1 or people[0].get('type')!='Person' or people[0].get('id','').rsplit('/',1)[-1:]!=c['rijks_people'] or c['roles']!=['primary']:raise ValueError('Exact single creator authority not matched')
    attribution=json.dumps([part,production.get('referred_to_by',[])],ensure_ascii=False)
    if re.search(r'\b(attributed|attribution|copy|copies|after|workshop|school|follower|circle|possibly|probably|anonymous|toegeschreven|kopie|naar|atelier|anoniem)\b',attribution,re.I):raise ValueError('Qualified attribution requires review')
    span=production.get('timespan',{})
    if not isinstance(span,dict):raise ValueError('Multiple creation intervals require review')
    lo=span.get('begin_of_the_begin','');hi=span.get('end_of_the_end','')
    if not re.match(r'^\d{4}-',lo) or not re.match(r'^\d{4}-',hi):raise ValueError('Museum date missing')
    lo,hi=int(lo[:4]),int(hi[:4])
    if not 1000<=lo<=hi<=1970 or (lo,hi)!=(c['creation_year_start'],c['creation_year_end']):raise ValueError('Museum dates differ or outside scope')
    date_names=[x.get('content','') for x in span.get('identified_by',[]) if x.get('type')=='Name']
    if not any(re.fullmatch(r'(?:(?:c\.|ca\.|circa|about)\s*)?\d{4}(?:\s*[-–—/]\s*\d{4})?',d,re.I) for d in date_names):raise ValueError('Unbounded or unsupported source date wording')
    rights={t.get('id') for x in o.get('subject_of',[]) if x.get('id')=='https://data.rijksmuseum.nl/'+c['external_id'] for r in x.get('subject_to',[]) for t in r.get('classified_as',[])}
    if rights!={CC0}:raise ValueError('Explicit metadata CC0 missing or conflicting')
    return {'source_year_start':lo,'source_year_end':hi,'source_date_text':date_names,'metadata_license':CC0}
def image_record(c,fetcher,_nga,_chicago):
    base='https://data.rijksmuseum.nl/'+c['external_id'];o=fetcher.metadata(base+'?_profile=la-framed');facts=source_match(c,o)
    xml=fetcher.xml(base+'?_profile=edm');image=core.rijks_edm(xml,c['external_id'],c['accession_number'])
    if not image:return None
    root=ET.fromstring(xml);rdf='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}';ns={'edm':'http://www.europeana.eu/schemas/edm/','ore':'http://www.openarchives.org/ore/terms/'}
    agg=root.find('ore:Aggregation',ns);provider=agg.find('edm:dataProvider',ns)
    if provider is None or provider.get(rdf+'resource')!='https://id.rijksmuseum.nl/2109266':raise ValueError('Source holding institution differs')
    page=agg.find('edm:isShownAt',ns).get(rdf+'resource','')
    if not page.startswith('https://www.rijksmuseum.nl/') or c['accession_number'] not in page:raise ValueError('Museum collection page not verified')
    credit=c['artist']+'; Rijksmuseum';checked=core.now()
    return dict(c,source_image_url=image['source_image_url'],page=page,raw={'object':{k:o.get(k) for k in ('id','type','identified_by','classified_as','produced_by','subject_of')},'edm':image},
       scope_evidence=facts,policy_url=PDM,rights_status='public_domain',license_label='Public Domain Mark 1.0',checked_at=checked,
       creator_credit=credit,attribution_text=c['artist']+'. '+c['title']+'. Rijksmuseum. Public Domain Mark 1.0 ('+PDM+'). Full-frame proportional resize and JPEG compression.',
       source_name='Rijksmuseum',source_record_url=page,image_url=image['source_image_url'],image_license='Public Domain Mark 1.0',image_license_url=PDM,
       rights_statement='Public Domain Mark 1.0',creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=checked,metadata_license=CC0)
def current_page_image(c,html,service):
    """Resolve a current, explicitly downloadable PDM image from public page data."""
    soup=BeautifulSoup(html,'html.parser');script=soup.find('script',id='__NUXT_DATA__')
    if script is None:raise ValueError('Current museum page has no structured object data')
    nodes=json.loads(script.get_text())
    def resolve(index,seen=()):
        if not isinstance(index,int) or isinstance(index,bool):return index
        if index<0:return None
        if index>=len(nodes) or index in seen:raise ValueError('Unreliable current-page reference mapping')
        value=nodes[index];trail=seen+(index,)
        if isinstance(value,dict):return {k:resolve(v,trail) for k,v in value.items()}
        if isinstance(value,list):return [resolve(v,trail) for v in value]
        return value
    objects=[resolve(n) for n,v in enumerate(nodes) if isinstance(v,dict) and 'objectNodeUri' in v and resolve(v['objectNodeUri'])=='https://id.rijksmuseum.nl/'+c['external_id']]
    if len(objects)!=1:raise ValueError('Current page object identity is not unique')
    o=objects[0]
    if o.get('objectNumber')!=c['accession_number'] or norm(o.get('title'))!=norm(c['title']):raise ValueError('Current page title or accession differs')
    def visit(value):
        if isinstance(value,dict):
            yield value
            for child in value.values():yield from visit(child)
        elif isinstance(value,list):
            for child in value:yield from visit(child)
    rights=[n.get('values') for n in visit(o.get('dataTab')) if n.get('name')=='Copyright']
    if len(rights)!=1 or len(rights[0])!=1:raise ValueError('Current image copyright missing or conflicting')
    link=BeautifulSoup(rights[0][0],'html.parser').find_all('a')
    if len(link)!=1 or link[0].get('href') not in (PDM,PDM+'deed.en') or link[0].get_text(strip=True)!='Public domain':raise ValueError('Current image lacks an explicit Public Domain Mark link')
    im=o.get('micrioImage') or {};ident=im.get('micrioId','')
    if im.get('type')!='MicrioImageApiModel' or not re.fullmatch('[A-Za-z0-9]+',ident) or im.get('isDownloadable') is not True or im.get('crop') is not None:raise ValueError('Current image download or full-frame mapping is unverified')
    if norm(im.get('altText'))!=norm(c['title']):raise ValueError('Current image label differs')
    base='https://iiif.micr.io/'+ident
    if service.get('id')!=base or service.get('type')!='ImageService3' or service.get('organisation',{}).get('slug')!='rijks-collectie':raise ValueError('Current image service identity differs')
    if any(service.get(k)!=im.get(k) for k in ('width','height')) or service['width']<1000:raise ValueError('Current image dimensions differ')
    return base+'/full/1000,/0/default.jpg'

def verify_image(im):
    current=im['raw'].get('current_collection_page')
    if current:
        assert current['receipt']['sha256']==core.sha(current['html'].encode())
        assert current['receipt']['url'].startswith('https://www.rijksmuseum.nl/en/collection/object/')
        expected=current_page_image(im,current['html'],current['image_service'])
    else:
        expected=core.rijks_edm(im['raw']['edm']['edm_document'],im['external_id'],im['accession_number'])['source_image_url']
    if im['source_image_url']!=expected or im['policy_url']!=PDM:raise ValueError('Approved Rijks image resource differs')

core.image_record=image_record
original_attach=core.attach
def attach(db,im,target):
    source_match(im,im['raw']['object'])
    verify_image(im)
    if not core.rijks_edm(im['raw']['edm']['edm_document'],im['external_id'],im['accession_number']):raise ValueError('Image rights changed')
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('Rijksmuseum target identity changed')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','creation_year_start','creation_year_end','date_precision','rijks_people','roles')):raise ValueError('Rijksmuseum target facts changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        iid=im['institution_ids'][target]
        if row['current_institution_id'] not in (None,iid):raise ValueError('Existing holding differs')
        current=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(row['artwork_id'],)).fetchall()
        if current and (len(current)!=1 or current[0]['institution_id']!=iid):raise ValueError('Existing holding assertion conflicts')
        if not current:
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('overnight-rijks-primary-images-20260915','Rijksmuseum current Linked Art and EDM records','museum_api','https://data.rijksmuseum.nl/',%s) ON CONFLICT(slug) DO NOTHING",(CC0,))
            sid=db.execute("SELECT id FROM sources WHERE slug='overnight-rijks-primary-images-20260915'").fetchone()['id']
            oid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/verified-rijks-holding/'+im['external_id']))
            db.execute("""INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
               VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted') ON CONFLICT(id) DO NOTHING""",
               (oid,row['artwork_id'],iid,sid,im['page'],'Current official Rijksmuseum collection record, exact object ID '+im['external_id']+', inventory '+im['accession_number']+', creator authority, title, classification and creation interval agree. Collection holding only; current display and ownership are not asserted.',im['checked_at']))
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach
original_event=core.event
def event(run,v):
    if v.get('outcome')=='failed' and v.get('error','').startswith(('Source ','Museum ','Exact ','Multiple ','Qualified ','Unbounded ','Explicit ','Rijksmuseum')):v={**v,'outcome':'metadata_needs_review'}
    return original_event(run,v)
core.event=event

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    with ro('postgres://localhost/artline') as db:rows=db.execute(QUERY+' AND a.primary_media_id IS NULL ORDER BY popular DESC,a.id').fetchall()
    with ro(dsn) as db:remote=db.execute(QUERY+' AND e.external_id=ANY(%s)',([c['external_id'] for c in rows],)).fetchall()
    index=collections.defaultdict(list)
    for r in remote:index[r['external_id']].append(r)
    accepted=[];held=[]
    for c in rows:
        matches=index[c['external_id']]
        if len(matches)!=1 or any(matches[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','date_precision','rijks_people','roles')):held.append({'id':c['artwork_id'],'reason':'Production identity mismatch'});continue
        if matches[0]['primary_media_id']:continue
        accepted.append(dict(c,provider='night-rijks',scheme='rijks-object',target_ids={'local':c['artwork_id'],'cloud':matches[0]['artwork_id']}))
    for target,dsn_ in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(dsn_) as db:
            institution=db.execute("SELECT id::text FROM institutions WHERE slug='rijksmuseum' AND status<>'archived'").fetchall()
            if len(institution)!=1:raise ValueError('Rijksmuseum institution missing')
            for c in accepted:c.setdefault('institution_ids',{})[target]=institution[0]['id']
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.id=ANY(%s::uuid[])',([c['target_ids'][target] for c in accepted],)).fetchall();core.save_new(run/(target+'-before.json'),before)
    core.save_new(path,{'created_at':core.now(),'candidates':accepted});core.save_new(run/'held.json',held)
    print('Rijksmuseum selected',len(accepted),'held',len(held),flush=True);return accepted

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Recovery backups required')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=select(a.run,dsn);done=set()
    done={key for key,r in core.latest_events(a.run).items() if r.get('outcome') in (('complete','failed','no_explicit_open_image','metadata_needs_review','prepared') if a.prepare_only else ('complete','failed','no_explicit_open_image','metadata_needs_review'))}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    for start in range(0,len(rows),50):
        if time.time()>=a.deadline:break
        group=rows[start:start+50]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-rijks',group[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if group[n::3]]
            for job in jobs:job.result()
        print(core.now(),'Rijksmuseum',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
