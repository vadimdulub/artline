import importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000291.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');fix={};review=[]
for fields,a in zip(b.CREATORS,b.new_artists()):
 rc=h.load(b.E/(fields[0]+'-capture.json'));raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
 text=BeautifulSoup(raw,'html.parser').select_one('main').get_text(' ',strip=True)
 assert str(a['death_year']) in text and (a['birth_year'] is None or str(a['birth_year']) in text)
 review.append(dict(artist=a,source=rc,source_text=text,decision='Official museum creator authority; complete global names/aliases and transliteration/lifetime candidates reviewed. No corresponding painter. Brounzos birth remains unknown and death circa1920. Selected work dates establish bounded activity only, not entire career.'))
 for r in rs:
  if r['raw']['creator_url']==rc['url']:fix['athens/'+r['source_id']]=dict(verified_artist_id=a['id'])
existing={'actress':'ba49f985-a313-52d1-873b-9802b666f388','flowers-4':'605fbe12-eebf-5183-887f-b4f7fdadb999','houses-2':'c3ca43f0-9e2f-547b-8f00-9c1fda658a80','liza-kottou':'ef2346a5-0fba-54f5-a3df-d0407aa148a6','the-uncle':'2a3ea04b-f281-541e-b18c-ef8916372247','female-dancers':'0b20ce09-67b9-5588-946e-7e9fa6029f0c'}
for r in rs:
 k='athens/'+r['source_id'];f=fix.setdefault(k,{})
 if 'Bouzianis' in r['creator_label']:f['verified_artist_id']='04b14091-e356-5935-88a9-161e6a1078dc'
 if r['source_id'] in existing:f['editorial_hold']='Existing illustrated George Bouzianis record '+existing[r['source_id']]+': matching title, creator, Athens holding, date and dimensions (legacy decimal loss on Flowers/Liza preserved). Excluded from new additions; no unrelated correction.'
 if r['source_id']=='chair-9073':f['editorial_hold']='Existing same-creator Chair 1b393cfe-dae5-5bfe-9a2c-c1816bf3b3c1 has unknown date/dimensions; same physical version requires composition reconciliation. No duplicate created.'
 if r['source_id']=='the-virgin-mary-with-infant-and-st-john-in-a-landscape':f['editorial_hold']='Source date late 1620 ambiguous between a year qualifier and late1620s; exact creation precision and JanII version review remain unresolved. No fabricated exact year.'
 if r['source_id']=='landscape-with-dancing-peasants':f.update(creator_link_hold=True,verified_artist_id=None,creator_identity_note='Source attributes work to an imitator of JanII Brueghel. No primary JanII link or invented anonymous painter; source date ca1600–1625 retained even though it needs attribution chronology research.')
 if r['source_id'] in ['seated-figure-2','reflection-of-a-dark-complexioned-girl']:f['source_type']='painting'
h.save(b.E/b.PHASE/'source-field-corrections.json.gz',fix)
b.save('creator-authority-decisions.json',dict(at=h.now(),new_creators=review,reused_creators=['04b14091-e356-5935-88a9-161e6a1078dc','8bc31704-810b-465b-907f-9a3e9dbbbd71'],qualified_creator_preserved=True,global_review='creator-authority-global-review.json',expanded_review='expanded-creator-global-reconciliation.json'))
d=h.load(b.E/'global-artwork-version-reconciliation.json');assert not d['global_accession_matches'] and not d['native_matches'] and not d['source_citation_matches']
b.save('artwork-version-decisions.json',dict(at=h.now(),existing_bouzianis=existing,held_chair='1b393cfe-dae5-5bfe-9a2c-c1816bf3b3c1',decision='Eight distinct selected museum inventories after global native URL/accession, exact title, linked and unlinked creator checks. Brounzos1874 nude and1877/1878 sacred paintings distinct from other-creator homonymous works. Brauner1945 Π.4083 portrait differs in title,77x56cm canvas and donation from existing1945 paintings. Bouzianis Π.3325/α is an individually catalogued watercolour/pencil sheet, not the full group; other source component suffixes not collapsed. Brueghel-imitator Π.192 is distinct from smallerJanII landscapes; maker qualification retained. Six existing illustrated works excluded, chair version and ambiguous late1620 held.',related_artworks_preserved=len(h.load(b.E/'other-identity-candidates-before.json.gz')['artworks']),not_current_display=True))
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==8 and len(p['held'])==8 and len(p['new_artists'])==3 and all(not x['before'] for x in p['records'])
print('Frozen',len(p['records']),'works,',len(p['new_artists']),'painters;',len(p['held']),'existing/held; plan',pin)
