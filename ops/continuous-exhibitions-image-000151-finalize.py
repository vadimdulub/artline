#!/usr/bin/env python3
"""Verify attribution and checkpoint the single bounded exhibition image batch."""
import fcntl, importlib.util, json, os, subprocess
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('batch151',Path(__file__).with_name('continuous-exhibitions-image-000151.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def finish():
    p=m.b.plan();pin=m.load(m.E/'plan-pin.json')['sha256'];pre=m.load(m.E/'transaction-preimage.json')
    dv=m.load(m.E/'independent-database-verification.json');sv=m.load(m.E/'independent-storage-verification.json');pv=m.load(m.E/'independent-public-verification.json')
    assert all(x['passed'] for x in [dv,sv,pv]);n=len(p['rows']);assert n==5==len(dv['rows'])==len(sv['rows'])==len(pv['assets'])
    assert len(pv['api_entries'])==len(pre['exact_links'])==5
    checks=[]
    with m.c.connect() as db:
        own=db.execute('select media_id::text,source_checksum,evidence_json from media_rights_evidence where adapter_version=%s order by media_id',(m.OP,)).fetchall()
        assert {x['media_id'] for x in own}=={x['media_id'] for x in p['rows']}
        for r in p['rows']:
            re=next(x for x in own if x['media_id']==r['media_id']);ev=re['evidence_json']
            assert ev['selection_sha256']==pin and ev['preimage_sha256']==p['preimage_sha256'] and ev['native_source_checksum']==re['source_checksum']==r['source_checksum']
            assert ev['visual_review']['actually_viewed'] and ev['visual_review']['sha256']==r['sha256'] and ev['dimension_discrepancy']==r['dimension_discrepancy']
            media=db.execute('select to_jsonb(x) r from media_assets x where id=%s',(r['media_id'],)).fetchone()['r']
            assert media['rights_status']=='restricted' and media['license_label']==r['source_rights_label'] and media['provider_name']=='WikiArt'
            assert pre['before'][r['artwork_id']]['artwork']['primary_media_id'] is None and pre['before'][r['artwork_id']]['attachments']==[]
            checks.append(dict(native_id=r['native_id'],media_id=r['media_id'],persisted_plan_source_review_checksums_verified=True,empty_transaction_preimage_proves_new_attachment=True,rights_status=media['rights_status'],physical_dimensions_discrepancy_retained=r['dimension_discrepancy']))
        memory=db.execute('select id::text,primary_media_id::text from artworks where id=%s',('c2c56c00-f1c1-5eee-bda9-fbfa7c725724',)).fetchone()
        initial=next(r for r in m.load(m.E/'startup-recovery-verification.json')['current'] if r['id']==memory['id'])
        assert memory['primary_media_id']==initial['primary_media_id']
    m.save(m.E/'independent-attribution-and-rights-verification.json',dict(at=m.c.now(),operation=m.OP,plan_sha256=pin,rows=checks,previous_memory_primary_preserved=memory,same_number_smithsonian_images_excluded=3,other_programme_changes_counted=0,passed=True))
    cp=m.load(m.E.parents[1]/'CHECKPOINT.json');initial=m.load(m.E/'startup-recovery-verification.json');assert cp['inflight']['batch']==151
    for k in ['supervisor_pid','worker_pid']:assert cp[k]==initial[k];os.kill(cp[k],0)
    ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
    workers=[x for x in ps if '/opt/homebrew/bin/codex exec ' in x and '--output-schema /Users/vadimdulub/Library/Application Support/Artline/continuous-exhibition-research/schema.json' in x]
    assert len(workers)==1 and int(workers[0].split()[0])==cp['worker_pid'] and int(workers[0].split()[1])==cp['supervisor_pid']
    lockpath=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
    holders=subprocess.check_output(['lsof','-a','-p',str(cp['supervisor_pid'])+','+str(cp['worker_pid']),str(lockpath)],text=True)
    assert all(str(cp[k]) in holders for k in ['supervisor_pid','worker_pid'])
    m.save(m.E/'continuation-process-verification.json',dict(at=m.c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],supervisor_and_worker_running=True,single_exhibition_worker=True,inherited_singleton_lock_open=True,lsof=holders,new_supervisor_started=False,supervisor_and_artwork_programme_changes=0,passed=True))
    rel=lambda name:str((m.E/name).relative_to(m.ROOT))
    names=['exact-operation-recovery-verification.json','required-input-verification.json','production-target-reconciliation.json','source-capture-verification.json','technical-verification.json','visual-review.json','visual-review-pin.json','rights-label-verification.json','backup-verification.json','storage-upload-verification.json','production-target-before-database-write.json','independent-file-verification.json','independent-database-verification.json','independent-storage-verification.json','independent-public-verification.json','independent-attribution-and-rights-verification.json','continuation-process-verification.json']
    next_task='Resume Moralis 1988 catalogue reconciliation at printed page267 (PDF268); 1974/1982 works are documentary-only candidates. The five image gaps from batch150 are delivered; do not recount them. Preserve Composition IV physical-dimension discrepancy. For the next image batch, rotate to the queued Cleveland route after native106595, respecting existing rights and multipart holds.'
    qpath=m.E.parents[1]/'source-queue.json';source_id='national_gallery_athens'
    with qpath.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);q=m.load(qpath);before=m.sha(qpath.read_bytes());original=json.loads(json.dumps(q))
        source=next(x for x in q['sources'] if x['source_id']==source_id)
        source.update(research_status='batch151_five_exact_moralis_images_verified',last_checked_at=m.c.now(),last_batch=151)
        source['cursor']['batch151Images']=dict(native_ids=[x['native_id'] for x in p['rows']],artwork_ids=[x['artwork_id'] for x in p['rows']],catalogue_numbers=[x['catalogue_number'] for x in p['rows']],provider='WikiArt',source_urls=[x['source_url'] for x in p['rows']],plan_sha256=pin,visual_review_sha256=m.sha((m.E/'visual-review.json').read_bytes()),verified_new_images=5,existing_connections_illustrated=5,existing_exhibitions_illustrated=1,complete_supplied_frames=5,dimension_discrepancies_preserved=1,evidence=rel('independent-attribution-and-rights-verification.json'),resume_printed_page=267,resume_pdf_page=268,next=next_task)
        source['cursor']['next']=next_task
        for hold in source.get('holds',[]):
            if hold.get('key')=='batch150-Π.7699-image-aspect':
                hold['image_review_batch151']=dict(at=m.c.now(),decision='Exact full supplied reproduction accepted; five image files delivered. Catalogue square physical dimensions remain discrepant with portrait reproduction; no catalogue dimension correction or artificial stretching.',physical_dimensions_resolved=False,evidence=rel('visual-review.json'))
        source['evidence']=list(dict.fromkeys(source.get('evidence',[])+[rel(x) for x in names]))
        # Assert exact preservation of every unrelated queue value, including supplements.
        check=json.loads(json.dumps(q));check['sources']=[next(x for x in original['sources'] if x['source_id']==source_id) if x['source_id']==source_id else x for x in check['sources']]
        assert check==original
        temp=qpath.with_suffix('.151.tmp');temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(temp,qpath)
        assert m.load(qpath)==q
    registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
    assert m.sha(registry.read_bytes())==m.load(m.E/'required-input-verification.json')['registry_sha256']
    m.save(m.E/'queue-update-verification.json',dict(at=m.c.now(),source_id=source_id,queue_before_sha256=before,queue_after_sha256=m.sha(qpath.read_bytes()),all_unrelated_entries_and_supplemental_sources_preserved=True,original_registry_unchanged=True,resume_printed_page=267,resume_pdf_page=268,passed=True))
    names.append('queue-update-verification.json')
    counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']};counts.update(new_images=5,existing_records_enriched=5)
    checkpoint=dict(at=m.c.now(),batch=151,stage='verified_complete',discovered=5,prepared=5,imported=5,verified=5,verified_counts=counts,existing_connections_illustrated=5,existing_exhibitions_illustrated=1,checklist_state='partial; unchanged',plan_sha256=pin,next_task=next_task,holds=['Composition IV: 73×73cm catalogue dimensions conflict with portrait source reproduction; retained without stretching or metadata correction.','Original1988 checklist still partial; no complete-checklist assertion.'],supervisor_unchanged=True,separate_artwork_programme_unchanged=True,local_catalogue_connections=0)
    m.save(m.E/'CHECKPOINT.json',checkpoint);m.save(m.R/'CHECKPOINT.json',checkpoint);names.append('CHECKPOINT.json')
    m.save(m.E/'final-verification.json',dict(at=m.c.now(),operation=m.OP,plan_sha256=pin,verified_counts=counts,attribution_from_persisted_rights_and_empty_transaction_preimages=True,prior_campaign_and_other_job_changes_excluded=True,verification_files=[dict(path=rel(x),sha256=m.sha((m.E/x).read_bytes())) for x in names],passed=True))
    names.append('final-verification.json')
    result=dict(outcome='progress',summary='Added five individually reviewed WikiArt images to exact documented Moralis1988 artworks. Public checksums, database associations and exhibition API links verified. Restricted rights, review states and Composition IV dimension discrepancy preserved; existing images unchanged. Queue and checkpoint saved; supervisor verified running.',next_task=next_task,blocker='',verified_counts=counts,evidence_paths=[rel(x) for x in ['independent-database-verification.json','independent-public-verification.json','independent-storage-verification.json','independent-attribution-and-rights-verification.json','backup-verification.json','visual-review.json','continuation-process-verification.json','queue-update-verification.json','CHECKPOINT.json','final-verification.json']])
    m.save(m.E/'bounded-result.json',result);m.save(m.R/'bounded-result.json',result)
    print(json.dumps(result))

if __name__=='__main__':finish()
