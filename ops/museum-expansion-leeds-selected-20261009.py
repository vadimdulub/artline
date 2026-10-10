"""Selected independent creator authorities and two museum-authored discovery stories."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-leeds-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
n.n.SITES['wikidata']='https://www.wikidata.org'
def main():
 url='https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q5545665%7CQ18954423%7CQ6515835&format=json';raw,c=n.n.capture('wikidata',url);x=json.loads(raw);m.save(RUN/'selected-authorities-001.json.gz',dict(at=m.now(),entities=x['entities'],capture=c,script_reference=ref(Path(__file__).resolve())))
 rows=[]
 for url in ['https://artsandculture.google.com/story/6wWBMGiTbKgAqA','https://artsandculture.google.com/story/LgXBCI9xcqeCxA']:
  raw,c=n.n.capture('gac',url);p=n.parsed(raw);rows.append(dict(url=url,capture=c,parsed=p));print(json.dumps(dict(url=url,text=p['text'],assets=[v for v in p['links'] if '/asset/' in v['href']])),flush=True)
 m.save(RUN/'selected-discovery-stories-001.json.gz',dict(at=m.now(),rows=rows,script_reference=ref(Path(__file__).resolve()),policy='Discovery only; featured loans and post1970 objects excluded until exact object ownership,creation and version review. No image bytes.'))
if __name__=='__main__':main()
