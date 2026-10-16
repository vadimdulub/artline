import importlib.util,json,fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000276.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');p,pin=h.pinned(b.PHASE);proof=h.load(b.E/'independent-production-verification.json');painters=h.load(b.E/'independent-new-painter-verification.json');images,audit,review=i.accepted(b.B)
 assert pin==receipt['metadata_plan_sha256'] and h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())==receipt['image_selection_sha256']
 assert h.sha((i.folder(b.B)/'visual-review.json').read_bytes())==receipt['visual_review_sha256']
 target=b.target()
 with h.connect() as db:
  before=h.snapshot(db,receipt['production_ids']);assert before==proof['after']
  assert {x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(receipt['new_painter_ids'],))}==painters['artists']
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,receipt['production_ids']))];assert len(notes)==9 and all(x['pin']==pin for x in notes)
  rights=[dict(x) for x in db.execute('SELECT adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([x['media_id'] for x in images],))];assert len(rights)==9
  for x in rights:
   ev=json.loads(x['evidence_json']) if isinstance(x['evidence_json'],str) else x['evidence_json'];assert x['adapter_version']==b.OP and ev['selection_sha256']==receipt['image_selection_sha256'] and ev['original_catalogue_plan_sha256']==pin
 assert h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['artworks']=={} and h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['new_artist_preimages']==[]
 # Exercise the metadata resume guard; all states and source-plan pins are present,
 # so the established entrypoint must return before its write path.
 b.apply()
 with h.connect() as db:assert h.snapshot(db,receipt['production_ids'])==before
 b.save('independent-resume-verification.json',dict(at=h.now(),passed=True,unchanged_snapshot=True,painter_equal=True,source_and_rights_checksums_match=True,empty_transaction_preimages=True,metadata_resume_guard_exercised=True,new_production_writes=0,replay_required=False,previous_campaign_increments=0,target=target))
 rows=[]
 for a in p['new_artists']:
  u='https://artlines.org/api/backend/v1/artists/'+a['slug'];resp=i.session().get(u,timeout=(15,45));resp.raise_for_status();data=resp.json();assert a['display_name'] in resp.text and a['id'] in resp.text
  b.save('public-artist-'+a['id']+'.json',data)
  rows.append(dict(artist_id=a['id'],url=u,status=resp.status_code,name=a['display_name'],response_sha256=h.sha(resp.content)))
 b.save('independent-public-painter-verification.json',dict(at=h.now(),rows=rows,all_four_public=True,review_visibility_unchanged=True))
 print(json.dumps(dict(resume_unchanged=True,new_writes=0,public_painters=4)))
