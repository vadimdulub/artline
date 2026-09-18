#!/usr/bin/env python3
"""One exact Museo Egizio painting, using the museum's own image and CC0 release."""
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('commercial_campaign',ROOT/'ops/italy-commercial-images.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c
PROVIDER='italy-egizio'
ID='24f45e88-535f-50a0-af77-b2e4bc9cf5af'
URL='https://collezioni.museoegizio.it/en-GB/material/Provv_3526/'
HOME='https://collezioni.museoegizio.it/en-GB'
IMAGE='https://collezioni.museoegizio.it/public/objects/images/0011AG_3ED7A781274265C40E2D4CB44ABCA1AC_big.jpg'
LICENCE='https://creativecommons.org/publicdomain/zero/1.0/'

def capture(url):
    key=c.core.sha(url.encode())
    path=c.RUN/'discovery/native-captures'/(key+'.html')
    receipt=c.load(path.with_suffix('.receipt.json'))
    if receipt['url']!=url or receipt.get('resolved_url')!=url or receipt['status']!=200 or receipt['sha256']!=c.core.sha(path.read_bytes()):
        raise ValueError('Primary source capture identity/checksum differs')
    return receipt,BeautifulSoup(path.read_text(),'html.parser')

def validate(im):
    if im['artwork_id']!=ID or im['external_id']!='Q117233361' or im['scheme']!='wikidata':
        raise ValueError('Unreviewed Egizio object')
    if im['institution_qid']!='Q19877' or {a['qid'] for a in im['creators']}!={'Q1155252'}:
        raise ValueError('Creator/holding differs')
    if (im['creation_year_start'],im['creation_year_end'],im['accession_number'])!=(1881,1881,'Provv.3526'):
        raise ValueError('Native inventory/date differs')
    receipt,soup=capture(URL);home,hsoup=capture(HOME)
    text=soup.get_text(' ',strip=True)
    for literal in ('Painting of the galleries by Lorenzo Delleani.','Provv. 3526','1881 CE','47 cm x 32 cm'):
        if literal not in text:raise ValueError('Native identity evidence missing')
    items=soup.select('.gallery-object .item')
    if len(items)!=1 or IMAGE.removeprefix('https://collezioni.museoegizio.it') not in str(items[0]):
        raise ValueError('Native image is not attached to this exact object')
    if not any(a.get('href')=='https://creativecommons.org/publicdomain/zero/1.0/deed.it' for a in items[0].find_all('a')):
        raise ValueError('Exact native image CC0 release missing')
    if 'The images are freely downloadable and reusable under a Creative Commons CC0 Public Domain licence.' not in hsoup.get_text(' ',strip=True):
        raise ValueError('Native collection reuse statement missing')
    if im['raw']['native_object']!=receipt or im['raw']['native_collection_policy']!=home:
        raise ValueError('Saved source evidence differs')
    expected={'page':URL,'source_image_url':IMAGE,'policy_url':LICENCE,'license_label':'CC0','rights_status':'cc0','creator_credit':'Museo Egizio, Torino'}
    if any(im[k]!=v for k,v in expected.items()):raise ValueError('Selected rights/source differs')

def research(label='round-02-egizio'):
    run=c.RUN/label
    if (run/'candidates.json').exists():return
    base=next(a for a in c.load(c.RUN/'eligible-image-gaps.json') if a['artwork_id']==ID)
    record=dict(base,provider=PROVIDER,scheme='wikidata',external_id='Q117233361',qid='Q117233361',
        page=URL,artist='Lorenzo Delleani')
    before={target:c.snapshot([record],dsn) for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]}
    for target,rows in before.items():
        if len(rows)!=1:raise ValueError('Ambiguous target')
        row=rows[0]
        if row['primary_media_id'] or row['date_scope']!='eligible' or not row['selected'] or row['status']!='review':raise ValueError('Target eligibility changed')
        if any(row[k]!=record[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):raise ValueError('Target metadata changed')
    record['target_ids']={t:rows[0]['target_id'] for t,rows in before.items()}
    native,_=capture(URL);home,_=capture(HOME)
    im=dict(record,source_image_url=IMAGE,policy_url=LICENCE,rights_status='cc0',license_label='CC0',
        checked_at=c.core.now(),creator_credit='Museo Egizio, Torino',
        image_selection_basis='exact_native_object_and_per_image_cc0',
        raw={'native_object':native,'native_collection_policy':home,
            'commercial_use_review':{'use':'Public or potentially commercial app',
                'basis':'Museum itself expressly offers this exact collection image for free reuse under CC0; linked CC0 download is on the exact Provv.3526 record. This is a museum release, not a third-party licence assertion.',
                'archive_policy_scope':'Separate archive Article 108 statement reviewed as context only; not asserted to cover this collection photograph.',
                'underlying_artwork':'Lorenzo Delleani died in 1908; native painting date 1881.',
                'checked_at':c.core.now()}},
        attribution_text=f'Lorenzo Delleani. {record["title"]} Image: Museo Egizio, Torino, Provv.3526. CC0 ({LICENCE}). Source: {URL} Full-frame proportional resize and JPEG compression.')
    validate(im)
    c.save(run/'candidates.json',{'selected_at':c.core.now(),'candidates':[record]})
    for target,rows in before.items():c.save(run/(target+'-before.json'),rows)
    c.save(run/'selected'/PROVIDER/(ID+'.json'),im)
    c.core.event(run,{'provider':PROVIDER,'artwork_id':ID,'external_id':'Q117233361','outcome':'rights_selected'})
    print('Exact native Egizio image selected; commercial CC0 release captured',flush=True)

if __name__=='__main__':research()
