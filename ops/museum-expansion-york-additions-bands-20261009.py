"""Bounded public date-band searches select paintings before native object capture."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlparse,parse_qs
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;PRIOR=n.RUN;RUN=m.RUN/'native/york-additions-20261009';n.RUN=RUN
BOUNDS=[1400,1500,1550,1600,1650,1700,1750,1800,1825,1850,1875,1900,1925,1950,1970]
def entries(raw,url):
 soup=n.BeautifulSoup(raw,'html.parser');out=[]
 for a in soup.select('a[href]'):
  if not a.select_one('.object_number'):continue
  fields={k:(a.select_one('.'+k).get_text(' ',strip=True) if a.select_one('.'+k) else None) for k in ['object_number','title','creator','dates']};link=urljoin(url,a['href']);ids=parse_qs(urlparse(link).query).get('id');assert ids and len(ids)==1 and ids[0].isdigit();out.append(dict(fields=fields,url=link,native_id=ids[0]))
 assert len(out)<=16;return out
def main():
 dest=RUN/'date-band-index-001.json.gz';assert not dest.exists();context=m.load(PRIOR/'native-extra-001.json.gz');first=next(v for v in context['rows'] if v.get('provider')=='york');c=first['capture'];raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256'];soup=n.BeautifulSoup(raw,'html.parser');choices={key:{o.get('value') for o in soup.find('select',attrs={'name':key}).select('option')} for key in ['Gs[value]','Ge[value]']};assert soup.find('input',attrs={'name':'Gs[operator]'})['value']=='>=' and soup.find('input',attrs={'name':'Ge[operator]'})['value']=='<=';assert soup.find('input',attrs={'name':'OB[]','value':'painting'});rows=[];fails=0;stop=False
 for lo,hi in zip(BOUNDS,BOUNDS[1:]):
  assert str(lo) in choices['Gs[value]'] and str(hi) in choices['Ge[value]'];params={'CL[0]':'Fine Art','OB[0]':'painting','Gs[operator]':'>=','Gs[value]':lo,'Ge[operator]':'<=','Ge[value]':hi,'limit':16,'collections_page':1};url='https://yorkmuseumstrust.org.uk/collections/search/?'+urlencode(params)
  try:
   b,cap=n.capture('york',url);hits=entries(b,url);row=dict(start=lo,end=hi,url=url,params=params,capture=cap,hits=hits);rows.append(row);outliers=[]
   for h in hits:
    years=[int(y) for y in re.findall(r'(\d+)\s+AD',h['fields']['dates'] or '')]
    if not years or min(years)<lo or max(years)>hi:outliers.append(h)
   row['date_filter_outliers']=outliers;print(json.dumps(dict(start=lo,end=hi,hits=len(hits),outliers=len(outliers))),flush=True);fails=0
   if outliers:stop=True;break
  except Exception as e:
   fails+=1;rows.append(dict(start=lo,end=hi,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
   if fails>=3 or any(x in str(e) for x in ['403','429']):stop=True;break
 m.save(dest,dict(at=m.now(),rows=rows,provider_stopped=stop,form_reference=n.ref(PRIOR/'native-extra-001.json.gz'),script_reference=n.ref(Path(__file__).resolve()),policy='Fourteen public form date bands,16painting hits maximum each; museum-scoped selected metadata only,not exhaustive1099paintings/15733fine-art records. Stop if date filters appear ignored or source refuses access. Inclusive boundaries are deduplicated by native object ID in later selection. Index production dates require exact object and lifespan/version review. No images,object pages or database mutations.'))
if __name__=='__main__':main()
