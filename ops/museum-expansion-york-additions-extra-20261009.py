"""One selected primary comparator; no image downloads or provider retries."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-york-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN;n.HOSTS={'nga':{'www.nga.gov','nga.gov'}}
def main():
 dest=RUN/'comparison-native-extra-001.json.gz';assert not dest.exists();url='https://www.nga.gov/artworks/496-madonna-and-child';raw,cap=n.capture('nga',url);p=n.parsed(raw);assert '1939.1.352' in p['text'] and 'earth-brown background' in p['text'];m.save(dest,dict(at=m.now(),rows=[dict(url=url,capture=cap,parsed=p,comparison_number=25,basis='NGA496 has plain dark background; York800 has backcloth with landscape beyond. Near dimensions do not establish identity.')],script_reference=s.ref(Path(__file__).resolve()),policy='One selected existing-record identity comparison. No current-display claim or image request.'));print(json.dumps(dict(captured=1,bytes=cap['receipt']['bytes'])),flush=True)
if __name__=='__main__':main()
