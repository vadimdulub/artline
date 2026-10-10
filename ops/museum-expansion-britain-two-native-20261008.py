"""Bounded independent native context captures; no Art UK access retry or images."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-britain-two-facts-20261008.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);m=f.m;RUN=f.RUN;n=f.module('n','museum-expansion-native-20261006.py');n.RUN=RUN;n.SITES={'nam':'https://collection.nam.ac.uk','laing':'https://www.northeastmuseums.org.uk'}
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();requests=[('nam','https://collection.nam.ac.uk/detail.php?acc=1964-02-42-1'),('laing','https://www.northeastmuseums.org.uk/laing/about-us/our-collections')];out=[]
 for provider,url in requests:
  try:
   raw,cap=n.capture(provider,url);soup=n.BeautifulSoup(raw,'html.parser');out.append(dict(provider=provider,url=url,capture=cap,text=soup.get_text(' ',strip=True)))
  except Exception as error:out.append(dict(provider=provider,url=url,error=type(error).__name__+': '+str(error)))
 m.save(dest,dict(at=m.now(),rows=out,script_reference=f.ref(Path(__file__).resolve()),policy='Selected native context only. Art UK remains on prior403 access hold; not retried. The Recruit official accession adds -1 to the existing Art UK inventory; metadata remains unchanged. Individual facts support only their own object, not the whole batch.'))
 print(json.dumps([dict(provider=v['provider'],error=v.get('error'),bytes=v.get('capture',{}).get('receipt',{}).get('bytes')) for v in out]),flush=True)
if __name__=='__main__':main()
