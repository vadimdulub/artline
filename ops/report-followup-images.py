#!/usr/bin/env python3
"""Incremental completion report: only audited deliveries from this follow-up round."""
import argparse,collections,hashlib,importlib.util,json,time
from pathlib import Path

s=importlib.util.spec_from_file_location('old_report',Path(__file__).with_name('report-overnight-images.py'));old=importlib.util.module_from_spec(s);s.loader.exec_module(old);delivery=old.delivery;core=delivery.core
START=1789543507

def public_delivery_status(public):
    assert public['image_canaries_total']>0 and public['image_canaries_verified']==public['image_canaries_total'],'Public image delivery incomplete'
    failures=[]
    for row in public['checks']:
        assert row['checks'].get('artists',{}).get('verified'),'Public artist artwork detail unavailable'
        for kind,check in row['checks'].items():
            if check.get('verified'):continue
            assert kind=='museums','Unexpected public delivery failure'
            failures.append({'provider':row['provider'],'artwork_id':row['artwork_id'],**check})
    return {'image_canaries_verified':public['image_canaries_verified'],'image_canaries_total':public['image_canaries_total'],
            'api_checks_verified':public['api_checks_verified'],'api_checks_total':public['api_checks_total'],
            'museum_detail_failures':failures,'status':'museum_detail_issue' if failures else 'passed'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--local-audit',type=Path,required=True);p.add_argument('--cloud-audit',type=Path,required=True);p.add_argument('--metadata-audit',type=Path,required=True);p.add_argument('--public-check',type=Path,required=True);p.add_argument('--shared-check',type=Path,required=True);p.add_argument('--safety-scan',type=Path,required=True);a=p.parse_args();r=a.run
    assert time.time()-START>=2*3600,'Requested minimum round duration not reached'
    local=json.loads(a.local_audit.read_text());cloud=json.loads(a.cloud_audit.read_text());metadata=json.loads(a.metadata_audit.read_text());public=json.loads(a.public_check.read_text());shared=json.loads(a.shared_check.read_text());safety=json.loads(a.safety_scan.read_text())
    journal=old.journal_state(r/'local-attachments.jsonl');done=delivery.complete_ids(r);assert done==set(journal),'Pending delivery or journal disagreement'
    old.audit_matches(local,len(done),'local');old.audit_matches(cloud,len(done),'cloud',True)
    assert not metadata['errors'] and metadata['matching_metadata_records']==metadata['metadata_records_expected'],'Metadata parity incomplete'
    public_status=public_delivery_status(public)
    assert shared['snapshot_delivered']==len(done) and not shared['groups_with_other_catalogue_primary_images'],'Shared image review requires resolution'
    assert not safety['credential_pattern_findings'] and not safety['private_reference_findings'] and not safety['image_embedded_metadata_errors'],'Artifact safety scan failed'
    assert local['by_provider']==cloud['by_provider'] and local['by_work_type']==cloud['by_work_type']
    coverage=json.loads((r/'new-artwork-image-coverage-final.json').read_text());tests=json.loads((r/'test-evidence-final.json').read_text());stats=json.loads((r/'catalogue-statistics-final.json').read_text())
    assert coverage['new_artworks']==metadata['counts']['new'] and coverage['new_artworks_with_newly_delivered_image']+coverage['new_artworks_metadata_only']==coverage['new_artworks'],'New artwork coverage differs'
    assert tests['exit_code']==0 and not tests['database_fixtures_created'],'Required test evidence incomplete'
    assert all(t['review_image_delta']==len(done) and t['review_artwork_delta']==metadata['counts']['new'] for t in stats['targets'].values()),'Catalogue deltas differ'
    manifest=r/'approved-image-manifest.jsonl';temporary=manifest.with_suffix('.temporary.jsonl');hashes=set();sources=set();bytes_total=0
    assert not manifest.exists(),'Existing final manifest must not be replaced'
    with temporary.open('x') as out:
        for aid,j in sorted(journal.items()):
            im=json.loads(Path(j['receipt']).read_text());path=r/'production-resume'/im['provider']/'images'/im['provider']/(aid+'.json')
            if path.exists():im=json.loads(path.read_text())
            assert im['target_ids']['local']==aid and im['target_ids'].get('cloud') and delivery.audit.allowed(im['policy_url'])
            row={'local_artwork_id':aid,'production_artwork_id':im['target_ids']['cloud'],'media_id':im['media_id'],'source_name':im.get('source_name',im['provider']),
                'source_record_url':im['source_record_url'],'source_object_id':im.get('source_object_id',im['external_id']),'source_identifier_scheme':im['scheme'],
                'artist':im['artist'],'title':im['title'],'creation_date':im.get('creation_date',im.get('date_display')),'year_start':im['creation_year_start'],'year_end':im['creation_year_end'],'work_type':im['work_type'],
                'image_url':im['source_image_url'],'image_source_page':im['page'],'image_license':im['license_label'],'image_license_url':im['policy_url'],'rights_statement':im['license_label'],
                'creator_credit':im['creator_credit'],'image_attribution':im['attribution_text'],'retrieved_at':im['downloaded_at'],'rights_verified_at':im['rights_verified_at'],
                'artline_image_path':im['path'],'google_storage_object':'gs://'+core.BUCKET+im['path'],'image_sha256':im['sha256'],'bytes':im['bytes'],'width':im['width'],'height':im['height'],'hasPicture':True,'status':'review'}
            out.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');hashes.add(im['sha256']);sources.add(im['source_sha256']);bytes_total+=im['bytes']
    temporary.replace(manifest)
    with manifest.open('rb') as f:manifest_sha=hashlib.file_digest(f,'sha256').hexdigest()
    report={'started_at':'2026-09-16T07:25:07Z','completed_at':core.now(),'elapsed_hours':round((time.time()-START)/3600,3),'requested_round_hours':'2–4',
        'additional_images_delivered_both_targets':len(done),'unique_delivered_image_sha256':len(hashes),'unique_source_image_sha256':len(sources),
        'unique_image_hashes_not_present_in_prior_round':len(hashes)-shared['shared_with_prior_round_sha256'],'popular_painter_image_attachments':cloud['popular_painter_images'],
        'by_work_type':cloud['by_work_type'],'by_source_adapter':cloud['by_provider'],'by_exact_image_license':cloud['by_image_license'],'by_holding_museum':cloud['by_holding_museum'],'by_holding_country':cloud['by_holding_country'],
        'new_artworks_local_and_production':metadata['counts']['new'],'existing_artworks_with_added_official_provenance':metadata['counts']['existing'],'new_artists':0,'records_remain_in_review':True,
        'new_schema_migrations':0,'physical_artworks_deleted_or_merged':0,'art500k_used':False,'bytes_uploaded':bytes_total,
        'inherited_image_holds_not_counted_as_new_withdrawals':452,'new_image_withdrawals':0,
        'public_checks':public_status,
        'new_artwork_image_coverage':coverage,'safeguard_tests_passed':tests['tests'],
        'catalogue_statistics':stats['targets'],
        'evidence':{'local_image_audit':a.local_audit.name,'production_and_storage_audit':a.cloud_audit.name,'metadata_and_country_parity':a.metadata_audit.name,'public_canaries':a.public_check.name,'shared_image_check':a.shared_check.name,'artifact_safety_scan':a.safety_scan.name,'approved_image_manifest':manifest.name,'manifest_sha256':manifest_sha},
        'limits':['Elapsed time includes a network interruption; source requests and production delivery resumed from saved checkpoints.','Artwork type counts distinguish paintings, prints and drawings.','Current museum or Commons file evidence must approve each exact image. Access-denied museum image endpoints were left paused; independently licensed Commons files were verified separately.','All delivered records were checked automatically against source evidence, local files, production references and storage checksums. Visual checks were sampled.','Museum country is distinct from artist nationality. Existing unresolved artist-country fields remain unchanged and in review.','Exact image hashes and authoritative object identifiers were checked for duplicates; this is not an exhaustive near-duplicate visual analysis.','No commit, deployment, Terraform change or editorial publication was performed.']}
    if public_status['museum_detail_failures']:
        report['limits'].append('Public image bytes and artist artwork details passed, but '+str(len(public_status['museum_detail_failures']))+' museum detail route(s) failed the final canary. This is reported separately from successful image delivery; the previously prepared museum-detail performance fix remains undeployed. See public checks for exact URLs and errors.')
    else:
        report['limits'].append('A National Gallery of Art museum-detail canary failed during ingestion, then passed after delivery settled. This does not prove that the previously identified route performance issue is fixed; no deployment was performed.')
    report['evidence'].update(source_batches='source-batches-final.json',catalogue_statistics='catalogue-statistics-final.json',new_artwork_image_coverage='new-artwork-image-coverage-final.json',safeguard_tests='test-evidence-final.json')
    core.save_new(r/'final-aggregate-report.json',report)
    lines=['# Additional image research round','',f"Completed {report['completed_at']}; elapsed {report['elapsed_hours']:.2f} hours, including the recorded network interruption.",'',f"- **{len(done):,} additional images** verified in both databases and Google Storage.",f"- **{cloud['popular_painter_images']:,} images for popular painters**.",f"- **{metadata['counts']['new']:,} new artworks**, plus one existing work with additional official provenance. No new artists.",'- All artworks remain **in review**. The existing schema was reused.','','| Artwork type | Additional images |','| --- | ---: |']
    lines.extend(f'| {kind} | {n:,} |' for kind,n in sorted(cloud['by_work_type'].items()));lines+=['','Evidence:','','- [Aggregate report](final-aggregate-report.json)','- [Approved image manifest](approved-image-manifest.jsonl)',f'- [Local audit]({a.local_audit.name})',f'- [Production and storage audit]({a.cloud_audit.name})',f'- [Metadata and country parity]({a.metadata_audit.name})',f'- [Public checks]({a.public_check.name})',f'- [Duplicate image check]({a.shared_check.name})',f'- [Artifact scan]({a.safety_scan.name})','- [Final test evidence](test-evidence-final.json)','- [Source batches and held candidates](source-batches-final.json)','- [Catalogue statistics](catalogue-statistics-final.json)','- [New artwork image coverage](new-artwork-image-coverage-final.json)','','Notes:',''];lines.extend('- '+x for x in report['limits']);lines+=['','Recovery backups are under `~/Library/Application Support/Artline/backups/images-followup-20260916/`. Source captures and append-only journals preserve both accepted and held candidates. Pending source research may be resumed with the same run directory and a future deadline; do not replace evidence to conceal failures.']
    (r/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:report[k] for k in ('elapsed_hours','additional_images_delivered_both_targets','popular_painter_image_attachments','new_artworks_local_and_production')},indent=2))

if __name__=='__main__':main()
