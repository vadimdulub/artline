import importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000276.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');assert len(rs)==9
corrections={};creator_reviews=[]
for fields,a in zip(b.CREATORS,b.new_artists()):
 key=fields[0];rc=h.load(b.E/(key+'-capture.json'));raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
 sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True);assert str(a['birth_year']) in text and a['death_display'] in text
 creator_reviews.append(dict(source=rc,artist=a,source_name=fields[2].replace(',',''),decision='Create source-backed review identity; all global name and alias variants, native URLs and coincident lifetimes reviewed. Jacopo Amiconi(1682–1752) and Caravaggio(1571–1610) are distinct, not matches. Shared lifetimes alone do not match the other differently named candidates.'))
 for r in rs:
  if r['raw']['creator_url']==rc['url']:corrections[r['provider']+'/'+r['source_id']]=dict(verified_artist_id=a['id'])
corrections['athens/portrait-of-nina-efkeidi-2356'].update(medium='Oil on pasteboard',dimensions=None,source_type='painting',source_field_review='No dimensions supplied; undivided description is medium, not dimensions. No value inferred.')
corrections['athens/dancing-hall-for-the-1st-act-of-the-opera-by-w-a-mozart-don-giovanni'].update(source_type='drawing',source_field_review='Crayon on paper is a drawing; preserve theatrical design title and inventory identity.')
h.save(b.E/b.PHASE/'source-field-corrections.json.gz',corrections)
b.save('creator-authority-decisions.json',dict(at=h.now(),creators=creator_reviews,unresolved_creator='Ambrosio Louis d’(19th century) retained as source label; no invented life dates or artist link'))
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 # Check global previously unlinked maker labels, including transliteration variants.
 workc=[dict(x) for x in db.execute("SELECT id::text,title,unlinked_creator_label,accession_number,current_institution_id::text,creation_year_start,creation_year_end,dimensions_text FROM artworks WHERE lower(unlinked_creator_label) ~ 'argyr|argir|aravad|aravant|anagnost|vranik|bernardo.?amiconi|amiconi.?bernardo|ambrosio.*louis|louis.*ambrosio' LIMIT 151")]
 b.save('unlinked-maker-global-reconciliation.json',dict(at=h.now(),rows=workc,limit=151));assert len(workc)<151
 print('UNLINKED',json.dumps(workc,ensure_ascii=False))
 assert len(workc)==5 and all(x['creation_year_end']<=1704 for x in workc)
 b.save('unlinked-maker-identity-decisions.json',dict(at=h.now(),rows=workc,decision='Christophes Argyrou1636 processional metal cross and Angelos Anagnostou1704 icons are distinct pre-birth makers and objects, with different first names, subjects, media, inventories and institutions. Not matches to four nineteenth/twentieth-century painter identities. Preserve unchanged.'))
 collisions=h.load(b.E/'additional-global-candidate-reconciliation.json')['artwork_candidates'];prior=h.snapshot(db,[x['id'] for x in collisions+workc]);h.save(b.E/'other-identity-candidates-before.json.gz',dict(artworks=prior))
 b.save('artwork-version-decisions.json',dict(at=h.now(),existing_same_title_candidates=collisions,decision='Nine distinct inventories absent globally. Eight same-museum self-portraits and Maleas Olive Trees have different maker, inventory and dimensions; preserved unchanged. Copenhagen Harbour remains held for separate same-creator version review. Holy Family explicitly after Giulio Romano is the1864 Louis d’Ambrosio copy, not the Renaissance original.'))
 h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==9 and len(p['new_artists'])==4 and not p['new_institutions'] and not p['held']
print('Frozen',len(p['records']),'artworks',len(p['new_artists']),'artists',pin)
