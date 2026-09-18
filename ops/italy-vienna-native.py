#!/usr/bin/env python3
"""Selected Italian paintings with exact Academy of Fine Arts native CC evidence."""
import argparse
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=module('campaign','italy-image-campaign.py')
w=module('commons','overnight-commons-images.py')
p=module('capture','italy-catalogue-pdf-evidence.py')
PROVIDER='italy-vienna'
HOST='collection.kunstsammlungenakademie.at'
IMAGE_HOST=HOST+'.zetcom.net'
URI='https://creativecommons.org/licenses/by/4.0/'
OBJECTS={'Q117857264':('1569','228','Sandro Botticelli'),
         'Q129897100':('1533','286','Antonio da Fabriano'),
         'Q106130077':('1740','119937','Titian'),
         'Q106129412':('938','339','Francesco Guardi')}

def inventory_search(image):
    """Verify the one public native inventory match where P973 is absent."""
    if image['external_id']!='Q106129412' or image['accession_number']!='GG-502':
        raise ValueError('No reviewed native inventory bridge for this work')
    proof=image['raw']['native_inventory_search'];receipt=proof['capture']
    url=f'https://{HOST}/solr/published/select?q=number_txt%3A%22GG-502%22&fq=type%3AObject&rows=2&wt=json'
    path=(ROOT/receipt['path']).resolve()
    if not path.is_relative_to(c.RUN.resolve()) or c.core.sha(path.read_bytes())!=receipt['sha256']:
        raise ValueError('Native inventory evidence checksum/path differs')
    if receipt.get('url')!=url or receipt.get('resolved_url')!=url or receipt.get('http_status')!=200 or receipt.get('ssl_verify_result')!=0:
        raise ValueError('Exact public native inventory search differs')
    response=json.loads(path.read_text())['response']
    if response.get('numFound')!=1 or response.get('numFoundExact') is not True or len(response['docs'])!=1:
        raise ValueError('Native inventory match is not unique')
    doc=response['docs'][0]
    if str(doc.get('oid'))!='938' or doc.get('number_s')!='GG-502' or doc.get('person_s')!='Francesco Guardi' or doc.get('person_ss')!=['339']:
        raise ValueError('Native inventory object/creator differs')
    if 'GG-502' not in w.values(image['raw']['wikidata'],'P217'):
        raise ValueError('Actual authority lacks native accession')

def validate(image):
    q=image['external_id'];ident,person,name=OBJECTS[q]
    if image['scheme']!='wikidata' or image['raw']['wikidata'].get('id')!=q:
        raise ValueError('Existing physical-object authority differs')
    w.entity_match(image,image['raw']['wikidata'],require_primary_image=False)
    raw=image['raw'];receipt=raw['native_capture'];url=f'https://{HOST}/de/collection/item/{ident}/'
    if not any(u.rstrip('/')==url.rstrip('/') for u in w.values(raw['wikidata'],'P973')):
        inventory_search(image)
    path=(ROOT/receipt['path']).resolve()
    if not path.is_relative_to(c.RUN.resolve()) or c.core.sha(path.read_bytes())!=receipt['sha256']:
        raise ValueError('Native capture checksum/path differs')
    if receipt.get('url')!=url or receipt.get('resolved_url')!=url or receipt.get('http_status')!=200 or receipt.get('ssl_verify_result')!=0:
        raise ValueError('Exact native page transport/identity differs')
    soup=BeautifulSoup(path.read_text(),'html.parser')
    native=json.loads(soup.find('script',id='__NEXT_DATA__').string)['props']['pageProps']['data']['item']
    if raw['native']!=native or native['Id']!=ident or native['ObjObjectNumberTxt']!=image['accession_number']:
        raise ValueError('Exact primary source object/accession differs')
    if native['ObjObjectNumberTxt'] not in w.values(raw['wikidata'],'P217') or native['ObjCollectionTxt_en']!='Paintings Gallery' or native['ObjCategoryVoc']['LabelTxt_en']!='painting':
        raise ValueError('Native accession/collection/type conflict')
    creators=[a for a in native['ObjPersonRef']['Items'] if a.get('LinkLabelTxt')]
    if len(creators)!=1 or creators[0]['ReferencedId']!=person or creators[0].get('RoleTxt_en')!='Artist' or creators[0].get('AttributionTxt') or creators[0].get('AttributionTxt_en'):
        raise ValueError('Native named creator/attribution differs')
    if image['artist']!=name or len(image['creators'])!=1 or image['creators'][0]['role']!='primary' or image['creators'][0]['death']+70>=2026:
        raise ValueError('Underlying artwork copyright/creator unresolved')
    dates=[a for a in native['ObjDateGrp'] if a.get('ObjDateFromTxt') and a.get('ObjDateToTxt')]
    if len(dates)!=1 or (int(dates[0]['ObjDateFromTxt']),int(dates[0]['ObjDateToTxt']))!=(image['creation_year_start'],image['creation_year_end']) or image['creation_year_end']>1970:
        raise ValueError('Native and catalogue creation intervals differ; editorial review required')
    media=native['ObjMultimediaMainImageRef']['Items']
    if len(media)!=1 or len(media[0]['Multimedia'])!=1:
        raise ValueError('Unique primary photographic image required')
    photo=media[0]['Multimedia'][0]
    if media[0].get('MulCCLizVoc',{}).get('LabelTxt')!='CC BY 4.0' or photo.get('license')!='CC BY 4.0' or photo.get('mime')!='image/jpeg':
        raise ValueError('Native photograph does not explicitly carry CC BY 4.0')
    credit=media[0].get('MulPhotocreditTxt_en','')+'; '+media[0].get('MulSourceTxt_en','')
    if not media[0].get('MulSourceTxt_en') or image['creator_credit']!=credit:
        raise ValueError('Exact institution/photographer credit missing')
    expected='https://'+IMAGE_HOST+'/'+photo['full']
    if native.get('ObjURLImageTxt')!=expected or image['source_image_url']!=expected or urlparse(expected).hostname!=IMAGE_HOST:
        raise ValueError('Exact native primary photograph differs')
    if image['page']!=url or image['rights_status']!='cc_by' or image['license_label']!='CC BY 4.0' or image['policy_url']!=URI:
        raise ValueError('Image attribution/licence differs from native source')
    if not soup.find(string=lambda value: value and value.strip()=='CC BY 4.0'):
        raise ValueError('Native rendered Creative Commons licence label missing')

def research(label,qids):
    run=c.RUN/label
    if not (run/'candidates.json').exists():
        records=[]
        for r in c.load(c.RUN/'eligible-image-gaps.json'):
            ids=[i for i in r['identifiers'] if i['scheme']=='wikidata' and i['id'] in qids]
            if len(ids)!=1:continue
            row=dict(r,provider=PROVIDER,scheme='wikidata',external_id=ids[0]['id'],qid=ids[0]['id'],page=ids[0]['url'],artist='; '.join(a['name'] for a in r['creators']))
            records.append(row)
        if len(records)!=len(qids):raise ValueError('Exact existing candidate set missing')
        for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
            before=c.snapshot(records,dsn)
            if len(before)!=len(records):raise ValueError('Ambiguous current database identities')
            for row in records:
                current=[a for a in before if a['local_id']==row['artwork_id']]
                if len(current)!=1:raise ValueError('Ambiguous target')
                v=current[0]
                if v['primary_media_id'] or v['date_scope']!='eligible' or not v['selected'] or v['status']=='archived':raise ValueError('Current eligible image gap differs')
                if any(v[k]!=row[k] for k in ('title','slug','creation_year_start','creation_year_end','work_type')):raise ValueError('Current source identity differs')
                row.setdefault('target_ids',{})[target]=v['target_id']
            c.save(run/(target+'-before.json'),before)
        c.save(run/'candidates.json',{'selected_at':c.core.now(),'candidates':records,'selection':'Existing Italian paintings; exact actual authority-to-native accession, creator, date and primary photograph CC licence required'})
    records=c.load(run/'candidates.json')['candidates'];fetcher=c.core.Fetcher(run/'metadata/authority')
    p.HOST=HOST;p.OUT=run/'metadata/native'
    for row in records:
        if row['artwork_id'] in c.core.latest_events(run):continue
        try:
            q=row['external_id'];ident=OBJECTS[q][0];url=f'https://{HOST}/de/collection/item/{ident}/'
            entity=w.api(fetcher,'www.wikidata.org',{'action':'wbgetentities','ids':q})['entities'][q]
            path,receipt=p.capture(url,'.html',3000000)
            soup=BeautifulSoup(path.read_text(),'html.parser');native=json.loads(soup.find('script',id='__NEXT_DATA__').string)['props']['pageProps']['data']['item']
            media=native['ObjMultimediaMainImageRef']['Items'][0]
            credit=media.get('MulPhotocreditTxt_en','')+'; '+media.get('MulSourceTxt_en','')
            im=dict(row,page=url,source_image_url=native['ObjURLImageTxt'],policy_url=URI,rights_status='cc_by',license_label='CC BY 4.0',checked_at=c.core.now(),raw={'wikidata':entity,'native':native,'native_capture':receipt},creator_credit=credit,attribution_text=f"{row['artist']}. {row['title']}. {native['ObjObjectNumberTxt']}. {credit}. {url}. CC BY 4.0 ({URI}). Full-frame proportional resize and JPEG compression.")
            if q=='Q106129412':
                im['raw']['native_inventory_search']=c.load(c.RUN/'vienna-academy-native/native-search/search-basis.json')
            validate(im);c.save(run/'selected'/PROVIDER/(im['artwork_id']+'.json'),im)
            c.core.event(run,{'provider':PROVIDER,'artwork_id':row['artwork_id'],'external_id':q,'outcome':'rights_selected'})
        except Exception as e:
            c.core.event(run,{'provider':PROVIDER,'artwork_id':row['artwork_id'],'external_id':row['external_id'],'outcome':'manual_review','reason':str(e)[:450]})
        print(label,row['title'],flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--label',default='round-50-vienna-native');a.add_argument('--qids',default='Q117857264,Q129897100');args=a.parse_args();research(args.label,args.qids.split(','))
