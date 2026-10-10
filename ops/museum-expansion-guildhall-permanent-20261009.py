"""Capture the official galleries page linked by retained collection history."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-guildhall-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
def main():
 dest=n.RUN/'permanent-galleries-001.json';assert not dest.exists();h=n.m.load(n.RUN/'collection-history-001.json');u=next(v['href'] for v in h['parsed']['links'] if v['text']=='Permanent Galleries page');raw,cap=n.g.p.n.capture('guildhall',u);n.m.save(dest,dict(at=n.m.now(),url=u,capture=cap,parsed=n.g.p.parsed(raw),discovery_reference=n.ref(n.RUN/'collection-history-001.json'),policy='Supplemental primary collection context. Explicit creation years only; no current-display inference from undated prose.'))
 print(json.dumps(dict(status=cap['receipt']['status'],bytes=cap['receipt']['bytes'])),flush=True)
if __name__=='__main__':main()
