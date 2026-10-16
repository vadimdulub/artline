#!/usr/bin/env python3
"""Artist-scoped Fragonard image reconciliation; production only, local DB unopened."""
import collections, concurrent.futures, gzip, importlib.util, json, re, sys, uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit

def module(name, file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

i=module('fragonard_delivery_base','illustrated-300k-20261011.py')
m=i.m; r=m.m
OP='fragonard-images-20261011';ROOT=m.ROOT;RUN=ROOT/'docs/research'/OP
AID='18f1c6ba-4184-4546-b5b8-dddcec11ded2'
PROFILE='https://www.wikiart.org/en/jean-honore-fragonard'
i.OP=OP;i.RUN=RUN;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
r.RUN=RUN
i.CFG['paris']=dict(name='Paris Musées',host='apicollections.parismusees.paris.fr',policy='https://creativecommons.org/publicdomain/zero/1.0/',rights='cc0',license='CC0 1.0',mid=None,scheme=None)
i.CFG['met']=dict(name='The Metropolitan Museum of Art',host='images.metmuseum.org',policy='https://www.metmuseum.org/about-the-met/policies-and-documents/open-access',rights='cc0',license='CC0 1.0',mid=None,scheme='met-object')

def index():
    m.save(RUN/'authorization.json',dict(at=m.now(),request='find pictures for Jean-Honoré Fragonard; we can cover all pictures!',target='production',local_database_connected=False,scope='All supported artist-scoped exact object image gaps; preserve existing images, catalogue metadata, attribution, status and holdings. Source-backed additional works allowed by standing expansion instruction.'))
    raw,receipt=r.capture(PROFILE+'/all-works/text-list')
    assert receipt['status']==200
    soup=r.BeautifulSoup(raw,'html.parser');items={}
    for link in soup.select('li a[href]'):
        if link['href'].startswith('/en/jean-honore-fragonard/'):
            url=urljoin(PROFILE,link['href']);items[url]=dict(title=link.get_text(' ',strip=True),url=url,date_text=link.parent.get_text(' ',strip=True))
    m.save(RUN/'wikiart-index.json',dict(receipt=receipt,items=list(items.values())))
    raw,rc=r.capture('https://www.wikiart.org/fr/App/Painting/PaintingsByArtist?artistUrl=jean-honore-fragonard&json=2')
    assert rc['status']==200;m.save(RUN/'wikiart-french-index.json',dict(receipt=rc,items=json.loads(raw)))
    def one(item):
        path=RUN/'wikiart-pages'/(m.sha(item['url'].encode())+'.json')
        if path.exists():return m.load(path)
        i.provider_slot('www.wikiart.org')
        try:
            page=r.wiki_fields(item['url']);assert page['artist_url']==PROFILE
            out=dict(state='captured',page=page)
        except Exception as exc:out=dict(state='held',url=item['url'],reason=str(exc))
        m.save(path,out);return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,items.values()))
    print('WikiArt pages',collections.Counter(x['state'] for x in results),flush=True)

def reconcile():
    b=m.load(RUN/'baseline.json.gz');works={w['artwork']['id']:w for w in b['artworks']};urls=collections.defaultdict(set);titles=collections.defaultdict(set)
    for x in b['identifiers']:
        e=x['e']
        if e['entity_id'] in works and e.get('canonical_url'):urls[e['canonical_url'].rstrip('/')].add(e['entity_id'])
    for x in b['citations']:
        e=x['c']
        if e.get('source_url'):urls[e['source_url'].rstrip('/')].add(e['entity_id'])
    for aid,w in works.items():
        if w['media'] and w['media'].get('source_page_url'):urls[w['media']['source_page_url'].rstrip('/')].add(aid)
        for key in ['title','alternate_title']:
            if w['artwork'].get(key):titles[m.norm(w['artwork'][key])].add(aid)
    def imagekey(url):return urlsplit(url or '').path.split('!')[0]
    fr={imagekey(x.get('image')):x for x in m.load(RUN/'wikiart-french-index.json')['items']}
    output=[]
    for p in sorted((RUN/'wikiart-pages').glob('*.json')):
        d=m.load(p)
        if d['state']!='captured':output.append(d);continue
        page=d['page'];f=fr.get(imagekey(page['metadata']['image']),{})
        candidates=urls[page['source_url'].rstrip('/')]
        basis='existing_source_url'
        if not candidates:
            candidates=titles[m.norm(page['title'])]|titles[m.norm(f.get('title'))];basis='title_or_french_translation'
        output.append(dict(url=page['source_url'],title=page['title'],french_title=f.get('title'),source_date=page['date'],location=page['fields'].get('Location'),basis=basis,candidates=[dict(id=aid,title=works[aid]['artwork']['title'],date=works[aid]['artwork']['date_display'],illustrated=bool(works[aid]['media']),museum=works[aid]['artwork']['current_institution_id']) for aid in sorted(candidates)]))
    m.save(RUN/'wikiart-reconciliation-v2.json',output)
    for row in output:
        if not row.get('candidates') or not all(c['illustrated'] for c in row['candidates']):print(json.dumps(row,ensure_ascii=False),flush=True)
    print('SOURCE COVERAGE',collections.Counter('existing_illustrated' if x.get('candidates') and all(c['illustrated'] for c in x['candidates']) else 'needs_review' for x in output))

def native():
    native=module('fragonard_rijks','recover-local-rijks-native-images-20261006.py')
    b=m.load(RUN/'baseline.json.gz');gaps={w['artwork']['id']:w['artwork'] for w in b['artworks'] if not w['media']}
    ex=[x['e'] for x in b['identifiers'] if x['e']['entity_id'] in gaps and 'rijks' in x['e']['scheme']]
    def one(e):
        a=gaps[e['entity_id']];dest=RUN/'native-rijks'/(a['id']+'.json')
        if dest.exists():return m.load(dest)
        try:
            i.provider_slot('www.rijksmuseum.nl');raw,rc=r.capture(e['canonical_url']);assert rc['status']==200
            obj=native.page_object(e,raw)
            assert obj['objectNumber']==a['accession_number']
            assert m.norm(obj['title'])==m.norm(a['title'])
            assert obj['objectNodeUri']=='https://id.rijksmuseum.nl/'+e['external_id']
            props=[p for c in obj['dataTab']['components'] for p in c.get('properties',[])]
            rights=[p['values'] for p in props if p.get('name')=='Copyright'];assert len(rights)==1
            assert 'creativecommons.org/publicdomain/mark/1.0' in str(rights)
            im=obj['micrioImage'];assert im['isDownloadable'] and im['crop'] is None
            assert m.norm(im['altText'])==m.norm(a['title']) and re.fullmatch('[A-Za-z0-9]+',im['micrioId'])
            assert a['creation_year_end'] and a['creation_year_end']<=1970
            source=dict(obj,assistivetext=obj['preferredDescription'])
            imageurl='https://iiif.micr.io/'+im['micrioId']+'/full/!1200,1200/0/default.jpg'
            row=dict(artwork_id=a['id'],native_id=e['external_id'],scheme=e['scheme'],title=a['title'],creator_label=obj['makerSubtitleLine'],source_url=e['canonical_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='rijks',expected_museum_id=a['current_institution_id'],image=dict(native_url=imageurl,image_url=imageurl,source=source,receipt=rc),plan_path=str(dest),plan_sha256=rc['sha256'],identity_basis='Exact current native object ID, inventory, title and explicitly uncropped downloadable primary photograph. Native maker qualifications preserved in credit.',rights_status='public_domain',rights_label='Public Domain Mark 1.0',rights_basis='Current native object page explicitly supplies Public Domain Mark for its photograph.',manual_visual_required=True)
            out=dict(state='matched',row=row,object=obj,receipt=rc)
        except Exception as exc:out=dict(state='held',artwork_id=a['id'],reason=str(exc),source=e)
        m.save(dest,out);return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,ex))
    print('Rijks',collections.Counter(x['state'] for x in results),flush=True)
    jobs={}
    for x in b['identifiers']:
        e=x['e']
        if e['entity_id'] in gaps and '/notice/joconde/' in (e['canonical_url'] or ''):jobs[e['entity_id']]=e['canonical_url']
    for x in b['citations']:
        c=x['c']
        if c['entity_id'] in gaps and '/notice/joconde/' in (c['source_url'] or ''):jobs[c['entity_id']]=c['source_url']
    def pop(job):
        aid,url=job;dest=RUN/'native-joconde'/(aid+'.json')
        if dest.exists():return m.load(dest)
        try:
            i.provider_slot('pop.culture.gouv.fr');raw,rc=r.capture(url);assert rc['status']==200
            soup=r.BeautifulSoup(raw,'html.parser');txt=soup.get_text(' ',strip=True)
            im=[x.get('src') for x in soup.select('img') if '/joconde/' in str(x.get('src','')) or '%2Fjoconde%2F' in str(x.get('src',''))]
            credit=re.findall(r'Crédits photographiques (.*?)(?:Identification du bien|Vous souhaitez|Référence de la notice)',txt)
            out=dict(artwork_id=aid,url=url,receipt=rc,credit=credit,image_urls=im,source_text=txt,state='held',reason='Photographic permission explicitly required' if 'utilisation soumise à autorisation' in txt else 'Image-specific reuse evidence needs review')
        except Exception as exc:out=dict(artwork_id=aid,url=url,state='held',reason=str(exc))
        m.save(dest,out);return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(pop,jobs.items()))
    print('Joconde',collections.Counter(x['reason'] for x in results),flush=True)

def prepare():
    provider=sys.argv[2];batch=provider+'-000'
    if provider=='rijks':rows=[m.load(p)['row'] for p in sorted((RUN/'native-rijks').glob('*.json')) if m.load(p)['state']=='matched']
    else:
        reviewed=m.load(RUN/'wikiart-reconciliation-v2.json');need={x['url'] for x in reviewed if not x.get('candidates') or not all(c['illustrated'] for c in x['candidates'])}
        rows=[]
        for p in sorted((RUN/'wikiart-pages').glob('*.json')):
            page=m.load(p)['page']
            if page['source_url'] not in need:continue
            date=page['date'] or {};aid=i.uid('candidate/'+page['source_id'])
            rows.append(dict(artwork_id=aid,native_id=page['source_id'],title=page['title'],creator_label=page['creator'],source_url=page['source_url'],accession_number=None,first=date.get('first'),last=date.get('last'),precision=date.get('precision','unknown'),work_type='unknown',provider='wikiart',image=dict(native_url=page['metadata']['image'],image_url=page['image_url'],source=page,receipt=page['receipt']),plan_path=str(p),plan_sha256=m.sha(p.read_bytes()),manual_visual_required=True,rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis']))
    dest=i.folder(batch)/'selection.json.gz'
    if not dest.exists():
        m.save(dest,dict(batch=batch,provider=provider,rows=rows,scope='Selected exact native image candidates for individual visual and identity review; preparation does not authorize attachment.'))
        m.save(i.folder(batch)/'pin.json',dict(sha256=m.sha(dest.read_bytes())))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda row:i.prepare_one(row,batch),rows))
    print('Prepared',provider,collections.Counter(x['state'] for x in results),flush=True)
    i.audit(batch)

def supplement():
    b=m.load(RUN/'baseline.json.gz');ws={w['artwork']['id']:w['artwork'] for w in b['artworks']};rows=[]
    pairs=[('b167cb9c-7fa9-4b55-9428-1efca5b6d35a','160016387','PDUT1194'),('a9e11c9c-1878-4ced-85cb-b1a4eec16bf7','460000192','J 29'),('5b46157a-40e8-411b-9c12-bfaf8cccc363','320026841','P2100')]
    for aid,oid,inventory in pairs:
        a=ws[aid];data=m.load(RUN/'paris-manifests'/(oid+'.json'));manifest=data['data'];metadata={v['label']:v['value'] for v in manifest['metadata']};canvas=manifest['sequences'][0]['canvases'][0]
        assert metadata['Numéro d’inventaire']==inventory and metadata['Auteur']==['Fragonard, Jean-Honoré']
        rights={v['label']:v['value'] for v in canvas['metadata']};assert rights['Copyright']=='https://creativecommons.org/publicdomain/zero/1.0/'
        imageurl=canvas['images'][0]['resource']['@id'];rc=data['receipt'];pop=m.load(RUN/'native-joconde'/(aid+'.json'))
        assert inventory in pop['source_text'] and oid in manifest['@id']
        rows.append(dict(artwork_id=aid,native_id=oid,scheme=None,title=a['title'],creator_label='Jean-Honoré Fragonard',source_url=metadata['Catalogue des œuvres de Paris Musées'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='paris',image=dict(native_url=imageurl,image_url=imageurl,source=manifest,receipt=rc),plan_path=str(RUN/'paris-manifests'/(oid+'.json')),plan_sha256=rc['sha256'],rights_status='cc0',rights_label=rights['Droits'],rights_basis='Exact image-level CC0 licence in the native IIIF canvas, distinct from other restricted photographs of the same object.',identity_basis='Existing accepted Joconde holding citation, exact native inventory '+inventory+', creator and title reconciled to the first native IIIF image. Existing catalogue date and unknown accession fields preserved.',confidence=.99))
    aid='01c94e55-924c-5078-b82f-e7f07a37be0a';a=ws[aid]
    path=ROOT/'docs/research/continuous-production-20261011/batches/000011/source-captures/372973.body.gz';raw=gzip.decompress(path.read_bytes());obj=json.loads(raw);rc=m.load(path.with_name('372973.receipt.json'));assert m.sha(raw)==rc['sha256']
    assert obj['objectID']==372973 and obj['accessionNumber']==a['accession_number'] and obj['title']==a['title'] and obj['isPublicDomain']
    assert obj['objectDate']==a['date_display'] and obj['artistWikidata_URL']=='https://www.wikidata.org/wiki/Q127171'
    imageurl=obj['primaryImageSmall'];rc=dict(rc,retrieved_at=rc['at'],evidence_reuse=str(path.relative_to(ROOT)))
    rows.append(dict(artwork_id=aid,native_id='372973',scheme='met-object',title=a['title'],creator_label=obj['artistDisplayName'],source_url=obj['objectURL'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='met',image=dict(native_url=imageurl,image_url=imageurl,source=obj,receipt=rc),plan_path=str(path),plan_sha256=rc['sha256'],rights_status='cc0',rights_label='The Metropolitan Museum of Art Open Access — CC0',rights_basis='Archived native API explicitly identifies this exact object primary image and isPublicDomain=true; no new request to held object/API surfaces.',identity_basis='Exact inventory, native object ID, title and literal ca. 1761 date agree. API range 1756–1766 is a search expansion of that same literal date; catalogue circa date and qualified after-Preti creator links remain unchanged.',confidence=.99))
    batch='native-000';dest=i.folder(batch)/'selection.json.gz'
    if not dest.exists():
        m.save(dest,dict(batch=batch,provider='native',rows=rows));m.save(i.folder(batch)/'pin.json',dict(sha256=m.sha(dest.read_bytes())))
    for row in rows:print(row['provider'],i.prepare_one(row,batch)['state'],flush=True)
    i.audit(batch)

def final_plan():
    decisions=m.load(RUN/'wikiart-final-decisions.json');rows=[];images=[]
    base={w['artwork']['id']:w for w in m.load(RUN/'baseline.json.gz')['artworks']}
    for row in i.selected('wikiart-000')['rows']:
        slug=row['source_url'].rsplit('/',1)[-1];decision=decisions[slug]
        if decision['action'] not in ['new','attach']:continue
        candidate=row['artwork_id'];prepared=m.load(i.folder('wikiart-000')/'prepared'/(candidate+'.json'));assert prepared['state']=='prepared'
        row=dict(row,action=decision['action'],identity_basis=decision['reason'],confidence=decision['confidence'],candidate_id=candidate,decision=decision)
        if decision['action']=='attach':
            row['artwork_id']=decision['artwork_id'];a=base[row['artwork_id']]['artwork'];assert not a['primary_media_id']
            row.update(title=a['title'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'])
        else:
            page=row['image']['source'];assert page['date'] and page['date']['last']<=1970
            row['work_type']='painting';row['source_fields']=page['fields'];row['date_display']=page['date']['display']
        row['before']=base[row['artwork_id']]['artwork'] if row['artwork_id'] in base else None
        prepared=dict(prepared,artwork_id=row['artwork_id'],media_id=i.uid('media/'+row['artwork_id']+'/'+prepared['sha256']),source_candidate_id=candidate,title=row['title'])
        rows.append(row);images.append(prepared)
    for row in i.selected('native-000')['rows']:
        prepared=m.load(i.folder('native-000')/'prepared'/(row['artwork_id']+'.json'));assert prepared['state']=='prepared'
        row=dict(row,action='attach',before=base[row['artwork_id']]['artwork']);rows.append(row);images.append(prepared)
    # Preserve a fresh full preimage for only the existing targets; no local catalogue connection.
    with r.connect() as db:
        existing=i.d.snapshot(db,[row['artwork_id'] for row in rows if row['action']=='attach'])
        for row in rows:
            if row['action']=='attach':assert existing[row['artwork_id']]['artwork']==row['before']
        sourceids=[row['native_id'] for row in rows if row['provider']=='wikiart' and row['action']=='new']
        collisions=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",(sourceids,)).fetchall();assert not collisions
    batch='delivery-000';dest=i.folder(batch)/'selection.json.gz'
    m.save(dest,dict(batch=batch,provider='mixed',rows=rows));m.save(i.folder(batch)/'pin.json',dict(sha256=m.sha(dest.read_bytes())))
    m.save(i.BACKUP/'supplement-plan-preimages.json.gz',existing)
    m.save(i.folder(batch)/'quality-audit.json',dict(prepared_images=images,preparation_holds=[],identity_holds={},sample_ids=[im['artwork_id'] for im in images],sample_policy='Every selected image individually viewed on recorded contact sheets; 190 existing artist images technically compared and flagged pairs visually reviewed. Full-frame proportions and byte hashes checked.'))
    review=m.load(RUN/'supplement-visual-review.json');assert set(review['candidate_ids'])==set(im.get('source_candidate_id',im['artwork_id']) for im in images)
    m.save(i.folder(batch)/'visual-review.json',dict(at=m.now(),batch_quality_decision='accept',decisions=[dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision='accept',note=review['note']) for im in images],source_visual_review=review))
    print('Final supplemental plan',len(rows),'images',sum(row['action']=='new' for row in rows),'new artworks',flush=True)

def deliver(batch='delivery-000',backup_prefix='supplement'):
    plan=i.selected(batch);pin=m.sha((i.folder(batch)/'selection.json.gz').read_bytes());assert pin==m.load(i.folder(batch)/'pin.json')['sha256']
    assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'
    i.upload(batch);images,audit,review=i.accepted(batch);ims={im['artwork_id']:im for im in images};rows=plan['rows'];ids=[row['artwork_id'] for row in rows]
    receipt=i.folder(batch)/'applied.json'
    if receipt.exists():return
    old=m.load(i.BACKUP/(backup_prefix+'-plan-preimages.json.gz'));data=collections.defaultdict(list)
    with r.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();before=i.d.snapshot(db,ids)
        assert before==old,'Concurrent target changes; replan without overwriting'
        existing_titles={m.norm(x['title']) for x in db.execute("SELECT a.title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'",(AID,))}
        sourceids=[row['native_id'] for row in rows if row['provider']=='wikiart' and row['action']=='new']
        assert not db.execute("SELECT id FROM external_identifiers WHERE scheme='wikiart-artwork' AND external_id=ANY(%s)",(sourceids,)).fetchall()
        assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
        m.save(i.BACKUP/(backup_prefix+'-locked-preimages.json.gz'),before)
        for provider in sorted({row['provider'] for row in rows}):
            cfg=i.CFG[provider];origin=urlsplit(next(row['source_url'] for row in rows if row['provider']==provider));base_url=origin.scheme+'://'+origin.netloc
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(i.uid('source/'+provider),OP+'-'+provider,cfg['name']+' — Fragonard image review',base_url,OP))
        for row in rows:
            aid=row['artwork_id'];im=ims[aid];cfg=i.CFG[row['provider']];sid=i.uid('source/'+row['provider']);rc=row['image']['receipt']
            assert m.load(i.folder(batch)/'uploads'/(aid+'.json'))['sha256']==im['sha256']
            if row['action']=='new':
                assert m.norm(row['title']) not in existing_titles
                fields=row['source_fields'];data['artworks'].append(dict(id=aid,slug='wikiart-'+row['native_id'],title=row['title'],normalized_title=m.norm(row['title']),date_display=row['date_display'],creation_year_start=row['first'],creation_year_end=row['last'],date_precision=row['precision'],work_type=row['work_type'],medium_text=fields.get('Media'),dimensions_text=fields.get('Dimensions'),status='review',research_candidate=True,created_by=m.ACTOR,updated_by=m.ACTOR))
                data['artwork_artists'].append(dict(artwork_id=aid,artist_id=AID,attribution_role='primary',attribution_note='Jean-Honoré Fragonard. Exact source creator profile; individually reviewed composition. '+row['source_url']))
                data['external_identifiers'].append(dict(id=i.uid('external/'+row['native_id']),entity_type='artwork',entity_id=aid,scheme='wikiart-artwork',external_id=row['native_id'],canonical_url=row['source_url'],source_id=sid,retrieved_at=rc['retrieved_at']))
            note=dict(operation=OP,plan_sha256=pin,identity_basis=row['identity_basis'],editorial_confidence=row['confidence'],source_page=row['image']['source'],source_receipt=rc,decision=row.get('decision'),metadata_evidence=row.get('metadata_evidence'),catalogue_metadata_preserved=row['action']=='attach',source_locations_not_accepted_as_holdings=True)
            data['citations'].append(dict(id=i.uid('citation/'+aid),entity_type='artwork',entity_id=aid,field_name='fragonard_image_identity_review',source_id=sid,source_record_id=row['native_id'],source_url=row['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=m.ACTOR))
            if row.get('metadata_evidence'):
                ev=row['metadata_evidence'];museum_sid=i.uid('source/'+ev['source_key']);origin=urlsplit(ev['url'])
                db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(id) DO NOTHING",(museum_sid,OP+'-'+ev['source_key'],ev['source_name'],origin.scheme+'://'+origin.netloc,OP))
                data['citations'].append(dict(id=i.uid('metadata-citation/'+aid),entity_type='artwork',entity_id=aid,field_name='creation_date_medium_dimensions',source_id=museum_sid,source_record_id=ev['record_id'],source_url=ev['url'],evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=ev['receipt']['retrieved_at'],created_by=m.ACTOR))
            credit=row['creator_label']+'. '+cfg['name']+'. '+row['rights_label']
            if row['provider']=='met':credit+='; '+row['image']['source']['creditLine']
            data['media_assets'].append(dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=row['source_url'],provider_name=cfg['name'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=row['title']+' — '+row['creator_label'],rights_status=row['rights_status'],license_label=row['rights_label'],license_url=cfg['policy'],creator_credit=credit,attribution_text=credit+'. Full source frame preserved; proportional resizing and JPEG compression.',retrieved_at=im['download']['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR))
            data['media_rights_evidence'].append(dict(media_id=im['media_id'],source_id=sid,source_record_id=row['native_id'],source_checksum=rc['sha256'],source_image_url=im['source_image_url'],policy_url=cfg['policy'],rights_basis=row['rights_basis'],adapter_version=OP,checked_at=m.now(),evidence_json=dict(note,download=im['download'],user_approval=m.load(RUN/'authorization.json'),visual_review=review)))
            data['artwork_media'].append(dict(artwork_id=aid,media_id=im['media_id'],sort_order=max([x['sort_order'] for x in before.get(aid,{}).get('attachments',[])],default=-1)+1,view_label='Full artwork reproduction'))
        for table in ['artworks','artwork_artists','external_identifiers','citations','media_assets','media_rights_evidence','artwork_media']:i.d.batch(db,table,data[table])
        for row in rows:db.execute('UPDATE artworks SET primary_media_id=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s AND primary_media_id IS NULL',(ims[row['artwork_id']]['media_id'],m.ACTOR,row['artwork_id']))
        cid=str(uuid.uuid5(uuid.NAMESPACE_URL,i.d.PERSONAL));collection=db.execute('SELECT curator_kind,institution_id FROM curated_collections WHERE id=%s FOR UPDATE',(cid,)).fetchone();assert collection==dict(curator_kind='owner',institution_id=None)
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(cid,)).fetchone()['n'];new=[row for row in rows if row['action']=='new'];assert position+len(new)<=100000
        i.d.batch(db,'curated_collection_items',[dict(id=i.uid('selection/'+row['artwork_id']),collection_id=cid,artwork_id=row['artwork_id'],position=position+n+1,reason='Personal owner selection for the requested Fragonard illustrated survey; not a museum masterpiece or current-display claim.',source_id=i.uid('source/wikiart'),source_url=row['source_url'],checked_at=row['image']['receipt']['retrieved_at']) for n,row in enumerate(new)])
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(cid,))
        after=i.d.snapshot(db,ids)
        for aid,oldrow in before.items():
            assert all(after[aid]['artwork'][k]==v for k,v in oldrow['artwork'].items() if k not in i.IGNORE)
            assert after[aid]['creators']==oldrow['creators'] and after[aid]['holdings']==oldrow['holdings']
        for row in new:
            a=after[row['artwork_id']]['artwork'];assert a['status']=='review' and a['published_at'] is None and a['current_institution_id'] is None
        for aid in ids:assert after[aid]['artwork']['primary_media_id']==ims[aid]['media_id']
        i.d.batch(db,'audit_log',[dict(id=i.uid('audit/'+aid),actor_user_id=m.ACTOR,action='fragonard_illustrated_survey',entity_type='artwork',entity_id=aid,request_id=OP,before_json=before.get(aid),after_json=after[aid]) for aid in ids])
        m.save(i.BACKUP/(backup_prefix+'-transaction-postimages.json.gz'),after)
    m.save(receipt,dict(at=m.now(),plan_sha256=pin,new_artworks=len(new),images=len(images),ids=ids,local_database_connected=False))
    print('Delivered',len(images),'supplemental images and',len(new),'new review artworks',flush=True)

def verify(batches=('rijks-000','delivery-000'),output='verification.json'):
    baseline=m.load(RUN/'baseline.json.gz');old={w['artwork']['id']:w for w in baseline['artworks']};expected={}
    for batch in batches:
        images,audit,review=i.accepted(batch)
        for im in images:
            assert m.sha(Path(im['path']).read_bytes())==im['sha256'] and Path(im['path']).stat().st_size==im['bytes']<=100000
            assert m.load(i.folder(batch)/'uploads'/(im['artwork_id']+'.json'))['public_byte_hash_verified']
            expected[im['artwork_id']]=im
    ids=list(expected);new=[row for batch in batches if batch!='rijks-000' for row in i.selected(batch)['rows'] if row['action']=='new'];newids={row['artwork_id'] for row in new}
    with r.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        now=i.d.snapshot(db,list(old)+list(newids));all_media_ids=[im['media_id'] for im in expected.values()]+[w['media']['id'] for w in old.values() if w['media']]
        media={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(ma) v FROM media_assets ma WHERE id=ANY(%s::uuid[])',(all_media_ids,))}
        for aid,w in old.items():
            a=now[aid]['artwork'];assert all(a[k]==v for k,v in w['artwork'].items() if k not in i.IGNORE)
            if aid not in expected:assert a==w['artwork'],'Unrelated original artwork changed'
            before_creators=sorted([x['aa'] for x in baseline['creators'] if x['aa']['artwork_id']==aid],key=lambda x:json.dumps(x,sort_keys=True))
            assert sorted(now[aid]['creators'],key=lambda x:json.dumps(x,sort_keys=True))==before_creators
            if w['media']:
                assert media[w['media']['id']]==w['media']
        for aid,im in expected.items():
            a=now[aid]['artwork'];assert a['primary_media_id']==im['media_id'];ma=media[im['media_id']]
            assert ma['checksum_sha256']==im['sha256'] and ma['storage_path']==im['storage_path'] and ma['byte_size']==im['bytes'] and ma['mime_type']=='image/jpeg'
            assert any(x['media_id']==im['media_id'] for x in now[aid]['attachments'])
        for row in new:
            a=now[row['artwork_id']]['artwork'];assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
            assert a['creation_year_start']==row['first'] and a['creation_year_end']==row['last'] and a['title']==row['title']
            assert a['current_institution_id'] is None and not now[row['artwork_id']]['holdings']
        rights=db.execute('SELECT count(*) n FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[]) AND adapter_version=%s',([im['media_id'] for im in expected.values()],OP)).fetchone()['n'];assert rights==len(expected)
        search=db.execute('SELECT count(*) n FROM artwork_search_documents s JOIN artworks a ON a.id=s.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id AND s.status=a.status AND s.title=a.title',(ids,)).fetchone()['n'];assert search==len(expected)
        counts=db.execute("SELECT count(*) works,count(a.primary_media_id) images FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'",(AID,)).fetchone();assert counts==dict(works=len(old)+len(newids),images=sum(bool(w['media']) for w in old.values())+len(expected))
        gaps=[dict(artwork_id=aid,title=v['artwork']['title'],source_date=v['artwork']['date_display']) for aid,v in now.items() if not v['artwork']['primary_media_id']]
        father=next(x['a'] for x in baseline['artists'] if x['a']['id']==AID);assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(AID,)).fetchone()['v']==father
    for batch in ['rijks-000']:
        for p in (i.folder(batch)/'applied').glob('*.json'):
            before=m.load(i.BACKUP/batch/('before-'+p.name.replace('.json','.json.gz')))
            for aid,w in before.items():assert now[aid]['holdings']==w['holdings']
    for aid,w in m.load(i.BACKUP/'supplement-locked-preimages.json.gz').items():assert now[aid]['holdings']==w['holdings']
    public=[]
    sample=[next(iter(expected)),*list(newids)[:2],'c41810a9-46be-590f-b84e-b4552ee10b5c','99c330a0-aefd-4edd-93ca-d33beed4de2a','a9e11c9c-1878-4ced-85cb-b1a4eec16bf7']
    for aid in sample:
        url='https://artlines.org/api/backend/v1/artists/jean-honore-fragonard-q127171/works/'+aid;resp=i.session().get(url,timeout=(15,45));resp.raise_for_status();assert expected[aid]['storage_path'] in resp.text
        image_resp=i.session().get('https://artlines.org'+expected[aid]['storage_path'],timeout=(15,45));image_resp.raise_for_status();assert m.sha(image_resp.content)==expected[aid]['sha256']
        public.append(dict(artwork_id=aid,url=url,status=resp.status_code,image_sha256=expected[aid]['sha256']))
    result=dict(at=m.now(),artist_id=AID,baseline=dict(works=len(old),images=sum(bool(w['media']) for w in old.values())),final=counts,new_images=len(expected),new_artworks=len(newids),rights_evidence=rights,search_documents=search,all_public_files_byte_verified=len(expected),fresh_public_samples=public,all_original_artwork_metadata_creators_holdings_and_states_preserved=True,all_190_original_media_rows_preserved=True,artist_record_preserved=True,local_database_connected=False,remaining_gaps=gaps)
    m.save(RUN/output,result);print(json.dumps({k:v for k,v in result.items() if k not in ['remaining_gaps','fresh_public_samples']},ensure_ascii=False),flush=True)

def followup_plan():
    """Resolve one unknown WikiArt date with exact native museum object evidence."""
    aid='5c450028-c54d-521b-889e-6d92c3f6ba0f';url='https://www.musee-jacquemart-andre.com/fr/oeuvres/debuts-modele'
    raw,rc=r.capture(url);assert rc['status']==200
    txt=r.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert 'Jean-Honoré Fragonard (1732 - 1806)' in txt and 'vers 1770, huile sur toile, 50 x 63 cm' in txt
    ev=dict(source_key='jacquemart-andre',source_name='Musée Jacquemart-André',record_id='debuts-modele',url=url,receipt=rc,title='Les débuts du modèle',source_date='vers 1770',medium='huile sur toile',dimensions='50 x 63 cm',wikiart_date_remains_unknown_in_source_evidence=True,note='Official museum highlights page names the exact painter and oval painting. Museum date resolves eligibility; no date inferred from artist lifespan. Source location retained as evidence without creating a holding or display record.')
    row=next(row for row in i.selected('wikiart-000')['rows'] if row['artwork_id']==aid)
    assert row['image']['source']['date'] is None
    reason='Exact WikiArt title/translation and Musée Jacquemart-André location agree with official Les débuts du modèle. Individually viewed oval composition: model seated at left, older woman behind, painter in salmon costume at right with mahlstick. Official circa 1770 date and oil-on-canvas medium establish eligible object scope. No matching title, object identifier or composition in the existing Fragonard catalogue.'
    decision=dict(action='new',confidence=.98,reason=reason)
    row=dict(row,action='new',identity_basis=reason,confidence=.98,candidate_id=aid,decision=decision,first=1770,last=1770,precision='circa',work_type='painting',source_fields=dict(row['image']['source']['fields'],Media='huile sur toile',Dimensions='50 x 63 cm'),date_display='vers 1770',before=None,metadata_evidence=ev)
    im=m.load(i.folder('wikiart-000')/'prepared'/(aid+'.json'));assert im['state']=='prepared'
    with r.connect() as db:
        ids=[v['id'] for v in db.execute("SELECT a.id::text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.status<>'archived'",(AID,))]
        assert len(ids)==322 and aid not in ids
        assert not db.execute("SELECT id FROM external_identifiers WHERE scheme='wikiart-artwork' AND external_id=%s",(row['native_id'],)).fetchall()
        assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchall()
        prior=i.d.snapshot(db,ids)
    m.save(i.BACKUP/'followup-catalogue-preimages.json.gz',prior)
    m.save(i.BACKUP/'followup-plan-preimages.json.gz',{})
    m.save(RUN/'wikiart-followup-decisions.json',{'the-beginnings-of-model':dict(decision,metadata_evidence=ev)})
    batch='delivery-001';dest=i.folder(batch)/'selection.json.gz'
    m.save(dest,dict(batch=batch,provider='wikiart',rows=[row]));m.save(i.folder(batch)/'pin.json',dict(sha256=m.sha(dest.read_bytes())))
    m.save(i.folder(batch)/'quality-audit.json',dict(prepared_images=[im],preparation_holds=[],identity_holds={},sample_ids=[aid],sample_policy='Image individually viewed at full delivery size and in earlier contact sheet; exact museum object identity manually reconciled.'))
    m.save(i.folder(batch)/'visual-review.json',dict(at=m.now(),batch_quality_decision='accept',decisions=[dict(artwork_id=aid,sha256=im['sha256'],artist=im['artist'],decision='accept',note=reason)]))
    print('Follow-up planned: one additional illustrated review painting',flush=True)

def followup_deliver():
    deliver('delivery-001','followup')

def final_verify():
    with r.connect() as db:
        old=m.load(i.BACKUP/'followup-catalogue-preimages.json.gz')
        assert i.d.snapshot(db,list(old))==old,'Follow-up changed a prior catalogue row'
    verify(('rijks-000','delivery-000','delivery-001'),'final-verification.json')

if __name__=='__main__':globals()[sys.argv[1]]()
