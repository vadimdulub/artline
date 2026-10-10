"""Bounded selection: first120 theatre index entries and dated art leads."""
import gzip,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-source-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);s=q.s;m=q.m;RUN=q.RUN
BASE='https://www.searchculture.gr'
def clean(t):return re.sub(r'\s+',' ',re.sub(r'\((EL|EN)\)\s*$','',t)).strip()
def fields(soup):
 out={};enriched={}
 for group in soup.select('.form-group'):
  label=group.select_one('label.control-label')
  if label is None:continue
  key=clean(label.get_text(' ',strip=True));vs=[clean(v.get_text(' ',strip=True))for v in group.select('.item-control-static')];vs=[v for v in vs if v]
  if key in out:raise ValueError('Repeated field '+key)
  out[key]=vs;ee=[clean(v.get_text(' ',strip=True))for v in group.select('.panel-enrichment')]
  if ee:enriched[key]=ee
 return out,enriched
def index(soup):
 out=[]
 for a in soup.select('a[href]'):
  u=urljoin(BASE,a['href'])
  if re.fullmatch(r'https://www.searchculture.gr/aggregator/edm/Kazantzakis/000092-\d+',u):
   title=clean(a.get_text(' ',strip=True));parent=a
   while parent and 'edm-entity-result'not in parent.get('class',[]):parent=parent.parent
   if title and not any(v['url']==u for v in out):out.append(dict(url=u,title=title,text=clean(parent.get_text(' ',strip=True))if parent else title))
 return out

def main():
 old=m.load(m.RUN/'native/rhodes-final-20261009/next-source-discovery-001.json.gz');rows=[];pages=[]
 for page in range(1,5):
  if page==1:
   rc=old['rows'][1]['receipt'];soup=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()),'html.parser')
  else:soup,rc=q.capture('theatre-index-page'+str(page)+'-001',BASE+'/aggregator/portal/collections/Kazantzakis/search?page.page='+str(page)+'&resultsMode=GRID')
  leads=index(soup);assert len(leads)==30,(page,len(leads));assert not set(v['url']for v in leads)&set(v['url']for v in rows);pages.append(dict(page=page,receipt=rc,leads=leads));rows+=leads;print(json.dumps(dict(page=page,index_leads=len(rows))),flush=True)
 art=BeautifulSoup(gzip.decompress((RUN/'captures/repository-art-category-001.body.gz').read_bytes()),'html.parser');existing={c['source_record_id'].split('-')[-1]for c in m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']['citations']};artleads=[];other=[]
 for el in art.select('.element-wrapper'):
  a=el.select_one('a[href]');sid=a['href'].rstrip('/').split('/')[-1];date=clean(el.select_one('.element-list-meta_element').get_text(' ',strip=True)).replace('Ημερομηνία: ','');title=clean(el.select_one('.element-list-title').get_text(' ',strip=True));v=dict(source_id=sid,url=BASE+'/aggregator/edm/DigKazantzakis/000201-'+sid,native_url=a['href'],title=title,index_date=date)
  if re.fullmatch(r'\d{4}',date)and int(date)<=1970 and sid not in existing:artleads.append(v)
  else:other.append(v)
 m.save(RUN/'selected-index-leads-001.json.gz',dict(at=m.now(),theatre_pages=pages,art_leads=artleads,art_index_other=other,art_category_reference=s.ref(RUN/'captures/repository-art-category-001.json'),policy='120/2772 theatre leads,dated art leads only. Native repeated2005 dates are not automatically trusted as physical creation,especially where aggregator date unknown. Existing18 museum records preserved. No images.'))
 selected=rows+artleads;output=[]
 for n,v in enumerate(selected):
  suffix=v['url'].split('/aggregator/edm/')[1];key='selected-'+suffix.replace('/','-')+'-001';soup,rc=q.capture(key,v['url']);literal,enrichment=fields(soup);assert literal.get('Τίτλος')and literal.get('Πάροχος');links=[dict(title=clean(a.get_text(' ',strip=True)),url=urljoin(v['url'],a['href']))for a in soup.select('a[href]')if '/records/'in a['href']or '/files/'in a['href']];output.append(dict(number=n+1,source_id=suffix,source_url=v['url'],index=v,fields=literal,enrichment=enrichment,links=links,receipt=rc));print(json.dumps(dict(number=n+1,source_id=suffix,title=literal['Τίτλος'],date=literal.get('Ημερομηνία'),types=literal.get('Τύπος')),ensure_ascii=False),flush=True);time.sleep(.12)
 m.save(RUN/'native-selection-001.json.gz',dict(at=m.now(),rows=output,selection_reference=s.ref(RUN/'selected-index-leads-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Selected individual public museum-provider metadata from SearchCulture. Literal and EKT-enriched creator fields kept separate. Source dates require physical-object review. No images or production writes.'))
if __name__=='__main__':main()
