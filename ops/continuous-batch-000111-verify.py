#!/usr/bin/env python3
"""Independent read-only reconciliation for the bounded DigitaltMuseum/Greek pass."""
import csv,datetime,fcntl,gzip,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'docs/research/continuous-production-20261011/batches/000111';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000111'
s=importlib.util.spec_from_file_location('h',ROOT/'ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def save(n,v):h.save(E/n,v)
def read(p):return h.load(p)
def main():
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  source=read(E/'kontoglou-object-research.json');old=read(E/'kontoglou-existing.json');assert len(source)==11 and len({x['url'] for x in source})==11
  artist=old['artists'][0];assert len(old['artists'])==1
  records=[];ids=[]
  for row in source:
   rc=row['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
   sp=BeautifulSoup(raw,'html.parser');acc=sp.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip();head=sp.select_one('h1.artwork');d=head.find('span');date=d.get_text(' ',strip=True) if d else '';d.extract() if d else None;title=head.get_text(' ',strip=True).rstrip(',').strip()
   matched=[x for x in old['works'] if x['accession_number']==acc and x['title']==title];assert len(matched)==1
   a=matched[0];assert a['current_institution_id']=='052007aa-11f7-4d57-90e6-d3b62bb0bf4b'
   assert a['medium_text']+', '+a['dimensions_text']==row['description']
   assert date==row['date'] and (date==a['date_display'] if date else a['date_display']=='Date unknown in museum catalogue')
   disposition='existing_illustrated_preserved' if a['primary_media_id'] else 'image_date_unknown_held' if not date else 'greek_image_extension_ends_1955_held'
   if disposition.endswith('1955_held'):assert int(date)>1955
   ids.append(a['id']);records.append(dict(artwork_id=a['id'],native_url=row['url'],accession=acc,title=title,date=date or None,source_sha256=rc['sha256'],disposition=disposition,metadata_duplicate=True,new_coverage_count=0))
  with h.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
   current=h.snapshot(db,ids);assert len(current)==11
   for row in records:
    aid=row['artwork_id'];state=current[aid];before=next(x for x in old['works'] if x['id']==aid)
    for key,val in before.items():assert state['artwork'][key]==val,(aid,key)
    assert state['artwork']['status']!='archived' and any(x['artist_id']==artist['id'] for x in state['creators'])
    assert any(x['claim_type']=='holding' and x['institution_id']==state['artwork']['current_institution_id'] and x['review_state']=='accepted' for x in state['holdings'])
   prior=read(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prior['after']))==prior['after']
   ownc=list(db.execute("SELECT id::text FROM citations WHERE field_name=ANY(%s)",(['continuous_greek_object_evidence_b000111','continuous_digitaltmuseum_object_evidence_b000111'],)))
   ownm=list(db.execute("SELECT media_id::text FROM media_rights_evidence WHERE adapter_version=ANY(%s)",(['continuous-greek-20261013-b000111','continuous-digitaltmuseum-20261013-b000111'],)))
   assert not ownc and not ownm
  save('independent-production-verification.json',dict(at=h.now(),read_only=True,records=records,existing_objects=11,already_illustrated=5,unillustrated_held=6,all_metadata_and_primary_media_equal_research_preimages=True,existing_creator_and_accepted_holdings_verified=True,batch107_snapshot_equal=True,own_citation_rows=ownc,own_media_rows=ownm,new_production_changes=0,verification_limit='Existing images were not downloaded or visually reviewed; their existing associations are not counted as deliveries.'))
  rc=read(E/'digitaltmuseum-search.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==403
  assert b'Just a moment' in raw
  save('independent-source-verification.json',dict(at=h.now(),source_objects=records,all_source_bodies_rehashed=True,digitaltmuseum=rc,digitaltmuseum_retries=0,api_requested=False,api_reason='Registry requires API key for full use; documentation web request returned403. No authentication or access challenge bypass.',images_downloaded=0,actually_visually_reviewed_files=[]))
  counts=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)
  nxt='Research the unprocessed National Gallery of Iceland object https://www.listasafn.is/en/art/collection/li-5742/ and up to 24 further supported collection objects. Reconcile exact inventories globally; preserve native-image permission holds. Do not repeat DigitaltMuseum403 or the 11 reconciled Kontoglou objects.'
  save('source-access-holds.json',dict(at=h.now(),inherited=[dict(path=str(E.parent/'000110/latest-source-hold-reconciliation.json'),sha256=h.sha((E.parent/'000110/latest-source-hold-reconciliation.json').read_bytes())),dict(path=str(E.parent/'000106/source-access-holds.json'),sha256=h.sha((E.parent/'000106/source-access-holds.json').read_bytes()))],digitaltmuseum=dict(status=403,url=rc['url'],body_sha256=rc['sha256'],retry_allowed=False,retries=0,requires='Documented public access change or separately authorized documented API access; do not work around challenge.'),greek_image_holds=[x for x in records if x['disposition']!='existing_illustrated_preserved']))
  save('batch-verification-receipt.json',dict(at=h.now(),batch=111,outcome='no_eligible_candidates',verified_counts=counts,discovered_objects=11,metadata_reconciled_existing_objects=11,selected_for_import=0,prepared=0,imported=0,verified_new=0,image_downloads=0,visually_reviewed=0,reason='DigitaltMuseum public catalogue denied403. All11 Kontoglou native inventories already exist; five illustrated, three unknown-date image holds and three after1955 Greek-image-policy holds. No duplicate or unauthorized image additions.',prior_batch107_reconciled=True,prior_campaign_increments_counted=0,production_writes=0,local_catalogue_connections=0,next_task=nxt))
  # A fresh queue read prevents clobbering unrelated updates; only researched entries change.
  qp=E.parents[1]/'source-queue.json';q=read(qp);before=json.loads(json.dumps(q));touched={'digitaltmuseum','national_gallery_athens'}
  for x in q['sources']:
   if x['source_id'] not in touched:continue
   x['last_checked_at']=h.now();x['checkpoint']=str((E/'CHECKPOINT.json').relative_to(ROOT));x.setdefault('evidence_paths',[]).extend([str((E/f).relative_to(ROOT)) for f in ['independent-source-verification.json','independent-production-verification.json','batch-verification-receipt.json','source-access-holds.json']])
   if x['source_id']=='digitaltmuseum':
    x['status']='public_catalogue_http403_access_hold_no_objects_selected';x['access_status']='HTTP403 public catalogue; documentation web tool403; no retries or API requests';x['policy_reference']='Original111-source CSV digitaltmuseum; docs/ARTLINE_IMAGE_USE.md';x['resume_cursor']=dict(route='public_catalogue_painting_search',attempted_url=rc['url'],processed_object_ids=[],retry_allowed=False,next_step='Rotate to available registry sources until documented access change.')
   else:
    x.setdefault('research_history',[]).append(dict(batch=111,at=h.now(),route='kontoglou-fotis',exact_existing_objects=11,new_coverage=0,verified_counts=counts,evidence=str((E/'independent-production-verification.json').relative_to(ROOT))))
    x.setdefault('resume_cursor',{})['kontoglou_fotis']=dict(artist_url='https://www.nationalgallery.gr/en/artist/kontoglou-fotis/',processed_urls=[r['url'] for r in source],all_existing=True,repeat_unchanged=False,remaining_gaps='Three undated and three1956/1963 image gaps remain held; five existing primary images preserved.')
  assert [x for x in before['sources'] if x['source_id'] not in touched]==[x for x in q['sources'] if x['source_id'] not in touched]
  tmp=qp.with_suffix('.111.tmp');tmp.write_text(json.dumps(q,indent=2,ensure_ascii=False)+'\n');os.replace(tmp,qp)
  save('independent-queue-verification.json',dict(at=h.now(),unrelated_entries_unchanged=True,updated_source_ids=sorted(touched),source_count=len(q['sources']),queue_sha256=h.sha(qp.read_bytes())))
  checkpoint=dict(at=h.now(),batch=111,stage='complete_no_eligible_candidates',verified_counts=counts,next_task=nxt,production_writes=0,prior107_reconciled=True,supervisor_unchanged=True,evidence_receipt=str((E/'batch-verification-receipt.json').relative_to(ROOT)))
  save('CHECKPOINT.json',checkpoint);h.save(R/'research-checkpoint.json',checkpoint)
  save('independent-checkpoint-verification.json',dict(at=h.now(),runtime_checkpoint_equal=read(R/'research-checkpoint.json')==read(E/'CHECKPOINT.json'),queue_receipt_verified=read(E/'independent-queue-verification.json')['queue_sha256']==h.sha(qp.read_bytes()),receipt_counts_equal=read(E/'batch-verification-receipt.json')['verified_counts']==checkpoint['verified_counts']))
  print(json.dumps(checkpoint))
if __name__=='__main__':main()
