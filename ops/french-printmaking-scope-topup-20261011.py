#!/usr/bin/env python3
"""Two reviewed reserve prints supplement circa-1970 records kept in review."""
import collections,csv,importlib.util,io,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('french-printmaking-delivery-20261011.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;MAIN=d.RUN;INITIAL_BACKUP=d.BACKUP;TOPUP=MAIN/'scope-topup';TOPUP_BACKUP=INITIAL_BACKUP/'scope-topup'

def stage():
 original,pin=d.final_plan();verification=m.load(MAIN/'production-verification.json')
 assert verification['eligible_with_selection_evidence']==2998 and len(verification['creation_scope_review_ids'])==2
 existing={r['artwork_id'] for r in original['rows']};artists={r['artist_id'] for r in original['rows']};reserve=set(original['eligible_reserve'])
 candidates=[r for r in d.identity_rows() if r['artwork_id'] in reserve and r['artist_id'] in artists and r['artist_identity']['action']=='existing' and m.dates(r['date']['date_display'],1970)]
 candidates.sort(key=lambda r:(r['date']['creation_year_start'],int(r['native_id'])))
 rows=candidates[:2];assert len(rows)==2
 images={}
 approved=set()
 for p in (MAIN/'visual-decisions').glob('*.json'):approved.update(m.load(p)['approved'])
 for r in rows:
  aid=r['artwork_id'];assert aid not in existing and aid in approved and aid not in original['held']
  im=m.load(MAIN/'prepared-images'/(aid+'.json'));assert im['outcome']=='prepared' and m.sha(Path(im['local_path']).read_bytes())==im['sha256'] and im['bytes']<=100000
  assert m.sha((d.ROOT/r['source_record_reference']).read_bytes())==r['source_record_sha256']
  images[aid]=im
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  before=m.dbutil.snapshot(db,list(images));assert not before
  for r in rows:
   date=r['date'];assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(date['creation_year_start'],date['creation_year_end'],date['date_precision'])).fetchone()['scope']=='eligible'
 data=dict(at=m.now(),rows=rows,images=images,held={},image_gaps={},authorization_sha256=original['authorization_sha256'],baseline_sha256=original['baseline_sha256'],selection=original['selection']+' Two additional reviewed reserve objects supplement the two circa-1970 date-review records.',parent_plan_sha256=pin,position_offset=len(original['rows']),collection_expected_ids=sorted(existing|set(images)))
 m.save(TOPUP/'authorization.json',(MAIN/'authorization.json').read_bytes());m.save(TOPUP/'delivery-plan.json.gz',data)
 newpin=m.sha((TOPUP/'delivery-plan.json.gz').read_bytes());m.save(TOPUP/'delivery-plan-pin.json',dict(sha256=newpin))
 m.save(TOPUP_BACKUP/'cloud-backup.json',m.load(INITIAL_BACKUP/'cloud-backup.json'))
 m.save(TOPUP_BACKUP/'delivery-preimages.json.gz',dict(at=m.now(),plan_sha256=newpin,parent_plan_sha256=pin,artworks=before))
 print(json.dumps(dict(plan_sha256=newpin,artworks=[dict(id=r['artwork_id'],native_id=r['native_id'],title=r['title'],date=r['date'],artist=r['creator_label']) for r in rows]),ensure_ascii=False),flush=True)

def complete():
 original,pin=d.final_plan();extra=m.load(TOPUP/'delivery-plan.json.gz');extra_pin=m.load(TOPUP/'delivery-plan-pin.json')['sha256'];assert m.sha((TOPUP/'delivery-plan.json.gz').read_bytes())==extra_pin
 first=m.load(MAIN/'production-verification.json');second=m.load(TOPUP/'production-verification.json');public=[m.load(folder/'public-verification.json') for folder in (MAIN,TOPUP)]
 assert first['plan_sha256']==pin and second['plan_sha256']==extra_pin and not first['errors'] and not second['errors']
 rows=original['rows']+extra['rows'];ids=[r['artwork_id'] for r in rows];assert len(ids)==len(set(ids))==3002
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  actual=[dict(r) for r in db.execute('SELECT id::text,status,published_at,primary_media_id::text,current_institution_id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) evidence FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))]
  assert len(actual)==3002
  images={**original['images'],**extra['images']}
  for a in actual:assert a['status']=='review' and a['published_at'] is None and a['primary_media_id']==images[a['id']]['media_id'] and a['current_institution_id']==d.IID and a['evidence']
  scopes=collections.Counter(a['scope'] for a in actual);assert scopes=={'eligible':3000,'review':2}
  review_ids=sorted(a['id'] for a in actual if a['scope']=='review');assert review_ids==sorted(first['creation_scope_review_ids'])
  collection_ids={r['artwork_id'] for r in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s',(d.COLLECTION,))};assert collection_ids==set(ids)
 receipts=0
 for folder,plan,expected_pin in [(MAIN,original,pin),(TOPUP,extra,extra_pin)]:
  for aid,im in plan['images'].items():
   u=m.load(folder/'uploads'/(aid+'.json'));assert u['plan_sha256']==expected_pin and u['sha256']==im['sha256'] and u['public_bytes_verified'];receipts+=1
 manifests=[]
 for folder in (MAIN,TOPUP):
  with (folder/'delivery-manifest.csv').open(encoding='utf-8-sig',newline='') as f:manifests.extend(csv.DictReader(f))
 assert len(manifests)==len(ids) and {r['artwork_id'] for r in manifests}==set(ids)
 output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=list(manifests[0])+['creation_scope']);writer.writeheader()
 for row in manifests:
  assert row['sha256']==images[row['artwork_id']]['sha256'];writer.writerow(dict(row,creation_scope='review' if row['artwork_id'] in review_ids else 'eligible'))
 combined_csv=output.getvalue().encode('utf-8-sig');m.save(MAIN/'delivery-manifest-combined.csv',combined_csv)
 report=dict(at=m.now(),plan_sha256=pin,supplement_plan_sha256=extra_pin,new_artworks=len(ids),images=len(images),fully_eligible_artworks=3000,creation_scope_review_artworks=2,creation_scope_review_ids=review_ids,artists=len({r['artist_id'] for r in rows}),new_artists=first['new_artists']+second['new_artists'],holding_assertions=len(ids),collection_items=len(collection_ids),public_image_hash_checks=receipts,anonymous_artwork_and_browsing_samples=sum(len(p['anonymous_artwork_checks']) for p in public),prepared_reserve_remaining=len(original['eligible_reserve'])-len(extra['rows']),date_precisions=dict(collections.Counter(r['date']['date_precision'] for r in rows)),date_periods=dict(through_1900=sum(r['date']['creation_year_end']<=1900 for r in rows),after_1900=sum(r['date']['creation_year_end']>1900 for r in rows)),image_rights_labels=dict(collections.Counter(r['rights_label'] for r in rows)),image_bytes=sum(im['bytes'] for im in images.values()),all_artworks_status='review',current_display_claims=0,movement_changes=0,local_database_connections=0,errors=[])
 m.save(MAIN/'completion-verification.json',report);m.save(INITIAL_BACKUP/'completion-verification.json',report)
 m.save(MAIN/'delivery-manifest-combined-checksum.json',dict(sha256=m.sha(combined_csv),rows=len(manifests)))
 m.save(INITIAL_BACKUP/'completion-state.json.gz',dict(at=report['at'],artworks=actual,plan_sha256=pin,supplement_plan_sha256=extra_pin))
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
 command=sys.argv[1]
 if command in ('stage','complete'):globals()[command]()
 else:
  assert command in ('upload','apply','verify','public_verify','manifest')
  d.RUN=TOPUP;d.BACKUP=TOPUP_BACKUP;getattr(d,command)()
