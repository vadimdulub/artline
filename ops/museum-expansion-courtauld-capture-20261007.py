#!/usr/bin/env python3
"""Retain bounded native Courtauld metadata GETs and read-only search-form POSTs."""
import argparse,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import requests
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-courtauld-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN;BASE='https://gallerycollections.courtauld.ac.uk'

def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def saved_body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw

def capture(request):
 method=request.get('method','get').lower();url=request['url'];data=request.get('data');assert method in ['get','post'] and url.startswith(BASE+'/')
 assert urlparse(url).path.startswith(('/object-','/collections/THES100018')) and '/assets/' not in url
 if method=='post':
  assert urlparse(url).path=='/collections/THES100018' and data is not None
  assert set(data)<=set('col_session search page sort sort_reverse per_page view_all mi_search_type parent csrf'.split())
  assert data.get('view_all','')=='' and data.get('per_page','') in ['', '52'] and 1<=int(data.get('page','1'))<=6
 key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest();root=RUN/'captures';receipt=root/(key+'.json');body=root/(key+'.body.gz');root.mkdir(exist_ok=True)
 if receipt.exists():
  rc=m.load(receipt);assert rc['request']==request;raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'];assert rc['status']==200;return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
 time.sleep(.4)
 with requests.request(method,url,data=data,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata; no images)'},timeout=(12,45),stream=True) as response:
  raw=b''
  for chunk in response.iter_content(65536):
   raw+=chunk;assert len(raw)<4_000_000,'Metadata response bound'
  rc=dict(request=request,url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(receipt,rc)
  response.raise_for_status();assert response.url.startswith(BASE+'/')
 return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))

def form_request(soup,name):
 form=soup.select_one('form[name="'+name+'"]');assert form is not None;method=form['method'].lower();assert method=='post';data={x['name']:x.get('value','') for x in form.select('input[name]')};assert len(data)==len(form.select('input[name]'))
 return dict(method=method,url=form['action'],data=data,source_form=name)

def parsed_index(raw):
 soup=BeautifulSoup(raw,'html.parser');rows=[]
 for card in soup.select('section.card.summary-box'):
  a=card.select_one('.text-wrap a[href]');assert a;name=a.select_one('h2');title=a.select_one('.card-summary-text');dates=[x for x in a.find_all('span',recursive=False) if x!=title and not x.select_one('h2')]
  assert len(dates)<=1 and title
  rows.append(dict(source_path=a['href'],url=urljoin(BASE,a['href']),creator_label=name.get_text(' ',strip=True) if name else None,title=title.get_text(' ',strip=True),date_display=dates[0].get_text(' ',strip=True) if dates else None,source_html=str(card)))
 assert 1<=len(rows)<=52 and len(rows)==len({x['url'] for x in rows})
 nxt=form_request(soup,'next_page');sort=form_request(soup,'sorted_results2')
 text=soup.get_text(' ',strip=True);total=re.search(r'([\d,]+)\s+items found',text);assert total
 return dict(rows=rows,total=int(total[1].replace(',','')),next_request=nxt,artist_sort_request=sort,full_text=text)

def parsed_object(raw):
 soup=BeautifulSoup(raw,'html.parser');fields=[]
 for heading in soup.select('h2.full_record_data_caption'):
  value=heading.find_next_sibling('div',class_='full_record_data_value');assert value is not None
  # Maker names are submit-button values, absent from plain DOM text. Preserve
  # their enclosing field-set and adjacent attribution/date text separately.
  makers=[]
  for form in value.select('form.adv_maker_search'):
   submit=form.select_one('input[type="submit"]');authority=form.select_one('input[name="adv_maker_id"]');assert submit
   makers.append(dict(name=submit.get('value'),authority_id=authority.get('value') if authority else None,field_set_html=str(form.parent),residual_text=form.parent.get_text(' ',strip=True)))
  fields.append(dict(label=heading.get_text(' ',strip=True),text=value.get_text(' ',strip=True),html=str(value),makers=makers))
 assert len([x for x in fields if x['label']=='Object Number'])==1
 return dict(headings=[x.get_text(' ',strip=True) for x in soup.select('h1')],fields=fields,full_text=soup.get_text(' ',strip=True),object_links=[dict(text=a.get_text(' ',strip=True),url=urljoin(BASE,a['href'])) for a in soup.select('a[href]') if a['href'].startswith('/object-')])

def selected_capture():
 indexes=[];seen=set();prev=None
 for page in range(1,5):
  path=RUN/f'painting-index-sorted-{page:03}.json.gz'
  if path.exists():v=m.load(path)
  else:
   if page==1:
    old=m.load(RUN/'painting-sorted-probe-001.json.gz');v=dict(page=page,capture=old['capture'],parsed=old['parsed'],source_reference=ref(RUN/'painting-sorted-probe-001.json.gz'))
   else:
    req=prev['parsed']['next_request'];assert int(req['data']['page'])==page;raw,cap=capture(req);v=dict(page=page,capture=cap,parsed=parsed_index(raw),previous_reference=ref(indexes[-1]))
   m.save(path,v)
  assert not seen.intersection(x['url'] for x in v['parsed']['rows']);seen.update(x['url'] for x in v['parsed']['rows']);indexes.append(path);prev=v
  print('INDEX',page,len(v['parsed']['rows']),v['parsed']['rows'][0]['creator_label'],v['parsed']['rows'][-1]['creator_label'],flush=True)
 objects=RUN/'objects';objects.mkdir(exist_ok=True);records=[]
 for path in indexes:
  for row in m.load(path)['parsed']['rows']:
   # An LP index row remains a loan lead; do not treat membership as ownership.
   if not row['source_path'].startswith('/object-p-'):continue
   dest=objects/(row['source_path'].removeprefix('/object-')+'.json.gz')
   if not dest.exists():
    raw,cap=capture(dict(method='get',url=row['url']));v=dict(index_row=row,index_reference=ref(path),capture=cap,parsed=parsed_object(raw));m.save(dest,v)
   v=m.load(dest);assert v['index_row']==row;records.append(ref(dest));print('OBJECT',len(records),row['source_path'],flush=True)
 dest=RUN/'selected-capture-001.json.gz'
 if not dest.exists():m.save(dest,dict(at=m.now(),indexes=[ref(p) for p in indexes],records=records,policy='First four artist-sorted painting pages only; native P-prefixed object metadata retained for review. LP loan leads retained in indexes. No image download, approval or database writes.'))
 print('COMPLETE',len(seen),len(records),flush=True)

def probe():
 old=m.load(RUN/'painting-index-probe-001.json.gz');idx=parsed_index(saved_body(old['capture']));m.save(RUN/'painting-index-parsed-001.json.gz',dict(index=idx,source_reference=ref(RUN/'painting-index-probe-001.json.gz')))
 req=idx['artist_sort_request'];raw,cap=capture(req);v=parsed_index(raw);m.save(RUN/'painting-sorted-probe-001.json.gz',dict(at=m.now(),request=req,capture=cap,parsed=v))
 print('SORTED',len(v['rows']),v['total'],[(x['creator_label'],x['title'],x['date_display']) for x in v['rows'][:6]],flush=True)
 for suffix,url in [('001',idx['rows'][0]['url']),('002',idx['rows'][1]['url'])]:
  body,cap=capture(dict(method='get',url=url));sp=BeautifulSoup(body,'html.parser');out=dict(at=m.now(),url=url,capture=cap,full_text=sp.get_text(' ',strip=True));m.save(RUN/('object-probe-'+suffix+'.json.gz'),out);print('OBJECT',suffix,out['full_text'],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['probe','selected'],nargs='?',default='probe');a=p.parse_args()
 if a.command=='probe':probe()
 else:selected_capture()
