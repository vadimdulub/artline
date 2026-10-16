import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000291.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with h.connect() as db:
 names=[dict(x) for x in db.execute('SELECT id::text,display_name name,birth_year,death_year,status FROM artists UNION SELECT a.id::text,al.alias,a.birth_year,a.death_year,a.status FROM artist_aliases al JOIN artists a ON a.id=al.artist_id')]
 terms=['voulg','bulg','vulg','βουλγ','brontz','brunts','broun','μπρου','buson','bussone','μπυσ','μπυσσ']
 matches=[x for x in names if any(t in h.norm(x['name']) for t in terms) or (x['birth_year'],x['death_year']) in [(1917,2000),(1822,1908)]]
 b.save('expanded-creator-global-reconciliation.json',dict(at=h.now(),terms=terms,all_names_and_aliases=len(names),matches=matches))
 d=h.load(b.E/'global-artwork-version-reconciliation.json');ids=[x['id'] for x in d['exact_normalized_titles']]
 rows=[dict(x) for x in db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,a.display_name,a.birth_year,a.death_year FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,))]
 b.save('global-title-creators.json',dict(at=h.now(),rows=rows))
 known=['actress','flowers-4','houses-2','liza-kottou','the-uncle','female-dancers']
 wids=[x['id'] for x in d['linked_creator_works'] if x['artist_id']=='04b14091-e356-5935-88a9-161e6a1078dc' and x['current_institution_id']==b.MID]
 cs=[dict(x) for x in db.execute("SELECT entity_id::text,source_url,field_name FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(wids,))]
 b.save('existing-bouzianis-source-identities.json',dict(at=h.now(),rows=cs))
 print('EXPANDED',json.dumps(matches,ensure_ascii=False));print('title creators',len(rows))
