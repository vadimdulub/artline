"""Selected creator/museum authorities and one portrait-pendant identity; metadata only."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;n.HOSTS['wikidata']={'www.wikidata.org'}
def main():
 ids=['Q7205781','Q8055361','Q12059583','Q8006450','Q7308581','Q21465567','Q4800678','Q20018580','Q119025474'];url='https://www.wikidata.org/w/api.php?action=wbgetentities&ids='+'%7C'.join(ids)+'&format=json';raw,c=n.capture('wikidata',url);data=json.loads(raw);assert set(data['entities'])==set(ids);m.save(RUN/'selected-authorities-001.json.gz',dict(at=m.now(),entities=data['entities'],capture=c,script_reference=n.ref(Path(__file__).resolve()),policy='Nine selected authorities/related object only. Secondary-source identities,not native holding confirmation or date enrichment.'))
 print(json.dumps({k:dict(label=v.get('labels',{}).get('en',{}).get('value'),description=v.get('descriptions',{}).get('en',{}).get('value')) for k,v in data['entities'].items()}),flush=True)
if __name__=='__main__':main()
