import importlib.util,re,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000276.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz')
with h.connect() as db:
 names=[dict(x) for x in db.execute('SELECT id::text,display_name name,birth_year,death_year FROM artists UNION SELECT a.id::text,al.alias,a.birth_year,a.death_year FROM artist_aliases al JOIN artists a ON a.id=al.artist_id')]
 terms=['argyr','argir','arghir','aravad','aravant','aravant','arabant','amicon','amikon','anagnost','vranik','αργυρ','αραβ','αμικ','αναγνωστ','βρανικ','d ambrosio','dambrosio']
 candidates=[x for x in names if any(t in h.norm(x['name']) for t in terms)]
 coincident=[x for x in names if (x['birth_year'],x['death_year']) in [(1825,1880),(1902,1971),(1886,1930),(1884,1963)]]
 native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND canonical_url=ANY(%s)",(list({r['raw']['creator_url'] for r in rs}),))]
 b.save('creator-authority-global-review.json',dict(at=h.now(),names_aliases_checked=len(names),terms=terms,candidates=candidates,coincident_lifetimes=coincident,native_url_matches=native))
 print(json.dumps(dict(candidates=candidates,coincident=coincident,native=native),ensure_ascii=False))
