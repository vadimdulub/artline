#!/usr/bin/env python3
"""Selected official Artefact catalogue records with museum and object identity guards."""
import argparse, collections, difflib, gzip, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('deep','ops/museums-exactly-one-deep-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
d=m.d;RUN=m.RUN;ROOT=m.ROOT
h=m.module('artefact_capture','research-havre-rouen-cyprus-20261006.py');h.RUN=RUN/'artefact'
BASE={x['institution']['id']:x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected']}
# Individually reviewed source authorities. Kirov is the city formerly named Vyatka;
# this is the Vasnetsov brothers art museum, not another city's similar-name museum.
AUTHORITIES=[
('abbaec64-5854-56a4-9c5c-02866b87ff2d','chuvashskiy-hudozhestvennyy-muzey',['Chuvash State Art Museum','Chuvash Art Museum','Чувашский государственный художественный музей']),
('538a5b06-8ddd-5fa3-8c7f-46261b6a0388','novosibirskiy-hudozhestvennyy-muzey',['Novosibirsk State Art Museum','Новосибирский государственный художественный музей']),
('9d197513-4c5d-539f-876f-f03f4e3ecff4','dagestanskiy-muzey-izobrazitelnyh-iskusstv',['Dagestan Museum of Fine Arts','Дагестанский музей изобразительных искусств']),
('17a8257e-6001-55f2-b544-c2a5131f3e50','krasnodarskiy-muzey-imeni-fa-kovalenko',['Krasnodar Museum named after F.A. Kovalenko','Краснодарский музей имени Ф.А. Коваленко']),
('714ace8d-3331-5090-87e0-d92fc3c21a9f','vyatskiy-hudozhestvennyy-muzey',['Vyatka Art Museum','Вятский художественный музей']),
('49f8803a-a3a0-58db-95f0-577b9a456865','murmanskiy-oblastnoy-hudozhestvennyy-muzey',['Murmansk Regional Art Museum','Мурманский областной художественный музей']),
('4990dd51-585d-5c1e-990c-d6835f7d4703','irkutskiy-hudozhestvennyy-muzey-im-vp-sukachyova',['Irkutsk Art Museum named after V.P. Sukachev','Иркутский художественный музей им. В.П. Сукачёва']),
('b728c50a-14f5-582e-8312-49397cdae059','tyumenskoe-muzeyno-prosvetitelskoe-obedinenie',['I.Ya. Slovtsov Museum Complex','Музейный комплекс им. И.Я. Словцова']),
('b481e7ac-6a14-5b9a-a6b4-7ad06f6e69ab','vladimiro-suzdalskiy-muzey-zapovednik',['Vladimir-Suzdal Museum-Reserve','Владимиро-Суздальский музей-заповедник']),
('fc792bb9-3d4f-542f-94b5-7a8ce4afce56','kurskaya-kartinnaya-galereya-im-aa-deyneki',['Kursk Picture Gallery named after A.A. Deineka','Курская картинная галерея им. А.А. Дейнеки']),
]

def capture(url):return h.capture(url,timeout=25)
def text(node):return node.get_text(' ',strip=True) if node else ''
def checked(rc):
    raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert d.sha(raw)==rc['sha256'] and rc['status']==200;return raw

def discovery():
    reviews=[]
    for iid,slug,names in AUTHORITIES:
        assert iid in BASE
        url='https://ar.culture.ru/en/museum/'+slug
        raw,rc=capture(url);assert rc['status']==200
        soup=BeautifulSoup(raw,'html.parser');title=text(soup.find('h1'))
        assert d.norm(title) in {d.norm(n) for n in names},(slug,title)
        caturl='https://ar.culture.ru/en/museum-catalog/'+slug
        craw,crc=capture(caturl);assert crc['status']==200
        node=BeautifulSoup(craw,'html.parser').select_one('.blocks_list_wrapper');filters=json.loads(node['data-filter']);assert filters['owner']
        selected=[];indexes=[]
        # Museum scoped metadata only, at most 48 candidate artworks per museum.
        for offset in [0,24]:
            params={'owner':filters['owner'],'isCatalogue':True,'l':24,'s':offset,'sel':'title label authors slug','o':json.dumps({'title.ru':1}),'totals':'true','locale':'en'}
            params={k:json.dumps(v)if isinstance(v,(dict,bool))else v for k,v in params.items()}
            u='https://ar.culture.ru/en/facets/Subject?'+urlencode(params)
            body,receipt=capture(u);assert receipt['status']==200
            response=json.loads(body);assert len(response['data'])<=24
            selected+=response['data'];indexes.append(dict(receipt=receipt,response=response))
            if offset+24>=response.get('total',0):break
        value=dict(museum=BASE[iid],slug=slug,names=names,title=title,authority_receipt=rc,catalogue_receipt=crc,filters=filters,indexes=indexes,candidates=selected)
        reviews.append(value);print(title,'selected',len(selected),'total',indexes[0]['response'].get('total'),flush=True)
    d.save(RUN/'artefact/selected-museum-catalogues.json.gz',reviews)

def dates_original(value):
    x=value.strip().lower().replace('–','-').replace('—','-');x=re.sub(r'\s+',' ',x)
    if re.fullmatch(r'(?:circa |c\. ?|около |ок\. ?)?[12]\d{3}(?: г\.?| год)?',x):
        year=int(re.search(r'[12]\d{3}',x)[0]);return year,year,'circa'if re.search(r'circa|c\.|ок',x)else'exact'
    r=re.fullmatch(r'([12]\d{3})\s*-\s*([12]\d{3})(?: гг\.?)?',x)
    if r and int(r[1])<=int(r[2]):return int(r[1]),int(r[2]),'range'
    r=re.fullmatch(r'([12]\d{2})0(?:s|-е(?: годы)?)',x)
    if r:return int(r[1]+'0'),int(r[1]+'9'),'range'
    # Broad bounds express the explicit source century. Keep original wording,
    # including early/late qualifiers, without inventing a more exact date.
    r=re.fullmatch(r'(?:(?:early|mid|middle of the|late|end of the|first half of the|second half of the) )?(1[0-9])(?:th|st|nd) century',x)
    if r:return (int(r[1])-1)*100+1,int(r[1])*100,'range'
    return None

def dates(value):
    x=re.sub(r'\s+',' ',value.strip()).replace('–','-').replace('—','-')
    x=re.sub(r'\s*(?:гг?\.?|год|годы)$','',x).strip()
    x=re.sub(r'^(?:около|ок\.|around|ca\.)\s*','circa ',x,flags=re.I)
    found=dates_original(x)
    if found:return found
    r=re.fullmatch(r'(?:circa )?([12]\d{3})\s*-\s*([12]\d{3})',x,re.I)
    if r and int(r[1])<=int(r[2]):return int(r[1]),int(r[2]),'circa_range'if x.lower().startswith('circa')else'range'
    r=re.fullmatch(r'(?:(?:early|mid|late|начало|конец|середина)[ -]*)?([12]\d{2})0(?:s|-е)',x,re.I)
    if r:return int(r[1]+'0'),int(r[1]+'9'),'decade'
    x=re.sub(r'^(early|mid|late)-',r'\1 ',x,flags=re.I)
    found=dates_original(x)
    if found:return found
    r=re.fullmatch(r'(?:(?:Начало|Конец|Середина|Первая половина|Вторая половина) )?(XV|XVI|XVII|XVIII|XIX)(?: в\.?| век| века)',x,re.I)
    if r:
        century={'XV':15,'XVI':16,'XVII':17,'XVIII':18,'XIX':19}[r[1].upper()]
        return (century-1)*100+1,century*100,'century'
    return None

def parse(raw,review,candidate):
    soup=BeautifulSoup(raw,'html.parser');block=soup.select_one('.subject_info_block');native=soup.select_one('#entity_id');canonical=soup.find('link',rel='canonical')
    if not block or not native or not canonical:return None,'native_object_page_missing'
    url='https://ar.culture.ru/en/subject/'+candidate['slug']
    if canonical['href'].rstrip('/') not in {url.rstrip('/'),url.replace('/en/','/ru/').rstrip('/')}:return None,'native_canonical_conflict'
    title=text(block.find('h1'));authors=[text(x) for x in block.select('.subject_info_block__author')]
    fields={text(g.select_one('.subject_info_block__group_label')):text(g.select_one('.subject_info_block__group_value')) for g in block.select('.subject_info_block__group')}
    holding=fields.get('Collection')or fields.get('Коллекция')
    if d.norm(holding) not in {d.norm(n) for n in review['names']}:return None,'collection_authority_requires_review'
    if d.norm(title) not in {d.norm(t) for t in candidate['title'].values()}:return None,'index_title_conflict'
    if candidate['slug']=='buhta-zolotoy-rog--turciya':return None,'source_creation_precedes_named_creator_life_requires_review'
    date=fields.get('Creation period')or fields.get('Период создания')
    years=dates(date or '')
    if not years:return None,'creation_date_requires_individual_review'
    if years[1]>1970:return None,'creation_after_1970_or_crossing_cutoff'
    medium=fields.get('Technique')or fields.get('Техника');low=(medium or '').lower()
    body=' '.join(text(node) for node in soup.select('.org_blocks .main_content'))
    # Explicit techniques support the class; uncertain types remain held.
    if re.search(r'\boil\b|\btempera\b|масло|темпер',low):kind='painting'
    elif re.search(r'water.?colou?r|акварел',low):kind='watercolor'
    elif re.search(r'etching|engraving|lithograph|офорт|гравюр|литограф',low):kind='print'
    elif re.search(r'pencil|charcoal|карандаш|уголь',low):kind='drawing'
    elif re.search(r'gouache|гуашь',low):kind='painting'
    else:return None,'work_type_requires_individual_review'
    icon=bool(re.search(r'\bicon\b|икона|иконопись',title+' '+body,re.I) and ('tempera'in low or 'темпер'in low))
    if not authors and not icon:return None,'creator_unstated_requires_review'
    if re.search(r'verso|reverse|back side|recto|на обороте|обороте',title+' '+body,re.I):return None,'two_sided_object_requires_review'
    facts=dict(title=title,creator_label='; '.join(authors)or None,first=years[0],last=years[1],date_precision=years[2],date_display=date,work_type=kind,object_form='icon'if icon else None,medium=medium,dimensions=fields.get('Dimensions')or fields.get('Размеры'),accession=None,source_url=canonical['href'],holding_basis='Official Artefact object catalogue explicitly names the reviewed museum collection. Museum-scoped native catalogue discovery and canonical object ID verified. Documented holdings only, no claim of current display or independent legal title.')
    return dict(facts=facts,native_id=native['value'],fields=fields,title=title,authors=authors,index_candidate=candidate,state_catalogue_urls=sorted({a['href'] for a in soup.select('a[href]') if 'goskatalog.ru' in a['href']})),None

def research(wave='artefact-corrected'):
    reviews=d.load(RUN/'artefact/selected-museum-catalogues.json.gz');records=[];held=[];n=0
    for review in reviews:
        for candidate in review['candidates']:
            url='https://ar.culture.ru/en/subject/'+candidate['slug'];n+=1
            try:
                raw,rc=capture(url)
                if rc['status']!=200:parsed,reason=None,'source_status_'+str(rc['status'])
                else:parsed,reason=parse(raw,review,candidate)
            except Exception as exc:parsed,reason=None,type(exc).__name__+': '+str(exc)[:150];rc=None
            if reason:held.append(dict(museum_id=review['museum']['id'],source_url=url,reason=reason,receipt=rc))
            else:
                key=parsed['native_id'];records.append(dict(artwork_id=d.uid('artefact/'+key),slug=m.OP+'-artefact-'+key,source_record_id=key,provider='artefact-native',origin='museum_selected_native_catalogue',museum=review['museum'],facts=parsed['facts'],source_receipt=rc,body_path=rc['body_path'],alternate_native_urls=parsed['state_catalogue_urls']+[url.replace('/en/','/ru/')],raw_source_record=dict(parsed=parsed,authority=review)))
            if n%12==0:print(n,'reviewed;',len(records),'eligible,',len(held),'held',flush=True)
        print(review['title'],sum(x['museum']['id']==review['museum']['id'] for x in records),'ready',flush=True)
    c=campaign();c.prepare_wave(wave,records,held)

def campaign():
    c=m.module('artefact_campaign','all-museums-minimum-100-20261006.py');c.RUN=RUN;c.OP=m.OP;c.BASE={x['institution']['id']:x for x in d.load(RUN/'baseline.json.gz')['selected']};c.d.connect=d.connect;return c

def check_body(row,cache):
    rs=row['raw_source_record'];authority=rs['authority'];raw=checked(row['source_receipt']);parsed,reason=parse(raw,authority,rs['parsed']['index_candidate'])
    assert not reason and parsed==rs['parsed'] and row['facts']==parsed['facts'] and row['source_record_id']==parsed['native_id']
    assert row['museum']['id']==authority['museum']['id'] and row['museum']['id']in BASE
    soup=BeautifulSoup(checked(authority['authority_receipt']),'html.parser');assert text(soup.find('h1'))==authority['title']
    cat=BeautifulSoup(checked(authority['catalogue_receipt']),'html.parser');assert json.loads(cat.select_one('.blocks_list_wrapper')['data-filter'])==authority['filters']
    found=False
    for index in authority['indexes']:
        assert json.loads(checked(index['receipt']))==index['response']
        if parsed['index_candidate']in index['response']['data']:found=True
    assert found

def configure(wave):
    c=campaign();c.configure(wave);out=c.d
    out.check_body=check_body;out.scheme=lambda row:'artefact-object';out.TARGET_FIELD='linked';out.TARGET_COUNT=40
    out.SOURCE_NAME='Selected official Artefact museum collection records, 8 October 2026';out.SOURCE_BASE_URL='https://ar.culture.ru/';out.DEFAULT_CONFIDENCE=.95
    out.CONFIDENCE_BASIS='Exact official Artefact native object ID and canonical page, museum-scoped catalogue membership, explicit Collection label reconciled with museum authority, source dates, technique, dimensions and creator labels. Holdings only; no current-display inference. Editorial assessment, not a calibrated probability.'
    original=out.connect
    def connect(readonly=True):
        db=original(readonly)
        if not readonly:db.execute("SET lock_timeout='180s'")
        return db
    out.connect=connect;return out

def plan():configure('artefact-corrected').plan()
def apply():
    assert d.load(RUN/'backups.json')['production']['status']=='SUCCESSFUL';configure('artefact-reviewed').apply()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');args=p.parse_args();globals()[args.phase]()
