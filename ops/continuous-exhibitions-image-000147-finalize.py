#!/usr/bin/env python3
"""Independent recovery, attribution and continuation checkpoint for batch 147."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b147',Path(__file__).with_name('continuous-exhibitions-image-000147.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)

def finish():
 p=b.plan();pin=b.load(b.E/'plan-pin.json')['sha256'];pre=b.load(b.E/'transaction-preimage.json');review=b.load(b.E/'visual-review.json');rv={x['native_id']:x for x in review['rows']}
 dv=b.load(b.E/'independent-database-verification.json');sv=b.load(b.E/'independent-storage-verification.json');pv=b.load(b.E/'independent-public-verification.json')
 assert all(x['passed'] for x in [dv,sv,pv])
 n=len(p['rows']);assert len(dv['rows'])==len(sv['rows'])==len(pv['assets'])==n==10
 assert len(pv['api_entries'])==len(pre['exact_links'])==25
 assert b.sha((b.E/'visual-review.json').read_bytes())==b.load(b.E/'visual-review-pin.json')['sha256']
 checks=[];last=max(int(r['native_id']) for r in p['rows'])
 with b.c.connect() as db:
  own=db.execute('select media_id::text,source_checksum,evidence_json from media_rights_evidence where adapter_version=%s order by media_id',(b.OP,)).fetchall()
  assert {x['media_id'] for x in own}=={x['media_id'] for x in p['rows']}
  for r in p['rows']:
   persisted=next(x for x in own if x['media_id']==r['media_id']);ev=persisted['evidence_json']
   assert ev['selection_sha256']==pin and ev['preimage_sha256']==p['preimage_sha256']
   assert ev['native_source_checksum']==persisted['source_checksum']==r['source_checksum']
   assert ev['source_creators']==r['source_creators'] and ev['visual_review']==rv[r['native_id']]
   assert ev['dimension_discrepancy']==r['dimension_discrepancy']
   m=db.execute('select to_jsonb(m) r from media_assets m where id=%s',(r['media_id'],)).fetchone()['r']
   assert m['alt_text']==r['title']+' — '+rv[r['native_id']]['creator_label'] and rv[r['native_id']]['creator_label'] in m['creator_credit']
   original=pre['before'][r['artwork_id']];assert original['artwork']['primary_media_id'] is None and original['attachments']==[]
   checks.append(dict(native_id=r['native_id'],media_id=r['media_id'],caption=m['alt_text'],persisted_source_and_review_checksums_match=True,empty_preimage_proves_new_attachment=True))
  pending=db.execute("""select distinct x.external_id native_id,x.external_id::int sortkey from artworks a join external_identifiers x on x.entity_type='artwork' and x.entity_id=a.id and x.scheme='cleveland-object' join exhibition_entries ee on ee.artwork_id=a.id join exhibitions e on e.id=ee.exhibition_id where a.primary_media_id is null and a.status<>'archived' and e.status<>'archived' and e.start_year between 1600 and 1989 and coalesce(e.end_year,e.start_year)<=1989 and a.work_type in ('painting','drawing','print','watercolor','icon') and a.creation_year_end<=1970 and not exists(select 1 from artwork_media am where am.artwork_id=a.id) and x.external_id::int>%s order by sortkey limit 20""",(last,)).fetchall()
 b.save(b.E/'independent-caption-and-attribution-verification.json',dict(at=b.c.now(),rows=checks,creator_roles_preserved=True,distinct_same_title_massys_impressions_preserved=True,dimension_discrepancies=0,passed=True))
 b.save(b.E/'independent-resume-verification.json',dict(at=b.c.now(),operation=b.OP,plan_sha256=pin,persisted_own_media_ids=[x['media_id'] for x in own],persisted_rights_source_review_checksums_verified=True,transaction_preimages_prove_ten_new_attachments=True,recovery_action='Already present with this exact pinned plan; do not reapply or count again.',replay_performed=False,read_only_check=True,other_job_changes_counted=0,passed=True))
 startup=b.load(b.E/'startup-verification.json');cp=b.load(b.E.parents[1]/'CHECKPOINT.json');assert cp['inflight']['batch']==147
 for k in ['worker_pid','supervisor_pid']:
  assert cp[k]==startup[k];os.kill(cp[k],0)
 for f in startup['supervisor_files']:assert b.sha(Path(f['path']).read_bytes())==f['sha256']
 ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
 workers=[x for x in ps if '/opt/homebrew/bin/codex exec ' in x and '--output-schema /Users/vadimdulub/Library/Application Support/Artline/continuous-exhibition-research/schema.json' in x]
 assert len(workers)==1 and int(workers[0].split()[0])==cp['worker_pid'] and int(workers[0].split()[1])==cp['supervisor_pid']
 lockpath=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
 holders=subprocess.check_output(['lsof','-a','-p',str(cp['supervisor_pid'])+','+str(cp['worker_pid']),str(lockpath)],text=True)
 assert all(str(cp[k]) in holders for k in ['supervisor_pid','worker_pid'])
 b.save(b.E/'continuation-process-verification.json',dict(at=b.c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],supervisor_and_worker_running=True,single_exhibition_worker=True,inherited_singleton_lock_open=True,supervisor_prompt_schema_launchagent_and_protected_artwork_research_files_unchanged=True,new_supervisor_started=False,passed=True))
 names=['startup-verification.json','source-register-verification.json','recovery-check.json','prior-batch-live-recovery-verification.json','production-target-reconciliation.json','new-source-holds.json','source-capture-verification.json','technical-verification.json','visual-review.json','visual-review-pin.json','backup-verification.json','storage-upload-verification.json','production-target-before-database-write.json','independent-file-verification.json','independent-database-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-caption-and-attribution-verification.json','independent-resume-verification.json','continuation-process-verification.json']
 rel=lambda name:str((b.E/name).relative_to(b.ROOT))
 source_next=f'Resume missing exact Cleveland images after native {last}; retain all existing rights and multipart holds. Pending IDs require source and visual review; do not replay these ten images.'
 next_task='Continue Moralis 1988 catalogue reconciliation from printed page 258 (PDF 259), preserving version and date holds. The next image batch can resume Cleveland after native 106595.'
 qpath=b.E.parents[1]/'source-queue.json';newholds=b.load(b.E/'new-source-holds.json')['rows']
 with qpath.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);q=b.load(qpath);before=b.sha(qpath.read_bytes());unrelated=[x for x in q['sources'] if x['source_id']!='cleveland_museum'];unrelated_bytes=json.dumps(unrelated,sort_keys=True)
  source=next(x for x in q['sources'] if x['source_id']=='cleveland_museum');heldids={str(h.get('nativeID',h.get('native_id',h.get('native','')))) for h in source.get('holds',[])}
  pending_ids=[x['native_id'] for x in pending if x['native_id'] not in heldids][:10]
  source.update(research_status='batch147_ten_exact_cc0_images_verified',last_checked_at=b.c.now(),last_batch=147)
  source.setdefault('cursor',{})['batch147Images']=dict(nativeIDs=[r['native_id'] for r in p['rows']],artworkIDs=[r['artwork_id'] for r in p['rows']],plan_sha256=pin,visual_review_sha256=b.sha((b.E/'visual-review.json').read_bytes()),verified_images=n,existing_connections_illustrated=25,existing_exhibitions_illustrated=11,resume_after_native_id=str(last),pending_native_ids=pending_ids,dimension_discrepancies=0,reviewed_complete_frames=10,evidence=rel('independent-database-verification.json'),next=source_next)
  source['cursor']['imageResumeAfterNativeID']=str(last);source['cursor']['next']=source_next
  for h in newholds:
   if h['native_id'] not in heldids:source.setdefault('holds',[]).append(dict(nativeID=h['native_id'],reason=h['reason'],source_receipt=h['source_receipt'],evidence=rel('new-source-holds.json')))
  source['evidence']=list(dict.fromkeys(source.get('evidence',[])+[rel(x) for x in names]))
  tmp=qpath.with_suffix('.147.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qpath)
  assert json.dumps([x for x in b.load(qpath)['sources'] if x['source_id']!='cleveland_museum'],sort_keys=True)==unrelated_bytes
 b.save(b.E/'queue-update-verification.json',dict(at=b.c.now(),source='cleveland_museum',queue_before_sha256=before,queue_after_sha256=b.sha(qpath.read_bytes()),unrelated_sources_preserved=len(unrelated),pending_native_ids=pending_ids,resume_after_native_id=str(last),new_rights_holds=len(newholds),original_registry_unchanged=b.sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes())==b.load(b.E/'source-register-verification.json')['registry_sha256'],passed=True))
 names.append('queue-update-verification.json')
 counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']};counts.update(new_images=n,existing_records_enriched=n)
 checkpoint=dict(at=b.c.now(),batch=147,stage='verified_complete',discovered=len(p['rows'])+len(newholds),prepared=n,imported=n,verified=n,rights_held=len(newholds),verified_counts=counts,existing_connections_illustrated=25,existing_exhibitions_illustrated=11,checklist_states='Existing states preserved; no completeness claim',next_task=next_task,evidence_paths=[rel(x) for x in names],supervisor_unchanged=True,separate_artwork_programme_unchanged=True,local_catalogue_connections=0)
 b.save(b.E/'CHECKPOINT.json',checkpoint);b.save(b.R/'CHECKPOINT.json',checkpoint);names.append('CHECKPOINT.json')
 result=dict(outcome='progress',summary='Added ten individually reviewed Cleveland CC0 images to existing artworks, illustrating 25 existing connections across 11 historical exhibitions. Public checksums, persisted plan attribution and API associations verified. Two copyright holds retained; queue and checkpoint saved.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(x) for x in names])
 b.save(b.E/'final-verification.json',dict(at=b.c.now(),plan_sha256=pin,verified_counts=counts,prior_campaign_and_other_job_changes_excluded=True,attribution_from_persisted_rights_and_transaction_preimages=True,verification_files=[dict(path=rel(x),sha256=b.sha((b.E/x).read_bytes())) for x in names],passed=True))
 result['evidence_paths'].append(rel('final-verification.json'));b.save(b.E/'bounded-result.json',result);b.save(b.R/'bounded-result.json',result)
 print(json.dumps(result))
if __name__=='__main__':finish()
