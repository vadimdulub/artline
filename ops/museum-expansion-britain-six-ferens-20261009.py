"""Public form searches for 101 selected Ferens accession numbers; no image downloads."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-six-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
n.SITES['hull_http']='http://museumcollections.hullcc.gov.uk'
def invkey(v):return re.sub(r'^KINCM:\s*','',v.strip().upper())
def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');objects=[dl for dl in soup.select('dl') if any(dt.get_text(' ',strip=True)=='Accession No:' for dt in dl.select('dt'))];assert len(objects)==1;fields={}
 for dt in objects[0].select('dt'):
  dd=dt.find_next_sibling();assert dd and dd.name=='dd';fields.setdefault(dt.get_text(' ',strip=True),[]).append(dd.get_text(' ',strip=True))
 dimensions=[[td.get_text(' ',strip=True) for td in tr.select('th,td')] for tr in soup.select('table.displayDimensions tr')]
 return dict(fields=fields,dimensions=dimensions)
def search_url(inventory):return n.SITES['hull_http']+'/collections/search-results/resultsoverview.php?'+urlencode(dict(accessionnumber=inventory,newsearch='new',museum2='Ferens Art Gallery',location='any'))
def main():
 dest=RUN/'ferens-native-001.json.gz';assert not dest.exists();rs=[r for r in m.load(RUN/'candidate-facts-001.json.gz')['rows'] if r['facts']['museum_qid']=='Q5444068'];assert len(rs)==101;selection=RUN/'ferens-native-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),rows=[dict(number=r['number'],artwork_id=r['existing_artwork_id'],inventory=r['facts']['inventory']) for r in rs],source_reference=ref(RUN/'candidate-facts-001.json.gz'),policy='Exact accession queries using observed public form,including required newsearch=new. Select Ferens,all display states. No broad results crawled.'))
 out=[];failures=0;stopped=False
 for r in rs:
  number=r['number'];row=dict(number=number,artwork_id=r['existing_artwork_id'],inventory=r['facts']['inventory']);destrow=RUN/'ferens-selected-001'/('%03d.json'%number);assert not destrow.exists();url=search_url(row['inventory'])
  try:
   raw,cap=n.capture('hull_http',url);soup=n.BeautifulSoup(raw,'html.parser');links=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if re.match(r'display\.php\?irn=\d+&',a['href'])});row.update(search_capture=cap,object_links=links)
   if len(links)==1:
    raw,cap=n.capture('hull_http',links[0]);data=parsed(raw);assert len(data['fields']['Accession No:'])==1;row.update(object_capture=cap,parsed=data,object_url=links[0],state='captured_exact_inventory' if invkey(data['fields']['Accession No:'][0])==invkey(row['inventory']) else 'native_inventory_mismatch')
   else:row['state']='no_unique_exact_inventory_result'
   failures=0
  except Exception as err:
   failures+=1;row.update(state='capture_error',error=type(err).__name__+': '+str(err));stopped=failures>=3 or any(v in str(err) for v in ['403','429','Forbidden'])
  m.save(destrow,row);out.append(dict(number=number,state=row['state'],reference=ref(destrow)));print(json.dumps(dict(number=number,state=row['state'],completed=len(out),selected=len(rs))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_numbers=[r['number'] for r in rs if r['number'] not in {r['number'] for r in out}],policy='Official current museum page explicitly publishes the legacy HTTP catalogue. HTTPS transport failure is not an access denial. Original HTTP public endpoint used. Native display labels are undated and retained only as evidence,not fresh on-view claims. Exact source metadata requires editorial identity review. Original inventory text,suffixes and dimensions retained.'))
if __name__=='__main__':main()
