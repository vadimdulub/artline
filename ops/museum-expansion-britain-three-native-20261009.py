"""Bounded native authority and selected object-page research, no image capture."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-three-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
n.RUN=RUN;n.SITES={'cardiff':'https://museum.wales','bristol':'https://www.bristolmuseums.org.uk','bristol-exhibition':'https://exhibitions.bristolmuseums.org.uk'}
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();out=[]
 requests=[('cardiff','https://museum.wales/cardiff/art/'),('bristol','https://www.bristolmuseums.org.uk/bristol-museum-and-art-gallery/'),('cardiff','https://museum.wales/collections/online/?'+urlencode(dict(field0='string',value0='NMW A 5052'))),('bristol-exhibition','https://exhibitions.bristolmuseums.org.uk/death/attitudes/')]
 for provider,url in requests:
  try:
   raw,cap=n.capture(provider,url);soup=n.BeautifulSoup(raw,'html.parser');links=[dict(text=a.get_text(' ',strip=True),href=a.get('href')) for a in soup.select('a[href]')];out.append(dict(provider=provider,url=url,capture=cap,text=soup.get_text(' ',strip=True),links=links))
  except Exception as error:out.append(dict(provider=provider,url=url,error=type(error).__name__+': '+str(error)))
 m.save(dest,dict(at=m.now(),rows=out,script_reference=ref(Path(__file__).resolve()),policy='Bounded native museum authority and selected object context. Collection pages support only their stated facts, not every artwork. No new ownership, custody or display claim. No images downloaded.'))
 m.save(RUN/'source-access-holds-001.json',dict(at=m.now(),new_holds=[dict(host='collections.bristolmuseums.org.uk',observed='web tool returned Blocked by robots.txt, non-retryable error when searching the official catalogue on 9 October 2026; previous homepage link open returned Internal Error.',retry=False)],preserved_previous_checkpoint_reference=ref(s.CP),policy='Do not retry or bypass the blocked Bristol catalogue. Existing Art UK403 and all earlier source holds remain. Accessible public museum exhibition/overview pages are separate sources.'))
 print(json.dumps([dict(provider=v['provider'],error=v.get('error'),bytes=v.get('capture',{}).get('receipt',{}).get('bytes')) for v in out]),flush=True)
if __name__=='__main__':main()
