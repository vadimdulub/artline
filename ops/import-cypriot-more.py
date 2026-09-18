#!/usr/bin/env python3
"""Selected Cypriot research: immutable evidence, read-only plan, guarded delivery.

No publication, inferred current holdings, or fixture writes. Run research,
images, plan, apply, verify in that order; image QA must precede apply.
"""
import argparse, base64, collections, hashlib, html, importlib.util, json, re, subprocess, uuid
from pathlib import Path
from urllib.parse import urlencode, quote
import requests
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/cypriot-more-20260914'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-more-20260914')
spec = importlib.util.spec_from_file_location('wiki', ROOT / 'ops/research-wikimedia-catalogues.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
w.RUN = RUN / 'wikimedia'
core = w.core
ACTOR = 'local-european-research'
SOURCE = 'cypriot-more-research-20260914'
SITE = 'https://artline-web-lpuqqlugnq-ew.a.run.app'

def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/cypriot-more/' + key))
def save(path, data): core.save_new(path, data)
def read(name): return json.loads((RUN / name).read_text())
def plain(value): return w.base.plain(value or '')

def date(value):
    text = plain(value).strip(); result = dict(first=None, last=None, precision='unknown', display=text or 'Creation date unknown', eligible=False)
    if re.fullmatch(r'\d{4}', text): first = last = int(text); precision = 'exact'
    elif re.fullmatch(r'c\. \d{4}', text): first = last = int(text[-4:]); precision = 'circa'
    elif re.fullmatch(r'before \d{4}', text): first = None; last = int(text[-4:]); precision = 'before'
    elif re.fullmatch(r'(?:between )?\d{4}(?: and |[-–])\d{4}', text): first, last = map(int, re.findall(r'\d{4}', text)); precision = 'range'
    elif re.fullmatch(r'\d{1,2} (?:January|December|February) \d{4}', text): first = last = int(text[-4:]); precision = 'exact'
    else: return result
    return dict(first=first, last=last, precision=precision, display=text, eligible=last <= 1970 and (first is None or 1100 <= first <= last))

def capture(key, url):
    receipt = RUN / 'primary-captures' / (key + '.receipt.json')
    if receipt.exists(): return json.loads(receipt.read_text())
    response = requests.get(url, timeout=(15, 45)); response.raise_for_status()
    assert len(response.content) < 20_000_000
    path = RUN / 'primary-captures' / (key + ('.pdf' if 'pdf' in response.headers.get('Content-Type', '') else '.html'))
    save(path, response.content)
    result = dict(url=url, final_url=response.url, retrieved_at=core.now(), sha256=core.sha(response.content), bytes=len(response.content), path=str(path.relative_to(ROOT)))
    save(receipt, result); return result

def research():
    raise SystemExit('Research is immutable selected.json; see research-cypriot-more.py and retained source captures.')

def images():
    selected=read('selected.json'); prepared=[]
    fetcher=core.Fetcher(RUN/'image-captures')
    fetcher.session.headers['User-Agent']=w.SESSION.headers['User-Agent']
    for work in selected['works']:
        if not work.get('commons_file'): continue
        assert work['date']['eligible'] and work['work_type']=='fresco'
        page=work['commons_page'];receipt=work['commons_receipt'];info=page['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
        assert page['title']==work['commons_file'] and not field('Restrictions')
        label=field('LicenseShortName');assert label in ('CC0','CC BY-SA 4.0')
        credit=plain(field('Artist'));assert credit in ('Croquemort Nestor','Zairon')
        markup=page['revisions'][0]['slots']['main']['*'];assert '{{own}}' in markup.lower()
        license_url=field('LicenseUrl').replace('http://creativecommons.org/', 'https://creativecommons.org/');assert license_url.startswith('https://creativecommons.org/')
        rights='cc0' if label=='CC0' else 'cc_by_sa'
        assert 0<info['size']<20_000_000 and info['width']*info['height']<40_000_000
        original=BACKUP/'selected-originals'/(work['key']+'.original')
        if original.exists():raw=original.read_bytes()
        else:raw,_=fetcher.get(info['url'],20_000_000);save(original,raw)
        assert hashlib.sha1(raw).hexdigest()==info['sha1'] and len(raw)==info['size']
        content,width,height,quality=core.compress(raw);checksum=core.sha(content);path='/assets/artworks/imported/cypriot-more/'+work['key']+'-'+checksum[:16]+'.jpg'
        save(ROOT/'apps/web/public'/path.lstrip('/'),content)
        artist=next(a for a in selected['artists'] if a['key']==work['artist'])
        prepared.append(dict(work_key=work['key'],id=uid('image/'+checksum),path=path,sha256=checksum,bytes=len(content),width=width,height=height,quality=quality,rights_status=rights,license_label=label,license_url=license_url,creator_credit=credit,attribution_text=artist['name']+'. '+work['title']+'. Photograph: '+credit+'. Wikimedia Commons; '+label+' ('+license_url+'). Source frame preserved; resized and JPEG compressed. Derivative under the same licence.',rights_basis='Underlying fifteenth/sixteenth-century mural is public domain; independently licensed own-work photograph under '+label+'. Creator, scene and site matched to retained heritage and per-file evidence; original SHA-1 verified.',source_page_url=info['descriptionurl'],source_image_url=info['url'],receipt=receipt,commons_page=page,original_sha256=core.sha(raw),checked_at=core.now()))
        print('Prepared',work['key'],len(content),'bytes',flush=True)
    save(RUN/'prepared-images.json',prepared)

def plan():
    data=read('selected.json'); images=read('prepared-images.json'); known={im['work_key']:im for im in images}
    for a in data['artists']:
        if not a.get('existing'):a.update(id=uid('artist/'+a['key']),slug='cypriot-painter-'+a['key'])
    for i in data['institutions']:
        assert i['existing'] and i['id'] and i['slug']
    for item in data['works']:item.update(id=uid('artwork/'+item['key']),slug='cypriot-artwork-'+item['key'],image=known.get(item['key']))
    for target in ('local','production'):
        with w.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='30s'")
            for a in data['artists']:
                aliases=list({w.norm(x) for x in [a['name'],*a['aliases']]})
                found=db.execute("SELECT a.id::text,a.display_name FROM artists a WHERE a.normalized_name=ANY(%s) OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.normalized_alias=ANY(%s)) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=%s)",(aliases,aliases,a['qid'])).fetchall()
                assert ([v['id'] for v in found]==[a['id']] if a.get('existing') else not found), (target,a['name'],'authority reconciliation',found)
            for work in data['works']:
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(work['source_scheme'],work['source_record_id'])).fetchone()
                a=next(a for a in data['artists'] if a['key']==work['artist'])
                assert not db.execute("SELECT aw.id FROM artwork_artists aa JOIN artworks aw ON aw.id=aa.artwork_id WHERE aa.artist_id=%s AND aw.normalized_title=%s",(a['id'],w.norm(work['title']))).fetchone()
            for work in data['works']:
                d=work['date']
                scope=db.execute('SELECT artline_creation_scope(%s::integer,%s::integer,%s::text) scope',(d['first'],d['last'],d['precision'])).fetchone()['scope']
                assert scope=='eligible' or not work['image'], (work['key'],scope)
            qids=[x['qid'] for x in data['works'] if x.get('qid')]
            assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(qids,)).fetchall()
            for i in data['institutions']:
                assert db.execute('SELECT id::text FROM institutions WHERE slug=%s AND lower(name)=%s',(i['slug'],i['name'].lower())).fetchone()['id']==i['id']
            assert db.execute("SELECT 1 FROM countries WHERE region_code='western-asia' LIMIT 1").fetchone()
        save(BACKUP/(target+'-preimages.json'),dict(at=core.now(),artists=[],artworks=[],note='Read-only exact authority, alias and object-identity checks passed; new rows only.'))
    save(RUN/'application-plan.json',data);pin=core.sha((RUN/'application-plan.json').read_bytes());save(RUN/'application-manifest.json',dict(plan_sha256=pin,artists=sum(not a.get('existing',False) for a in data['artists']),artworks=len(data['works']),images=len(images),unknown_dates=sum(x['date']['precision']=='unknown' for x in data['works'])));print('Plan pinned',pin)

def apply():
    raw=(RUN/'application-plan.json').read_bytes();pin=core.sha(raw);data=json.loads(raw)
    assert read('application-manifest.json')['plan_sha256']==pin
    qa=read('quality-review.json');assert qa['approved'] and qa['plan_sha256']==pin
    assert core.sha((BACKUP/'local-before.dump').read_bytes())==read('local-backup.json')['sha256']
    assert read('production-backup.json')['status']=='SUCCESSFUL'
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    for im in read('prepared-images.json'):
        content=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(content)==im['sha256'] and len(content)<=100000
        blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata={'sha256':im['sha256'],'license':im['license_label']};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(content,content_type='image/jpeg',if_generation_match=0)
        blob.reload();assert blob.size==len(content) and blob.md5_hash==base64.b64encode(hashlib.md5(content).digest()).decode()
    artists={a['key']:a for a in data['artists']};inst={i['key']:i for i in data['institutions']}
    for target in ('local','production'):
        if (RUN/('applied-'+target+'.json')).exists():continue
        with w.base.connect(target=='production') as db,db.transaction():
            db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='45s'");db.execute('SELECT pg_advisory_xact_lock(%s)',(559220260914,))
            db.execute("INSERT INTO countries(code,name,region_code,historical_note) VALUES('CY','Cyprus','western-asia','UN M49 geographical grouping: https://unstats.un.org/unsd/methodology/m49/overview/ . Cultural affiliation, activity and citizenship remain separate; no modern citizenship inferred for historical painters.') ON CONFLICT DO NOTHING")
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Cypriot artist expansion: selected museum and heritage research','collection_page','https://leventisgallery.org/') ON CONFLICT(slug) DO NOTHING",(uid('source'),SOURCE))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
            def citation(kind,ident,field,url,record_id,evidence,checked):
                w.base.insert(db,'citations',dict(entity_type=kind,entity_id=ident,field_name=field,source_id=sid,source_record_id=record_id,source_url=url,evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=checked,created_by=ACTOR))
            for i in data['institutions']:
                if i['existing']:
                    assert db.execute('SELECT id::text FROM institutions WHERE slug=%s',(i['slug'],)).fetchone()['id']==i['id']
                    continue
                w.base.insert(db,'institutions',dict(id=i['id'],slug=i['slug'],name=i['name'],normalized_name=w.norm(i['name']),kind=i['kind'],website_url=i['url'],wikidata_id=i.get('qid'),status='review',description='Institution identity documented in this research; current display is not asserted.'))
                w.base.insert(db,'source_institutions',dict(source_id=sid,institution_id=i['id']))
            for a in data['artists']:
                if a.get('existing'):
                    assert db.execute('SELECT display_name FROM artists WHERE id=%s',(a['id'],)).fetchone()['display_name']==a['name']
                    continue
                # Recheck identities under the same transaction lock before new rows.
                keys=[w.norm(x) for x in [a['name'],*a['aliases']]]
                assert not db.execute("SELECT 1 FROM artists a WHERE a.normalized_name=ANY(%s) OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.normalized_alias=ANY(%s)) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=%s)",(keys,keys,a['qid'])).fetchone()
                fields=dict(id=a['id'],slug=a['slug'],display_name=a['name'],sort_name=a['name'],normalized_name=w.norm(a['name']),entity_type='person',birth_year=a['birth'],death_year=a['death'],timeline_start_year=a['first'],timeline_end_year=a['last'],timeline_display=str(a['first'])+'–'+str(a['last']) if a['basis']=='life' else 'Documented work: '+str(a['first']),timeline_basis=a['basis'],biography_md=a['biography']+'\n\n[Source]('+a['source_url']+').',status='review',created_by=ACTOR,updated_by=ACTOR)
                if a['basis']=='activity':
                    display=('Agiasmati: 1494 or early 16th century (source conflict)' if a['key']=='philippos-goul' else 'Documented work: '+str(a['first'])+('–'+str(a['last']) if a['last']!=a['first'] else ''))
                    fields.update(active_start_year=a['first'],active_end_year=a['last'],activity_display=display,timeline_display=display)
                w.base.insert(db,'artists',fields)
                for name in sorted(set([a['name'],*a['aliases']])):db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(a['id'],name,w.norm(name)))
                if a['qid']:w.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='wikidata',external_id=a['qid'],canonical_url='https://www.wikidata.org/wiki/'+a['qid'],source_id=sid,retrieved_at=a['receipt']['retrieved_at']))
                if a['source_url'].startswith('https://leventisgallery.org/artists/'):w.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='leventis-artist-profile',external_id=a['key'],canonical_url=a['source_url'],source_id=sid,retrieved_at=a['receipt']['retrieved_at']))
                w.base.insert(db,'artist_countries',dict(artist_id=a['id'],country_code='CY',relationship_type=a['country_relationship'],is_primary=False,note=a['country_note']))
                citation('artist',a['id'],'cypriot_identity_and_dates',a['source_url'],a['key'],a,a['receipt']['retrieved_at'])
                if a['woman']:
                    evidence=a['gender_evidence']
                    assert evidence['explicit_women_statement'] and evidence['source_url']==a['source_url']
                    w.base.insert(db,'artist_gender_evidence',dict(artist_id=a['id'],is_woman=True,basis='Explicit foundation exhibition identifies these women artists; no inference from names or portraits.',source_url=a['source_url'],source_record_id=a['key'],source_checksum=a['receipt']['sha256'],evidence_json=Jsonb(evidence),checked_at=a['receipt']['retrieved_at']))
            for work in data['works']:
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(work['source_scheme'],work['source_record_id'])).fetchone()
                im=work['image'];a=artists[work['artist']];d=work['date']
                if im:
                    w.base.insert(db,'media_assets',dict(id=im['id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=work['title']+' — '+a['name'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['receipt']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR))
                    w.base.insert(db,'media_rights_evidence',dict(media_id=im['id'],source_id=sid,source_record_id=im['commons_page']['title'],source_checksum=im['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis=im['rights_basis'],adapter_version='cypriot-more-v1',checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                w.base.insert(db,'artworks',dict(id=work['id'],slug=work['slug'],title=work['title'],alternate_title=work.get('alternate_title'),normalized_title=w.norm(work['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=work['work_type'],medium_text=work['medium'],accession_number=work['accession'],description_md='Documented work by '+a['name']+'. Source metadata and image availability remain in review.',current_institution_id=None,current_location_text=None,primary_media_id=im['id'] if im else None,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                w.base.insert(db,'artwork_artists',dict(artwork_id=work['id'],artist_id=a['id'],attribution_role='primary',attribution_note='Named source creator; exact museum catalogue or Commons object evidence retained for review.'))
                w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=work['id'],scheme=work['source_scheme'],external_id=work['source_record_id'],canonical_url=work['source_url'],source_id=sid,retrieved_at=work['receipt']['retrieved_at']))
                if work['holding']:w.base.insert(db,'artwork_location_assertions',dict(artwork_id=work['id'],claim_type='holding',institution_id=inst[work['holding']]['id'],context='collection',source_id=sid,source_url=work['source_url'],evidence_note='Source collection label: '+str(work['collection_label'] or work['raw_metadata']['category'])+'. Source claim retained in review; no accepted holding or on-view assertion.',checked_at=work['receipt']['retrieved_at'],review_state='review'))
                citation('artwork',work['id'],'cypriot_object_research',work['source_url'],work['source_record_id'],{k:v for k,v in work.items() if k not in ('image','commons_page')},work['receipt']['retrieved_at'])
                if im:w.base.insert(db,'artwork_media',dict(artwork_id=work['id'],media_id=im['id'],sort_order=0,view_label='Mural scene or partial view (source frame)' if work['work_type']=='fresco' else 'Selected source reproduction'))
        save(RUN/('applied-'+target+'.json'),dict(at=core.now(),plan_sha256=pin,artists=sum(not a.get('existing',False) for a in artists.values()),artworks=len(data['works']),images=len(read('prepared-images.json')),status='review',atomic_transaction=True))
        print(target,'applied',sum(not a.get('existing',False) for a in artists.values()),'new artists,',sum(a.get('existing',False) for a in artists.values()),'reused artists,',len(data['works']),'works',flush=True)

def verify():
    data=read('application-plan.json');artist_ids=[a['id'] for a in data['artists']];work_ids=[x['id'] for x in data['works']];snapshots={}
    for target in ('local','production'):
        with w.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            artists=db.execute("SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.timeline_start_year,a.timeline_end_year,a.timeline_basis,a.status,(SELECT jsonb_agg(jsonb_build_object('country',c.country_code,'relationship',c.relationship_type)) FROM artist_countries c WHERE c.artist_id=a.id) countries FROM artists a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id",(artist_ids,)).fetchall()
            works=db.execute("SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.research_candidate,a.current_institution_id::text,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id",(work_ids,)).fetchall()
            assert len(artists)==len(artist_ids) and len(works)==len(work_ids)
            assert all(a['status']=='review' for a in artists)
            assert all(x['status']=='review' and x['research_candidate'] and x['current_institution_id'] is None for x in works)
            assert all(x['scope']=='eligible' and x['byte_size']<=100000 for x in works if x['storage_path'])
            assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND (claim_type='display' OR review_state<>'review')",(work_ids,)).fetchone()
            links=db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id',(work_ids,)).fetchall();assert len(links)==len(work_ids)
            women=db.execute('SELECT artist_id::text,is_woman FROM artist_gender_evidence WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id',(artist_ids,)).fetchall()
            snapshots[target]=dict(artists=artists,works=works,links=links,women=women)
        save(RUN/('verified-'+target+'.json'),snapshots[target])
    assert snapshots['local']==snapshots['production'],'Scoped local/production parity differs'
    checks=[]
    for im in read('prepared-images.json'):
        response=requests.get(SITE+im['path'],timeout=45);response.raise_for_status();assert core.sha(response.content)==im['sha256'];checks.append(dict(url=SITE+im['path'],status=response.status_code,sha256=im['sha256']))
    response=requests.get(SITE+'/api/backend/v1/timeline',params=dict(start=1100,end=2000,popular='false',country='CY'),timeout=45);response.raise_for_status();timeline=response.json();assert timeline['total']>=len(read('local-before.json')['cypriot_artists'])
    save(RUN/'final-verification.json',dict(at=core.now(),parity=True,artists=len(artists),artworks=len(work_ids),images=checks,timeline_total=timeline['total'],review_only=True))
    print('Verified parity and public assets:',len(artists),'artists,',len(work_ids),'works, timeline',timeline['total'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['research','images','plan','apply','verify']);args=parser.parse_args();globals()[args.phase]()
