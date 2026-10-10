"""Inspect the current public Salford collection interface from its observed museum link."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-seven-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN
def main():
 dest=RUN/'salford-catalogue-probe-001.json';assert not dest.exists();index=m.load(RUN/'native-probes-001.json');page=next(v for v in index['rows'] if v['url']=='https://salfordmuseum.com/explore/collection/');links=[v['href'] for v in page['parsed']['links'] if v['text']=='View online collection'];assert len(set(links))==1;url=links[0];p.n.SITES['salford_catalogue']='https://collections.salfordmuseum.com';row=dict(at=m.now(),url=url,discovery_reference=p.ref(RUN/'native-probes-001.json'))
 try:
  raw,cap=p.n.capture('salford_catalogue',url);data=p.parsed(raw);row.update(state='captured_interface',capture=cap,parsed=data)
 except Exception as e:row.update(state='source_error',error=type(e).__name__+': '+str(e))
 m.save(dest,row);print(json.dumps(dict(state=row['state'],error=row.get('error'),parsed=row.get('parsed'))),flush=True)
if __name__=='__main__':main()
