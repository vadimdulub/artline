"""Bounded selected metadata discovery through the published Ferens public catalogue."""
import hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlsplit,parse_qs
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=m.RUN/'native/ferens-additions-20261009';n.RUN=RUN;BASE='http://museumcollections.hullcc.gov.uk';n.SITES={'ferens':BASE};IID='9172ebcd-f052-5736-a3ba-a8612ac75c60'
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parsed(raw):
 s=n.BeautifulSoup(raw,'html.parser');return dict(text=s.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=urljoin(BASE,a['href'])) for a in s.select('a[href]')],forms=[str(f) for f in s.select('form')])
def main():
 dest=RUN/'native-search-probe-001.json';assert not dest.exists();url=BASE+'/collections/search-results/resultsoverview.php?'+urlencode(dict(title='painting',newsearch='new',museum2='Ferens Art Gallery',location='any'));raw,cap=n.capture('ferens',url);s=n.BeautifulSoup(raw,'html.parser');data=parsed(raw)
 # Resolve links against this result path,not the site root.
 data['links']=[dict(text=a.get_text(' ',strip=True),href=urljoin(url,a['href'])) for a in s.select('a[href]')]
 m.save(dest,dict(at=m.now(),url=url,capture=cap,parsed=data,script_reference=ref(Path(__file__).resolve()),policy='Public form selects painting and Ferens,all display states,with required newsearch radio. Bounded metadata-first selection toward200; no exhaustive collection or image download. Previous access holds remain.'))
 print(json.dumps(dict(text=data['text'][data['text'].find('Search Results Found'):],links=[v for v in data['links'] if v['text'].startswith('View All')])),flush=True)
if __name__=='__main__':main()
