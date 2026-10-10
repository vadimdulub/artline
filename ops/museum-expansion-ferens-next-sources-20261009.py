"""Two official collection landing-page probes for the preserved next-museum queue."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-ferens-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN
def main():
 dest=RUN/'next-source-probes-001.json';assert not dest.exists();out=[]
 for provider,url in [('guildhall','https://www.cityoflondon.gov.uk/things-to-do/attractions-museums-entertainment/guildhall-art-gallery/collections'),('salford','https://salfordmuseum.com/explore/collections/')]:
  p.n.SITES[provider]=url.split('/')[0]+'//'+url.split('/')[2];v=dict(provider=provider,url=url)
  try:
   raw,cap=p.n.capture(provider,url);soup=p.n.BeautifulSoup(raw,'html.parser');v.update(state='captured_landing',capture=cap,text=soup.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]')])
  except Exception as e:v.update(state='source_error',error=type(e).__name__+': '+str(e))
  out.append(v)
 m.save(dest,dict(at=m.now(),rows=out,script_reference=p.ref(Path(__file__).resolve()),policy='Official landing pages only,not object confirmation. Observed catalogue links retained for next scoped selection. No ArtUK access,images,emails or catalogue writes.'))
 print(json.dumps([dict(provider=v['provider'],state=v['state'],links=[x for x in v.get('links',[]) if any(t in (x['text']+' '+x['url']).lower() for t in ['collection','catalog','artuk','smartify'])]) for v in out]),flush=True)
if __name__=='__main__':main()
