"""Capture official collection history, retaining source dates and scope limits."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-guildhall-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
def main():
 dest=n.RUN/'collection-history-001.json';assert not dest.exists();u='https://www.cityoflondon.gov.uk/things-to-do/attractions-museums-entertainment/guildhall-art-gallery/collections/collections-history';raw,cap=n.g.p.n.capture('guildhall',u);p=n.g.p.parsed(raw);n.m.save(dest,dict(at=n.m.now(),url=u,capture=cap,parsed=p,discovered_by='web search turn956search4',policy='Official collection history,updated2022. Explicit acquisition and version statements can corroborate selected works. No inference of current display from historical prose.'));print(json.dumps(dict(status=cap['receipt']['status'],bytes=cap['receipt']['bytes'])),flush=True)
if __name__=='__main__':main()
