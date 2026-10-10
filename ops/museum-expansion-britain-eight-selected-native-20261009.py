"""Selected collection context and object narratives from observed official links."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-eight-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
def main():
 dest=RUN/'native-selected-001.json';assert not dest.exists();probe=m.load(RUN/'native-probes-001.json');links={urljoin(v['url'],x['href']) for v in probe['rows'] if 'parsed' in v for x in v['parsed']['links']};chosen=[('edinburgh','https://cultureedinburgh.com/things-to-see-and-do/fine-art-collection'),('southampton','https://southamptoncityartgallery.com/collection/20th-century-british-painting/'),('southampton','https://southamptoncityartgallery.com/collection/surrealists/'),('southampton','https://southamptoncityartgallery.com/collection/st-ives/'),('southampton','https://southamptoncityartgallery.com/whats-on/unlocking-collections-percy-delf-smith/'),('southampton','https://southamptoncityartgallery.com/whats-on/assembly-narrative-art-from-southampton-city-art-gallerys-collection/')];out=[];failures={};stopped=set()
 for provider,url in chosen:
  assert url in links
  if provider in stopped:out.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   raw,cap=n.n.capture(provider,url);p=n.parsed(raw);row=dict(provider=provider,url=url,capture=cap,parsed=p);failures[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=cap['receipt']['bytes'],text=p['text'][:15000])),flush=True)
  except Exception as e:
   failures[provider]=failures.get(provider,0)+1;row=dict(provider=provider,url=url,error=type(e).__name__+': '+str(e));print(json.dumps(row),flush=True)
   if failures[provider]>=3 or any(t in str(e) for t in ['403','429']):stopped.add(provider)
  out.append(row)
 m.save(dest,dict(at=m.now(),rows=out,stopped_providers=sorted(stopped),probe_reference=ref(RUN/'native-probes-001.json'),script_reference=ref(Path(__file__).resolve()),policy='Selected native collection narratives,not exhaustive artwork downloads. Exact object correspondence still requires review. No images or current-display assertions.'))
if __name__=='__main__':main()
