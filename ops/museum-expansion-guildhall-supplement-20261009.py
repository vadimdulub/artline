"""Bounded publisher sources discovered during explicit version research."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-guildhall-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
SOURCES=[
 ('dyce-dated','https://artsandculture.google.com/asset/george-herbert-at-bemerton/qwF9gzxjLpAUCA'),
 ('dyce-medium','https://artsandculture.google.com/asset/george-herbert-at-bemerton-william-dyce/tQHBB3xavGDShw?hl=en'),
 ('faith-story','https://artsandculture.google.com/story/faith-city-of-london-corporation/TAVBbPVYBd2CJg?hl=en'),
 ('cuyp-loans-story','https://artsandculture.google.com/story/in-the-light-of-cuyp-dordrechts-museum/2QXRF_i5lV-Lcw?hl=en')]
def main():
 out=[]
 for key,url in SOURCES:
  dest=n.RUN/(key+'-001.json');assert not dest.exists();raw,cap=n.g.p.n.capture('guildhall_gac',url);s=n.g.p.n.BeautifulSoup(raw,'html.parser');links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in s.select('a[href]') if '/asset/' in a['href']];n.m.save(dest,dict(at=n.m.now(),url=url,capture=cap,parsed=n.g.parsed(raw),asset_links=links,discovery='Web results turn960search0 through turn960search4',policy='Selected metadata and textual version evidence. Dordrecht exhibition loans are not Dordrecht holdings; no image download or current-display inference.'));out.append(n.ref(dest));print(json.dumps(dict(key=key,bytes=cap['receipt']['bytes'],assets=links)),flush=True)
 n.m.save(n.RUN/'supplement-captured-001.json',dict(at=n.m.now(),rows=out,script_reference=n.ref(Path(__file__).resolve())))
if __name__=='__main__':main()
