#!/usr/bin/env python3
"""Final production proof and source-complete report for the fifth cohort."""
import argparse
import collections
import html
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('round_five',ROOT/'ops/run-random-200-round5-20261007.py')
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
d=x.d;s=x.s;m=x.m;r=x.r;RUN=x.RUN;BACKUP=x.BACKUP


def verify():
    dest=RUN/'final-verification.json'
    if dest.exists():print('Final verification preserved',flush=True);return
    expected_count=len(m.cohort())
    assert len(list((RUN/'verified').glob('*.json')))==expected_count
    deliveries=list(d.pinned_deliveries());assert len(deliveries)==expected_count
    expected={}
    for path in (BACKUP/'batch-after').glob('*/*.json.gz'):expected.update(r.load(path)['records'])
    rows=[row for plan,pin in deliveries for row in plan['rows']]
    images=[(im,pin) for plan,pin in deliveries for im in plan['images']]
    assert len(expected)==len(rows)==len({row['artwork_id'] for row in rows})
    assert len(images)==len({im['artwork_id'] for im,pin in images})==len({im['sha256'] for im,pin in images})
    pairs={pair['artist']['id']:pair for pair in m.cohort()}
    baseline={work['id']:work for aid in pairs for work in r.load(RUN/'catalogue-works'/(aid+'.json.gz'))}
    review_path=RUN/'concurrent-target-image-review.json'
    reviewed=r.load(review_path)['reviewed'] if review_path.exists() else {}
    image_target_ids={im['artwork_id'] for im,pin in images}
    row_pins={row['artwork_id']:pin for plan,pin in deliveries for row in plan['rows']}
    location_review_path=RUN/'concurrent-location-review.json'
    location_reviews=d.location_reviews()
    actual={};changes=[];profile_changes=[];target_changes=[]
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        ids=list(expected)
        for start in range(0,len(ids),500):
            part=ids[start:start+500];current=s.snapshots(db,part)
            for aid,value in current.items():
                if value!=expected[aid]:
                    if d.reviewed_location_change(aid,expected[aid],value,row_pins[aid],'postcommit'):continue
                    review=reviewed.get(aid)
                    assert review and review['before']==expected[aid] and review['after']==value,'Unreviewed campaign target change'
                    assert aid not in image_target_ids and review['count_as_this_campaign_image'] is False
                    assert review['catalogue_metadata_creators_holdings_publication_unchanged']
                    target_changes.append({'artwork_id':aid,'classification':review['classification'],'media_id':value['artwork']['primary_media_id']})
            assert set(current)==set(part),'Campaign target missing'
            actual.update(current)
        print('Final record snapshots verified:',len(actual),flush=True)
        for aid,review in location_reviews.items():
            assert actual[aid]['locations']==review['after']['locations']
            assert actual[aid]['creators']==review['after']['creators']
            for key in ['current_institution_id','current_location_text','location_checked_at','status','published_at']:
                assert actual[aid]['artwork'][key]==review['after']['artwork'][key]
            if review['stage']=='preapply':
                row=next(row for row in rows if row['artwork_id']==aid)
                note=db.execute('SELECT evidence_note FROM citations WHERE id=%s',(m.uid('identity/'+row['source_id']),)).fetchone()
                assert json.loads(note['evidence_note'])['concurrent_location_preservation']==d.reviewed_location_change(aid,review['before'],review['after'],row_pins[aid],'preapply')
        for start in range(0,len(images),500):
            part=images[start:start+500]
            media=db.execute('''SELECT to_jsonb(ma) media,to_jsonb(e) rights FROM media_assets ma
                JOIN media_rights_evidence e ON e.media_id=ma.id WHERE ma.id=ANY(%s::uuid[])''',([im['media_id'] for im,pin in part],)).fetchall()
            byid={row['media']['id']:row for row in media};assert len(byid)==len(part)
            for im,pin in part:
                row=byid[im['media_id']];asset=row['media'];ev=row['rights']
                assert actual[im['artwork_id']]['artwork']['primary_media_id']==im['media_id']
                assert asset['storage_path']==im['path'] and asset['checksum_sha256']==im['sha256'] and asset['byte_size']==im['bytes']<=100000
                assert asset['width']==im['width'] and asset['height']==im['height']
                assert asset['rights_status']==im['rights_status'] and asset['verified_at'] is None
                assert asset['license_label']==im['source_rights_label']+' (WikiArt source label)'
                assert ev['source_image_url']==im['source_image_url'] and ev['source_record_id']==im['source_id']
                assert ev['evidence_json']['plan_sha256']==pin and ev['evidence_json']['authorization']['cohort_sha256']==r.load(RUN/'authorization.json')['cohort_sha256']
                receipt=r.load(RUN/'image-uploads'/(im['artwork_id']+'.json'))
                assert receipt['public_bytes_verified'] and receipt['sha256']==im['sha256'] and receipt['plan_sha256']==pin
                assert r.sha(Path(im['visual_path']).read_bytes())==im['sha256']
        print('Final images, rights assertions, approval and public receipts verified:',len(images),flush=True)
        sources={row['source_id']:row['artwork_id'] for row in rows};keys=list(sources)
        for start in range(0,len(keys),500):
            part=keys[start:start+500]
            identifiers=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",(part,)).fetchall()
            assert {row['external_id']:row['entity_id'] for row in identifiers}=={key:sources[key] for key in part}
        for row in rows:
            current=actual[row['artwork_id']]
            if row['action']=='create':
                obj=current['artwork'];assert obj['status']=='review' and obj['research_candidate'] and obj['published_at'] is None
                assert obj['current_institution_id'] is None and not current['locations']
                assert len(current['creators'])==1 and current['creators'][0]['artist_id']==row['artist_id']
        noted_rows=[row for row in rows if row.get('reviewed_source_discrepancy')]
        if noted_rows:
            notes=db.execute('SELECT id::text,evidence_note FROM citations WHERE id=ANY(%s::uuid[])',
                ([m.uid('identity/'+row['source_id']) for row in noted_rows],)).fetchall()
            by_note={note['id']:json.loads(note['evidence_note']) for note in notes}
            assert len(by_note)==len(noted_rows)
            for row in noted_rows:
                assert by_note[m.uid('identity/'+row['source_id'])]['reviewed_source_discrepancy']==row['reviewed_source_discrepancy']
        untouched=sorted(set(baseline)-set(actual));current={aid:v['artwork'] for aid,v in actual.items()}
        for start in range(0,len(untouched),500):
            part=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',(untouched[start:start+500],)).fetchall()
            current.update({v['artwork']['id']:v['artwork'] for v in part})
        for aid in untouched:
            old=baseline[aid]['artwork'];now=current[aid]
            diff={k:{'before':v,'now':now.get(k)} for k,v in old.items() if now.get(k)!=v}
            if diff:changes.append({'artwork_id':aid,'title':old['title'],'targeted_by_campaign':False,'changes':diff})
        for row in db.execute('SELECT to_jsonb(a) artist FROM artists a WHERE id=ANY(%s::uuid[])',(list(pairs),)).fetchall():
            artist=row['artist'];old=pairs[artist['id']]['artist'];diff={k:{'before':v,'now':artist.get(k)} for k,v in old.items() if artist.get(k)!=v}
            if diff:profile_changes.append({'artist_id':artist['id'],'changes':diff,'scope':'This operation writes no artist profile columns.'})
        query="SELECT aa.artist_id::text artist_id,count(DISTINCT a.id) active_records,count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) images FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY GROUPING SETS ((aa.artist_id),())"
        query_plan=db.execute('EXPLAIN (FORMAT JSON) '+query,(list(pairs),)).fetchone()
        totals=db.execute(query,(list(pairs),)).fetchall();byartist={v['artist_id']:v for v in totals if v['artist_id']}
        total=next(v for v in totals if v['artist_id'] is None)
    r.save(RUN/'final-count-query-plan.json',query_plan)
    r.save_gz(BACKUP/'final-production-snapshots.json.gz',{'at':r.now(),'records':actual,'baseline_current':current})
    r.save(RUN/'concurrent-production-changes.json',{'at':r.now(),'untargeted_artwork_changes':changes,'artist_profile_changes':profile_changes,'reviewed_source_evidence_target_image_additions':target_changes,'reviewed_concurrent_holding_updates':list(location_reviews)})
    result={'at':r.now(),'operation':m.OP,'painters':expected_count,'records_verified':len(actual),'images_verified':len(images),
        'new_review_records':sum(row['action']=='create' for row in rows),'matched_existing_records':sum(row['action']=='existing' for row in rows),
        'source_identifiers_verified':len(sources),'unique_active_records':total['active_records'],'unique_images':total['images'],
        'reviewed_source_notes_verified':len(noted_rows),
        'baseline':r.load(RUN/'snapshot.json'),'per_artist':[{'artist_id':aid,'artist':pair['artist']['display_name'],**byartist.get(aid,{'active_records':0,'images':0})} for aid,pair in pairs.items()],
        'concurrent_untargeted_artwork_changes':len(changes),'concurrent_artist_profile_changes':len(profile_changes),
        'concurrent_source_evidence_target_image_additions':len(target_changes),
        'reviewed_concurrent_holding_updates':len(location_reviews),
        'concurrent_location_review_sha256':r.sha(location_review_path.read_bytes()) if location_reviews else None,
        'concurrent_location_review_files':{review['review_file']:review['review_sha256'] for review in location_reviews.values()},
        'new_records_remain_review':True,'existing_images_metadata_holdings_publication_preserved':True,'local_database_changed':False,
        'all_sampled_painter_outcomes_verified':True,'all_200_painter_outcomes_verified':expected_count==200,'bounded_application_api_checks':'Per-painter verified and api-verification receipts; all expected delivered image IDs checked.',
        'errors':[]}
    r.save(dest,result);print('Final production proof complete:',result['new_review_records'],'new records;',len(images),'images',flush=True)


def report():
    proof=r.load(RUN/'final-verification.json');assert proof['painters']==len(m.cohort()) and not proof['errors']
    d.report();summary=r.load(RUN/'summary.json');deliveries={v['artist']['id']:v for v,pin in d.pinned_deliveries()}
    image_jobs=[(im,pin) for data,pin in d.pinned_deliveries() for im in data['images']]
    review_path=RUN/'concurrent-target-image-review.json'
    concurrent_images=r.load(review_path)['reviewed'] if review_path.exists() else {}
    images={im['artwork_id']:im for im,pin in image_jobs};pairs={v['artist']['id']:v for v in m.cohort()}
    names={aid:{s.normalized(n) for n in [pair['artist']['display_name'],pair['source']['name']] if len(s.normalized(n).split())>=2} for aid,pair in pairs.items()}
    sources=[];created=[];related={};dispositions=collections.Counter();index_total=0;available=0;recovered=0
    for data,pin in d.plans():
        artist=data['artist'];aid=artist['id'];delivery=deliveries[aid];accepted={row['source_id']:row for row in delivery['rows']}
        index_total+=data['source_index_count']
        for row in data['rows']:
            page=row.get('page');sid=row.get('source_id');target=row.get('artwork_id');action=row['action'];reason=row.get('reason') or row.get('image_hold') or ''
            idx=row.get('record',{}).get('index',{})
            if target in delivery['held']:action='hold';reason=delivery['held'][target]
            elif sid in accepted:action='created_review' if row['action']=='create' else 'existing_matched'
            im=images.get(target);date=s.source_date(page) if page else idx.get('date')
            image_state='uploaded' if im else ('existing_image_preserved' if row.get('has_image') else 'none')
            if sid in accepted and not im and not row.get('has_image'):
                if not date:image_state='undated_deferred';reason=reason or 'Unknown creation date retained in review; image awaits dated scope evidence.'
                prep=RUN/'prepared-images'/(str(target)+'.json')
                if prep.exists() and r.load(prep)['outcome']=='preparation_held':image_state='source_image_held';reason=r.load(prep).get('error') or 'Source image failed validation'
            if target in concurrent_images:image_state='concurrent_image_added_by_other_workflow'
            if target in delivery.get('manual_image_holds',{}) and sid in accepted:
                assert im is None
                image_state='reviewed_image_held';reason=delivery['manual_image_holds'][target]
            if page:
                available+=1
                recovered+=int((RUN/'page-retries'/aid/(r.sha(page['url'].encode())+'.json.gz')).exists())
            record={'artist':artist['display_name'],'artist_id':aid,'title':row.get('title',idx.get('title')),'source_url':row.get('source_url',idx.get('url')),
                'source_id':sid,'source_index_row':idx.get('source_row'),'action':action,'artwork_id':target if sid in accepted else '',
                'proposed_artwork_id':target,'source_date':date.get('date_display') if date else idx.get('source_date'),
                'source_date_raw':page['fields'].get('Date',page['metadata'].get('year')) if page else idx.get('source_date'),
                'source_rights_label':row.get('source_rights_label'),'rights_status':row.get('rights_status'),'editorial_identity_confidence':row.get('confidence'),
                'image_state':image_state,'image_url':'https://artlines.org'+im['path'] if im else '',
                'concurrent_image_url':'https://artlines.org'+concurrent_images[target]['media']['media']['storage_path'] if target in concurrent_images else '',
                'reason':reason,'candidate_ids':';'.join(row.get('candidate_ids',[])),'related_source_versions':';'.join(row.get('related_sources',[]))}
            sources.append(record);dispositions[action]+=1
            if action=='created_review':created.append(record)
            if page:
                title=' '+s.normalized(row['title'])+' '
                for subject,nameset in names.items():
                    if subject!=aid and any(' '+name+' ' in title for name in nameset):
                        related[(subject,sid)]={'artist':pairs[subject]['artist']['display_name'],'artist_id':subject,'relation':'title_name_lead',
                            'creator':artist['display_name'],'title':row['title'],'artwork_id':target if sid in accepted else '',
                            'source_url':row['source_url'],'state':action,'basis':'Full creator name occurs in another sampled creator’s source title; relationship lead, no creator reassignment.'}
        idx=r.load(RUN/'indexes'/(aid+'.json.gz'))
        for item in idx['items']:
            if item['date'] and item['date']['creation_year_start']>1970:
                sources.append({'artist':artist['display_name'],'artist_id':aid,'title':item['title'],'source_url':item['url'],
                    'action':'excluded_after_1970','source_date':item['source_date'],'reason':'Explicit post-1970 index date; image not downloaded.'});dispositions['excluded_after_1970']+=1
    assert len(sources)==index_total
    for row in r.load(RUN/'cached-related-work-leads-v2.json.gz')['rows']:
        key=(row['artist_id'],row['source_id'])
        if key not in related:related[key]={**row,'state':'captured_source_relationship_lead'}
    rejected=r.load(RUN/'related-lead-decisions.json')['rejected'] if (RUN/'related-lead-decisions.json').exists() else []
    for row in rejected:related.pop((row['artist_id'],row['source_id']),None)
    conflict_leads_path=RUN/'creator-conflict-relationship-leads.json'
    if conflict_leads_path.exists():
        for row in r.load(conflict_leads_path)['rows']:related[(row['artist_id'],row['source_id'])]=row
    leads=r.load(RUN/'expanded-creator-leads.json')
    lead_evidence=r.load(RUN/'creator-lead-object-evidence.json.gz')
    for lead in leads:
        aid=lead['artist_id'];work=lead['artwork']
        creators=lead_evidence['records'][work['id']]['creators']
        state='already_linked_creator' if any(c['artist_id']==aid for c in creators) else ('existing_creator_conflict' if creators else 'existing_review_lead')
        related[(aid,work['id'])]={'artist':pairs[aid]['artist']['display_name'],'artist_id':aid,'relation':'unlinked_creator_label',
            'creator':work['unlinked_creator_label'],'title':work['title'],'artwork_id':work['id'],'source_url':'',
            'state':state,'linked_creator_ids':';'.join(c['artist_id'] for c in creators),'creator_links_checked_at':lead_evidence['at'],
            'basis':'Existing object-level creator label matches a full name/alias candidate. Existing creator links are preserved; attribution and same-object evidence required before any new linking.'}
    for row in related.values():
        for key in ['artist','creator','title']:
            if isinstance(row.get(key),str):row[key]=html.unescape(row[key])
    uploaded=[{'artist':im['artist'],'artist_id':im['artist_id'],'artwork_id':im['artwork_id'],'title':im['title'],'source_url':im['source_page_url'],
        'source_image_url':im['source_image_url'],'source_rights_label':im['source_rights_label'],'rights_status':im['rights_status'],
        'image_url':'https://artlines.org'+im['path'],'sha256':im['sha256'],'bytes':im['bytes'],'width':im['width'],'height':im['height'],'plan_sha256':pin} for im,pin in image_jobs]
    assert len(uploaded)==proof['images_verified'] and len(created)==proof['new_review_records']
    index_gaps=r.load(RUN/'source-index-gaps.json')['painters']
    gaps_by_artist={row['artist_id']:row for row in index_gaps}
    per_artist={row['artist_id']:row for row in proof['per_artist']};source_counts=collections.Counter(row['artist_id'] for row in sources)
    lead_counts=collections.Counter(row['artist_id'] for row in leads)
    for row in summary['painters_report']:
        aid=row['artist_id'];row.update(source_entries=source_counts[aid],after_records=per_artist[aid]['active_records'],after_images=per_artist[aid]['images'],unlinked_creator_leads=lead_counts[aid],source_index_gap=gaps_by_artist.get(aid,{}).get('reason',''))
    totals=summary['totals'];totals.update(source_entries=len(sources),created=len(created),images_added=len(uploaded),
        before_records=proof['baseline']['artworks'],before_images=proof['baseline']['images'],after_records=proof['unique_active_records'],after_images=proof['unique_images'],
        unlinked_creator_leads=len(leads),title_relationship_leads=sum(row['relation']=='title_name_lead' for row in related.values()),
        captured_source_pages=available,recovered_source_pages=recovered,unlinked_source_index_entries=len(r.load(RUN/'unlinked-index-entries.json.gz')),
        concurrent_untargeted_artwork_changes=proof['concurrent_untargeted_artwork_changes'])
    totals['unavailable_painter_indexes']=len(index_gaps)
    totals['related_artwork_leads']=len(related)
    totals['reviewed_source_notes']=proof['reviewed_source_notes_verified']
    totals['concurrent_source_evidence_target_image_additions']=proof['concurrent_source_evidence_target_image_additions']
    totals['concurrent_net_record_delta']=totals['after_records']-totals['before_records']-totals['created']
    totals['source_holds']=sum(row['source_holds'] for row in summary['painters_report'])
    totals['concurrent_net_image_delta']=totals['after_images']-totals['before_images']-totals['images_added']
    summary.update(at=r.now(),complete=True,final_verification='final-verification.json',source_dispositions=dict(dispositions),
        related_scope='Existing creator-label candidates and full-name references in this cohort and previously captured English WikiArt artwork pages are preserved as relationship leads. This is not an exhaustive worldwide relationship catalogue.',
        image_policy='WikiArt is approved under the 6 October 2026 user instruction. Actual per-image rights assertions, including restricted or unknown labels, remain separate from user approval. Complete-frame derivatives are at most 100,000 bytes; source originals are archived outside Documents.',
        validation='All delivered images were decoded, measured, checked for source aspect ratio, byte budget and hashes, and compared for duplicate reproductions. Visual review covers documented per-artist samples, every title/date existing match, low-resolution/quality cases and every artwork-JSON image whose visible page uses a generic frame. It does not claim manual viewing of every image. Production records, media, rights evidence, source IDs, reviewed source-discrepancy notes and live bounded gallery API results were verified.',
        source_index_gaps=index_gaps,
        limitations='Unavailable creator indexes are documented in source-index-gaps.json without replacing painters in the fixed sample. Unlinked source index rows, unresolved versions/attributions, unavailable pages and undated images remain explicit review holds. Complete available source-list coverage is not a catalogue raisonné. Current query plans do not establish performance at ten million artworks; large-scale load testing remains separate backend work.',
        preservation='All new records remain in review. This campaign preserved existing images, catalogue metadata, creator assertions, holdings, current-display claims and publication states. Concurrent changes by other workflows are recorded separately. No local database writes, commits, deployment or deletion.')
    assert proof['painters']==200
    summary['sampling_eligibility_review']='sampling-nonperson-review.json'
    for name,rows in [('painters.csv',summary['painters_report']),('source-dispositions.csv',sources),('new-review-records.csv',created),('uploaded-images.csv',uploaded),('related-artwork-leads.csv',list(related.values())),('rejected-relationship-leads.csv',rejected)]:x.csv_file(name,rows)
    temp=RUN/'summary.partial';temp.write_text(json.dumps(summary,ensure_ascii=False,indent=2));temp.replace(RUN/'summary.json')
    e=html.escape;table=''.join('<tr>'+''.join('<td>'+e(str(row.get(k,'')))+'</td>' for k in ['artist','source_entries','created','images_added','after_records','after_images','source_holds','delivery_holds','undated_image_holds','reviewed_image_holds'])+'</tr>' for row in summary['painters_report'])
    links=' · '.join('<a href="'+name+'">'+label+'</a>' for name,label in [('selected-200-painters.csv','New random sample'),('painters.csv','200 painter outcomes'),('uploaded-images.csv','Uploaded images'),('new-review-records.csv','New review records'),('source-dispositions.csv','Every source disposition'),('related-artwork-leads.csv','Related works'),('manual-identity-holds.json','Reviewed identity holds'),('manual-image-holds.json','Deferred images'),('reviewed-source-discrepancies.json','Source conflicts and qualifications'),('source-index-gaps.json','Unavailable indexes'),('final-verification.json','Verification'),('summary.json','Summary')])
    page='<!doctype html><meta charset="utf-8"><title>Fifth random 200-painter production report</title><style>body{font:16px system-ui;max-width:1450px;margin:35px auto;padding:20px;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#eef2f4;position:sticky;top:0}</style><h1>Another 200 painters — completed production import</h1><p>'+e(f"{len(created):,} new review records · {len(uploaded):,} images uploaded · {len(related):,} related-work leads")+'</p><p>'+links+'</p>'
    for key in ['scope','date_policy','image_policy','preservation','related_scope','validation','limitations']:page+='<p>'+e(summary[key])+'</p>'
    page+='<table><thead><tr><th>Painter</th><th>Source entries</th><th>New records</th><th>Images added</th><th>Current records</th><th>Current images</th><th>Source holds</th><th>Delivery holds</th><th>Undated image holds</th><th>Reviewed image holds</th></tr></thead><tbody>'+table+'</tbody></table>'
    temp=RUN/'report.partial';temp.write_text(page);temp.replace(RUN/'report.html')
    print(json.dumps({'complete':True,'painters':proof['painters'],'new_review_records':len(created),'images_uploaded':len(uploaded),'source_entries':len(sources),'related_leads':len(related),'source_dispositions':dict(dispositions)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['verify','report']);args=parser.parse_args();globals()[args.phase]()
