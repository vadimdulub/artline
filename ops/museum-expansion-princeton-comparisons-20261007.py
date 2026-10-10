#!/usr/bin/env python3
"""Selected public comparison metadata; no images or catalogue mutations."""
import importlib.util,json,time
from pathlib import Path
from urllib.parse import urlparse
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-princeton-native-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
def main():
 rows=[('cma-greek-robe','https://openaccess-api.clevelandart.org/api/artworks/?accession_number=1963.600'),('met-autumn','https://collectionapi.metmuseum.org/public/collection/v1/objects/11278'),('met-kandinsky','https://collectionapi.metmuseum.org/public/collection/v1/objects/369093')]
 for key,url in rows:
  path=n.RUN/('comparison-'+key+'-001.json.gz');error=n.RUN/('comparison-'+key+'-error-002.json');assert not error.exists()
  original=n.RUN/('comparison-'+key+'-error-001.json')
  if original.exists():
   assert n.m.load(original)['error']=='AssertionError()'
   assessment=n.RUN/('comparison-'+key+'-assessment-001.json')
   assert not assessment.exists();n.m.save(assessment,dict(at=n.m.now(),error_reference=n.ref(original),assessment='Local provider-domain guard stopped execution before any HTTP request. Use a dedicated comparison provider restricted to the exact official API host. This is not a remote refusal or a source retry.'))
  try:
   provider='princeton-comparison-'+key;n.n.SITES[provider]='https://'+urlparse(url).netloc
   raw,cap=n.n.capture(provider,url);dest=n.RUN/'comparison-captures'/Path(cap['body_path']).name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();dest.write_bytes((n.m.ROOT/cap['body_path']).read_bytes());cap['body_path']=str(dest.relative_to(n.m.ROOT))
   x=dict(at=n.m.now(),url=url,capture=cap,data=json.loads(raw),selection='Single exact existing-object physical-version comparison; no images');assert not path.exists();n.m.save(path,x);print(json.dumps(dict(key=key,status=x['capture']['receipt']['status'])),flush=True);time.sleep(3)
  except Exception as e:n.m.save(error,dict(at=n.m.now(),url=url,error=repr(e),policy='Retained failure. No automatic retry or transport change.'));raise
if __name__=='__main__':main()
