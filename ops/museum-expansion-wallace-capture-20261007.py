#!/usr/bin/env python3
"""Bounded official Wallace metadata discovery; no database or image writes."""
import argparse,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import parse_qs,urljoin,urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-wallace-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN
BASE='https://wallacelive.wallacecollection.org';d.n.SITES['wallace']=BASE

def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def capture(url):
 assert url.startswith(BASE+'/eMP/eMuseumPlus') and 'DynamicAsset' not in url and 'TspImage.link' not in url
 return d.n.capture('wallace',url)
def saved_body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def text(el):return el.get_text(' ',strip=True) if el else None
def creator(el):
 statement=text(el)
 # Strip only literal parenthesized numeric lifespan, never attribution wording.
 label=re.sub(r'\s*\(\s*\d{3,4}\s*[-–]\s*\d{3,4}\s*\)\s*',' ',statement or '').strip()
 return statement,label or None
def index(raw,url,cap):
 soup=BeautifulSoup(raw,'html.parser');rows=[]
 for el in soup.select('#collectionDetailList .detailListItem'):
  title=el.select_one('.tspTitleLink');assert title and title.parent.name=='a';statement,label=creator(el.select_one('.LbArtist'))
  rows.append(dict(title=text(title),creator_label=label,creator_statement=statement,date_display=text(el.select_one('.LbDate')),place_display=text(el.select_one('.LbPlaceartist')),click_url=urljoin(url,title.parent['href']),source_html=str(el)))
 assert 1<=len(rows)<=21
 nxt=soup.select('a[href*="moduleContextFunctionBar.navigator.next"]');urls={urljoin(url,a['href']) for a in nxt};assert len(urls)<=1
 return dict(at=m.now(),url=url,capture=cap,rows=rows,next_url=next(iter(urls),None),full_text=soup.get_text(' ',strip=True))
def object_page(raw,url):
 soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('#collectionDetail');assert main
 bookmarks=main.select('input.tspBookmarkField[value]');assert len(bookmarks)==1;bookmark=bookmarks[0]['value'];parsed=urlparse(bookmark);q=parse_qs(parsed.query)
 assert parsed.hostname=='wallacelive.wallacecollection.org' and q['module']==['collection'] and q['service']==['ExternalInterface'] and len(q['objectId'])==1 and q['objectId'][0].isdigit()
 sid=q['objectId'][0];statement,label=creator(main.select_one('.ListArtist'));title=text(main.select_one('.ListTitlepic'));assert title
 def field(cls):
  els=main.select('.'+cls);assert len(els)<=1
  return text(els[0].select_one('.tspValue')) if els else None
 dimensions=[text(x) for x in main.select('.ListDimensions .masse')]
 active=main.select_one('#collectionReferences .referenceTabItemActive');tabs=[dict(label=text(a),url=urljoin(url,a['href'])) for a in main.select('#collectionReferences dt a[href]') if a['href']!='#']
 return dict(source_id=sid,source_url=bookmark.replace('wallacecollection.org:443/','wallacecollection.org/'),literal_bookmark=bookmark,title=title,creator_label=label,creator_statement=statement,date_display=field('ListDatesall'),medium=field('ListMaterial'),inventory=field('ListMuseumno'),dimensions=dimensions,location_label=field('ListLocation'),active_tab=text(active),active_text=text(main.select_one('#collectionReferences .reference')),tabs=tabs,detail_text=text(main),detail_html=str(main),fields=[dict(classes=el.get('class',[]),text=text(el)) for el in main.select('#collectionDetailItem .listDescription > ul > li')])

def main(pages):
 assert 1<=pages<=16;probe=m.load(RUN/'painting-index-probe-001.json.gz');url=probe['url'];counts=dict(index_pages=0,objects=0,object_errors=0,tab_errors=0)
 for page in range(1,pages+1):
  dest=RUN/'native-index-001'/f'page-{page:03}.json.gz'
  if dest.exists():idx=m.load(dest);assert idx['url']==url
  else:
   raw,cap=capture(url);idx=index(raw,url,cap);m.save(dest,idx)
  counts['index_pages']+=1
  for pos,row in enumerate(idx['rows']):
   objfile=RUN/'native-objects-001'/f'page-{page:03}-row-{pos:02}.json.gz'
   if objfile.exists():record=m.load(objfile);assert record['index_row']==row
   else:
    record=dict(at=m.now(),index_reference=ref(dest),index_row=row,read_only=True,policy='Selected public metadata only; no images or import approvals. Source location labels are evidence, not fresh display claims. Native creator lifespans remain separate from creation.')
    try:
     raw,cap=capture(row['click_url']);parsed=object_page(raw,row['click_url']);record.update(capture=cap,parsed=parsed)
     assert parsed['title']==row['title'] and parsed['creator_label']==row['creator_label'] and parsed['date_display']==row['date_display'],'Index/object mismatch'
     tabs=[]
     for tab in parsed['tabs']:
      if tab['label'] not in ['Provenance','Marks/Inscriptions']:continue
      result=dict(request=tab)
      try:
       body,tc=capture(tab['url']);tp=object_page(body,tab['url']);assert tp['source_id']==parsed['source_id'] and tp['active_tab']==tab['label']
       for key in ['title','creator_statement','date_display','medium','inventory','dimensions']:assert tp[key]==parsed[key]
       result.update(capture=tc,parsed=tp)
      except Exception as ex:result['error']=type(ex).__name__+': '+str(ex)
      tabs.append(result)
     record['tabs']=tabs
    except Exception as ex:record['error']=type(ex).__name__+': '+str(ex)
    m.save(objfile,record)
   counts['objects']+=1;counts['object_errors']+=int('error' in record);counts['tab_errors']+=sum('error' in t for t in record.get('tabs',[]))
   print('OBJECT',page,pos,record.get('parsed',{}).get('source_id'),record.get('error','captured'),flush=True)
  print('PAGE',page,counts,flush=True);url=idx['next_url']
  if not url:break
 m.save(RUN/f'capture-pass-{pages:03}.json.gz',dict(at=m.now(),counts=counts,next_url=url,policy='Bounded subset of1095 Pictures and Miniatures search results, not an exhaustive collection download; metadata only. Candidate classification and individual editorial review remain required.'))
 print(json.dumps(counts),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pages',type=int,default=12);args=p.parse_args();main(args.pages)
