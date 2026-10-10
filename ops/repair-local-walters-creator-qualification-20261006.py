#!/usr/bin/env python3
"""Retain native question-mark creator qualifiers in existing image evidence."""
import argparse,copy,importlib.util,json,re,uuid
from pathlib import Path

s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('recover-local-walters-native-images-20261006.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);core=w.core
RUN=core.ROOT/'docs/research/local-walters-creator-qualification-20261006'
OPERATIONS=['local-walters-native-images-20261006','local-walters-followup-images-20261006','local-walters-later-images-20261006','local-walters-midcentury-images-20261006']

def apply():
 if (RUN/'apply-receipt.json').exists():raise ValueError('Correction already applied; run verify')
 changes=[]
 for name in OPERATIONS:
  run=RUN.parent/name;w.RUN=run;w.base.RUN=run
  approved={x['artwork_id'] for x in json.loads((run/'apply-receipt.json').read_bytes())['receipts'] if x['result']=='attached'}
  for im in w.base.prepared():
   if im['artwork_id'] not in approved or not re.search(r'\(\s*\?\s*\)',im['raw']['native_facts']['author']):continue
   new=copy.deepcopy(im);new['raw']['native_facts']=w.facts(new,core.ROOT/new['raw']['native_capture']['path'])
   if w.QUALIFICATION_NOTICE not in new['attribution_text']:new['attribution_text']+=' '+w.QUALIFICATION_NOTICE
   w.verify_image(new)
   selected=run/'selected'/w.PROVIDER/(im['artwork_id']+'.json');old_selected=json.loads(selected.read_bytes());new_selected=copy.deepcopy(old_selected)
   new_selected['raw']['native_facts']=new['raw']['native_facts'];new_selected['attribution_text']=new['attribution_text'];w.verify_image(new_selected)
   changes.append(dict(operation=name,old=im,new=new,old_selected=old_selected,new_selected=new_selected))
 if len(changes)!=7:raise ValueError('Expected seven already attached question-mark creator lines')
 backup=w.base.ARCHIVE/'backups'/RUN.name/str(uuid.uuid4());core.save_new(backup/'changes.json',changes)
 locked=[]
 with w.base.connect(False) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute('SELECT pg_advisory_xact_lock(610052026)')
  for change in sorted(changes,key=lambda x:x['old']['artwork_id']):
   old=change['old'];row=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence
    FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id
    WHERE a.id=%s AND m.id=%s FOR UPDATE OF a,m,e''',(old['artwork_id'],old['media_id'])).fetchone()
   if not row or row['media']['attribution_text']!=old['attribution_text'] or row['evidence']['evidence_json']!={k:v for k,v in old.items() if k not in ('artist','title')}:raise ValueError('Existing media evidence changed')
   if row['media']['checksum_sha256']!=old['sha256'] or core.sha((core.ROOT/'apps/web/public'/old['path'].lstrip('/')).read_bytes())!=old['sha256']:raise ValueError('Image bytes changed')
   locked.append(row)
  core.save_new(backup/'locked-before.json',locked)
  for change in changes:
   im=change['new']
   db.execute('UPDATE media_assets SET attribution_text=%s,updated_at=now() WHERE id=%s',(im['attribution_text'],im['media_id']))
   db.execute('''UPDATE media_rights_evidence SET evidence_json=%s,source_checksum=%s,rights_basis=%s,checked_at=now() WHERE media_id=%s''',
    (w.base.Jsonb({k:v for k,v in im.items() if k not in ('artist','title')}),core.sha(core.encode(im['raw'])),"Exact museum object, inventory and photograph-specific CC0 grant. The native creator line contains '(?)'; that qualifier is retained in the image attribution and evidence. Catalogue creator links and review status are unchanged.",im['media_id']))
 for change in changes:
  run=RUN.parent/change['operation'];aid=change['old']['artwork_id']
  for relative,value in [(Path('images')/(aid+'.json'),change['new']),(Path('selected')/w.PROVIDER/(aid+'.json'),change['new_selected'])]:
   path=run/relative;core.save_new(run/'history'/'before-creator-qualification'/relative,path.read_bytes());path.write_bytes(core.encode(value))
 core.save_new(RUN/'apply-receipt.json',dict(at=core.now(),local_only=True,media_records_updated=len(changes),artwork_records_updated=0,image_bytes_changed=False,backup=str(backup),artwork_ids=[x['old']['artwork_id'] for x in changes]))
 print('Retained creator question-mark qualifications on',len(changes),'existing images; no artwork or image-byte changes',flush=True)

def verify():
 receipt=json.loads((RUN/'apply-receipt.json').read_bytes());backup=Path(receipt['backup']);changes=json.loads((backup/'changes.json').read_bytes())
 locked={r['artwork']['id']:r for r in json.loads((backup/'locked-before.json').read_bytes())};checks=[]
 with w.base.connect() as db:
  for change in changes:
   im=change['new'];w.RUN=RUN.parent/change['operation'];w.base.RUN=w.RUN;w.verify_image(im)
   actual=json.loads((w.RUN/'images'/(im['artwork_id']+'.json')).read_bytes())
   if actual!=im:raise ValueError('Prepared evidence differs from corrected evidence')
   row=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence
    FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=%s''',(im['artwork_id'],)).fetchone()
   if row['artwork']!=locked[im['artwork_id']]['artwork']:raise ValueError('Artwork changed during qualification correction')
   if row['media']['attribution_text']!=im['attribution_text'] or row['evidence']['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Corrected database evidence differs')
   if row['evidence']['source_checksum']!=core.sha(core.encode(im['raw'])):raise ValueError('Corrected source checksum differs')
   if row['media']['rights_status']!='cc0' or core.sha((core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes())!=im['sha256']:raise ValueError('Licence or image bytes changed')
   checks.append(dict(artwork_id=im['artwork_id'],inventory=im['accession_number'],native_author=im['raw']['native_facts']['author'],artwork_unchanged=True,image_bytes_unchanged=True))
 core.save_new(RUN/'verification.json',dict(at=core.now(),passed=True,verified=len(checks),checks=checks));print('Verified corrected qualification evidence and unchanged artworks:',len(checks),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['apply','verify']);a=p.parse_args()
 apply() if a.phase=='apply' else verify()
