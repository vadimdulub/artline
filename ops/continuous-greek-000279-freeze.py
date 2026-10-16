import importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000279.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');assert len(rs)==14
corrections={};reviews=[]
for fields,a in zip(b.CREATORS,b.new_artists()):
 rc=h.load(b.E/(fields[0]+'-capture.json'));raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200;sp=BeautifulSoup(raw,'html.parser');txt=sp.get_text(' ',strip=True);assert str(a['birth_year']) in txt and a['death_display'] in txt
 reviews.append(dict(source=rc,artist=a,decision='Create review painter from official museum authority and dated works; global names, aliases, original-language/transliteration variants, native URLs and coincident lifetimes reviewed. Coincident-life candidates have different names and are distinct people.'))
 for r in rs:
  if r['raw']['creator_url']==rc['url']:corrections[r['provider']+'/'+r['source_id']]=dict(verified_artist_id=a['id'])
for r in rs:
 k=r['provider']+'/'+r['source_id'];corrections.setdefault(k,{})
 if 'Koutlidis Foundation' in r['credit']:corrections[k]['editorial_hold']='Source credits E. Koutlidis Foundation Collection; separate collection/custody identity needs resolution before assigning National Gallery holding. No legal ownership or current-display inference.'
 if r['source_id'] in ['mandragora','meteora-3']:corrections[k].update(source_type='painting',source_field_review='Official paintings index and explicit pigment/tempera support establish pictorial painting; medium preserved verbatim.')
h.save(b.E/b.PHASE/'source-field-corrections.json.gz',corrections);b.save('creator-authority-decisions.json',dict(at=h.now(),creators=reviews))
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 aliases=[dict(x) for x in db.execute('SELECT id::text,display_name name FROM artists UNION SELECT a.id::text,al.alias FROM artist_aliases al JOIN artists a ON a.id=al.artist_id')]
 expanded=['asteri','arliot','arlyot','argyr','argir','arghir','lyber','liberop','liverop','асtер','астери','арлиот','либероп','аргир','αρλι','αστερι','αργυρ','λυμπερ','λιμπερ','λυβερ','λιβερ']
 extra=[x for x in aliases if any(t in h.norm(x['name']) for t in expanded)];print('EXPANDED',json.dumps(extra,ensure_ascii=False));assert {x['id'] for x in extra}<={'1484dfb5-083a-5494-bbfa-760b1360b850'}
 b.save('expanded-creator-global-reconciliation.json',dict(at=h.now(),terms=expanded,matches=extra,checked_names_aliases=len(aliases)))
 unlinked=h.load(b.E/'unlinked-maker-global-reconciliation.json')['rows'];assert len(unlinked)==20
 prior=h.snapshot(db,[x['id'] for x in unlinked]);h.save(b.E/'other-identity-candidates-before.json.gz',dict(artworks=prior))
 b.save('artwork-version-decisions.json',dict(at=h.now(),existing_unlinked_creator_objects=unlinked,decision='Asteriadis already occurs as object-level creator labels, not as a canonical painter. Preserve all20 existing objects and statuses. Existing Maroussi(Cypresses,Cloudy Landscape) is1958,54x73cm at a different collection; selected AthensΠ.4464 is1950,60x80cm, donated by Ministry. Other20 source subjects, dimensions or inventories distinguish these versions from selected Hydra1927 and Meteora1960. No global native/inventory/title collisions found; no other objects changed.',foundation_hold_count=3))
 h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==11 and len(p['new_artists'])==3 and len(p['held'])==3 and not p['new_institutions'];print('FROZEN',len(p['records']),len(p['new_artists']),pin)
