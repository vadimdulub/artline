#!/usr/bin/env python3
"""Bounded primary museum research for the frozen country draw; no DB writes."""
import argparse,collections,concurrent.futures,importlib.util,json,re,threading,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-chinese-art-20261008.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
ROOT=b.ROOT;RUN=ROOT/'docs/research/random-country-collections-20261009';PDM='https://creativecommons.org/publicdomain/mark/1.0/'
def phase(code):b.RUN=RUN/code;b.RUN.mkdir(parents=True,exist_ok=True)
def save(n,v):b.save(n,v)
def page(url,source=None):
 raw,rc=(source or b.Source()).get(url,as_json=False);return BeautifulSoup(raw,'html.parser'),rc
def nextitem(url,source=None):
 sp,rc=page(url,source);data=json.loads(sp.select_one('#__NEXT_DATA__').string)['props']['pageProps'];return data['data']['item'],rc
def bounds(text):
 text=(text or '').strip();t=re.sub(r'^(?:c\.?|ca\.?|circa|um|about|around|vers|environ)\s*','',text,flags=re.I)
 t=re.sub(r'^between (\d{3,4}) and (\d{3,4})$',r'\1–\2',t,flags=re.I)
 if re.fullmatch(r'\d{3,4}',t):return int(t),int(t)
 x=re.fullmatch(r'(\d{3,4})\s*[-–—/]\s*(\d{3,4})',t)
 if x:return int(x[1]),int(x[2])
 x=re.fullmatch(r'(\d{4})\s*[-–—/]\s*(\d{2})',t)
 if x:return int(x[1]),int(x[1][:2]+x[2])
 x=re.fullmatch(r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Summer|Winter|Spring|Autumn)\s+(\d{4})',t,re.I)
 if x:return int(x[1]),int(x[1])
 years=re.findall(r'\b[12]\d{3}\b',text)
 if years and min(map(int,years))>1970:return min(map(int,years)),max(map(int,years))
 return None,None
def record(provider,raw,rc,**kw):
 lo,hi=bounds(kw.get('date_display'));return b.candidate(provider,raw,rc,year_start=lo,year_end=hi,image_url=None,image_license_url=None,image_rights_label='Reproduction permission not established',**kw)
def clean_name(x):return re.sub(r'\s*\([^)]*\)\s*$','',x or '').strip()
def accept(r,held):
 if r['date_decision']=='after_cutoff':held.append(dict(key=r['provider']+'/'+r['source_id'],reason='Created after 1970',date=r['date_display']));return False
 if re.search(r'\b(?:on loan|permanent loan|lent by|Leihgabe|Dauerleihgabe|Depositum)\b',r.get('credit') or '',re.I):held.append(dict(key=r['provider']+'/'+r['source_id'],reason='Loan/deposit requires separate holding classification',credit=r['credit']));return False
 assert len(r.get('accession_number') or '')<150
 return True
def zurich():
 phase('CH');d=b.load('zurich-discovery.json.gz')['next']['props']['pageProps'];ids=sorted({x['ReferencedId'] for c in d['collections'] if c['Id'] in ['3003','9001'] for x in c['OclObjectRef']['Items']},key=int);out=[];held=[];source=b.Source()
 for pos,oid in enumerate(ids,1):
  u='https://collection.kunsthaus.ch/en/collection/item/'+oid
  try:
   x,rc=nextitem(u,source);assert x['Id']==oid
   label=x.get('ObjPersonMasonryTxt') or clean_name(x.get('ObjPersonListTxt'));typ=(x.get('ObjCategoryVoc') or {}).get('LabelTxt') or 'unknown'
   if not re.search('painting|drawing|print|sculpt|watercolour|pastel|fresco',typ,re.I):held.append(dict(key='zurich/'+oid,reason='Outside selected pictorial/sculptural categories',type=typ));continue
   r=record('zurich',x,rc,source_id=oid,title=x['ObjTitleTxt'],alternate_title=x.get('ObjTitleFurtherTxt'),museum='Kunsthaus Zürich',source_url=u,creator_label=label,date_display=x.get('ObjDateTxt'),source_type=typ,medium=x.get('ObjMaterialTechniqueTxt'),dimensions=x.get('ObjDimensionsTxt'),accession_number=x.get('ObjObjectNumberTxt') or x.get('Inv. Nr.'),credit=x.get('ObjCreditlineTxt'),selection_basis='Official Masterpieces and Evergreens selections; metadata selected before images')
   people=x.get('ObjPersonMultipleRef',{}).get('Items',[])
   if len(people)==1:r['creator_source_url']='https://collection.kunsthaus.ch/en/artists/artist/'+people[0]['ReferencedId'];r['creator_life_source']=people[0].get('PerDateTxt')
   photos=x.get('ObjMultimediaMainImageRef',{}).get('Items',[]);photo=next((p for p in photos if any(mm.get('full')==x.get('DefaultImage') for mm in p.get('Multimedia',[]))),None)
   if photo:
    r['image_rights_label']=photo.get('MulPhotocreditTxt') or 'Unknown';r['image_candidate_url']=urljoin('https://collection.kunsthaus.ch/',x.get('DefaultImage') or '')
    if re.search('public domain|gemeinfrei|CC0',r['image_rights_label'],re.I):r.update(image_url=r['image_candidate_url'],image_license_url=PDM)
   if accept(r,held):out.append(r)
  except Exception as e:held.append(dict(key='zurich/'+oid,reason=str(e)[:300]))
  if pos%50==0:print('Zurich metadata',pos,'/',len(ids),flush=True)
 save('zurich-records.json.gz',dict(records=out,held=held,inspected=len(ids)));print('Zurich selected',len(out),flush=True)
def basel():
 phase('CH');source=b.Source();sp,rc=page('https://kunstmuseumbasel.ch/de/sammlung/schwerpunkte',source);ids=[]
 for f in sp.select('figure.masterpieces__item'):
  a=f.find('a',href=True);match=re.search(r'(?:gw|ew)\d{2}-(\d{7})-',a['href']) if a else None
  if match:ids.append(str(int(match[1])))
 ids=list(dict.fromkeys(ids));assert ids;out=[];held=[]
 for oid in ids:
  u='https://sammlung.kunstmuseumbasel.ch/en/collection/item/'+oid
  try:
   x,rc=nextitem(u,source);f=lambda k:x.get(k,{}).get('LabelTxt');label=clean_name(f('ObjDetailCaption2Txt'));medium=f('ObjDetailMaterialTechniqueTxt') or ''
   typ='painting' if re.search('Öl|Tempera|Leinwand|Acryl|Mischtechnik',medium) else 'sculpture' if re.search('Bronze|Gips|Holz|Marmor',medium) else 'drawing' if re.search('Bleistift|Kreide|Tusche|Aquarell',medium) else 'unknown'
   r=record('basel',x,rc,source_id=oid,title=f('ObjDetailCaption1Txt'),museum='Kunstmuseum Basel',source_url=u,creator_label=label,date_display=f('ObjDetailDateTxt'),source_type=typ,medium=medium or None,dimensions=f('ObjDetailDimensionTxt'),accession_number=f('ObjDetailNumberTxt'),credit=f('ObjDetailCreditlineTxt'),selection_basis='Official museum highlights')
   photos=x.get('ObjDetailMultimediaRef',{}).get('Items',[]);photo=next((p for p in photos if any(mm.get('full')==x.get('DefaultImage') for mm in p.get('Multimedia',[]))),None)
   if photo:
    rights=photo.get('ImageCopyrightTxt',{}).get('LabelTxt');r['image_rights_label']=rights
    if rights=='Bilddaten gemeinfrei - Kunstmuseum Basel' and f('ObjDetailRightsTxt')==rights:r.update(image_url=urljoin('https://sammlung.kunstmuseumbasel.ch/',x['DefaultImage']),image_license_url='https://download.kunstmuseumbasel.ch/')
   if accept(r,held):out.append(r)
  except Exception as e:held.append(dict(key='basel/'+oid,reason=str(e)[:300]))
 page('https://download.kunstmuseumbasel.ch/',source)
 save('basel-records.json.gz',dict(records=out,held=held,inspected=len(ids)));print('Basel selected',len(out),flush=True)
def mcba():
 phase('CH');source=b.Source();urls=set();out=[];held=[]
 for n in range(1,5):
  sp,rc=page('https://www.mcba.ch/en/collection/'+('page/'+str(n)+'/' if n>1 else ''),source)
  for h in sp.select('[itemprop=name]'):
   a=h.find_parent('a',href=True)
   if a:urls.add(urljoin(rc['final_url'],a['href']))
  for a in sp.select('a[href]'):
   if re.search(r'/en/collection/[^/?]+/$',a['href']) and a.get_text(' ',strip=True) and re.search(r'\d{4}',a.get_text()):urls.add(a['href'])
 for n,u in enumerate(sorted(urls),1):
  try:
   sp,rc=page(u,source);h=sp.select_one('h1');label=h.select_one('[itemprop=artist]').get_text(' ',strip=True);td=h.select_one('[itemprop=name]').get_text(' ',strip=True);title,dt=td.rsplit(', ',1)
   node=sp.find(string=lambda s:s and 'Inv.' in s);assert node;info=node.parent.parent;med=info.select_one('[itemprop=artMedium]');medium=med.get_text(' ',strip=True) if med else None;acc=re.search(r'Inv\.\s*(.+)',node.parent.get_text(' ',strip=True))[1]
   r=record('mcba',dict(object_label=info.get_text(' ',strip=True),title_date=td),rc,source_id=u.rstrip('/').split('/')[-1],title=title,museum='Cantonal Museum of Fine Arts',source_url=u,creator_label=label,date_display=dt,source_type='painting' if re.search('oil|tempera|acrylic|gouache',medium or '',re.I) else 'drawing' if re.search('watercolour|pencil|ink|pastel',medium or '',re.I) else 'print' if re.search('woodcut|lithograph|etching|engraving',medium or '',re.I) else 'sculpture' if re.search('bronze|plaster|marble',medium or '',re.I) else 'unknown',medium=medium,dimensions=None,accession_number=acc,credit=None,selection_basis='First four official online catalogue pages')
   if accept(r,held):out.append(r)
  except Exception as e:held.append(dict(url=u,reason=str(e)[:300]))
 save('mcba-records.json.gz',dict(records=out,held=held,inspected=len(urls)));print('Lausanne selected',len(out),flush=True)
def winterthur():
 phase('CH');source=b.Source();d=b.load('winterthur-discovery.json.gz');urls=[x['url'] for x in d['links'] if '/en/collection/' in x['url'] and x['url']!=d['url']];out=[];held=[]
 for u in list(dict.fromkeys(urls)):
  if '/contemporary-art/' in u:continue
  sp,rc=page(u,source)
  for pos,node in enumerate(sp.select('.module--image__caption')):
   st=node.find('strong');em=node.find('em')
   if not(st and em):continue
   lines=[t.strip() for t in node.get_text('\n',strip=True).splitlines() if t.strip()];creator=st.get_text(' ',strip=True);title=em.get_text(' ',strip=True);idx=lines.index(title);date=lines[idx+1].lstrip(', ') if idx+1<len(lines) else None
   credit=' '.join(lines[idx+2:]);raw=dict(caption=node.get_text(' ',strip=True),lines=lines)
   r=record('swiss-highlight',raw,rc,source_id='winterthur/'+urlsplit(u).path.rstrip('/').split('/')[-1]+'/'+str(pos),title=title,museum='Kunstmuseum Winterthur, Winterthur, Switzerland',source_url=u+'#artline-caption-'+str(pos),creator_label=creator,date_display=date,source_type='unknown',medium=None,dimensions=None,accession_number=None,credit=credit,selection_basis='Official collection department highlights; individual artwork caption, not exhibition ownership inference')
   if re.search(r'\(\d{4}\)',date or ''):r['date_decision']='date_review';r['year_start']=r['year_end']=None
   if accept(r,held):out.append(r)
 save('winterthur-records.json.gz',dict(records=out,held=held,inspected=len(out)+len(held)));print('Winterthur selected',len(out),flush=True)
if __name__=='__main__':
 import sys
 globals()[sys.argv[1]]()
