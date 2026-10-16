#!/usr/bin/env python3
"""One reviewed WikiArt translation duplicate; retain source IDs and history."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('million-wikiart-images-20261011.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m
RUN=m.RUN/'wikiart/antoniazzo-reconciliation';OLD='d9960c05-d85c-51c9-abe3-9b802cea2d4f';CANON='4c060840-f8ec-538b-ad36-11e056630016';IDS=[OLD,CANON]
def plan():
 path=RUN/'plan.json.gz'
 if path.exists():return m.load(path)
 prepared={aid:m.load(m.RUN/'wikiart/images-001/prepared'/(aid+'.json')) for aid in IDS}
 assert prepared[OLD]['sha256']==prepared[CANON]['sha256']
 assert prepared[OLD]['page']['date']==prepared[CANON]['page']['date']
 assert prepared[OLD]['page']['artist_url']==prepared[CANON]['page']['artist_url']
 with w.r.connect() as db:
  before=w.d.snapshots(db,IDS)
  ext=[r['v'] for r in db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(IDS,))]
 for aid in IDS:
  a=before[aid]['artwork'];assert a['status']=='review' and a['primary_media_id'] is None and a['current_institution_id'] is None
  assert (a['creation_year_start'],a['creation_year_end'])==(1495,1500)
  assert not before[aid]['attachments'];assert len(before[aid]['creators'])==1 and before[aid]['creators'][0]['attribution_role']=='primary'
 assert before[OLD]['creators'][0]['artist_id']==before[CANON]['creators'][0]['artist_id']
 out=dict(at=m.now(),before=before,identifiers=ext,prepared=prepared,canonical_id=CANON,archived_duplicate_id=OLD,
  visual_review='Both source pages reproduce the identical complete Madonna and Child holding a bird, including identical crack patterns, ornament, hands, faces and source frame. Derivative byte hashes match. English and Spanish titles translate the same subject; both pages give 1495–1500 and the same creator profile. No distinct physical version is evidenced.',
  method='Keep the English-title record and its native WikiArt ID. Archive the duplicate Spanish-title row with a redirect and reconciliation citation. Its separate native ID remains on the archived history because the database permits one identifier per scheme per entity; future source imports still recognize that ID. Preserve all dates, creator links, source citations and unknown holdings.')
 m.save(path,out);m.save(RUN/'pin.json',dict(sha256=m.sha(path.read_bytes())));m.save(m.BACKUP/'wikiart/antoniazzo-reconciliation/before.json.gz',out);return out
def apply():
 if (RUN/'applied.json').exists():return
 p=plan();pin=m.load(RUN/'pin.json')['sha256'];assert pin==m.sha((RUN/'plan.json.gz').read_bytes())
 with w.r.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(IDS,)).fetchall()
  before=w.d.snapshots(db,IDS);citation=m.uid('wikiart-translation-reconciliation/'+OLD)
  if db.execute('SELECT 1 FROM citations WHERE id=%s',(citation,)).fetchone():assert before[OLD]['artwork']['status']=='archived'
  else:
   assert before==p['before'],'Record changed since visual reconciliation';source=next(e for e in p['identifiers'] if e['entity_id']==OLD and e['scheme']=='wikiart-artwork')
   w.n.copy_rows(db,'citations',[dict(id=citation,entity_type='artwork',entity_id=CANON,field_name='million_catalogue_identity_reconciliation',source_id=source['source_id'],source_record_id=source['external_id'],source_url=source['canonical_url'],evidence_note=json.dumps(dict(plan_sha256=pin,review=p),ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
   w.n.copy_rows(db,'slug_redirects',[dict(id=m.uid('wikiart-translation-redirect/'+OLD),entity_type='artwork',entity_id=CANON,old_slug=before[OLD]['artwork']['slug'])])
   db.execute("UPDATE artworks SET status='archived',updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s",(m.ACTOR,OLD));after=w.d.snapshots(db,IDS)
   assert after[CANON]==before[CANON];assert after[OLD]['creators']==before[OLD]['creators'];db.commit()
 m.save(RUN/'applied.json',dict(at=m.now(),canonical_id=CANON,archived_duplicate_id=OLD,plan_sha256=pin,native_identifiers_retained=True));print('Consolidated one confirmed WikiArt translation duplicate',flush=True)
def verify():
 p=plan()
 with w.r.connect() as db:
  after=w.d.snapshots(db,IDS);assert after[OLD]['artwork']['status']=='archived';assert after[CANON]==p['before'][CANON]
  assert all(after[OLD]['artwork'][k]==v for k,v in p['before'][OLD]['artwork'].items() if k not in {'status','updated_by','updated_at','revision'})
  assert after[OLD]['creators']==p['before'][OLD]['creators'] and after[OLD]['attachments']==p['before'][OLD]['attachments']
  ext=[r['v'] for r in db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(IDS,))];assert ext==p['identifiers']
  assert db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND old_slug=%s AND entity_id=%s",(p['before'][OLD]['artwork']['slug'],CANON)).fetchone()
  assert db.execute('SELECT count(*) n FROM artwork_search_documents s JOIN artworks a USING(id) WHERE a.id=ANY(%s::uuid[]) AND s.status=a.status AND s.title=a.title',(IDS,)).fetchone()['n']==2
 with w.r.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts'];m.save(RUN/'verification.json',dict(at=m.now(),archived_duplicates=1,canonical_metadata_preserved=True,identifiers_preserved=True,local_baseline_equal=True));print('Verified reconciliation, source identities, redirect and search documents',flush=True)
def image_selection():
 assert (RUN/'verification.json').exists();phase=m.RUN/'wikiart/images-005';rows=m.load(m.RUN/'wikiart/images-001/selection.json.gz')['rows'];row=next(r for r in rows if r['artwork_id']==CANON)
 with w.r.connect() as db:before=w.d.snapshots(db,[CANON])
 assert before[CANON]['artwork']['primary_media_id'] is None;row['artwork']=before[CANON]['artwork'];im=m.load(m.RUN/'wikiart/images-001/prepared'/(CANON+'.json'))
 m.save(phase/'selection.json.gz',dict(at=m.now(),rows=[row],local_baseline=m.load(m.RUN/'baseline.json.gz')['local_readonly_counts'],selection_basis='Single canonical Antoniazzo Romano record after individually verified translation-duplicate reconciliation.'))
 m.save(phase/'pin.json',dict(sha256=m.sha((phase/'selection.json.gz').read_bytes())));m.save(m.BACKUP/'wikiart/images-005/selection-preimages.json.gz',before);m.save(phase/'prepared'/(CANON+'.json'),im)
 m.save(phase/'authorization.json',dict(at=m.now(),user_instruction="nice, add more images use wikiart and don't think about rights!",source_approval='Approved WikiArt source; actual source labels retained.',production_images_authorized=True,local_readonly=True))
 m.save(phase/'visual-review.json',{CANON:dict(at=m.now(),decision='accept',sha256=im['sha256'],visual_review=plan()['visual_review'],duplicate_resolution=str((RUN/'verification.json').relative_to(m.RUN)))})
 print('Prepared one canonical WikiArt image for delivery',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['plan','apply','verify','image_selection']);a=ap.parse_args();globals()[a.action]()
