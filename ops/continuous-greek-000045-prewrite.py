#!/usr/bin/env python3
import importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b45',Path(__file__).with_name('continuous-greek-batch-000045.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];sources=[]
with h.connect() as db:
 assert not h.snapshot(db,ids)
 for r in p['records']:
  rc=r['evidence'];raw=Path(rc['body_path']).read_bytes();assert rc['status']==200 and h.sha(raw)==rc['sha256'];sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();title=head.get_text(' ',strip=True).rstrip(',').strip();acc=sp.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip()
  assert (title,acc,date)==(r['title'],r['accession_number'],r['date_display']);assert r['first']<=r['last']<=1970
  assert r['creator_label']==sp.select_one('p.artist').get_text(' ',strip=True)
  image=sp.select_one('.img-magnifier-container img');assert (image.get('data-zoom-image') or image['src'])==r['raw']['image_url'];assert title in image['alt']
  desc=sp.select_one('p.description').get_text(' ',strip=True)
  if desc=='Woodcut':assert r['medium']=='Woodcut' and r['dimensions'] is None and h.worktype(r)=='print'
  else:assert desc==r['medium']+', '+r['dimensions']
  urls=[r['source_url'],r['source_url'].replace('/en/artwork/','/artwork/')]
  found=db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall();assert not found
  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,acc)).fetchall()
  titles=db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=%s LIMIT 30',(h.norm(title),)).fetchall()
  sources.append(dict(artwork_id=r['artwork_id'],title=title,inventory=acc,source_sha256=rc['sha256'],source_url=rc['url'],source_date=date,creator_label=r['creator_label'],dimensions=r['dimensions'],work_type=h.worktype(r),global_title_candidates=titles,identity_basis='Exact unique museum inventory and native URL absent; generic same-title objects elsewhere do not establish same physical object; support, dimensions and supplied copy wording preserved'))
b.save('independent-prewrite-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,records=sources,new_artwork_preimages={},production_target=b.target(),local_catalogue_connections=0))
b.save('superseded-plans.json',dict(at=h.now(),never_applied=['greek-objects','greek-objects-v2'],active_phase=b.PHASE,active_pin=pin,corrections=['Woodcut without dimensions is medium, not dimensions','Source-explicit watercolour and woodcut classified as watercolor and print'],no_production_writes_from_superseded_plans=True))
print('Verified prewrite',len(sources),pin)
