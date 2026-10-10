import importlib.util,json,time
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f','ops/museum-expansion-fitzwilliam-native-20261007.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;n=f.n;R=f.RUN
urls=[('wikiart','https://www.wikiart.org/en/george-hemming-mason/landscape-1869'),('wikiart','https://www.wikiart.org/en/john-everett-millais/the-bridesmaid'),('wikiart','https://www.wikiart.org/en/philip-wilson-steer/hydrangeas-1901')]+[('wikidata','https://www.wikidata.org/wiki/Special:EntityData/'+q+'.json') for q in ['Q106874666','Q50820390','Q50821640']]
out=[]
for kind,url in urls:
 provider='fitzwilliam-'+kind;n.SITES[provider]='https://www.'+kind+'.org'
 try:
  raw,cap=n.capture(provider,url)
  if kind=='wikidata':parsed=json.loads(raw)
  else:
   soup=BeautifulSoup(raw,'html.parser');parsed=dict(full_text=soup.get_text(' ',strip=True),h1=[a.get_text(' ',strip=True) for a in soup.select('h1')],h2=[a.get_text(' ',strip=True) for a in soup.select('h2')],fields=[a.get_text(' ',strip=True) for a in soup.select('.wiki-layout-artist-info li')],canonical=[a['href'] for a in soup.select('link[rel=canonical]')])
  out.append(dict(url=url,kind=kind,capture=cap,parsed=parsed));print('OK',url,flush=True)
 except Exception as error:out.append(dict(url=url,kind=kind,error=str(error)));print('ERROR',url,str(error),flush=True)
 time.sleep(.5)
m.save(R/'existing-followup-exact-sources-001.json.gz',dict(at=m.now(),records=out,policy='Selected metadata comparisons only. No images, no artwork changes. Correlated WikiArt/Wikidata claims do not independently establish present display.'))
