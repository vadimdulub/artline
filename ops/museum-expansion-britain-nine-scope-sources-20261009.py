"""Selected creation-scope evidence; no metadata rewrites or image downloads."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;n.HOSTS['cas']={'contemporaryartsociety.org','www.contemporaryartsociety.org'};n.HOSTS['lenkiewicz']={'www.robertlenkiewicz.org','robertlenkiewicz.org'}
SOURCES=[('cas','https://contemporaryartsociety.org/objects/chronic-blue-1986'),('lenkiewicz','https://www.robertlenkiewicz.org/projects'),('box','https://www.theboxplymouth.com/blog/news/portraits-to-make-you-think')]
def main():
 dest=RUN/'creation-scope-sources-001.json.gz';assert not dest.exists();rows=[]
 for provider,url in SOURCES:
  try:
   raw,c=n.capture(provider,url);p=n.parsed(raw);rows.append(dict(provider=provider,url=url,capture=c,parsed=p));print(json.dumps(dict(provider=provider,url=url,status=200,bytes=c['receipt']['bytes'],text_length=len(p['text']))),flush=True)
  except Exception as e:rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,script_reference=n.ref(Path(__file__).resolve()),policy='CAS exact1986work/accession and foundation Project3 dating inform holds. Exhibition/project dates are not silently made artwork creation years. Museum article date is retained only if native capture succeeds; web-index discovery otherwise explicitly limited. No images or metadata changes.'))
if __name__=='__main__':main()
