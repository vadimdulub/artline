import importlib.util,re,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000282.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');assert len(rs)==19
fix={};review=[]
for fields,a in zip(b.CREATORS,b.new_artists()):
 rc=h.load(b.E/(fields[0]+'-capture.json'));raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
 text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert str(a['birth_year']) in text and str(a['death_year']) in text
 review.append(dict(artist=a,source=rc,decision='Official museum authority name and life dates; global all-artist names and aliases, transliteration variants and coincident lifetimes reviewed. No matching painter exists. Source URLs and original labels retained; activity only from selected object dates.'))
 for r in rs:
  if r['raw']['creator_url']==rc['url']:fix[r['key'] if 'key' in r else 'athens/'+r['source_id']]=dict(verified_artist_id=a['id'])
for r in rs:
 k='athens/'+r['source_id'];fix.setdefault(k,{})
 if 'Koutlidis' in r['credit']:fix[k]['editorial_hold']='Koutlidis Foundation collection credit; holding/custody identity needs separate reconciliation. Not equated to National Gallery ownership.'
 if '?' in r['date_display']:fix[k]['editorial_hold']='Questioned ca.1955 date requires individual editorial review; no firm structured date or image eligibility assumed.'
 if r['source_id']=='portrait-of-a-lady-15':fix[k]['verified_artist_id']='ccd92ccd-af63-4cd3-affd-294e30823eb3'
 if r['source_id']=='portrait-of-elia-demidof':fix[k]['verified_artist_id']='60f33266-c69a-4596-9aa8-2527f81220b0'
h.save(b.E/b.PHASE/'source-field-corrections.json.gz',fix)
b.save('creator-authority-decisions.json',dict(at=h.now(),new_creators=review,reused_creators=[dict(source='Bashkirtseff Maria',artist_id='ccd92ccd-af63-4cd3-affd-294e30823eb3',basis='Existing Maria/Marie Bashkirtseff transliteration aliases and identical1858–1884 life dates'),dict(source='Benjamin Constant',artist_id='60f33266-c69a-4596-9aa8-2527f81220b0',basis='Existing Jean Joseph Benjamin Constant; identical1845–1902 dates and exact surname/forename')],global_review='creator-authority-global-review.json',expanded_review='expanded-creator-global-reconciliation.json'))
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 prior=h.load(b.E/'global-artwork-version-reconciliation.json');assert not prior['global_accession_matches']
 ids=list({r['id'] for r in prior['linked_creator_works']}|{r['id'] for r in h.load(b.E/'unlinked-maker-global-reconciliation.json')['rows']})
 h.save(b.E/'other-identity-candidates-before.json.gz',dict(artworks=h.snapshot(db,ids)))
 b.save('artwork-version-decisions.json',dict(at=h.now(),existing_compared=len(ids),decision='No exact native URL or accession exists globally. Known-creator works inspected for titles, dates, dimensions and museum. All seven Asteriadis sheets/canvas have distinct inventories and compositions from earlier Hydra, Maroussi and Meteora. Berard1943 horizontal Etude at a different museum is not the1940 vertical Harmony. Foundation and questioned date cases held. Existing candidate records remain untouched.',not_current_display=True))
 h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==13 and len(p['held'])==6 and len(p['new_artists'])==3;print('FROZEN',len(p['records']),len(p['new_artists']),pin)
