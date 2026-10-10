import importlib.util,json
from pathlib import Path
p=Path.cwd()/'ops/museum-expansion-britain-seven-native-20261009.py';z=importlib.util.spec_from_file_location('n',p);n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
u='https://www.cityoflondon.gov.uk/things-to-do/attractions-museums-entertainment/keats-house/letters-fanny-keats-and-fanny-brawne/the-journey-of-the-letters'
dest=n.RUN/'keats-institution-context-001.json';assert not dest.exists();raw,c=n.n.capture('guildhall',u);n.m.save(dest,dict(at=n.m.now(),url=u,capture=c,parsed=n.parsed(raw),discovered_by='web search turn955search0',policy='Official Keats House source names Fanny portrait,1880,date and Keats House accession K/PZ/05/019. Old KH-prefixed Guildhall-labelled candidates require collection versus branch mapping,not an automatic Guildhall holding. Other KH objects not individually corroborated.'))
print(json.dumps({'saved':str(dest),'status':c['receipt']['status']}))
