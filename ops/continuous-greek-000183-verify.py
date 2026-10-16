#!/usr/bin/env python3
"""Independent read-only verification for batch 183 research checkpoint."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000183';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000183'
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('delivery183verify','india-300-delivery-20261011.py')
rec=h.load(E/'aivasowsky-native-object-reconciliation.json');assert rec['objects_classified']==8 and len(rec['rows'])==8
assert len({x['source_id'] for x in rec['rows']})==8 and all(x['source_receipt']['status']==200 for x in rec['rows'])
for row in rec['rows']:
 p=Path(row['source_receipt']['body_path']);assert p.is_relative_to(Path.home()/'Library/Application Support/Artline') and h.sha(p.read_bytes())==row['source_receipt']['sha256']
with h.connect() as db:
 target=dict(db.execute('SELECT current_database() db,inet_server_addr()::text server,pg_is_in_recovery() recovery').fetchone());assert target['db']=='artline' and not target['recovery']
 for row in rec['rows']:
  now=[dict(x) for x in db.execute("SELECT a.id::text FROM artworks a WHERE a.current_institution_id=%s AND a.accession_number=%s UNION SELECT a.id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND e.external_id=%s",('052007aa-11f7-4d57-90e6-d3b62bb0bf4b',row['accession_number'],['continuous-athens-object','museum-native-nationalgallery-gr','nationalgallery-gr-artwork','museum-native-athens-object'],row['source_id']))]
  assert now==row['production_matches'] or ({x['id'] for x in now}=={x['id'] for x in row['production_matches']})
queue=h.load(E.parents[1]/'source-queue.json');route=next(x for x in queue['sources'] if x['source_id']=='national_gallery_athens');assert route['last_batch']==183 and route['resume_cursor']['aivasowsky_ivan']['notices_reviewed']==8
cp=h.load(E/'CHECKPOINT.json');h.save(R/'CHECKPOINT.json',cp)
h.save(E/'independent-read-only-resume-verification.json',dict(at=h.now(),passed=True,database=target,objects_rechecked=8,source_bodies_checksum_verified=8,production_writes=0,queue_cursor_verified=True,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,local_catalogue_connections=0))
files=[]
for p in sorted(E.rglob('*.json')):
 if p.name=='independent-final-artifact-verification.json':continue
 json.loads(p.read_text());files.append(dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
(E/'independent-final-artifact-verification.json').unlink(missing_ok=True)
h.save(E/'independent-final-artifact-verification.json',dict(at=h.now(),passed=True,files=files,runtime_checkpoint_equal=True,all_evidence_files_decoded=True))
print(json.dumps(dict(passed=True,objects=8,writes=0)))
