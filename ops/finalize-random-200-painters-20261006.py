#!/usr/bin/env python3
"""Correction-aware production proof and complete source-disposition exports."""
import argparse, collections, concurrent.futures, csv, html, importlib.util, json, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-random-200-painters-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
r=d.r;s=d.s;m=d.m;RUN=d.RUN;BACKUP=d.BACKUP

def resolution():
    dest=RUN/'cross-creator-resolution.json'
    if dest.exists():return
    audit=r.load(RUN/'cross-creator-image-audit.json');assert len(audit['groups'])==1
    keep='e39b5f86-77ed-57d2-bc69-27384b754fb0';hold='4f3f43ea-0f1f-5479-b456-2d2e6faabe3e'
    note={'at':r.now(),'kept_artwork_id':keep,'held_artwork_id':hold,'cross_creator_audit_sha256':r.sha((RUN/'cross-creator-image-audit.json').read_bytes()),
          'review':'The full reproduction was visually inspected. Its lower-left monogram reads VR within the date 19 / 02, supporting the WikiArt Théo van Rysselberghe identification. Cross has the identical bytes under the unexplained title Aguttes; that conflicting entry is excluded from import. No alternative image, catalogue title, date, holding or publication state is substituted.',
          'primary_catalogue_url':'https://www.christies.com/en/lot/lot-5035343',
          'primary_catalogue_receipt_sha256':r.sha((RUN/'cross-creator-primary-source.json.gz').read_bytes()),
          'primary_catalogue_note':'Christie’s records a seated nude leaning on its hands by Théo, with a lower-left VR stamp and 1902 date. It also cautions that the stamp/date could have been added later. This supports the creator assessment; no auction provenance, medium, dimensions or date qualification is imported because the auction image could not be independently fetched (HTTP 403).',
          'confidence':.95,'confidence_note':'Editorial identity confidence, not a calibrated probability.'}
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        prior=s.snapshots(db,[keep]);assert prior[keep]['artwork']['status']=='review'
        assert not db.execute('SELECT id FROM artworks WHERE id=%s',(hold,)).fetchone()
        im=r.load(RUN/'prepared-images'/(keep+'.json'));assert prior[keep]['artwork']['primary_media_id']==im['media_id']
        db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
          VALUES(%s,'artwork',%s,%s,'random_200_cross_creator_review',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING''',
          (m.uid('cross-creator-review/'+keep),keep,m.uid('source/wikiart'),im['source_id'],im['source_page_url'],json.dumps(note,ensure_ascii=False),r.now(),m.ACTOR))
        assert s.snapshots(db,[keep])==prior
    r.save(dest,note);print('Cross-creator conflict reviewed; one source entry held',flush=True)

def image_jobs():
    jobs=[(im,pin) for data,pin in d.pinned_deliveries() for im in data['images']]
    if (RUN/'supplemental-applied.json').exists():
        data=r.load(RUN/'supplemental-plan.json.gz');pin=r.load(RUN/'supplemental-pin.json')['sha256']
        jobs.extend((im,pin) for im in data['images'])
    return jobs

def verify():
    if (RUN/'final-verification.json').exists():
        print('Final verification already recorded',flush=True);return
    if (BACKUP/'final-production-snapshots.json.gz').exists():
        finish_api(r.load(BACKUP/'final-production-snapshots.json.gz'));return
    assert len(list((RUN/'verified').glob('*.json')))==200
    assert (RUN/'cross-creator-resolution.json').exists()
    assert len(list((RUN/'date-corrections').glob('*.json')))==200
    expected={}
    for p in (BACKUP/'batch-after').glob('*/*.json.gz'):expected.update(r.load(p)['records'])
    expected.update(r.load(BACKUP/'alias-consolidation-after.json.gz')['records'])
    for p in (BACKUP/'date-after').glob('*.json.gz'):expected.update(r.load(p)['records'])
    if (BACKUP/'supplemental-after.json.gz').exists():expected.update(r.load(BACKUP/'supplemental-after.json.gz')['records'])
    aliases=r.load(RUN/'alias-consolidation-applied.json');canonical={x['from']:x['to'] for x in aliases['moves']}
    jobs=image_jobs();delivered={canonical.get(im['artwork_id'],im['artwork_id']):(im,pin) for im,pin in jobs}
    assert len(delivered)==len(jobs)
    assert len({im['sha256'] for im,pin in jobs})==len(jobs),'Unresolved identical delivered reproductions'
    counts=[];all_active={};actual_expected={};source_ids={};concurrent_changes=[];artist_changes=[]
    for data,pin in d.pinned_deliveries():
        for row in data['rows']:source_ids[row['source_id']]=canonical.get(row['artwork_id'],row['artwork_id'])
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        ids=list(expected)
        for start in range(0,len(ids),500):
            actual=s.snapshots(db,ids[start:start+500]);wanted={k:expected[k] for k in ids[start:start+500]}
            assert actual==wanted,'Correction-aware production snapshot mismatch'
            actual_expected.update(actual)
        print('Final audit: all campaign record snapshots match',len(actual_expected),flush=True)
        for start in range(0,len(jobs),500):
            part=jobs[start:start+500]
            rows=db.execute('''SELECT to_jsonb(ma) media,to_jsonb(e) rights FROM media_assets ma
                JOIN media_rights_evidence e ON e.media_id=ma.id WHERE ma.id=ANY(%s::uuid[])''',([im['media_id'] for im,pin in part],)).fetchall()
            byid={x['media']['id']:x for x in rows};assert len(byid)==len(part)
            for im,pin in part:
                target=canonical.get(im['artwork_id'],im['artwork_id']);x=byid[im['media_id']];ma=x['media'];ev=x['rights']
                assert actual_expected[target]['artwork']['primary_media_id']==im['media_id']
                assert ma['storage_path']==im['path'] and ma['checksum_sha256']==im['sha256'] and ma['byte_size']==im['bytes']<=100000
                assert ma['width']==im['width'] and ma['height']==im['height']
                assert ma['rights_status']==im['rights_status'] and ma['verified_at'] is None
                assert ma['license_label']==im['source_rights_label']+' (WikiArt source label)'
                assert ev['source_image_url']==im['source_image_url'] and ev['source_record_id']==im['source_id'] and ev['evidence_json']['plan_sha256']==pin
                upload=r.load(RUN/'image-uploads'/(im['artwork_id']+'.json'))
                assert upload['public_bytes_verified'] and upload['sha256']==im['sha256'] and upload['plan_sha256']==pin
                assert r.sha(Path(im['visual_path']).read_bytes())==im['sha256']
        print('Final audit: all media, rights and public-upload receipts match',len(jobs),flush=True)
        keys=list(source_ids)
        for start in range(0,len(keys),500):
            ext=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",(keys[start:start+500],)).fetchall()
            assert {x['external_id']:x['entity_id'] for x in ext}=={k:source_ids[k] for k in keys[start:start+500]}
        print('Final audit: canonical source identifiers match',len(source_ids),flush=True)
        pairs={p['artist']['id']:p for p in m.cohort()}
        baseline={x['id']:x for aid in pairs for x in r.load(RUN/'catalogue-works'/(aid+'.json.gz'))}
        current={aid:x['artwork'] for aid,x in actual_expected.items()}
        missing=sorted(set(baseline)-set(current))
        for start in range(0,len(missing),500):
            rows=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',(missing[start:start+500],)).fetchall()
            current.update({x['artwork']['id']:x['artwork'] for x in rows})
        for aid,old in baseline.items():
            obj=current[aid];allowed={'primary_media_id','revision','updated_at','updated_by'} if aid in delivered else set()
            changed={k:{'before':v,'now':obj.get(k)} for k,v in old['artwork'].items() if k not in allowed and obj.get(k)!=v}
            if changed:
                assert aid not in expected,'Campaign target changed beyond authorized scope: '+aid
                concurrent_changes.append({'artwork_id':aid,'title':old['title'],'targeted_by_campaign':False,'changes':changed})
            if old['primary_media_id'] and aid in expected:assert obj['primary_media_id']==old['primary_media_id']
        artists=db.execute('SELECT to_jsonb(a) artist FROM artists a WHERE id=ANY(%s::uuid[])',(list(pairs),)).fetchall()
        assert len(artists)==200
        for x in artists:
            a=x['artist'];old=pairs[a['id']]['artist']
            changes={k:{'before':v,'now':a.get(k)} for k,v in old.items() if a.get(k)!=v}
            if changes:artist_changes.append({'artist_id':a['id'],'changes':changes,'scope':'No artist profile columns were written by this campaign.'})
        # Other authorized workflows may add records during this multi-hour pass.
        # Use an ID-only painter-scoped projection to separate their effects.
        live_ids={x['id'] for x in db.execute("SELECT DISTINCT a.id::text id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'",(list(pairs),)).fetchall()}
        extra_ids=sorted(live_ids-set(current))
        for start in range(0,len(extra_ids),500):
            rows=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',(extra_ids[start:start+500],)).fetchall()
            current.update({x['artwork']['id']:x['artwork'] for x in rows})
        all_active={aid:current[aid] for aid in live_ids}
        # Plan inspected separately: scope through indexed painter links, then artwork PKs.
        totals=db.execute("SELECT aa.artist_id::text artist_id,count(DISTINCT a.id) active_records,count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) images FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY GROUPING SETS ((aa.artist_id),())",(list(pairs),)).fetchall()
        byartist={x['artist_id']:x for x in totals if x['artist_id']}
        total=next(x for x in totals if x['artist_id'] is None)
        assert total['active_records']==len(all_active) and total['images']==sum(bool(x['primary_media_id']) for x in all_active.values())
        for aid,pair in pairs.items():
            counts.append({'artist_id':aid,'artist':pair['artist']['display_name'],**byartist.get(aid,{'active_records':0,'images':0})})
        for data,pin in d.pinned_deliveries():
            for row in data['rows']:
                if row['action']!='create' or row['artwork_id'] in canonical:continue
                obj=actual_expected[row['artwork_id']]['artwork']
                assert obj['status']=='review' and obj['research_candidate'] and obj['published_at'] is None
                assert obj['current_institution_id'] is None and not actual_expected[row['artwork_id']]['locations']
    db_result={'at':r.now(),'records':actual_expected,'active_cohort_artworks':all_active,'per_artist':counts,
               'concurrent_untargeted_artwork_changes':concurrent_changes,'concurrent_artist_profile_changes':artist_changes,'concurrent_added_or_newly_linked_ids':extra_ids}
    r.save_gz(BACKUP/'final-production-snapshots.json.gz',db_result)
    r.save(RUN/'concurrent-production-changes.json', {k:v for k,v in db_result.items() if k in ['at','concurrent_untargeted_artwork_changes','concurrent_artist_profile_changes','concurrent_added_or_newly_linked_ids']})
    print('Final audit: baseline reviewed;',len(concurrent_changes),'untargeted concurrent changes preserved',flush=True)
    finish_api(db_result)

def finish_api(db_result):
    """Resume API checks from the completed, immutable database proof."""
    expected=db_result['records'];all_active=db_result['active_cohort_artworks'];counts=db_result['per_artist']
    concurrent_changes=db_result['concurrent_untargeted_artwork_changes'];artist_changes=db_result['concurrent_artist_profile_changes'];extra_ids=db_result['concurrent_added_or_newly_linked_ids']
    aliases=r.load(RUN/'alias-consolidation-applied.json');canonical={x['from']:x['to'] for x in aliases['moves']}
    jobs=image_jobs();delivered={canonical.get(im['artwork_id'],im['artwork_id']):(im,pin) for im,pin in jobs}
    # Recheck live API for every painter affected by post-verification corrections.
    pairs={x['artist']['id']:x for x in m.cohort()}
    affected={x['artist_id'] for x in aliases['moves']}
    if (RUN/'supplemental-applied.json').exists():affected.update(im['artist_id'] for im in r.load(RUN/'supplemental-plan.json.gz')['images'])
    def api(aid):
        dest=RUN/'final-api-verification'/(aid+'.json.gz')
        if dest.exists():
            old=r.load(dest);return {'artist_id':aid,'pages':len(old['pages']),'images_verified':len(old['expected_image_ids'])}
        artist=pairs[aid]['artist'];params={'limit':50,'image_only':'true'};pages=[];found={};cursors=set()
        while True:
            for attempt in range(4):
                response=requests.get('https://artlines.org/api/backend/v1/artists/'+artist['slug']+'/works',params=params,timeout=(15,45))
                if response.status_code not in [500,502,503,504] or attempt==3:break
                print('Retrying temporary gallery response',artist['display_name'],response.status_code,flush=True);time.sleep(2+attempt*3)
            response.raise_for_status();body=response.json()
            pages.append({'url':response.url,'status':response.status_code,'body':body});found.update({x['id']:x for x in body['items']})
            cursor=body.get('next_cursor')
            if not cursor:break
            assert cursor not in cursors and len(pages)<1000;cursors.add(cursor);params['cursor']=cursor
        wanted={k:im for k,(im,pin) in delivered.items() if im['artist_id']==aid}
        for target,im in wanted.items():assert found[target]['media_url']==im['path'] and found[target]['rights_status']==im['rights_status']
        assert not set(canonical)&set(found),'Archived duplicate leaked through API'
        r.save_gz(dest,{'at':r.now(),'pages':pages,'expected_image_ids':list(wanted)})
        print('Final gallery verified',artist['display_name'],len(wanted),'images',flush=True)
        return {'artist_id':aid,'pages':len(pages),'images_verified':len(wanted)}
    api_results=[api(aid) for aid in sorted(affected)]
    result={'at':r.now(),'database_snapshot_at':db_result['at'],'painters':200,'checked_records':len(expected),'images_verified':len(jobs),'per_artist':counts,
            'unique_active_records':len(all_active),'unique_images':sum(bool(x['primary_media_id']) for x in all_active.values()),
            'baseline':r.load(RUN/'snapshot.json'),'correction_api_verification':api_results,
            'all_main_painter_api_receipts':200,'metadata_and_existing_images_preserved':True,'new_records_remain_review':True,
            'preservation_scope':'Every campaign target matches its committed snapshot plus documented corrections. Concurrent changes outside this campaign are preserved and recorded separately.',
            'concurrent_untargeted_artwork_changes':len(concurrent_changes),'concurrent_artist_profile_changes':len(artist_changes),'concurrent_added_or_newly_linked_records':len(extra_ids),
            'cross_creator_exact_duplicate_groups_delivered':0,'local_database_writes':0,'errors':[]}
    r.save(RUN/'final-verification.json',result);print('Final correction-aware verification',result['checked_records'],'records;',len(jobs),'images',flush=True)

def write_csv(name,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row));path=RUN/(name+'.partial')
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    path.replace(RUN/name)

def report():
    final=r.load(RUN/'final-verification.json');assert final['painters']==200 and not final['errors']
    d.report();summary=r.load(RUN/'summary.json');alias=r.load(RUN/'alias-consolidation-applied.json')
    canonical={x['from']:x['to'] for x in alias['moves']};byartist={x['artist_id']:x for x in final['per_artist']}
    pairs={x['artist']['id']:x for x in m.cohort()};deliveries={x['artist']['id']:x for x,pin in d.pinned_deliveries()}
    image_by_source={im['source_id']:im for im,pin in image_jobs()}
    sources=[];related=[];created=[];source_counts=collections.Counter();pages_available=0;recovered=0
    # Broad aliases such as Clovio's "Don Giulio" produce unrelated sitter matches.
    # Use full canonical and source names for title relationships.
    names={aid:{s.normalized(n) for n in [p['artist']['display_name'],p['source']['name']] if len(s.normalized(n).split())>=2} for aid,p in pairs.items()}
    for data,pin in d.plans():
        artist=data['artist'];aid=artist['id'];delivery=deliveries[aid];accepted={x['source_id']:x for x in delivery['rows']}
        for row in data['rows']:
            page=row.get('page');sid=row.get('source_id');proposed=row.get('artwork_id');target=canonical.get(proposed,proposed)
            action=row['action'];reason=row.get('reason') or row.get('image_hold') or ''
            if proposed in delivery['held']:action='hold';reason=delivery['held'][proposed]
            elif sid in accepted:action='created_review' if row['action']=='create' else 'existing_matched'
            if proposed in canonical:action='existing_reconciled';reason='Reused older object after exact-source alias reconciliation; six redundant campaign records archived without deletion.'
            confidence=row.get('confidence')
            if proposed=='e39b5f86-77ed-57d2-bc69-27384b754fb0':
                confidence=.95;reason='Cross-creator duplicate reviewed: source Théo attribution supported by visible VR monogram; conflicting Cross entry held. See cross-creator-resolution.json; auction date qualification retained as evidence only.'
            im=image_by_source.get(sid);date=s.source_date(page) if page else None
            image_state='uploaded' if im else ('existing_image_preserved' if row.get('has_image') else 'none')
            if action in ['created_review','existing_matched','existing_reconciled'] and not im and not row.get('has_image'):
                if not date:image_state='undated_deferred';reason=reason or 'Source date unknown; retain review metadata and defer image.'
                else:
                    prep=RUN/'prepared-images'/(str(proposed)+'.json')
                    if prep.exists() and r.load(prep)['outcome']=='preparation_held':image_state='source_image_held';reason=r.load(prep).get('error') or 'Source below resolution threshold'
            if page:
                pages_available+=1
                if (RUN/'page-retries'/aid/(r.sha(page['url'].encode())+'.json.gz')).exists():recovered+=1
            rec={'artist':artist['display_name'],'artist_id':aid,'title':row.get('title',row.get('record',{}).get('index',{}).get('title')),
                 'source_url':row.get('source_url',row.get('record',{}).get('index',{}).get('url')),'source_id':sid,'action':action,
                 'artwork_id':target if sid in accepted else '', 'proposed_artwork_id':proposed,'source_date':date.get('date_display') if date else row.get('record',{}).get('index',{}).get('source_date'),
                 'source_date_raw':page['fields'].get('Date',page['metadata'].get('year')) if page else row.get('record',{}).get('index',{}).get('source_date'),
                 'source_rights_label':row.get('source_rights_label'),'editorial_identity_confidence':confidence,'image_state':image_state,'image_url':'https://artlines.org'+im['path'] if im else '',
                 'reason':reason,'candidate_ids':';'.join(row.get('candidate_ids',[])),'related_source_versions':';'.join(row.get('related_sources',[]))}
            sources.append(rec);source_counts[action]+=1
            if action=='created_review':created.append(rec)
            if page:
                title=' '+s.normalized(row['title'])+' '
                for subject,nameset in names.items():
                    if subject!=aid and any(' '+name+' ' in title for name in nameset):
                        related.append({'artist':pairs[subject]['artist']['display_name'],'artist_id':subject,'relation':'title_name_lead','creator':artist['display_name'],
                                        'title':row['title'],'artwork_id':target if sid in accepted else '', 'source_url':row['source_url'],
                                        'state':action,'basis':'Full artist name occurs in another sampled creator’s source title; subject/influence relation remains a research lead, not a creator reassignment.'})
        idx=r.load(RUN/'indexes'/(aid+'.json.gz'))
        for x in idx['items']:
            if x['date'] and x['date']['creation_year_start']>1970:
                sources.append({'artist':artist['display_name'],'artist_id':aid,'title':x['title'],'source_url':x['url'],'action':'excluded_after_1970','source_date':x['source_date'],'reason':'Source index explicitly dates creation after 1970; image not downloaded.'});source_counts['excluded_after_1970']+=1
    leads=r.load(RUN/'expanded-creator-leads.json');resolved={x['to'] for x in alias['moves']}
    for lead in leads:
        aid=lead['artist_id'];w=lead['artwork']
        related.append({'artist':pairs[aid]['artist']['display_name'],'artist_id':aid,'relation':'unlinked_creator_label','creator':w['unlinked_creator_label'],
                        'title':w['title'],'artwork_id':w['id'],'source_url':'',
                        'artwork_url':'https://artlines.org/artists/'+pairs[aid]['artist']['slug']+'/works/'+w['id'] if w['id'] in resolved else '',
                        'state':'creator_link_reconciled' if w['id'] in resolved else 'existing_review_lead',
                        'basis':'Existing object-level creator label matches a full-name/alias candidate; attribution and object identity require evidence before linking.'})
    uploaded=[{'artist':im['artist'],'artist_id':im['artist_id'],'artwork_id':canonical.get(im['artwork_id'],im['artwork_id']),'title':im['title'],
               'source_url':im['source_page_url'],'source_image_url':im['source_image_url'],'source_rights_label':im['source_rights_label'],'rights_status':im['rights_status'],
               'image_url':'https://artlines.org'+im['path'],'sha256':im['sha256'],'bytes':im['bytes'],'width':im['width'],'height':im['height'],'plan_sha256':pin} for im,pin in image_jobs()]
    assert len(sources)==14513 and len({x['source_url'] for x in sources})==14513
    supplemental=collections.Counter(im['artist_id'] for im in r.load(RUN/'supplemental-plan.json.gz')['images']) if (RUN/'supplemental-applied.json').exists() else collections.Counter()
    archives=collections.Counter(x['artist_id'] for x in alias['moves']);lead_counts=collections.Counter(x['artist_id'] for x in leads)
    for row in summary['painters_report']:
        aid=row['artist_id'];row.update(created_gross=row['created'],created=row['created']-archives[aid],redundant_new_records_archived=archives[aid],creator_links_added=archives[aid],
                                       images_added=row['images_added']+supplemental[aid],after_records=byartist[aid]['active_records'],after_images=byartist[aid]['images'],unlinked_creator_leads=lead_counts[aid])
    totals=summary['totals'];totals.update(created_gross=totals['created'],created=totals['created']-6,images_added=len(uploaded),after_records=final['unique_active_records'],after_images=final['unique_images'],
                                         before_records=final['baseline']['artworks'],before_images=final['baseline']['images'],unlinked_creator_leads=len(leads),creator_links_added=6,redundant_new_records_archived=6,
                                         title_relationship_leads=sum(x['relation']=='title_name_lead' for x in related),captured_source_pages=pages_available,recovered_source_pages=recovered,unavailable_source_pages=13665-pages_available)
    totals.update(concurrent_untargeted_artwork_changes=final['concurrent_untargeted_artwork_changes'],
                  concurrent_net_record_delta=totals['after_records']-totals['before_records']-totals['created']-6,
                  concurrent_net_image_delta=totals['after_images']-totals['before_images']-totals['images_added'])
    summary.update(complete=True,final_verification='final-verification.json',source_dispositions=dict(source_counts),at=r.now(),
                   related_scope='519 existing creator-label leads were retained and researched; six secure same-object creator links were repaired. Full-name references in titles across the captured cohort source inventory are exported as subject/relationship leads. This is not an exhaustive worldwide related-artwork catalogue.',
                   validation='Every delivered image was decoded, checked for dimensions, complete source aspect ratio, <=100000 bytes, checksums, exact rights evidence and duplicate reproductions. Visual QA uses documented per-painter samples plus all title/date existing matches and low-quality candidates; supplemental recoveries were all viewed. All 200 painter outcomes were verified in production. Painters receiving images were also checked through the bounded application API, with repeat API checks after corrections.',
                   limitations='Unresolved versions, creator attributions and unavailable source pages remain explicitly held. Complete WikiArt index coverage is not a catalogue raisonné. The 187.8 ms representative painter lookup does not establish performance at 10 million artworks; large-scale load benchmarking remains separate backend work.',
                   preservation='New active records remain in review. This operation preserved prior images, catalogue metadata, holdings, current-display claims and publication on all its targets; it wrote no painter biography fields. Concurrent changes to untargeted records are preserved and documented in concurrent-production-changes.json, and are separated from this campaign’s additions. Six redundant rows introduced by this operation were archived after reuse of older records; no records or media were deleted. No local database writes, commits or deployment.')
    for name,rows in [('painters.csv',summary['painters_report']),('source-dispositions.csv',sources),('related-artwork-leads.csv',related),('uploaded-images.csv',uploaded),('new-review-records.csv',created)]:write_csv(name,rows)
    temp=RUN/'summary.partial';temp.write_text(json.dumps(summary,ensure_ascii=False,indent=2));temp.replace(RUN/'summary.json')
    e=html.escape
    table=''.join('<tr>'+''.join('<td>'+e(str(row.get(k,'')))+'</td>' for k in ['artist','created','images_added','after_records','after_images','source_holds','delivery_holds','undated_image_holds'])+'</tr>' for row in summary['painters_report'])
    links=' · '.join('<a href="'+name+'">'+label+'</a>' for name,label in [('painters.csv','200 painters'),('uploaded-images.csv','Uploaded images'),('new-review-records.csv','New review records'),('source-dispositions.csv','All 14,513 source dispositions'),('related-artwork-leads.csv','Related artwork leads'),('final-verification.json','Verification'),('summary.json','Full summary')])
    page='<!doctype html><meta charset="utf-8"><title>200 painters — production import report</title><style>body{font:16px system-ui;max-width:1450px;margin:35px auto;padding:20px;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#eef2f4;position:sticky;top:0}</style><h1>200 painters — completed production import</h1><p>'+e(f"{totals['created']:,} net new review records · {len(uploaded):,} images added · 6 existing creator links repaired")+'</p><p>'+links+'</p>'
    for k in ['scope','date_policy','image_policy','preservation','related_scope','validation','limitations']:page+='<p>'+e(summary[k])+'</p>'
    page+='<p>'+e(f"Source coverage: 14,513 entries; {pages_available:,} captured pages, {13665-pages_available} unavailable pages, and 848 index-dated post-1970 works excluded before image selection. Production backup: 1791282469599 (SUCCESSFUL).")+'</p><table><thead><tr><th>Painter</th><th>Net new records</th><th>Images added</th><th>Total records</th><th>Total images</th><th>Source holds</th><th>Delivery holds</th><th>Undated image holds</th></tr></thead><tbody>'+table+'</tbody></table>'
    temp=RUN/'report.partial';temp.write_text(page);temp.replace(RUN/'report.html')
    print(json.dumps({'complete':True,'totals':totals,'source_dispositions':dict(source_counts)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['resolution','verify','report']);args=parser.parse_args();globals()[args.phase]()
