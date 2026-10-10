"""Selected original sculpture/relief candidates; no comprehensive object downloads."""
import csv,gzip,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-source-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-20261010';q.RUN=RUN;q.CAP=RUN/'captures'
old=m.ROOT/'docs/research/greek-museums-20261008/delivery.csv';prior=[r for r in csv.DictReader(old.open(encoding='utf-8-sig'))if 'Kilkis'in str(r)];assert len(prior)==18
known={r['source_url'].split('?')[0]for r in prior};selection=[];pages=[]
# Three public index pages cover only65 index cards; detail selection is limited to sculpture/relief.
for page in [1,2,3]:
 if page==1:
  rc=m.load(q.CAP/'searchculture-collection-001.json');soup=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()),'html.parser')
 else:soup,rc=q.capture('searchculture-index-page'+str(page)+'-001','https://www.searchculture.gr/aggregator/portal/collections/Efa_Kilkis_col/search?language=en&page.page='+str(page)+'&resultsMode=GRID')
 cards=[];seen=set()
 for a in soup.select('a[href]'):
  parent=a
  while parent and 'edm-entity-result'not in parent.get('class',[]):parent=parent.parent
  if parent is None or not a.get_text(' ',strip=True):continue
  href=a.get('href','');match=re.search(r'/aggregator/edm/Efa_Kilkis_col/000224-[A-Za-z0-9-]+',href)
  if not match:continue
  url=urljoin('https://www.searchculture.gr',match.group(0))
  if url in seen:continue
  seen.add(url);text=parent.get_text(' ',strip=True);title=a.get_text(' ',strip=True)
  isart=any(v in text for v in ['Sculpture','Relief','Figurine'])
  state='already_in_historical_delivery'if url in known else'selected_detail_candidate'if isart else'other_index_record'
  card=dict(title=title,url=url,text=text,state=state);cards.append(card)
  if state=='selected_detail_candidate':selection.append(card)
 pages.append(dict(page=page,receipt=rc,cards=cards));print(json.dumps(dict(page=page,cards=len(cards),selected_so_far=len(selection))),flush=True)
assert sum(len(v['cards'])for v in pages)==65;assert len({v['url']for v in selection})==len(selection)
assert 0<len(selection)<=30,len(selection)
m.save(RUN/'selected-index-leads-001.json.gz',dict(at=m.now(),pages=pages,selected=selection,historical_records=prior,historical_reference=q.s.ref(old),policy='Only new figurine,sculpture andrelief index candidates selected.65 index cards do not prove65eligibleartworks ornewrecords.18knownworks excluded byhistorical source URL; fresh fullproduction identity check still required. Index enriched periods are not native creation dates.'))
rows=[]
for n,v in enumerate(selection):
 sid=v['url'].split('/aggregator/edm/')[1];soup,rc=q.capture('selected-'+sid.replace('/','-')+'-001',v['url']);links=[dict(title=a.get_text(' ',strip=True),url=urljoin(v['url'],a['href']))for a in soup.select('a[href]')if 'efa-kilkis.gr/artworks/'in a['href']];rows.append(dict(number=n+1,source_id=sid,index=v,receipt=rc,text=soup.get_text(' ',strip=True),native_links=links));print(json.dumps(dict(selected_object=n+1,source_id=sid)),flush=True);time.sleep(.15)
m.save(RUN/'selected-object-discovery-001.json.gz',dict(at=m.now(),rows=rows,index_reference=q.s.ref(RUN/'selected-index-leads-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),policy='Metadata leads only; individual native dates,physical units,museum location andlive duplicates still require review. Noimages orDBwrites.'))
