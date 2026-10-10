"""Bounded public native catalogue discovery; preserve raw pages without images."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-milan-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
n=s.module('n','museum-expansion-native-20261006.py');n.RUN=RUN;n.SITES={'milan':'https://collezioni-online.museoscienza.org','brighton':'https://brightonmuseums.org.uk','ulster':'https://www.nationalmuseumsni.org'}
def main():
 dest=RUN/'native-probes-001.json';assert not dest.exists();rows=[]
 for provider,url in [('milan','https://collezioni-online.museoscienza.org/settori/collezioni-d-arte'),('brighton','https://brightonmuseums.org.uk/discovery/'),('ulster','https://www.nationalmuseumsni.org/collections')]:
  try:
   raw,cap=n.capture(provider,url);p=n.BeautifulSoup(raw,'html.parser');row=dict(provider=provider,url=url,capture=cap,text=p.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a.get('href')) for a in p.select('a[href]')],forms=[str(a) for a in p.select('form')])
  except Exception as e:row=dict(provider=provider,url=url,error=type(e).__name__+': '+str(e))
  rows.append(row);print(json.dumps(dict(provider=provider,error=row.get('error'),bytes=row.get('capture',{}).get('receipt',{}).get('bytes'))),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,script_reference=ref(Path(__file__).resolve()),previous_checkpoint_reference=ref(s.CP),policy='Public native overview discovery only. No object-level holding inferred from a collection overview. Preserve prior access holds; no images or exhaustive downloading. Brighton and Ulster remain separate future selected object reviews.'))
if __name__=='__main__':main()
