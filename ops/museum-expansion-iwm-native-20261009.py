"""Bounded independent-source metadata capture; IWM provider is on access hold."""
import hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-native-20261006.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=m.RUN/'native/iwm-holdings-20261009';n.RUN=RUN;n.SITES={'wikidata':'https://www.wikidata.org'}
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def parsed(raw):
 s=n.BeautifulSoup(raw,'html.parser');return dict(text=s.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in s.select('a[href]')])
def main():
 dest=RUN/'institution-authorities-001.json.gz';assert not dest.exists();url='https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q749808%7CQ23315190&format=json';raw,c=n.capture('wikidata',url);x=json.loads(raw);assert set(x['entities'])=={'Q749808','Q23315190'};m.save(dest,dict(at=m.now(),entities=x['entities'],capture=c,script_reference=ref(Path(__file__).resolve()),policy='Independent institution authorities only; not artwork holdings evidence. No IWM requests after403.'))
 for q,e in x['entities'].items():print(json.dumps(dict(qid=q,label=e.get('labels',{}).get('en'),description=e.get('descriptions',{}).get('en'),statements={p:e['claims'].get(p) for p in ['P31','P361','P527','P749','P856','P571']})),flush=True)
if __name__=='__main__':main()
