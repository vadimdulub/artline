#!/usr/bin/env python3
"""Selected independent photos compared with exact official catalogue sheets.

No fabricated Wikidata entities. Native SIRBeC identity and human comparison of
the official catalogue reproduction with the independent photograph are required
before attachment. Catalogue PDF reproductions themselves are never uploaded.
"""
import argparse
import collections
import importlib.util
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
x=module('crosswalk','italy-image-crosswalks.py')
p=module('official_pdf','italy-catalogue-pdf-evidence.py')
c,w=x.c,x.w
dual=module('photographic_licence','italy-photo-licence.py')
PROVIDER='italy-primary-photo'
PHOTOS={
    'B0020-00116':48553909, 'B0020-00017':48540302,
    'B0010-00481':48540300, 'B0020-00434':48526566,
    'C0050-00078':165471882, 'C0050-00711':165469276,
    'L0090-00002':128913142, 'B0050-00060':62644278,
    'B0030-00124':48553893, 'B0030-00125':48553897,
    'C0050-01313':165470471, 'B0030-00207':48540765,
    'B0050-00044':62644185, 'B0020-00326':6544410,
    'B0020-00429':48540781, 'B0020-00151':88461889,
    'C0050-00613':165469249, '2d020-00893':62644518,
    'B0010-00488':48553918,
}

def select(label,cohort='direct-photo-discovery',source_round=None,rights_source_round=None):
    run=c.RUN/label
    if (run/'candidates.json').exists():return
    used={r['artwork_id'] for f in c.RUN.glob('*/candidates.json') for r in c.load(f)['candidates']}
    previous={}
    if rights_source_round:
        source=c.RUN/rights_source_round
        events=c.core.latest_events(source)
        source_rows=[r for r in c.load(source/'candidates.json')['candidates']
                     if events.get(r['artwork_id'],{}).get('reason')=='Explicit rendered image licence absent or conflicting'
                     and not c.institution_policy_reason(r)]
        used-={r['artwork_id'] for r in source_rows}
    elif source_round:
        source=c.RUN/source_round
        previous={r['artwork_id']:r for r in c.load(source/'visual-review.json')['images'] if r['outcome']=='held'}
        used-=set(previous)
        source_rows=[r for r in c.load(source/'candidates.json')['candidates'] if r['artwork_id'] in previous]
    else:
        source_rows=c.load(c.RUN/cohort/'selected-existing-gaps.json')['records']
    records=[]
    for row in source_rows:
        if row['artwork_id'] in used:continue
        identifiers=[i for i in row['identifiers'] if i['id'] in PHOTOS]
        if len(identifiers)!=1:continue
        i=identifiers[0]
        record=dict(row,provider=PROVIDER,scheme=i['scheme'],external_id=i['id'],
            page=i['url'],artist='; '.join(a['name'] for a in row['creators']),
            commons_pageid=PHOTOS[i['id']],native_catalogue_url=i['url'])
        if row['artwork_id'] in previous:
            prior=previous[row['artwork_id']]
            if PHOTOS[i['id']]==prior.get('primary_catalogue_comparison',{}).get('commons_pageid'):
                raise ValueError('A visually rejected file cannot be selected again')
            record['previous_visual_hold']={'round':source_round,'review':prior}
        if row['institution_slug'] in x.MUSEUMS:
            verified_site=x.MUSEUMS[row['institution_slug']][1]
            if verified_site!=record.get('website_url'):
                record['holding_website_resolution']={'catalogue_value':record.get('website_url'),
                    'verified_official_url':verified_site,'source':'Previously verified institution authority/name/location in italy-image-crosswalks.py',
                    'catalogue_metadata_write':False}
                record['website_url']=verified_site
        records.append(record)
    local=c.snapshot(records,'postgres://127.0.0.1/artline');cloud=c.snapshot(records,c.core.cloud_dsn())
    indexes=[]
    for group in (local,cloud):
        idx=collections.defaultdict(list)
        for row in group:idx[row['local_id']].append(row)
        indexes.append(idx)
    selected=[];held=[]
    for record in records:
        groups=[idx[record['artwork_id']] for idx in indexes]
        if any(len(g)!=1 for g in groups):
            held.append(dict(record,reason='Ambiguous current database target'));continue
        before=[g[0] for g in groups]
        if any(v['primary_media_id'] or v['date_scope']!='eligible' or not v['selected'] or v['status']=='archived' for v in before):
            held.append(dict(record,reason='Current eligibility/media differs'));continue
        if any(any(v[k]!=record[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')) for v in before):
            held.append(dict(record,reason='Current object metadata differs'));continue
        record['target_ids']={t:v['target_id'] for t,v in zip(('local','cloud'),before)}
        selected.append(record)
    c.save(run/'candidates.json',{'selected_at':c.core.now(),'candidates':selected,
        'selection':'Existing eligible Italy museum objects; selected photographic leads require exact primary catalogue and visual comparison before attachment'})
    c.save(run/'local-before.json',local);c.save(run/'cloud-before.json',cloud);c.save(run/'selection-held.json',held)
    print(label,'selected',len(selected),'held',len(held),flush=True)

def original_source_context(record,page):
    """Resolve only the Academy's explicitly linked historical collection portal."""
    meta=page.get('imageinfo',[{}])[0].get('extmetadata',{})
    source=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution'))
    alias='raccoltestorichedibrera.altervista.org'
    hosts={urlparse(a.get('href','')).hostname for a in BeautifulSoup(source,'html.parser').find_all('a')}
    if alias not in hosts:return record,None
    proof=c.load(c.RUN/'academy-source-portal/resolution.json')
    if record['institution_slug']!='accademia-brera-collections' or proof.get('institution_slug')!=record['institution_slug'] or proof.get('alias_host')!=alias:
        raise ValueError('Historical collection portal belongs to a different institution')
    receipt=proof['capture'];path=(ROOT/receipt['path']).resolve()
    official='https://www.accademiadibrera.milano.it/index.php/it/patrimonio-storico'
    if receipt['url']!=official or receipt.get('resolved_url')!=official or receipt.get('http_status')!=200 or receipt.get('ssl_verify_result')!=0:
        raise ValueError('Official portal relationship transport/identity not verified')
    if not path.is_relative_to(c.RUN.resolve()) or c.core.sha(path.read_bytes())!=receipt['sha256']:
        raise ValueError('Official portal relationship capture checksum/path differs')
    links=BeautifulSoup(path.read_text(),'html.parser').find_all('a')
    if not any(urlparse(a.get('href','')).hostname==alias and 'Raccolte Storiche di Brera' in a.get_text(' ',strip=True) for a in links):
        raise ValueError('Exact named historical collection link absent from official institution page')
    return dict(record,website_url='https://'+alias+'/'),proof

def underlying_creator_evidence(record):
    """Keep a missing biography unchanged; verify the one researched lifetime range."""
    evidence=[]
    for artist in record['creators']:
        if artist['role']!='primary':
            raise ValueError('Underlying artwork attribution needs independent review')
        if artist.get('death'):
            if artist['death']+70>=2026:
                raise ValueError('Underlying artwork copyright needs independent review')
            continue
        if artist.get('qid')!='Q222923' or artist['name']!='Vincenzo Foppa':
            raise ValueError('Missing artist lifetime needs independent primary evidence')
        proof=c.load(c.RUN/'creator-rights/Foppa/lifetime-review.json');receipt=proof['native_pdf']
        pdf=(ROOT/receipt['path']).resolve();textpath=(ROOT/proof['text_path']).resolve()
        if not pdf.is_relative_to(c.RUN.resolve()) or not textpath.is_relative_to(c.RUN.resolve()) or c.core.sha(pdf.read_bytes())!=receipt['sha256'] or c.core.sha(textpath.read_bytes())!=proof['text_sha256']:
            raise ValueError('Native creator lifetime evidence checksum/path differs')
        if receipt['url']!='https://www.lombardiabeniculturali.it/opere-arte/schede-complete/F0010-00920/' or receipt.get('ssl_verify_result')!=0 or receipt.get('http_status')!=200:
            raise ValueError('Native creator lifetime evidence transport/identity differs')
        text=textpath.read_text()
        if proof.get('creator_qid')!=artist['qid'] or proof.get('creator_name')!=artist['name'] or proof.get('latest_death_year_supported')!=1516 or proof.get('death_range_as_written')!='1515/16':
            raise ValueError('Reviewed native creator lifetime range differs')
        for literal in ('Nome di persona o ente: Foppa, Vincenzo','Dati anagrafici/Periodo di attività: 1430-1516','Vincenzo Foppa (1427/30-1515/16)'):
            if literal not in text:raise ValueError('Named creator and lifetime range absent from native catalogue')
        evidence.append(proof)
    if not record['creators']:raise ValueError('Underlying named creator missing')
    return evidence

def file_rights(record,page,sdc,rendered=None):
    """Explicit per-file rights and photographer provenance, independent of Q IDs."""
    if c.institution_policy_reason(record):
        raise ValueError('Institution-specific reproduction permission remains unresolved')
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
    field=lambda k:meta.get(k,{}).get('value','')
    label=field('LicenseShortName');uri=w.canonical_licence_uri(field('LicenseUrl'))
    revision=page.get('revisions',[{}])[0].get('revid')
    if rendered and rendered.get('kind')=='explicit_photographic_licence':
        label,uri=dual.validate(record,page,rendered)
    elif not uri and rendered and rendered.get('pageid')==page.get('pageid') and rendered.get('revid')==revision:
        uri=rendered.get('uri','')
    if label=='Public domain':
        if field('Copyrighted')!='False' or uri!=w.PDM:raise ValueError('Public-domain flag/URI missing or conflicting')
        status='public_domain'
    elif label=='CC0':
        if uri!=w.CC0:raise ValueError('CC0 URI missing or conflicting')
        status='cc0'
    elif re.fullmatch(r'CC BY(?:-SA)? (?:1\.0|2\.0|2\.5|3\.0|4\.0)',label):
        code='by-sa' if 'BY-SA' in label else 'by';version=label.rsplit(' ',1)[-1]
        if uri!=f'https://creativecommons.org/licenses/{code}/{version}/':raise ValueError('Photo licence URI/version mismatch')
        status='cc_by_sa' if code=='by-sa' else 'cc_by'
    else:raise ValueError('Photograph licence not approved')
    if field('Restrictions'):raise ValueError('Explicit image restriction needs review')
    text=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if not revision or not text:raise ValueError('Exact source revision absent')
    if re.search(r'\{\{\s*(?:copyvio|no permission|no source|delete|disputed|wrong license|Not-PD-US)',text,re.I):
        raise ValueError('Commons rights dispute')
    if re.search(r'\b(detail|particolare|dettaglio|verso|reverse|collage|montage)\b',page['title'],re.I):
        raise ValueError('Photograph is labelled as a detail/reverse/composite')
    source=field('Credit')+' '+field('Attribution')
    if re.search(r'lombardiabeniculturali\.it|sirbecweb[^/]*\.partnertecnologico\.it',source,re.I):
        raise ValueError('Regional catalogue reproduction licence not independently cleared for upload')
    origin_record,_=original_source_context(record,page)
    w.origin.verify(origin_record,page)
    if re.search(r'art500k|wikiart|wikipaintings|pinterest|wallpaper|fineartamerica|wga\.hu|web gallery of art|rusmuseum|nationalgallery\.org\.uk',source,re.I):
        raise ValueError('Unapproved original image source')
    if record['institution_slug'] in ('uffizi','european-uffizi','galleria-degli-uffizi'):
        raise ValueError('Institutional publication review outstanding')
    if label=='Public domain' and (w.ids(sdc,'P275')-{'Q98592850','Q19652','Q7257361'} or 'Q50423863' in w.ids(sdc,'P6216')):
        raise ValueError('Structured copyright/licence conflict')
    underlying_creator_evidence(record)
    credit=w.plain(field('Artist'))
    if not credit:raise ValueError('Photographic creator credit missing')
    for key in ('Credit','Attribution'):
        extra=w.plain(field(key))
        if extra and extra not in credit:credit+='; '+extra
    if status in ('cc_by','cc_by_sa'):
        photographers=w.photographic_credits(record,page)
        if not photographers:raise ValueError('Named photographic attribution missing')
        for name in photographers:
            if w.norm(name) not in w.norm(credit):credit+='; Photographic credit: '+name
    if len(credit)>4000:raise ValueError('Unbounded photo attribution')
    original=not info.get('thumburl') and info.get('size',100000000)<=8000000 and info.get('width',10000)*info.get('height',10000)<=40000000
    url=info.get('url') if original else info.get('thumburl')
    if not url or urlparse(url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org'):
        raise ValueError('Unapproved Commons image delivery')
    return info,credit,label,uri,status,url,original

def research(label):
    run=c.RUN/label;fetcher=w.core.Fetcher(run/'metadata/commons-evidence')
    rows=c.load(run/'candidates.json')['candidates']
    done=c.core.latest_events(run)
    for n,record in enumerate(rows,1):
        if record['artwork_id'] in done:continue
        try:
            sid=record['external_id'];url=f'https://www.lombardiabeniculturali.it/opere-arte/schede-complete/{sid}/'
            pdf,receipt=p.capture(url,'.pdf',10000000)
            extracted=pdf.with_suffix('.txt')
            if not extracted.exists():subprocess.run(['pdftotext','-layout',str(pdf),str(extracted)],check=True)
            data=w.api(fetcher,'commons.wikimedia.org',{'action':'query','pageids':record['commons_pageid'],
                'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
            page=data.get('query',{}).get('pages',{}).get(str(record['commons_pageid']))
            if not page or page.get('pageid')!=record['commons_pageid']:raise ValueError('Exact selected Commons page absent')
            sdc=w.api(fetcher,'commons.wikimedia.org',{'action':'wbgetentities','ids':'M'+str(page['pageid'])}).get('entities',{}).get('M'+str(page['pageid']),{})
            try:
                rendered=w.rendered_rights_uri(fetcher,page)
            except ValueError as error:
                if str(error)!='Explicit rendered image licence absent or conflicting':raise
                rendered=dual.resolve(fetcher,record,page)
            info,credit,licence,uri,status,url,original=file_rights(record,page,sdc,rendered)
            actual_qids=set(re.findall(r'(?:wikidata|Wikidata)\s*=\s*(Q\d+)',page['revisions'][0]['slots']['main']['*']))|w.ids(sdc,'P6243')
            entities={}
            if actual_qids:
                entities=w.api(fetcher,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(sorted(actual_qids))}).get('entities',{})
            im=dict(record,page=info['descriptionurl'],source_image_url=url,policy_url=uri,
                rights_status=status,license_label=licence,checked_at=c.core.now(),
                image_selection_basis='exact_primary_catalogue_and_pending_visual_comparison',
                raw={'commons':page,'structured_data':sdc,'actual_authorities':entities,
                     'primary_catalogue_pdf':receipt,'primary_catalogue_text_path':str(extracted.relative_to(ROOT)),
                     'primary_catalogue_text_sha256':c.core.sha(extracted.read_bytes())},
                creator_credit=credit,
                attribution_text=f"{record['artist']}. {record['title']}. Image credit: {credit}. {info['descriptionurl']}. {licence} ({uri}). Full-frame proportional resize and JPEG compression; applicable ShareAlike terms retained.")
            if rendered:im['rendered_licence_evidence']=rendered
            lifetime_evidence=underlying_creator_evidence(record)
            if lifetime_evidence:im['raw']['underlying_creator_evidence']=lifetime_evidence
            _,source_resolution=original_source_context(record,page)
            if source_resolution:im['image_original_source_resolution']=source_resolution
            if original:im['commons_original_sha1']=info['sha1']
            c.save(run/'selected'/PROVIDER/(record['artwork_id']+'.json'),im)
            c.core.event(run,{'provider':PROVIDER,'artwork_id':record['artwork_id'],'external_id':sid,
                'outcome':'rights_selected','identity_review':'Official catalogue and prepared photo must be visually compared before attachment'})
        except Exception as error:
            c.core.event(run,{'provider':PROVIDER,'artwork_id':record['artwork_id'],'external_id':record['external_id'],
                'outcome':'manual_review','reason':str(error)[:400]})
        print(label,n,'/',len(rows),record['title'][:60],flush=True)

def validate_attachment(image,review):
    """Fail closed unless exact source bytes and physical-object review agree."""
    if review.get('outcome')!='approved' or review.get('artwork_id')!=image['artwork_id'] or review.get('sha256')!=image['sha256']:
        raise ValueError('Approval is absent or applies to different image bytes/object')
    proof=review.get('primary_catalogue_comparison',{})
    raw=image['raw'];receipt=raw['primary_catalogue_pdf']
    if raw.get('underlying_creator_evidence',[])!=underlying_creator_evidence(image):
        raise ValueError('Underlying creator lifetime evidence differs from source review')
    if proof.get('outcome')!='same_physical_work' or proof.get('source_id')!=image['external_id']:
        raise ValueError('Exact primary physical-object review missing')
    if proof.get('pdf_sha256')!=receipt['sha256'] or c.core.sha((ROOT/receipt['path']).read_bytes())!=receipt['sha256']:
        raise ValueError('Reviewed primary catalogue PDF checksum mismatch')
    expected_url='https://www.lombardiabeniculturali.it/opere-arte/schede-complete/'+image['external_id']+'/'
    if receipt['url']!=expected_url or receipt.get('ssl_verify_result')!=0 or receipt.get('http_status')!=200:
        raise ValueError('Exact primary catalogue URL or transport verification differs')
    text_path=ROOT/raw['primary_catalogue_text_path'];text=text_path.read_text()
    if c.core.sha(text_path.read_bytes())!=raw['primary_catalogue_text_sha256'] or image['external_id'] not in text:
        raise ValueError('Exact primary catalogue text identity/checksum differs')
    if proof.get('commons_pageid')!=raw['commons']['pageid'] or proof.get('commons_revision')!=raw['commons']['revisions'][0]['revid']:
        raise ValueError('Reviewed independent photo identity/revision differs')
    if not proof.get('inventory') or not proof.get('visual_observation') or not proof.get('source_pages'):
        raise ValueError('Catalogue inventory/pages/visual observation absent')
    if not re.search(r'^Numero:\s*'+re.escape(proof['inventory'])+r'\s*$',text,re.M):
        raise ValueError('Reviewed inventory is not transcribed in the exact catalogue')
    if proof.get('creator_confirmed')!=True or proof.get('holding_confirmed')!=True or proof.get('date_confirmed')!=True:
        raise ValueError('Primary object metadata review incomplete')
    actual=set(raw['actual_authorities'])
    if set(proof.get('reviewed_authorities',[]))!=actual:
        raise ValueError('Actual authority statements have not all been reviewed')
    if w.ids(raw['structured_data'],'P6243')-actual:
        raise ValueError('Unreviewed structured physical-object identity')
    for qid,entity in raw['actual_authorities'].items():
        if entity.get('id')!=qid or not w.ids(entity,'P31')&w.PAINTED:
            raise ValueError('Conflicting/missing actual painting authority')
        if w.ids(entity,'P170')!={a['qid'] for a in image['creators']} or any(set(cl.get('qualifiers',{}))-{'P7452'} for cl in w.claims(entity,'P170')):
            raise ValueError('Actual authority creator/attribution conflict')
        if not w.ids(entity,'P195') & set(proof.get('holding_authorities',[])):
            raise ValueError('Actual authority holding conflict')
        for value in w.values(entity,'P571'):
            match=re.match(r'^\+(\d+)-',value.get('time','')) if isinstance(value,dict) else None
            if match and value.get('precision',0)>=9:
                year=int(match[1])
                if year>1970 or not image['creation_year_start']-5<=year<=image['creation_year_end']+5:
                    raise ValueError('Actual authority date conflict')
    info,credit,label,uri,status,url,original=file_rights(image,raw['commons'],raw['structured_data'],image.get('rendered_licence_evidence'))
    _,source_resolution=original_source_context(image,raw['commons'])
    if image.get('image_original_source_resolution')!=source_resolution:
        raise ValueError('Original institutional portal resolution differs from reviewed evidence')
    if any(image[k]!=v for k,v in {'license_label':label,'policy_url':uri,'rights_status':status,'source_image_url':url,'creator_credit':credit}.items()):
        raise ValueError('Prepared image rights/credit differ from exact file evidence')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['select','research'])
    parser.add_argument('--label',default='round-26-primary-photographs')
    parser.add_argument('--cohort',default='direct-photo-discovery')
    parser.add_argument('--source-round')
    parser.add_argument('--rights-source-round')
    parser.add_argument('--mapping',type=Path);args=parser.parse_args()
    if args.mapping:PHOTOS=c.load(args.mapping)['selected_photos']
    if args.phase=='select':select(args.label,args.cohort,args.source_round,args.rights_source_round)
    else:research(args.label)
