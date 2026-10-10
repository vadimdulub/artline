#!/usr/bin/env python3
"""Bounded Japanese pictorial-art selection, source captures and museum highlights."""
import argparse,collections,concurrent.futures,gzip,hashlib,importlib.util,json,re,time,unicodedata
from pathlib import Path
from urllib.parse import quote,urljoin,parse_qs,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-chinese-art-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
r.RUN=r.ROOT/'docs/research/asian-collections-import-20261008/japan'
def convert(provider,w,rc):
 common=dict(source_id=str(w['id']),title=w.get('title'),culture='Japan')
 if provider=='cleveland':
  if w.get('legal_status')!='accessioned':return None
  common.update(museum='The Cleveland Museum of Art',accession_number=w.get('accession_number'),source_url=w['url'].replace('http:','https:'),creator_label='; '.join(x.get('description') or x.get('name') or '' for x in w.get('creators',[])) or None,date_display=w.get('creation_date'),year_start=w.get('creation_date_earliest'),year_end=w.get('creation_date_latest'),medium=w.get('technique'),source_type=w.get('type'),image_url=(w.get('images')or{}).get('web',{}).get('url'),image_rights_label=w.get('share_license_status'),image_license_url=r.CC0 if w.get('share_license_status')=='CC0' and not w.get('copyright') else None,credit=w.get('creditline'))
 elif provider=='chicago':
  if w.get('fiscal_year_deaccession'):return None
  iid=w.get('image_id');common.update(museum='Art Institute of Chicago',accession_number=w.get('main_reference_number'),source_url='https://www.artic.edu/artworks/'+str(w['id']),creator_label=w.get('artist_display'),date_display=w.get('date_display'),year_start=w.get('date_start'),year_end=w.get('date_end'),medium=w.get('medium_display'),source_type=w.get('artwork_type_title'),image_url=f'https://www.artic.edu/iiif/2/{iid}/full/843,/0/default.jpg' if iid else None,image_rights_label='Public domain' if w.get('is_public_domain') else w.get('copyright_notice') or 'Not designated public domain',image_license_url=r.CC0 if w.get('is_public_domain') else None,credit=w.get('credit_line'))
 elif provider=='mia':
  if w.get('country')!='Japan':return None
  loc=(w.get('Cache_Location')or'').replace('\\','/');rend=w.get('Primary_RenditionNumber')or'';pd=w.get('rights_type')=='Public Domain' and w.get('restricted') in [None,0] and not w.get('image_copyright') and w.get('Rights_Image_Display')=='Full'
  common.update(museum='Minneapolis Institute of Art',accession_number=w.get('accession_number'),source_url='https://collections.artsmia.org/art/'+str(w['id']),creator_label=w.get('artist')or None,date_display=w.get('dated'),year_start=None,year_end=None,medium=w.get('medium'),source_type=w.get('classification'),image_url='https://img.artsmia.org/web_objects_cache/'+loc+'/'+rend[:-4]+'_800.jpg' if loc and rend.endswith('.jpg') else None,image_rights_label=w.get('rights_type'),image_license_url='https://creativecommons.org/publicdomain/mark/1.0/' if pd else None,credit=w.get('creditline'))
 out=r.candidate(provider,w,rc,**common)
 if provider=='cleveland' and (w.get('cover_accession_number') or w.get('record_type')!='object'):out['decision']='part_or_ensemble_review'
 date=out.get('date_display')or''
 if provider=='mia':
  match=re.fullmatch(r'(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',date)
  if match:
   out['year_start']=int(match[1]);out['year_end']=int(match[2]or match[1]);out['date_decision']='within_cutoff_source_bounds' if out['year_end']<=1970 else 'after_cutoff' if out['year_start']>1970 else 'date_review'
  elif re.fullmatch(r'(?:early |mid-|late |first half of |second half of )?(?:[1-9]|1[0-9])(?:st|nd|rd|th) century',date,re.I):out['date_decision']='within_cutoff_source_period'
 if out.get('year_start')==0 or out.get('year_end')==0 or re.search(r'\b(?:undated|unknown|after|later cast|later print|reprint|printed later)\b',date,re.I):out['date_decision']='date_review'
 return out
def cleveland():
 src=r.Source();rows={};totals={}
 fields='id,accession_number,title,creation_date,creation_date_earliest,creation_date_latest,culture,technique,type,measurements,creators,legal_status,record_type,cover_accession_number,creditline,url,share_license_status,copyright,images,department,external_resources'
 for kind,cap in [('Painting',700),('Calligraphy',150),('Print',700),('Drawing',100)]:
  for skip in range(0,cap,100):
   data,rc=src.get('https://openaccess-api.clevelandart.org/api/artworks/',dict(department='Japanese Art',type=kind,limit=100,skip=skip,fields=fields));totals[kind]=data['info']['total']
   for w in data['data']:
    out=convert('cleveland',w,rc)
    if out:rows[out['source_id']]=out
   print('Japan CMA',kind,skip+len(data['data']),'/',totals[kind],flush=True)
   if len(data['data'])<100 or skip+100>=totals[kind]:break
 r.save('cleveland.json.gz',dict(records=list(rows.values()),source_totals=totals,bounded=True))
def chicago():
 src=r.Source();rows={};fields='id,title,main_reference_number,date_start,date_end,date_display,artist_display,artist_id,artist_ids,place_of_origin,dimensions,medium_display,credit_line,fiscal_year_deaccession,artwork_type_title,department_title,is_public_domain,copyright_notice,image_id'
 query={'bool':{'filter':[{'term':{'place_of_origin.keyword':'Japan'}},{'terms':{'artwork_type_title.keyword':['Painting','Drawing and Watercolor','Print','Miniature Painting']}}]}}
 for page in range(1,11):
  data,rc=src.get('https://api.artic.edu/api/v1/artworks/search',{'params':json.dumps(dict(query=query,fields=fields.split(','),limit=100,page=page))})
  for w in data['data']:
   out=convert('chicago',w,rc)
   if out:rows[out['source_id']]=out
  print('Japan AIC',len(rows),'/',data['pagination']['total'],flush=True)
  if page>=data['pagination']['total_pages']:break
 r.save('chicago.json.gz',dict(records=list(rows.values()),source_total=data['pagination']['total'],bounded=True))
def mia():
 src=r.Source();rows={};query='country:"Japan" AND (classification:"Paintings" OR classification:"Drawings" OR classification:"Prints" OR classification:"Calligraphy")'
 for skip in range(0,1000,200):
  data,rc=src.get('https://search.artsmia.org/'+quote(query,safe=''),dict(size=200,**{'from':skip}));assert data.get('query')==query and not data.get('timed_out')
  for hit in data['hits']['hits']:
   out=convert('mia',hit['_source'],rc)
   if out:rows[out['source_id']]=out
  print('Japan Mia',len(rows),'/',data['hits']['total'],flush=True)
  if skip+200>=data['hits']['total']['value']:break
 r.save('mia.json.gz',dict(records=list(rows.values()),source_total=data['hits']['total'],bounded=True))
def ota():
 old=json.loads((r.ROOT/'docs/research/edo-japanese-museums-20260925/candidates.json').read_bytes());rows=[]
 for w in old['artworks']:
  url=w['source']['url'];html,rc=r.Source().get(url,as_json=False);text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True)
  # Re-fetch and confirm the individual collection caption before reusing facts.
  canonical=lambda value:''.join(c for c in unicodedata.normalize('NFKD',value).lower() if c.isalnum())
  assert canonical(w['title']) in canonical(text),(w['title'],url)
  rows.append(r.candidate('ota',w,rc,source_id=url.rstrip('/').rsplit('/',1)[-1],title=w['title'],museum='Ōta Memorial Museum of Art',accession_number=None,source_url=url,creator_label=w['creator_label'],date_display=w['date_display'],year_start=w['start_year'],year_end=w['end_year'],medium=w.get('medium'),source_type=w['work_type'],culture='Japanese art',image_url=None,image_license_url=None,image_rights_label='No open museum-image license established',credit='Ōta Memorial Museum of Art',identity_note='Specific museum impression or painting. A composition at another museum is not this physical object.'))
 r.save('ota.json.gz',dict(records=rows))
def highlights():
 rows=[];src=r.Source()
 def add(title,creator,date,lo,hi,museum,url,rc,raw,kind='painting',image=None):
  rows.append(r.candidate('japan-highlights',raw,rc,source_id=hashlib.sha256((url+'|'+title).encode()).hexdigest()[:20],title=title,museum=museum,accession_number=None,source_url=url,creator_label=creator,date_display=date,year_start=lo,year_end=hi,source_type=kind,medium=None,culture=None,image_url=image,image_license_url=None,image_rights_label='No open reuse permission established for this image',credit=museum))
 url='https://www.momak.go.jp/English/collection/';html,rc=src.get(url,as_json=False);soup=BeautifulSoup(html,'html.parser')
 for a in soup.select('a[data-lightbox][data-title]'):
  group=a['data-lightbox'];number=int(re.search(r'\d+',group)[0])
  if number>4:continue
  p=a.find_next_sibling('p') or a.find('p');title=p.find('i').get_text(' ',strip=True);date=p.find('small').get_text(' ',strip=True);creator=p.get_text(' ',strip=True).split(title,1)[0].strip(' ,')
  # Japanese makers in these selected pictorial categories; foreign works are not relabelled.
  if not re.match(r'^[A-Z]{3,}\b',creator):continue
  years=re.findall(r'\b\d{4}\b',date);assert len(years)==1
  year=int(years[0]);add(title,creator,date,year,year,'The National Museum of Modern Art, Kyoto',url,rc,dict(caption=p.get_text(' ',strip=True),collection_group=group),'print' if number==4 else 'drawing' if number==3 else 'painting',a['href'])
 url='https://www.adachi-museum.or.jp/en/archives/collection/yokoyama-taikan';html,rc=src.get(url,as_json=False);soup=BeautifulSoup(html,'html.parser');links=list(dict.fromkeys(a['href'] for a in soup.select('a[href*="/archives/collection/"]')))[:13]
 for url in links:
  html,rc=src.get(url,as_json=False);soup=BeautifulSoup(html,'html.parser');creator=soup.find('h1').get_text(' ',strip=True)
  for el in soup.select('.swiper-slide'):
   title=el.select_one('.works_name');caption=el.select_one('.caption')
   if not title or not caption:continue
   title=title.get_text(' ',strip=True);text=caption.get_text(' ',strip=True);match=re.search(r'(?<!\d)(\d{4})(?!\d)',text)
   year=int(match[1]) if match else None;date=match[1] if match else None
   add(title,creator,date,year,year,'Adachi Museum of Art',url,rc,dict(caption=text),'painting',el.find('img')['src'] if el.find('img') else None)
 r.save('highlights.json.gz',dict(records=rows));print('Japanese modern museum highlights',len(rows),flush=True)
def emuseum():
 src=r.Source();base='https://emuseum.nich.go.jp';html,rc=src.get(base+'/result?langId=en&webView=0&class=1',as_json=False);soups=[BeautifulSoup(html,'html.parser')]
 for page in range(2,6):
  url=base+'/result_add';payload=dict(langId='en',area='',region='',title='',century='',cptype='',c_e='',owner='',freeword='',**{'class':'1'},webView='0',pageCnt=str(page));key=r.hashlib.sha256(json.dumps(dict(url=url,payload=payload),sort_keys=True).encode()).hexdigest();p=r.RUN/'captures'/(key+'.json')
  if p.exists():receipt=json.loads(p.read_bytes());raw=gzip.decompress(p.with_suffix('.body.gz').read_bytes());assert r.hashlib.sha256(raw).hexdigest()==receipt['sha256']
  else:
   if src.blocked:break
   time.sleep(.6);response=src.session.post(url,data=payload,timeout=(10,40));raw=response.content
   receipt=dict(url=url,method='POST public pagination',request=payload,final_url=response.url,status=response.status_code,retrieved_at=r.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt));p.with_suffix('.body.gz').write_bytes(gzip.compress(raw,mtime=0))
  assert receipt['status']==200
  soups.append(BeautifulSoup(raw,'html.parser'))
 urls=list(dict.fromkeys(urljoin(base,a['href']) for soup in soups for a in soup.select('a[href*="/detail"]')));assert len(urls)==286
 rows=[];errors=[]
 for n,url in enumerate(urls,1):
  try:
   html,rc=src.get(url,as_json=False);soup=BeautifulSoup(html,'html.parser');title=soup.select_one('#titleName strong').get_text(' ',strip=True);groups=soup.select('#summary > ul');facts=[[li.get_text(' ',strip=True) for li in g.select(':scope > li')] for g in groups]
   assert len(facts)>=2
   first,second=facts[0],facts[1];museum=next(x for x in second if x.endswith('National Museum'));idx=second.index(museum);assert len(second)==idx+2
   accession=second[-1];details=second[:idx]
   date=next((x for x in details if re.search(r'period|dynasty|centur|\b1[0-9]{3}\b',x,re.I)),None)
   dim=next((x for x in details if x!=date and re.search(r'\d[\d.]*\s*[x×]|\b(?:Height|Width)\b|\d\s*cm',x,re.I)),None)
   medium='; '.join(x for x in details if x not in [date,dim]) or None
   creator=first[0] if first and re.match(r'^(?:By |Attributed |Purportedly |Painted |Traditionally |Signed )',first[0],re.I) else None
   lo=hi=None;decision='date_review';years=[int(x) for x in re.findall(r'(?<!\d)(\d{4})(?!\d)',date or '')]
   if years:
    lo=min(years);hi=max(years);decision='within_cutoff_source_bounds' if hi<=1970 else 'after_cutoff' if lo>1970 else 'date_review'
   elif re.search(r'\b(?:[1-9]|1[0-9])(?:st|nd|rd|th)[ -]centur',date or '',re.I):decision='within_cutoff_source_period'
   row=r.candidate('emuseum',dict(summary_groups=facts,description=soup.select_one('#summary').find_next_sibling().get_text(' ',strip=True) if soup.select_one('#summary').find_next_sibling() else '',quantity=first[-1] if first else None),rc,source_id=parse_qs(urlsplit(url).query)['content_base_id'][0],title=title,museum=museum,accession_number=accession,source_url=url,creator_label=creator,date_display=date,year_start=lo,year_end=hi,medium=medium,dimensions=dim,source_type='painting',culture=None,image_url=None,image_license_url=None,image_rights_label='Image reuse permission not established',credit='National Institutes for Cultural Heritage, Japan',identity_note='Official museum-owned National Treasure/Important Cultural Property. Source-record ensembles remain one inventory unit. Origin may be Japanese, Chinese or another source-specified culture, not inferred from holding country.');row['date_decision']=decision;rows.append(row)
  except Exception as e:
   errors.append(dict(url=url,error=str(e)))
   if src.blocked:break
  if n%25==0:r.save('emuseum.json.gz',dict(records=rows,errors=errors));print('e-Museum',n,'/',len(urls),'accepted',len(rows),flush=True)
 r.save('emuseum.json.gz',dict(records=rows,errors=errors))
def assemble():
 rows=[]
 for name in ['cleveland','chicago','mia','ota','emuseum','highlights']:
  p=r.RUN/(name+'.json.gz')
  if p.exists():rows+=r.load(p.name)['records']
 excluded=[x for x in rows if x['date_decision']=='after_cutoff'];selected=[x for x in rows if x['date_decision']!='after_cutoff']
 r.save('source-records.json.gz',selected);r.save('excluded.json.gz',excluded);r.save('research-summary.json',dict(at=r.now(),selected=len(selected),excluded_post1970=len(excluded),by_museum=dict(collections.Counter(x['museum'] for x in selected))))
 print('Japan selected',len(selected),'post-cutoff excluded',len(excluded),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args()
 if a.phase=='apis':
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   for f in [pool.submit(fn) for fn in [cleveland,chicago,mia]]:f.result()
 else:globals()[a.phase]()
