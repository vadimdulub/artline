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
RUN = ROOT / 'docs/research/cypriot-painters-20260914'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/cypriot-painters-20260914')
spec = importlib.util.spec_from_file_location('wiki', ROOT / 'ops/research-wikimedia-catalogues.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
w.RUN = RUN / 'wikimedia'
core = w.core
ACTOR = 'local-european-research'
SOURCE = 'cypriot-selected-research-20260914'
SITE = 'https://artline-web-lpuqqlugnq-ew.a.run.app'

def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/cypriot-selection/' + key))
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
    assert not (RUN / 'selected.json').exists()
    institutions = [
        dict(key='leventis-gallery', name='A. G. Leventis Gallery', kind='museum', url='https://cypriotartists.leventisgallery.org/'),
        dict(key='state-gallery-cyprus', name='State Gallery of Contemporary Cypriot Art', kind='museum', url='https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/state-gallery-of-contemporary-art/', qid='Q22661779'),
    ]
    state_receipt = capture('state-gallery', institutions[1]['url'])
    people = []; works = []; holds = []
    crosswalk = {'ioannis-kissonergis':'Q23904701','adamantios-diamantis':'Q12873034','loukia-nicolaides-vassiliou':'Q23835856','george-pol-georghiou':'Q21463551'}
    # A bounded selection of eight artworks per museum-profiled modern painter.
    for a in read('leventis-artists-response.json')['artists']:
        key = a['slug']; qid = crosswalk.get(key); source = 'https://cypriotartists.leventisgallery.org/en/' + key + '/biography'
        receipt = read('primary-artists/' + key + '.receipt.json')
        entity = w.entities([qid])[0][qid] if qid else None
        if entity:
            assert (w.year(entity,'P569'), w.year(entity,'P570')) == (int(a['birthYear']), int(a['deathYear']))
        people.append(dict(key=key, name=a['title'], qid=qid, birth=int(a['birthYear']), death=int(a['deathYear']), first=int(a['birthYear']), last=int(a['deathYear']), basis='life', aliases=w.labels(entity) if entity else [a['title'],'Solon Frangoulides','Solomos Fragoulides','Σολωμός Φραγκουλίδης'], country_relationship='cultural_affiliation', country_note='Identified in the A. G. Leventis Gallery Pioneers of Cypriot Art catalogue; affiliation is not an exclusive citizenship assertion.', source_url=source, receipt=receipt, biography='Cypriot painter documented in the A. G. Leventis Gallery artist catalogue. Biography and interpretation remain in review.', woman=bool(entity and {v.get('id') for v in w.values(entity,'P21')} == {'Q6581072'})))
        count = 0
        for raw in a['artworks']['all']:
            d = date(raw['date'])
            reason = None
            if d['last'] and not d['eligible']: reason = 'Known creation date after 1970 or range crossing cutoff'
            elif 'photo of the original' in (raw['collection'] or '').lower(): reason = 'Original destroyed; photographic surrogate needs distinct object review'
            elif 'various studies' in raw['title'].lower(): reason = 'Grouped studies require distinct physical-object identification'
            elif not (raw['temporary_exhibitions'] or raw['category']=='Our Collections'): reason = 'Museum connection requires further object evidence'
            elif count >= 8: reason = 'Outside bounded eight-work selection for this painter'
            if reason: holds.append(dict(key='leventis-'+str(raw['id']), title=html.unescape(raw['title']), reason=reason)); continue
            med = plain(raw['medium']); kind = 'watercolor' if 'watercolour' in med.lower() else 'painting' if any(x in med.lower() for x in ['oil','tempera']) else 'drawing' if any(x in med.lower() for x in ['pencil','charcoal','ink']) else 'unknown'
            collection = plain(raw['collection']) or None
            holding = 'leventis-gallery' if raw['category']=='Our Collections' else 'state-gallery-cyprus' if collection and collection.startswith('State Gallery') else None
            works.append(dict(key='leventis-'+str(raw['id']), artist=key, title=html.unescape(raw['title']), date=d, work_type=kind, medium=med or None, accession=raw['number'], source_url='https://cypriotartists.leventisgallery.org/en/'+key+'/works/'+raw['slug'], receipt=receipt, source_record_id=str(raw['id']), source_scheme='leventis-cypriot-artwork', museum_connection=dict(institution='leventis-gallery', basis='Museum catalogue collection item' if raw['category']=='Our Collections' else 'Explicit historical exhibition in museum catalogue', exhibition=plain(raw['temporary_exhibitions'])), holding=holding, collection_label=collection, image_candidate_url=raw['image'], image=None, image_hold='Museum reproduction has no verified reuse licence; source link retained, no download.', raw_metadata={k:raw[k] for k in ('title','date','medium','number','collection','temporary_exhibitions','publications','category')}))
            count += 1
    # Museum-linked nineteenth-century Cypriot painter and one selected work.
    qid='Q331256'; entity, er = w.entities([qid]); e=entity[qid]
    people.append(dict(key='vasilis-michaelides', name='Vasilis Michaelides', qid=qid, birth=1849, death=1917, first=1849, last=1917, basis='life', aliases=w.labels(e), country_relationship='cultural_affiliation', country_note='Source identifies the Cypriot poet and painter; not inferred from a museum location.', source_url='https://www.limassol.org.cy/uploads/History-Center-pdfs/08dd27d8eb.pdf', receipt=capture('michaelides-municipal-museum','https://www.limassol.org.cy/uploads/History-Center-pdfs/08dd27d8eb.pdf'), biography='Cypriot poet and painter (1849–1917). His painting Madonna and Child is documented in the State Gallery collection.', woman=False))
    e, receipts=w.entities(['Q22661822']); e=e['Q22661822']; v=w.value(w.claims(e,'P571')[0]); assert v['time'].startswith('+1875-') and v['before']==0 and v['after']==5
    works.append(dict(key='madonna-michaelides', qid='Q22661822', artist='vasilis-michaelides', title='Madonna and Child', alternate_title='Μαντόνα και Παιδί', date=dict(first=1875,last=1880,precision='range',display='1875–1880 (source uncertainty)',eligible=True), date_note='Wikidata time value 1875 has before=0 and after=5 years; uncertainty retained. Commons displays 1875. Neither source supports inventing a precise year.', work_type='painting', medium='Oil on canvas', accession=None, source_url='https://www.wikidata.org/wiki/Q22661822', source_record_id='Q22661822', source_scheme='wikidata', receipt=receipts['Q22661822'], museum_connection=dict(institution='state-gallery-cyprus',basis='Wikidata P195 and Commons collection metadata; Europeana 280 object reference'), holding='state-gallery-cyprus', collection_label='State Gallery of Contemporary Art', image=None, commons_file='File:Madonna and Child - Vasilis Michaelides.jpg'))
    # Cyprus activity is represented as activity, without asserting Cypriot birth.
    theo_receipt=capture('apsevdis-tourism','https://www.visitcyprus.com/discover-cyprus/routes/religious-routes/monasticism-and-asceticism-route-e-religious-route/')
    qid='Q108041020'; e=w.entities([qid])[0][qid]
    people.append(dict(key='theodore-apsevdis',name='Theodore Apsevdis',qid=qid,birth=None,death=None,first=1183,last=1183,basis='activity',aliases=w.labels(e),country_relationship='active',country_note='Cyprus Tourism documents work at the Egkleistra of Agios Neophytos; it describes him as Constantinopolitan. Cyprus is an activity relationship, not birthplace or citizenship.',source_url=theo_receipt['url'],receipt=theo_receipt,biography='Byzantine painter active in Cyprus. Birth and death dates are unresolved; the timeline uses documented work in 1183.',woman=False))
    # Two separately identified surviving scenes, not the disputed Araka panel.
    for key,title,file in [('apsevdis-saint','Fresco of a Saint','Theodore Apsevdis Fresco.png'),('apsevdis-joseph','Fresco of Joseph','Theodore Apsevdis Fresco of Joseph.png')]:
        works.append(dict(key=key,artist='theodore-apsevdis',title=title,date=date('1183'),work_type='fresco',medium=None,accession=None,source_url='https://commons.wikimedia.org/wiki/File:'+quote(file.replace(' ','_')),source_record_id='File:'+file,source_scheme='commons-artwork',receipt=read('commons-candidates.json' if key.endswith('saint') else 'commons-candidates-2.json')['receipt'],museum_connection=None,holding=None,collection_label=None,image=None,commons_file='File:'+file,selection_note='Research selection of a documented Byzantine painting scene in Cyprus. No museum masterpiece designation or present holding is asserted.',context_source=theo_receipt))
    save(RUN/'selected.json',dict(at=core.now(),artists=people,institutions=institutions,works=works,holds=holds,policy='Review-only named-creator records; unknown dates retained. Museum exhibitions distinct from holdings. No images downloaded before selection.'))
    print('Selected',len(people),'artists',len(works),'works',len(holds),'held')

def images():
    selected=read('selected.json'); prepared=[]
    spec=importlib.util.spec_from_file_location('image_review',ROOT/'ops/prepare-wikimedia-catalogue-images.py'); ir=importlib.util.module_from_spec(spec);spec.loader.exec_module(ir)
    fetcher=core.Fetcher(RUN/'image-captures')
    fetcher.session.headers['User-Agent']=w.SESSION.headers['User-Agent']
    for work in selected['works']:
        if not work.get('commons_file'): continue
        assert work['date']['eligible']
        data, receipt=w.fetch('https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',format='json',titles=work['commons_file'],prop='imageinfo|revisions',iiprop='url|extmetadata|sha1|size|mime',rvprop='ids|content',rvslots='main')))
        page=next(iter(data['query']['pages'].values()));info=page['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
        assert field('LicenseShortName')=='Public domain' and field('Copyrighted')=='False' and not field('Restrictions')
        markup=page['revisions'][0]['slots']['main']['*'];assert 'PD-Art' in markup
        assert work['title'].lower() in plain(field('ImageDescription')).lower() or work['key']=='madonna-michaelides'
        artist=next(a for a in selected['artists'] if a['key']==work['artist'])
        assert artist['name'].lower() in plain(field('Artist')).lower()
        assert 0<info['size']<20_000_000 and info['width']*info['height']<40_000_000
        original=BACKUP/'selected-originals'/(work['key']+'.original')
        if original.exists(): raw=original.read_bytes()
        else: raw,_=fetcher.get(info['url'],20_000_000);save(original,raw)
        assert hashlib.sha1(raw).hexdigest()==info['sha1'] and len(raw)==info['size']
        content,width,height,quality=core.compress(raw);checksum=core.sha(content);path='/assets/artworks/imported/cypriot-selection/'+work['key']+'-'+checksum[:16]+'.jpg'
        save(ROOT/'apps/web/public'/path.lstrip('/'),content)
        credit=ir.image_credit(meta);license_url='https://creativecommons.org/publicdomain/mark/1.0/'
        prepared.append(dict(work_key=work['key'],id=uid('image/'+checksum),path=path,sha256=checksum,bytes=len(content),width=width,height=height,quality=quality,rights_status='public_domain',license_label='Public domain',license_url=license_url,creator_credit=credit,attribution_text=artist['name']+'. '+work['title']+'. '+credit+'. Wikimedia Commons; Public Domain Mark. Source frame preserved, resized and JPEG compressed.',source_page_url=info['descriptionurl'],source_image_url=info['url'],receipt=receipt,commons_page=page,original_sha256=core.sha(raw),checked_at=core.now()))
        print('Prepared',work['key'],len(content),'bytes',flush=True)
    save(RUN/'prepared-images.json',prepared)

def plan():
    data=read('selected.json'); images=read('prepared-images.json'); known={im['work_key']:im for im in images}
    for a in data['artists']:a.update(id=uid('artist/'+a['key']),slug='cypriot-painter-'+a['key'])
    for i in data['institutions']:i.update(id=uid('institution/'+i['key']),slug=i['key'])
    for item in data['works']:item.update(id=uid('artwork/'+item['key']),slug='cypriot-artwork-'+item['key'],image=known.get(item['key']))
    for target in ('local','production'):
        with w.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='30s'")
            for a in data['artists']:
                aliases=list({w.norm(x) for x in [a['name'],*a['aliases']]})
                found=db.execute("SELECT a.id::text,a.display_name FROM artists a WHERE a.normalized_name=ANY(%s) OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.normalized_alias=ANY(%s)) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=%s)",(aliases,aliases,a['qid'])).fetchall()
                assert not found, (target,a['name'],'existing authority/name requires reconciliation',found)
            titles=[x['title'].lower() for x in data['works']];urls=[x['source_url'] for x in data['works']]
            # Exact source matches anywhere, plus named-label candidates; no global enrichment.
            found=db.execute("SELECT a.id::text,a.title,a.unlinked_creator_label FROM artworks a WHERE EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_url=ANY(%s)) OR (lower(a.title)=ANY(%s) AND a.unlinked_creator_label ~* 'Kisson|Diamant|Frang|Nicolaid|Georghiou|Michaelid|Apsev')",(urls,titles)).fetchall();assert not found,found
            qids=[x['qid'] for x in data['works'] if x.get('qid')]
            assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(qids,)).fetchall()
            for i in data['institutions']:
                assert not db.execute('SELECT id FROM institutions WHERE slug=%s OR lower(name)=%s OR wikidata_id=%s',(i['slug'],i['name'].lower(),i.get('qid'))).fetchall()
            assert db.execute("SELECT 1 FROM countries WHERE region_code='western-asia' LIMIT 1").fetchone()
        save(BACKUP/(target+'-preimages.json'),dict(at=core.now(),artists=[],artworks=[],note='Read-only exact authority, alias and object-identity checks passed; new rows only.'))
    save(RUN/'application-plan.json',data);pin=core.sha((RUN/'application-plan.json').read_bytes());save(RUN/'application-manifest.json',dict(plan_sha256=pin,artists=len(data['artists']),artworks=len(data['works']),images=len(images),unknown_dates=sum(x['date']['precision']=='unknown' for x in data['works'])));print('Plan pinned',pin)

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
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Cypriot painters: primary museum catalogue and verified image evidence','collection_page','https://cypriotartists.leventisgallery.org/') ON CONFLICT(slug) DO NOTHING",(uid('source'),SOURCE))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
            def citation(kind,ident,field,url,record_id,evidence,checked):
                w.base.insert(db,'citations',dict(entity_type=kind,entity_id=ident,field_name=field,source_id=sid,source_record_id=record_id,source_url=url,evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=checked,created_by=ACTOR))
            for i in data['institutions']:
                w.base.insert(db,'institutions',dict(id=i['id'],slug=i['slug'],name=i['name'],normalized_name=w.norm(i['name']),kind=i['kind'],website_url=i['url'],wikidata_id=i.get('qid'),status='review',description='Institution identity documented in this research; current display is not asserted.'))
                w.base.insert(db,'source_institutions',dict(source_id=sid,institution_id=i['id']))
            for a in data['artists']:
                # Recheck identities under the same transaction lock before new rows.
                keys=[w.norm(x) for x in [a['name'],*a['aliases']]]
                assert not db.execute("SELECT 1 FROM artists a WHERE a.normalized_name=ANY(%s) OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND x.normalized_alias=ANY(%s)) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=%s)",(keys,keys,a['qid'])).fetchone()
                fields=dict(id=a['id'],slug=a['slug'],display_name=a['name'],sort_name=a['name'],normalized_name=w.norm(a['name']),entity_type='person',birth_year=a['birth'],death_year=a['death'],timeline_start_year=a['first'],timeline_end_year=a['last'],timeline_display=str(a['first'])+'–'+str(a['last']) if a['basis']=='life' else 'Documented work: '+str(a['first']),timeline_basis=a['basis'],biography_md=a['biography']+'\n\n[Source]('+a['source_url']+').',status='review',created_by=ACTOR,updated_by=ACTOR)
                if a['basis']=='activity':fields.update(active_start_year=a['first'],active_end_year=a['last'],activity_display='Documented work: '+str(a['first']))
                w.base.insert(db,'artists',fields)
                for name in sorted(set([a['name'],*a['aliases']])):db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(a['id'],name,w.norm(name)))
                if a['qid']:w.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='wikidata',external_id=a['qid'],canonical_url='https://www.wikidata.org/wiki/'+a['qid'],source_id=sid,retrieved_at=a['receipt']['retrieved_at']))
                if a['key'] not in ('vasilis-michaelides','theodore-apsevdis'):w.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='leventis-cypriot-artist',external_id=a['key'],canonical_url=a['source_url'],source_id=sid,retrieved_at=a['receipt']['retrieved_at']))
                w.base.insert(db,'artist_countries',dict(artist_id=a['id'],country_code='CY',relationship_type=a['country_relationship'],is_primary=False,note=a['country_note']))
                citation('artist',a['id'],'cypriot_identity_and_dates',a['source_url'],a['key'],a,a['receipt']['retrieved_at'])
                if a['woman']:
                    gender=w.entities([a['qid']])[0][a['qid']]['claims']['P21'];evidence=dict(qid=a['qid'],claims=gender)
                    w.base.insert(db,'artist_gender_evidence',dict(artist_id=a['id'],is_woman=True,basis='Explicit Wikidata P21 identity statement; no inference from name or portrait.',source_url='https://www.wikidata.org/wiki/'+a['qid'],source_record_id=a['qid'],source_checksum=core.sha(core.encode(evidence)),evidence_json=Jsonb(evidence),checked_at=a['receipt']['retrieved_at']))
            for work in data['works']:
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(work['source_scheme'],work['source_record_id'])).fetchone()
                im=work['image'];a=artists[work['artist']];d=work['date']
                if im:
                    w.base.insert(db,'media_assets',dict(id=im['id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=work['title']+' — '+a['name'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['receipt']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR))
                    w.base.insert(db,'media_rights_evidence',dict(media_id=im['id'],source_id=sid,source_record_id=im['commons_page']['title'],source_checksum=im['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis='Explicit per-file Public Domain Mark for old two-dimensional painting; named creator and object identity reviewed; source frame and original SHA-1 preserved.',adapter_version='cypriot-selected-v1',checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                w.base.insert(db,'artworks',dict(id=work['id'],slug=work['slug'],title=work['title'],alternate_title=work.get('alternate_title'),normalized_title=w.norm(work['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=work['work_type'],medium_text=work['medium'],accession_number=work['accession'],description_md='Documented work by '+a['name']+'. Source metadata and image availability remain in review.',current_institution_id=None,current_location_text=None,primary_media_id=im['id'] if im else None,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                w.base.insert(db,'artwork_artists',dict(artwork_id=work['id'],artist_id=a['id'],attribution_role='primary',attribution_note='Named source creator; exact museum catalogue or Commons object evidence retained for review.'))
                w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=work['id'],scheme=work['source_scheme'],external_id=work['source_record_id'],canonical_url=work['source_url'],source_id=sid,retrieved_at=work['receipt']['retrieved_at']))
                if work['holding']:w.base.insert(db,'artwork_location_assertions',dict(artwork_id=work['id'],claim_type='holding',institution_id=inst[work['holding']]['id'],context='collection',source_id=sid,source_url=work['source_url'],evidence_note='Source collection label: '+str(work['collection_label'] or work['raw_metadata']['category'])+'. Source claim retained in review; no accepted holding or on-view assertion.',checked_at=work['receipt']['retrieved_at'],review_state='review'))
                citation('artwork',work['id'],'cypriot_object_research',work['source_url'],work['source_record_id'],{k:v for k,v in work.items() if k!='image'},work['receipt']['retrieved_at'])
                if im:w.base.insert(db,'artwork_media',dict(artwork_id=work['id'],media_id=im['id'],sort_order=0,view_label='Mural detail (source frame)' if work['artist']=='theodore-apsevdis' else 'Selected source reproduction'))
        save(RUN/('applied-'+target+'.json'),dict(at=core.now(),plan_sha256=pin,artists=len(artists),artworks=len(data['works']),images=len(read('prepared-images.json')),status='review',atomic_transaction=True))
        print(target,'applied',len(artists),'artists',len(data['works']),'works',flush=True)

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
    response=requests.get(SITE+'/api/backend/v1/timeline',params=dict(start=1100,end=2000,popular='false',country='CY'),timeout=45);response.raise_for_status();timeline=response.json();assert timeline['total']>=len(artists)-1
    save(RUN/'final-verification.json',dict(at=core.now(),parity=True,artists=len(artists),artworks=len(work_ids),images=checks,timeline_total=timeline['total'],review_only=True))
    print('Verified parity and public assets:',len(artists),'artists,',len(work_ids),'works, timeline',timeline['total'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['research','images','plan','apply','verify']);args=parser.parse_args();globals()[args.phase]()
