"""Observe the collection UI's public facet controls for a bounded painting selection."""
import gzip
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('z',Path(__file__).with_name('museum-expansion-zongolopoulos-source-20261010.py'))
z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
m,q,OLD=z.m,z.q,z.RUN
RUN=m.RUN/'native/zongolopoulos-paintings-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)


def main():
    old=m.load(OLD/'source-discovery-001.json.gz');rc=old['receipt']
    html=gzip.decompress((m.ROOT/rc['body_path']).read_bytes()).decode()
    assert "var collectionShortName = 'ZoggopoulosF'"in html
    assert "'/onlyFacetPanel?language=' + lang"in html and "var lang = 'en'"in html
    url=z.BASE+'/aggregator/portal/collections/ZoggopoulosF/onlyFacetPanel?language=en'
    soup,receipt=q.q.capture('facet-controls-001',url)
    data=dict(at=m.now(),receipt=receipt,observed_ui_script_reference=q.s.ref(OLD/'captures/collection-profile-001.json'),
        text=q.clean(soup.get_text(' ',strip=True)),
        inputs=[dict(tag=e.name,attributes=e.attrs,label=q.clean(e.parent.get_text(' ',strip=True)))for e in soup.select('input,select')],
        links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(url,a['href']),attributes=a.attrs)for a in soup.select('a[href]')],
        script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Public UI-observed GET facet endpoint. No guessed internal route, collection-wide download or DB access. Production token refresh still failed at this wave start, terminal exit1; public research remains possible.')
    m.save(RUN/'facet-discovery-001.json.gz',data)
    print(json.dumps(dict(text=data['text'][:9000],inputs=data['inputs'][:25]),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
