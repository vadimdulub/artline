#!/usr/bin/env python3
"""Cyprus painter coverage audit and selected, evidenced image additions."""
import argparse
import concurrent.futures
import collections
import csv
import io
import hashlib
import html
import importlib.util
import json
import re
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode,quote,urlsplit,urlunsplit
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('top100',ROOT/'ops/wikiart-top100-20260920.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
c=t.c;m=t.m
RUN=ROOT/'docs/research/cyprus-images-20260920'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
GATE=threading.Lock()


def read(path):return json.loads(path.read_bytes())


def fetch(url):
    key=m.core.sha(url.encode());path=RUN/'captures'/(key+'.body');receipt=path.with_suffix('.json')
    if path.exists():
        raw=path.read_bytes();evidence=read(receipt)
        if m.core.sha(raw)!=evidence['sha256']:raise ValueError('Capture checksum differs')
        if evidence['http_status']!=200:raise ValueError('Cached source was not accessible: '+url)
        return raw,evidence
    with GATE:
        response=m.requests.get(url,headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected artwork research)'},timeout=(15,45))
        time.sleep(1.1)
    if len(response.content)>20_000_000:raise ValueError('Metadata response exceeds limit')
    evidence={'url':url,'final_url':response.url,'checked_at':m.core.now(),'http_status':response.status_code,
        'sha256':m.core.sha(response.content),'bytes':len(response.content),'path':str(path.relative_to(ROOT))}
    m.save_atomic(path,response.content);m.save_atomic(receipt,evidence)
    response.raise_for_status()
    return response.content,evidence


def audit():
    path=RUN/'baseline.json'
    if path.exists():return
    targets={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            artists=db.execute("""SELECT to_jsonb(a) artist,
                coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
                (SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id) countries,
                coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers
                FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code='CY')
                ORDER BY a.display_name""").fetchall()
            for row in artists:
                works=c.artist_works(db,row['artist']['id'])
                m.save_atomic(RUN/'catalogue'/target/(row['artist']['id']+'.json'),works)
                row['works']=sum(w['status']!='archived' for w in works)
                row['images']=sum(w['status']!='archived' and w['primary_media_id'] is not None for w in works)
            targets[target]=artists
    result={'at':m.core.now(),'targets':targets}
    m.save_atomic(path,result);m.save_atomic(BACKUP/'cohort-baseline.json',result)
    print({target:{'painters':len(rows),'works':sum(r['works'] for r in rows),'images':sum(r['images'] for r in rows)} for target,rows in targets.items()},flush=True)


def discover_one(row):
    artist=row['artist'];path=RUN/'commons-discovery'/(artist['id']+'.json')
    if path.exists():return
    names=list(dict.fromkeys([artist['display_name']]+row['aliases']))[:8]
    query=' OR '.join('"'+name.replace('"','')+'"' for name in names)
    url='https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','generator':'search',
        'gsrsearch':query,'gsrnamespace':6,'gsrlimit':40,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime',
        'rvprop':'ids|content','rvslots':'main'})
    raw,receipt=fetch(url);data=json.loads(raw)
    if 'error' in data:raise ValueError(str(data['error']))
    pages=list(data.get('query',{}).get('pages',{}).values())
    m.save_atomic(path,{'artist':artist,'names':names,'receipt':receipt,'pages':pages,'continuation':data.get('continue')})
    print('Commons review',artist['display_name'],len(pages),'files',flush=True)


def discover():
    baseline=read(RUN/'baseline.json')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(discover_one,baseline['targets']['local']))
    raw,receipt=fetch('https://www.wikiart.org/en/artists-by-nation/cypriot')
    m.save_atomic(RUN/'wikiart-directory-review.json',{'receipt':receipt,
        'finding':'The directory lists [ a y s h ], born 1986, outside the artwork cutoff; none of the 27 existing Cyprus painters is listed.'})


def museum_candidates():
    baseline=read(RUN/'baseline.json');rows=baseline['targets']['local'];artists={r['artist']['slug']:r for r in rows}
    candidates=[]
    for previous in ('cypriot-painters-20260914','cypriot-expansion-20260914','cypriot-more-20260914'):
        path=ROOT/'docs/research'/previous/'application-plan.json';data=read(path)
        for w in data['works']:
            if w.get('image') or not w.get('image_candidate_url'):continue
            artist=artists.get('cypriot-painter-'+w['artist'])
            if not artist:continue
            candidates.append({'artist':artist['artist']['display_name'],'artist_id':artist['artist']['id'],
                'artwork_id':w['id'],'title':w['title'],'date':w['date'],'source_url':w['source_url'],
                'image_candidate_url':w['image_candidate_url'],'prior_hold':w.get('image_hold'),
                'source_plan':str(path.relative_to(ROOT)),'source_plan_sha256':m.core.sha(path.read_bytes())})
    m.save_atomic(RUN/'existing-museum-image-candidates.json',candidates)
    print('Existing museum image candidates',len(candidates),'painters',len({r['artist_id'] for r in candidates}),flush=True)


def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/cyprus-images-20260920/'+value))


def select_open():
    baseline=read(RUN/'baseline.json');artists={r['artist']['slug']:r['artist'] for r in baseline['targets']['local']}
    selections=[
        ('commons-discovery/a7015b36-85ce-5ebb-b561-ce9f3424e6ad.json','File:Theodore Apsevdis Jesus.png','theodore-apsevdis','Jesus Pantocrator',1183),
        ('commons-discovery/a7015b36-85ce-5ebb-b561-ce9f3424e6ad.json','File:Theodore Apsevdis Virgin and Child.png','theodore-apsevdis','Virgin and Child',1183),
        ('heritage-discovery/galata.json','File:Galata Theotokos Geburt.jpg','symeon-axentis','Nativity of Christ, Church of the Archangel at Galata',1514),
        ('heritage-discovery/galata.json','File:Galata Theotokos Stifter.jpg','symeon-axentis','Donors of the Church of the Archangel at Galata',1514),
    ]
    heritage_path=ROOT/'docs/research/cypriot-expansion-20260914/primary-captures/venice-routes.pdf'
    heritage=read(heritage_path.with_suffix('.receipt.json'))
    if m.core.sha(heritage_path.read_bytes())!=heritage['sha256']:raise ValueError('Heritage evidence differs')
    heritage={**heritage,'path':str(heritage_path.relative_to(ROOT)),
        'review_note':'The Church of Archangelos, Galata section explicitly names Symeon Afxentis and 1514, including the donor panel above the north gate.'}
    selected=[]
    for source,file,key,title,year in selections:
        discovery=read(RUN/source);page=next(p for p in discovery['pages'] if p['title']==file)
        info=page['imageinfo'][0];meta=info['extmetadata'];markup=page['revisions'][0]['slots']['main']['*']
        if meta['LicenseShortName']['value']!='Public domain' or '{{PD-Art' not in markup:
            raise ValueError('Open image rights evidence differs')
        artist=artists['cypriot-painter-'+key]
        selected.append({'id':uid('artwork/'+file),'slug':'cyprus-images-'+uid(file),'artist':artist,'title':title,
            'date_display':str(year),'creation_year_start':year,'creation_year_end':year,'date_precision':'exact','work_type':'fresco',
            'source_url':info['descriptionurl'],'scheme':'commons-artwork','source_id':file,'image_url':info['url'],
            'source_receipt':discovery['receipt'],'source_metadata':page,'commons_sha1':info['sha1'],'commons_size':info['size'],
            'rights_status':'public_domain','license_label':'Public domain','license_url':'https://creativecommons.org/publicdomain/mark/1.0/',
            'creator_credit':('Theodore Apsevdis; photograph supplied by Tzim78; Wikimedia Commons' if key=='theodore-apsevdis'
                else 'Symeon Axentis; source: Maria Constantoudaki-Kitromilides, The Churches of the Virgin Podithou and of the Theotokos, Bank of Cyprus, 2007; Wikimedia Commons'),
            'rights_basis':'Commons per-file PD-Art declaration for a faithful reproduction of a medieval two-dimensional painting; source and credit retained.',
            'selection_basis':'Personal selection of a distinct surviving Cypriot fresco scene; not a museum masterpiece designation.',
            'attribution_basis':('Commons artwork record names Theodore Apsevdis and dates the scene to 1183; source attribution retained in review.'
                if key=='theodore-apsevdis' else 'Commons identifies the Church of the Archangel/Theotokos at Galata. Cyprus Tourism identifies its 1514 wall paintings as the work of Symeon Afxentis. Commons generic unknown-artist/about-1500 wording retained alongside this primary heritage identification.'),
            'context_receipt':heritage if key=='symeon-axentis' else None,'new_record':True,'requires_source_policy':False})
    m.save_atomic(RUN/'open-selected.json',selected)
    print('Selected open images',len(selected),flush=True)


def select_museum():
    if not (RUN/'source-policy-authorization.json').exists():raise ValueError('Source extension is not authorized')
    baseline=read(RUN/'baseline.json');artists={r['artist']['slug']:r['artist'] for r in baseline['targets']['local']}
    existing={}
    for p in (RUN/'catalogue/local').glob('*.json'):
        for w in read(p):
            for e in w['identifiers'] or []:existing[(e['scheme'],e['external_id'])]=w
    spec=importlib.util.spec_from_file_location('cypriot_dates',ROOT/'ops/import-cypriot-selection.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    selected=[];held=[]
    for path in sorted((RUN/'leventis-current').glob('*.json')):
        if '.receipt.' in path.name:continue
        a=read(path);artist=artists['cypriot-painter-'+a['slug']];receipt=read(path.with_suffix('.receipt.json'))
        receipt['path']=str(path.relative_to(ROOT))
        if m.core.sha(path.read_bytes())!=receipt['sha256']:raise ValueError('Museum metadata checksum differs')
        for raw in a['artworks']['all']:
            date=old.date(raw['date']);page='https://cypriotartists.leventisgallery.org/en/'+a['slug']+'/works/'+raw['slug']
            if date['last'] is None or date['last']>1955:
                held.append({'artist':artist['display_name'],'title':html.unescape(raw['title']),'source_url':page,'reason':'Creation date unresolved or after 1955','date':date});continue
            if any(x in (raw.get('collection') or '').lower() for x in ['photo of the original','destroyed']):
                held.append({'artist':artist['display_name'],'title':raw['title'],'source_url':page,'reason':'Destroyed original or surrogate needs object review'});continue
            prior=existing.get(('leventis-cypriot-artwork',str(raw['id'])))
            if prior and prior['primary_media_id']:continue
            if prior and (m.norm(prior['title'])!=m.norm(raw['title']) or prior['creation_year_end']!=date['last']):
                raise ValueError('Existing museum artwork identity/date differs')
            title=prior['title'] if prior else html.unescape(raw['title'])
            selected.append({'id':prior['artwork_id'] if prior else uid('leventis/'+str(raw['id'])),
                'slug':prior['slug'] if prior else 'cyprus-images-leventis-'+str(raw['id']),'artist':artist,'title':title,
                'date_display':date['display'],'creation_year_start':date['first'],'creation_year_end':date['last'],'date_precision':date['precision'],
                'work_type':prior['work_type'] if prior else ('painting' if 'oil' in (raw['medium'] or '').lower() else 'unknown'),
                'medium_text':old.plain(raw['medium']) or None,'accession_number':raw['number'],
                'source_url':page,'scheme':'leventis-cypriot-artwork','source_id':str(raw['id']),'image_url':raw['image'],
                'source_receipt':receipt,'source_metadata':raw,'rights_status':'restricted' if '©' in (raw.get('collection') or '') else 'unknown',
                'license_label':'Source copyright retained; no reuse licence verified' if '©' in (raw.get('collection') or '') else 'No reuse licence verified',
                'license_url':page,'creator_credit':artist['display_name']+'; A. G. Leventis Gallery'+('; '+old.plain(raw['collection']) if raw.get('collection') else ''),
                'rights_basis':'User explicitly extended the WikiArt collection workflow to Cyprus museum/artist sources on 20 September 2026; creation date ends by 1955. Source copyright and unknown reuse permission preserved; no independently obtained licence claimed.',
                'selection_basis':'Personal selection from the museum’s documented painter catalogue; source exhibition/collection statements retained separately without accepted holding or on-view claims.',
                'attribution_basis':'The museum artist catalogue names this painter and supplies the exact object record.',
                'new_record':prior is None,'before_record':prior['before_record'] if prior else None,'requires_source_policy':True})
    for campaign in ('cypriot-expansion-20260914','cypriot-more-20260914'):
        for prior in read(ROOT/'docs/research'/campaign/'application-plan.json')['works']:
            if prior['artist'] not in ('victor-ioannides','joseph-chourri'):continue
            artist=artists['cypriot-painter-'+prior['artist']]
            raw,receipt=fetch(prior['source_url']);soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
            date=prior['date'];expected_year=str(date['last'])
            if expected_year not in text or ('Joseph Chourri' not in text and 'Βίκτωρα Ιωαννίδη' not in text):
                raise ValueError('Archive creator/date differs')
            links=list(dict.fromkeys(a['href'] for a in soup.select('a[href]') if '/files/original/' in a['href']))
            if len(links)!=1:raise ValueError('Archive reproduction is ambiguous')
            old_record=next(w for w in read(RUN/'catalogue/local'/(artist['id']+'.json')) if w['artwork_id']==prior['id'])
            fields={element.select_one('h3').get_text(' ',strip=True):element.get_text(' ',strip=True) for element in soup.select('.element') if element.select_one('h3')}
            selected.append({'id':prior['id'],'slug':old_record['slug'],'artist':artist,'title':old_record['title'],
                'date_display':old_record['date_display'],'creation_year_start':old_record['creation_year_start'],'creation_year_end':old_record['creation_year_end'],
                'date_precision':old_record['date_precision'],'work_type':old_record['work_type'],'source_url':prior['source_url'],
                'scheme':prior['source_scheme'],'source_id':prior['source_record_id'],'image_url':links[0],
                'source_receipt':receipt,'source_metadata':fields,'rights_status':'restricted','license_label':'Source requires written consent for reproduction',
                'license_url':prior['source_url'],'creator_credit':artist['display_name']+'; '+('Holy Monastery of Saint Neophytos' if prior['artist']=='joseph-chourri' else 'Pattichion Municipal Museum; Phedonas Potamitis Collection')+'; Apsida, Cyprus University of Technology',
                'rights_basis':'The archive’s written-consent restriction is retained. User explicitly authorized the same Cyprus museum/artist collection policy; no permission from the copyright holder is asserted.',
                'selection_basis':'Fill an existing image gap in the selected Cyprus collection; source museum/archive provenance retained.',
                'attribution_basis':'Archive description names the painter; the monastery/museum contributor is not treated as the historical creator.',
                'new_record':False,'before_record':old_record['before_record'],'requires_source_policy':True})
    m.save_atomic(RUN/'museum-selected.json',selected);m.save_atomic(RUN/'museum-date-holds.json',held)
    print('Selected museum/archive images',len(selected),'new artworks',sum(w['new_record'] for w in selected),flush=True)


def prepare_open():prepare('open-selected.json')
def prepare_museum():prepare('museum-selected.json')
def prepare_supplement():prepare('supplement-selected.json')


def select_supplement():
    artists={r['artist']['slug']:r['artist'] for r in read(RUN/'baseline.json')['targets']['local']}
    selected=[];held=[]
    artist=artists['cypriot-painter-victor-ioannides']
    index=read(RUN/'ioannides-archive-index.json')
    # Bounded owner highlights: 24 of 289 archive entries, with variety across genres.
    omitted={74,127,159,191}
    for n,raw in enumerate(index):
        if not raw['years'] or max(raw['years'])>1955:continue
        if n in omitted:
            held.append({'record':raw,'reason':'Outside the bounded 24-work owner highlight selection; preserve metadata for later review.'});continue
        years=raw['years']
        if len(years)!=1:raise ValueError('Artist archive date needs review')
        year=years[0];image_name=raw['image_url'].rsplit('/',1)[1]
        medium=re.split(r'\s*[-–]\s*'+str(year),raw['caption'].lstrip('('))[0].strip()
        work_type='drawing' if raw['category']=='caricatures' else ('unknown' if raw['category']=='mixed-technique' else 'painting')
        selected.append({'id':uid('ioannides/'+image_name),'slug':'cyprus-images-ioannides-'+uid(image_name),
            'artist':artist,'title':raw['title'],'date_display':str(year),'creation_year_start':year,'creation_year_end':year,
            'date_precision':'exact','work_type':work_type,'medium_text':medium,'source_url':raw['source_url'],
            'scheme':'victor-ioannides-archive','source_id':image_name,'image_url':raw['image_url'],
            'source_receipt':raw['source_receipt'],'source_metadata':raw,'rights_status':'restricted',
            'license_label':'© 2019 Victor Ioannides. All Rights Reserved.','license_url':raw['source_url'],
            'creator_credit':artist['display_name']+'; Victor Ioannides artist archive; '+raw['caption'],
            'rights_basis':'Artist archive copyright retained. User explicitly extended the collection workflow to Cyprus artist sources; no independently obtained licence claimed.',
            'selection_basis':'Personal owner highlight selected from the artist archive: a bounded selection of early portraits, landscapes, still lifes, genre scenes and works on paper; not a museum designation.',
            'attribution_basis':'The artist archive associates this title, dated caption and exact image in one portfolio item.',
            'new_record':True,'requires_source_policy':True})
    if len(selected)!=24:raise ValueError('Bounded artist selection differs')
    url='https://leventisgallery.org/artworks/tremetiousia/'
    raw,receipt=fetch(url);soup=BeautifulSoup(raw,'html.parser');body=soup.get_text(' ',strip=True)
    image_urls=list(dict.fromkeys(a['href'] for a in soup.select('a[href]') if '473-George-Pol.' in a['href']))
    if len(image_urls)!=1 or '1955' not in body or 'AGLG 473' not in body:raise ValueError('Museum identity differs')
    artist=artists['cypriot-painter-george-pol-georghiou']
    selected.append({'id':uid('leventis/AGLG473'),'slug':'cyprus-images-tremetiousia-aglg473','artist':artist,
        'title':'Tremetiousia','date_display':'1955','creation_year_start':1955,'creation_year_end':1955,
        'date_precision':'exact','work_type':'painting','medium_text':'Oil on plywood','accession_number':'AGLG 473',
        'source_url':url,'scheme':'leventis-gallery-artwork','source_id':'AGLG 473','image_url':image_urls[0],
        'source_receipt':receipt,'source_metadata':{'page_text':body},'rights_status':'unknown',
        'license_label':'No reuse licence verified','license_url':url,'creator_credit':'George Pol. Georghiou; A. G. Leventis Gallery',
        'rights_basis':'User-authorized Cyprus museum collection workflow; unresolved reproduction permission retained.',
        'selection_basis':'Personal highlight from the museum’s Cyprus collection. Museum provenance is evidenced in the citation; no current display claim.',
        'attribution_basis':'Museum record AGLG 473 explicitly identifies the 1955 oil painting, distinguishing it from the 1957 lithograph.',
        'new_record':True,'requires_source_policy':True})
    artist=artists['cypriot-painter-giovanni-kyprios']
    prior=next(w for w in read(RUN/'catalogue/local'/(artist['id']+'.json')) if w['id' if 'id' in w else 'artwork_id']=='48c8d4d5-9caa-5e9f-86e6-8ca873b7d460')
    pdf=ROOT/'docs/research/cypriot-expansion-20260914/primary-captures/venice-routes.pdf'
    receipt={**read(pdf.with_suffix('.receipt.json')),'path':str(pdf.relative_to(ROOT))}
    if m.core.sha(pdf.read_bytes())!=receipt['sha256']:raise ValueError('PDF evidence differs')
    original=Path('/tmp/artline-cyprus-pdf-images/image-000.jpg').read_bytes()
    m.save_atomic(ORIGINALS/(prior['artwork_id']+'.original'),original)
    image_evidence={'pdf_page':76,'printed_page':77,'figure':100,'pdf_image_object':320,
        'extraction_command':'pdfimages -f 76 -l 76 -j venice-routes.pdf image','embedded_sha256':m.core.sha(original),
        'original_width':586,'original_height':384,'photograph_credit':'Michalis Theocharides, credited for figure 100 on printed page 2',
        'review':'Full embedded dome photograph inspected beside source caption. No crop, no compositing; source includes surrounding architecture.'}
    m.save_atomic(RUN/'dome-extraction-receipt.json',image_evidence)
    selected.append({'id':prior['artwork_id'],'slug':prior['slug'],'artist':artist,'title':prior['title'],
        'date_display':prior['date_display'],'creation_year_start':prior['creation_year_start'],'creation_year_end':prior['creation_year_end'],
        'date_precision':prior['date_precision'],'work_type':prior['work_type'],'source_url':receipt['url']+'#page=76',
        'scheme':'cypriot-more-object','source_id':'kyprios-dome','image_url':receipt['url']+'#page=76',
        'source_receipt':receipt,'source_metadata':image_evidence,'rights_status':'unknown','license_label':'No reproduction licence verified for this photograph',
        'license_url':receipt['url'],'creator_credit':'Giovanni Kyprios; photograph: Michalis Theocharides; Cyprus Tourism Organisation, Cyprus–Venice Cultural Routes, 2011, figure 100',
        'rights_basis':'The medieval artwork and the modern photograph are distinguished. Photographer credit retained; no public-domain claim for the photo. User-authorized Cyprus heritage source collection workflow.',
        'selection_basis':'Fill the existing selected dome-fresco record using the documented complete source photograph.',
        'attribution_basis':'The Cyprus Tourism catalogue explicitly dates the dome frescoes by Ioannis Kyprios to 1589–1590 and captions this exact dome photograph.',
        'new_record':False,'before_record':prior['before_record'],'requires_source_policy':True})
    m.save_atomic(RUN/'supplement-selected.json',selected);m.save_atomic(RUN/'supplement-selection-holds.json',held)
    print('Supplement selected',len(selected),'new records',sum(w['new_record'] for w in selected),flush=True)


def prepare(filename):
    for work in read(RUN/filename):
        path=RUN/'prepared'/(work['id']+'.json')
        if path.exists() or (RUN/'prepared-held'/path.name).exists():continue
        original=ORIGINALS/(work['id']+'.original')
        if original.exists():raw=original.read_bytes()
        else:
            parsed=urlsplit(work['image_url'])
            download_url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,'','')) if parsed.netloc=='upload.wikimedia.org' else work['image_url']
            response=m.requests.get(download_url,headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected catalogue research)'},timeout=(15,45));response.raise_for_status();raw=response.content
            if len(raw)>20_000_000:raise ValueError('Selected image exceeds original limit')
            m.save_atomic(original,raw)
        if work.get('commons_sha1') and (hashlib.sha1(raw).hexdigest()!=work['commons_sha1'] or len(raw)!=work['commons_size']):
            raise ValueError('Selected Commons original differs')
        content,width,height,quality=m.core.compress(raw);checksum=m.core.sha(content)
        image_path='/assets/artworks/imported/cyprus-images-20260920/'+work['id']+'-'+checksum[:16]+'.jpg'
        if len(content)>100000:raise ValueError('Derivative exceeds image size limit')
        m.save_atomic(ROOT/'apps/web/public'/image_path.lstrip('/'),content)
        prepared={'work':work,'id':uid('media/'+checksum),'path':image_path,'sha256':checksum,'bytes':len(content),
            'width':width,'height':height,'quality':quality,'original':str(original),'original_sha256':m.core.sha(raw),'checked_at':m.core.now()}
        m.save_atomic(path,prepared)
        print('Prepared',work['title'],len(content),'bytes',flush=True)


def target_state(db,im):
    w=im['work']
    artist=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE slug=%s',(w['artist']['slug'],)).fetchone()
    if not artist or not m.same_artwork(artist['record'],w['artist']):raise ValueError('Painter identity changed')
    exact=db.execute("""SELECT a.id::text FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
        WHERE e.scheme=%s AND e.external_id=%s""",(w['scheme'],w['source_id'])).fetchall()
    record=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(w['id'],)).fetchone()
    record=record['record'] if record else None
    if any(r['id']!=w['id'] for r in exact):raise ValueError('Source identifier belongs to another artwork')
    if w['new_record']:
        if record is not None and record['primary_media_id']!=im['id']:raise ValueError('New artwork ID is already occupied')
        duplicates=db.execute("""SELECT a.id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            WHERE aa.artist_id=%s AND a.normalized_title=%s AND a.status<>'archived' AND a.id<>%s""",
            (artist['record']['id'],m.norm(w['title']),w['id'])).fetchall()
        if duplicates:raise ValueError('Existing painter/title needs reconciliation')
    elif (record is None or not m.same_artwork(record,w['before_record'])
        or record['current_institution_id']!=w['before_record']['current_institution_id']):raise ValueError('Existing artwork identity differs')
    creators=db.execute("""SELECT p.slug,aa.attribution_role FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id
        WHERE aa.artwork_id=%s ORDER BY p.slug""",(w['id'],)).fetchall() if record else []
    if record and creators!=[{'slug':w['artist']['slug'],'attribution_role':'primary'}]:raise ValueError('Artwork creator differs')
    if record and record['primary_media_id'] not in (None,im['id']):raise ValueError('Existing primary image preserved')
    return {'artist':artist['record'],'artwork':record,'creators':creators,'source_identifiers':exact}


def plan_delivery():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    if not (RUN/'visual-review-approved.json').exists():raise ValueError('Visual review is incomplete')
    approved=read(RUN/'visual-review-approved.json')['approved']
    if {i['work']['id']:i['sha256'] for i in images}!=approved:raise ValueError('Visual review does not cover exact images')
    if len({i['id'] for i in images})!=len(images):raise ValueError('Duplicate selected image')
    for im in images:
        if im['work']['creation_year_end'] is None or im['work']['creation_year_end']>1955:raise ValueError('Image date is ineligible')
        if m.core.sha(Path(im['original']).read_bytes())!=im['original_sha256']:raise ValueError('Original differs')
        source=im['work']['source_receipt']
        if m.core.sha((ROOT/source['path']).read_bytes())!=source['sha256']:raise ValueError('Source receipt differs')
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            for im in images:
                path=RUN/'delivery-plans'/target/(im['work']['id']+'.json')
                if path.exists():continue
                state=target_state(db,im);backup=BACKUP/'preimages'/target/path.name
                media=db.execute('SELECT to_jsonb(ma) record FROM media_assets ma WHERE id=%s',(im['id'],)).fetchone()
                if media:raise ValueError('Selected media ID already exists')
                duplicates=db.execute('SELECT id::text FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchall()
                if duplicates:raise ValueError('Exact image already exists and needs reconciliation: '+im['work']['title'])
                m.save_atomic(backup,{'target':state,'media_before':media})
                m.save_atomic(path,{'state':state,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes())})
            print('Recovery plans',target,len(images),flush=True)


def apply_one(db,im,target):
    w=im['work'];plan=read(RUN/'delivery-plans'/target/(w['id']+'.json'))
    if m.core.sha(Path(plan['backup']).read_bytes())!=plan['backup_sha256']:raise ValueError('Recovery preimage differs')
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    with db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(plan['state']['artist']['id'],))
        current=target_state(db,im)
        if current['artwork'] and current['artwork']['primary_media_id']==im['id']:
            return {'outcome':'already_attached','created':w['new_record'],'after':current['artwork']}
        if current!=plan['state']:raise ValueError('Target changed after recovery snapshot')
        sid=db.execute("""INSERT INTO sources(id,slug,name,source_type,base_url)
            VALUES(%s,'cyprus-images-20260920','Cyprus painters: selected museum, artist and heritage image evidence','collection_page','https://leventisgallery.org/')
            ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id""",(uid('source'),)).fetchone()['id']
        if w['new_record']:
            db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
                work_type,medium_text,accession_number,status,research_candidate,created_by,updated_by)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",
                (w['id'],w['slug'],w['title'],m.norm(w['title']),w['date_display'],w['creation_year_start'],w['creation_year_end'],w['date_precision'],
                 w['work_type'],w.get('medium_text'),w.get('accession_number'),m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                (w['id'],current['artist']['id'],w['attribution_basis']))
            db.execute("""INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                VALUES('artwork',%s,%s,%s,%s,%s,%s)""",(w['id'],w['scheme'],w['source_id'],w['source_url'],sid,im['checked_at']))
        credit=w['creator_credit']+'. Source frame preserved; proportionally resized and JPEG compressed.'
        db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
            checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
            VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (im['id'],im['path'],w['source_url'],'Wikimedia Commons' if w['scheme']=='commons-artwork' else 'Cyprus museum/artist source',
             im['width'],im['height'],im['bytes'],im['sha256'],w['title']+' — '+w['artist']['display_name'],w['rights_status'],w['license_label'],
             w['license_url'],w['creator_credit'],credit,im['checked_at'],im['checked_at'] if w['rights_status'] in ('public_domain','cc0','cc_by','cc_by_sa') else None,m.ACTOR))
        db.execute("""INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,
            rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,'cyprus-selected-v1',%s,%s)""",
            (im['id'],sid,w['source_id'],w['source_receipt']['sha256'],w['image_url'],w['license_url'],w['rights_basis'],im['checked_at'],m.Jsonb(im)))
        db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
            VALUES('artwork',%s,%s,'cyprus_image_identity',%s,%s,%s,%s,%s)""",
            (w['id'],sid,w['source_id'],w['source_url'],json.dumps(w,ensure_ascii=False),im['checked_at'],m.ACTOR))
        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',
            (im['id'],m.ACTOR,w['id']))
        already=db.execute('SELECT artline_has_selection_evidence(%s) selected',(w['id'],)).fetchone()['selected']
        if w['new_record'] or not already:
            collection=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
            if collection['curator_kind']!='owner' or collection['institution_id'] is not None:raise ValueError('Personal collection identity differs')
            before_items=db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE collection_id=%s AND artwork_id=%s',(collection_id,w['id'])).fetchall()
            m.save_atomic(BACKUP/'personal-selection'/target/(w['id']+'.json'),{'collection':collection,'items':before_items})
            db.execute("""INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                SELECT %s,%s,coalesce(max(position),0)+1,%s,%s,%s,%s FROM curated_collection_items WHERE collection_id=%s
                ON CONFLICT(collection_id,artwork_id) DO NOTHING""",(collection_id,w['id'],w['selection_basis'],sid,w['source_url'],im['checked_at'],collection_id))
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
        after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(w['id'],)).fetchone()['record']
    return {'outcome':'attached','created':w['new_record'],'before':plan['state']['artwork'],'after':after}


def deliver():
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    for im in images:
        output=RUN/'uploads'/(im['work']['id']+'.json')
        if output.exists():continue
        data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if m.core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Selected image differs')
        blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'artwork-id':im['work']['id']};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except m.PreconditionFailed:blob.reload(timeout=30)
        if blob.size!=len(data) or blob.md5_hash!=m.base64.b64encode(hashlib.md5(data).digest()).decode():raise ValueError('Uploaded bytes differ')
        m.save_atomic(output,{'at':m.core.now(),'path':im['path'],'sha256':im['sha256'],'generation':blob.generation})
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            for im in images:
                path=RUN/'applied'/target/(im['work']['id']+'.json')
                if path.exists():continue
                result=apply_one(db,im,target);m.save_atomic(path,result)
                print('Attached',target,im['work']['artist']['display_name'],im['work']['title'],flush=True)


def verify():
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    expected={im['work']['id']:im for im in images};errors=[];targets={};baseline=read(RUN/'baseline.json')
    ignored={'primary_media_id','revision','updated_at','updated_by'}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.read_only(dsn) as db:
            ids=list(expected)
            rows=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(ma) media,
                artline_has_selection_evidence(a.id) selected FROM artworks a
                JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])''',(ids,)).fetchall()
            byid={r['artwork']['id']:r for r in rows};checks=[]
            for aid,im in expected.items():
                w=im['work'];r=byid.get(aid);receipt_path=RUN/'applied'/target/(aid+'.json')
                problems=[]
                if not r or not receipt_path.exists():
                    errors.append({'target':target,'artwork_id':aid,'error':'Missing artwork/media or delivery receipt'});continue
                receipt=read(receipt_path);media=r['media']
                if r['artwork']!=receipt['after']:problems.append('Artwork differs from committed receipt')
                if not r['selected']:problems.append('Missing owner or museum selection evidence')
                for k,v in {'id':im['id'],'storage_path':im['path'],'checksum_sha256':im['sha256'],'byte_size':im['bytes'],
                    'width':im['width'],'height':im['height'],'rights_status':w['rights_status'],'source_page_url':w['source_url'],
                    'license_label':w['license_label'],'license_url':w['license_url'],'creator_credit':w['creator_credit']}.items():
                    if media[k]!=v:problems.append('Media field differs: '+k)
                if w['rights_status'] in ('unknown','restricted') and media['verified_at'] is not None:problems.append('Unresolved rights incorrectly verified')
                evidence=db.execute('SELECT evidence_json FROM media_rights_evidence WHERE media_id=%s',(im['id'],)).fetchall()
                if [e['evidence_json'] for e in evidence]!=[im]:problems.append('Source evidence differs')
                citations=db.execute("SELECT evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='cyprus_image_identity'",(aid,)).fetchall()
                if len(citations)!=1 or json.loads(citations[0]['evidence_note'])!=w:problems.append('Identity citation differs')
                state=target_state(db,im)
                if w['new_record'] and (state['artwork']['status']!='review' or not state['artwork']['research_candidate'] or state['artwork']['current_institution_id'] is not None):
                    problems.append('New record review/holding state differs')
                checks.append({'artwork_id':aid,'verified':not problems,'new_record':w['new_record']})
                errors.extend({'target':target,'artwork_id':aid,'error':p} for p in problems)
            cohort=[]
            for before in baseline['targets'][target]:
                artist=before['artist'];current=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(artist['id'],)).fetchone()['record']
                if current!=artist:errors.append({'target':target,'artist_id':artist['id'],'error':'Painter profile changed'})
                countries=db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=%s',(artist['id'],)).fetchall()
                if sorted([r['record'] for r in countries],key=lambda x:x['country_code'])!=sorted(before['countries'] or [],key=lambda x:x['country_code']):
                    errors.append({'target':target,'artist_id':artist['id'],'error':'Painter country association changed'})
                works=c.artist_works(db,artist['id']);now={w['artwork_id']:w for w in works}
                old=read(RUN/'catalogue'/target/(artist['id']+'.json'))
                for previous in old:
                    wid=previous['artwork_id'];latest=now.get(wid);excluded=ignored if wid in expected else set()
                    if not latest or {k:v for k,v in latest['before_record'].items() if k not in excluded}!={k:v for k,v in previous['before_record'].items() if k not in excluded}:
                        errors.append({'target':target,'artwork_id':wid,'error':'Existing artwork metadata changed'})
                cohort.append({'artist_id':artist['id'],'artist':artist['display_name'],'slug':artist['slug'],
                    'before_works':before['works'],'before_images':before['images'],
                    'after_works':sum(w['status']!='archived' for w in works),
                    'after_images':sum(w['status']!='archived' and w['primary_media_id'] is not None for w in works),
                    'remaining_gaps':[{'artwork_id':w['artwork_id'],'title':w['title'],'date_display':w['date_display'],
                        'creation_year_start':w['creation_year_start'],'creation_year_end':w['creation_year_end'],
                        'reason':'Creation date unresolved' if w['creation_year_end'] is None else ('After the 1955 image cutoff' if w['creation_year_end']>1955 else 'No selected, exact-object image identified in reviewed sources')}
                        for w in works if w['status']!='archived' and w['primary_media_id'] is None]})
            targets[target]={'verified':sum(x['verified'] for x in checks),'checks':checks,'cohort':cohort}
    base='https://artline-web-lpuqqlugnq-ew.a.run.app'
    def check_public(im):
        w=im['work'];local=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        result={'artwork_id':w['id'],'local_file_verified':m.core.sha(local)==im['sha256'] and len(local)==im['bytes'] and len(local)<=100000}
        try:
            response=m.requests.get(base+im['path'],timeout=(15,45))
            result.update(file_http_status=response.status_code,public_file_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
            response=m.requests.get(base+'/api/backend/v1/artists/'+w['artist']['slug']+'/works/'+w['id'],timeout=(15,45))
            data=response.json() if response.status_code==200 else {}
            result.update(api_http_status=response.status_code,api_verified=response.status_code==200 and data.get('title')==w['title'] and data.get('media_url')==im['path'])
        except m.requests.RequestException as e:result.update(error=str(e)[:200])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:public=list(pool.map(check_public,images))
    errors.extend({'error':'Public delivery check failed',**r} for r in public if not all(r.get(k) for k in ('local_file_verified','public_file_verified','api_verified')))
    result={'at':m.core.now(),'images':len(images),'new_artworks':sum(im['work']['new_record'] for im in images),
        'existing_gaps_filled':sum(not im['work']['new_record'] for im in images),'painters_with_additions':len({im['work']['artist']['id'] for im in images}),
        'rights':dict(collections.Counter(im['work']['rights_status'] for im in images)),
        'maximum_bytes':max(im['bytes'] for im in images),'total_bytes':sum(im['bytes'] for im in images),
        'targets':targets,'public_checks':public,'errors':errors}
    path=RUN/('verification-'+str(int(time.time()))+'.json');m.save_atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('targets','public_checks')},ensure_ascii=False),flush=True)
    print('Verification receipt',path,flush=True)
    if errors:raise SystemExit(1)


def report():
    verification_path=max(RUN.glob('verification-*.json'),key=lambda p:p.stat().st_mtime)
    result=read(verification_path)
    if result['errors']:raise ValueError('Delivery verification has unresolved errors')
    images=[read(p) for p in sorted((RUN/'prepared').glob('*.json'))]
    cohort=result['targets']['local']['cohort'];cloud=result['targets']['cloud']['cohort']
    if {r['artist_id']:r for r in cohort}!={r['artist_id']:r for r in cloud}:raise ValueError('Cohort totals differ across databases')
    additions=collections.Counter(im['work']['artist']['id'] for im in images)
    new=collections.Counter(im['work']['artist']['id'] for im in images if im['work']['new_record'])
    gaps=[{'artist':row['artist'],'artist_id':row['artist_id'],**gap} for row in cohort for gap in row['remaining_gaps']]
    reasons=collections.Counter(g['reason'] for g in gaps)
    totals={'painters':len(cohort),'artworks':sum(r['after_works'] for r in cohort),'images':sum(r['after_images'] for r in cohort),
        'remaining_image_gaps':len(gaps),'painters_without_artwork_records':sum(r['after_works']==0 for r in cohort),
        'painters_with_images':sum(r['after_images']>0 for r in cohort),'gap_reasons':dict(reasons)}
    m.save_atomic(RUN/'remaining-image-gaps.json',gaps)
    m.save_atomic(RUN/'final-verification.json',result);m.save_atomic(RUN/'cyprus-totals.json',totals)
    inventory=[]
    for im in sorted(images,key=lambda x:(x['work']['artist']['display_name'],x['work']['title'])):
        w=im['work'];inventory.append({'artist':w['artist']['display_name'],'artwork_id':w['id'],'title':w['title'],
            'date_display':w['date_display'],'new_artwork':w['new_record'],'source_url':w['source_url'],
            'image_source_url':w['image_url'],'rights_status':w['rights_status'],'image_path':im['path'],
            'bytes':im['bytes'],'sha256':im['sha256']})
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(inventory[0]));writer.writeheader();writer.writerows(inventory)
    m.save_atomic(RUN/'delivered-artworks.csv',out.getvalue().encode())
    m.save_atomic(RUN/'painter-coverage.json',cohort)
    lines=['# Cyprus painter images — 20 September 2026','',
        f"Completed in **local and production**: **{result['images']} image attachments**, including **{result['existing_gaps_filled']} existing image gaps** and **{result['new_artworks']} new review artworks**, across **{result['painters_with_additions']} painters**.",'',
        f"All **{totals['painters']} existing Cyprus-linked painter profiles** were audited. The cohort now contains **{totals['artworks']} artworks and {totals['images']} images**, up from 93 works and 33 images. This is a selected expansion, not a complete illustrated catalogue: {len(gaps)} recorded works still lack images, and {totals['painters_without_artwork_records']} profiles still have no sourced artwork records.",'',
        '[View Cyprus in Artline](https://artline-web-lpuqqlugnq-ew.a.run.app/?country=CY&popular=false). The popularity filter is disabled so the Cyprus research collection is included.','',
        '## Coverage','',
        '| Painter | New works | Added images | Total works | Total images | Remaining image gaps |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    lines.extend(f"| {r['artist']} | {new[r['artist_id']]} | {additions[r['artist_id']]} | {r['after_works']} | {r['after_images']} | {len(r['remaining_gaps'])} |" for r in cohort)
    lines.extend(['','## Sources and selection','',
        'WikiArt’s Cyprus directory and bounded Commons metadata searches were reviewed for all 27 existing painters. The WikiArt directory supplied no matching eligible painter profile. The user explicitly extended the WikiArt collection workflow to Cyprus museum and artist sources, retaining the 1955 artwork-creation cutoff, source links and actual rights labels. See [policy authorization](source-policy-authorization.json) and [image policy](../../ARTLINE_IMAGE_USE.md).','',
        '- The [Leventis five-pioneer catalogue](https://cypriotartists.leventisgallery.org/en) was checked at object level: 53 works, with dated selections for Georghiou, Loukia Nicolaides-Vassiliou and Solomos Frangoulides. Seven additional Loukia works are new review records. Undated Kissonerghis works and later Diamantis paintings retain their image gaps.',
        '- The current museum pages identify Georghiou’s [Tremetiousia, AGLG 473](https://leventisgallery.org/artworks/tremetiousia/) as the 1955 oil painting, distinct from the later lithograph, and Michaeledes’s [Those Left Behind, AGLG 504](https://leventisgallery.org/artworks/those-left-behind/) as a 1950 painting.',
        '- [Victor Ioannides’s artist archive](https://victor-ioannides.com/) supplied 289 portfolio entries across ten categories. Twenty-four early works were selected as personal highlights from 28 entries with explicit dates ending by 1955. Four eligible entries were left outside this bounded selection. The full index and dated captions remain in [archive metadata](ioannides-archive-index.json).',
        '- The Apsida archive supplies all seven existing [Joseph Chourri icons](https://apsida.cut.ac.cy/items/show/15208), dated 1544, and Ioannides’s [Portrait of Leukios Zenon](https://apsida.cut.ac.cy/items/show/23267), dated 1939. The archive’s written-consent restrictions remain recorded.',
        '- Three distinct fresco scenes use Commons per-file public-domain reproduction evidence: one Apsevdis Pantocrator and two Symeon Axentis scenes at the Church of the Archangel/Theotokos in Galata. The tourism guide’s named 1514 attribution is retained alongside Commons’ less-specific metadata; nearby Podithou decoration is not assigned to Axentis.',
        '- The [Cyprus Tourism Organisation’s Venice guide](https://www.visitcyprus.com/wp-content/uploads/2015/11/Cyprus_Venice_Cultural_Routes_2011_EN.pdf#page=76) supplies the exact Kyprios dome photograph, figure 100. The complete embedded JPEG was extracted without cropping; the source credits **Michalis Theocharides**. The 1589–1590 dome record is preserved. The 1593 bema Ascension remains an image gap.',
        '',
        '## Review state and remaining gaps','',
        f"Remaining gaps: **{reasons['After the 1955 image cutoff']} works after 1955**, **{reasons['Creation date unresolved']} with unresolved creation dates**, and **{reasons['No selected, exact-object image identified in reviewed sources']} without a selected exact-object image**. See [every remaining gap](remaining-image-gaps.json). Missing artwork records for {totals['painters_without_artwork_records']} profiles were preserved without inventing titles or dates. Artist biographies, country relationships, publication state and prior primary images were preserved.",
        '',
        'One prepared Apsevdis candidate labelled Virgin and Child remains held: its image depicts the Flight into Egypt and the attribution requires reconciliation. Its source, original and derivative were retained, without creating an artwork or attaching an image. Four other dated Ioannides entries remain metadata-only selection leads. Unknown museum dates and later paintings were not made eligible by using the painter’s lifespan.',
        '',
        f"Rights labels for the {result['images']} attached reproductions: "+', '.join(f"**{v} {k}**" for k,v in sorted(result['rights'].items()))+'. The user’s workflow authorization is not recorded as permission from a copyright holder. Unresolved/restricted media have no rights-verification timestamp. All source links and actual restrictions remain in the database. New works remain `review` / `research_candidate` and are personal owner selections, without accepted museum holdings or current-on-view assertions.',
        '',
        '## Delivery and verification','',
        f"All {result['images']} derivatives were visually inspected and preserve the full supplied frame. The largest is **{result['maximum_bytes']:,} bytes**, below the 100,000-byte limit. Originals remain separately archived. No generated or reconstructed art was used.",
        '',
        f"Read-only final checks verified all {result['images']} artwork/media associations in both databases, exact rights evidence and source citations, review state, personal selection evidence, and preservation of all existing cohort artwork metadata. All {result['images']} public image files returned matching SHA-256 checksums, and all {result['images']} public artwork API responses returned the expected title and image. Verification reported **zero errors**. These are bounded content checks, not a catalogue-scale load test.",
        '',
        'Uploads used conditional creation and byte checks before database references were attached. Each artwork update was transactional, with identity rechecks and exact recovery preimages. No test database, fixture insertion, commit, deployment or infrastructure change was needed.',
        '',
        f"Recovery snapshots and visual review: `{BACKUP}/`. Originals: `{ORIGINALS}/`. Application images: `apps/web/public/assets/artworks/imported/cyprus-images-20260920/`.",
        '',
        '[Delivered artwork inventory](delivered-artworks.csv) · [all painter coverage](painter-coverage.json) · [final verification](final-verification.json) · [cohort totals](cyprus-totals.json) · [visual review](visual-review-approved.json)',
        ''])
    m.save_atomic(RUN/'README.md','\n'.join(lines).encode())
    for name in ('README.md','final-verification.json','painter-coverage.json','delivered-artworks.csv','cyprus-totals.json','visual-review-approved.json'):
        m.save_atomic(BACKUP/'completion'/name,(RUN/name).read_bytes())
    print(json.dumps(totals,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['audit','discover','museum_candidates','select_open','prepare_open','select_museum','prepare_museum','select_supplement','prepare_supplement','plan_delivery','deliver','verify','report'])
    globals()[parser.parse_args().phase]()
