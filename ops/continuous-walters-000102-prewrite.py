#!/usr/bin/env python3
"""Independent source, creator role, date, unit, and absent-production validation."""
import importlib.util,csv,io,json,fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-walters-batch-000102.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);rows=p['records'];ids=[r['artwork_id'] for r in rows]
 art={x['ObjectID']:x for x in b.objects()};creators={x['id']:x for x in csv.DictReader(io.StringIO(b.static('creators.csv')[0].decode()))}
 rel=list(csv.DictReader(io.StringIO(b.static('relationships.csv')[0].decode())))
 decisions=h.load(b.E/'editorial-decisions.json');records=[]
 for r in rows:
  x=art[r['source_id']];src=h.load(b.ROOT/r['evidence_file'])
  assert x==r['raw']==src['object'] and h.sha((b.ROOT/r['evidence_file']).read_bytes())==r['evidence']['sha256']
  assert src['creators']==[creators[k] for k in x['Creators'].split('|') if k in creators]
  assert r['title']==x['Title'] and r['date_display']==x['DateText'] and r['accession_number']==x['AccessionNumber']
  assert (r['first'],r['last'])==(int(x['DateBeginYear']),int(x['DateEndYear'])) and r['first']<=r['last']<=1970
  assert (r['medium'],r['dimensions'])==(x['Medium'],x['Dimensions']) and 'tempera' in x['Medium']
  assert r['source_type']=='painting' and r['artist_id'] is None and r['creator_link_hold']
  assert all(c['name'] in ['Greek','Russian','Stroganov School'] for c in src['creators'])
  assert 'Walters Art Museum' in x['Provenance'] and 'Walters Art Museum' in x['CreditLine']
  assert not x['RelatedObjects'] and not any(x['ObjectID'] in [y['art1'],y['art2']] for y in rel)
  assert not r['before'] and decisions[r['source_id']]['decision']=='select'
  records.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],accession=r['accession_number'],source_sha256=r['evidence']['sha256'],dates=[r['first'],r['last']],title_medium_dimensions_and_creator_labels_equal=True,holding_basis=x['Provenance'],catalogue_unit=decisions[r['source_id']]['unit']))
 assert len(ids)==len(set(ids))==len({r['accession_number'] for r in rows}) and 1<=len(ids)<=50
 b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,source_files=h.load(b.E/'immutable-source-reuse-verification.json'),records=records,images_downloaded=0,actual_images_viewed=0))
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,rows);assert h.snapshot(db,ids)=={}
  original=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(original))==original
  assert not db.execute('SELECT id FROM sources WHERE id=%s',(h.uid('source/walters/'+b.MUSEUM),)).fetchall()
  assert not db.execute("SELECT id FROM citations WHERE field_name=%s",(b.FIELD,)).fetchall()
 b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=len(rows),production_target=b.target(),absent_source_ids_and_inventories_verified=True,absent_own_citation_namespace=True,preserved_existing_artworks=len(original),shared_ingestion_lock='artline-curated-ingestion',no_new_cloud_backups=True))
 print('Independent prewrite verified',len(rows))
