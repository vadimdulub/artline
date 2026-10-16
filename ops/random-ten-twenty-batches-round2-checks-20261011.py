#!/usr/bin/env python3
"""Round-two delivery checks, including grouped personal-selection display ranks."""
import importlib.util,json,collections,re
from pathlib import Path
sp=importlib.util.spec_from_file_location('d','ops/random-ten-twenty-batches-round2-delivery-20261011.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
s=d.s;m=d.m;r=d.r;q=d.q;RUN=d.RUN;BACKUP=d.BACKUP
PRIOR_RUNS=[d.ROOT/entry['path'] for entry in r.load(RUN/'sampling-frame.json.gz')['prior_cohorts']]
PRIOR_RUNS=[path.parent for path in PRIOR_RUNS]

def preflight():
    """Check the complete frozen delivery without mutating production."""
    dest=RUN/'production-preflight.json'
    if dest.exists():print('Preserving production preflight',flush=True);return
    expected_count=len(m.cohort())
    deliveries=list(d.pinned_deliveries());assert len(deliveries)==expected_count
    pairs=m.cohort();previous=[pair for folder in PRIOR_RUNS for pair in r.load(folder/'cohort.json')['painters']]
    assert len({v['artist']['id'] for v in pairs})==expected_count
    assert not {v['artist']['id'] for v in pairs}&{v['artist']['id'] for v in previous}
    assert not {v['source']['url'] for v in pairs}&({v['source']['url'] for v in previous}|{'https://www.wikiart.org/en/otto-dix'})
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    approved,visual_holds=d.visual_decisions()
    quality=r.load(RUN/'quality-final-candidates.json')
    quality_review=r.load(RUN/'quality-final-review.json')
    assert quality['painters']==quality_review['painters']==expected_count
    assert quality_review['candidate_sha256']==r.sha((RUN/'quality-final-candidates.json').read_bytes())
    assert quality_review['all_title_and_architectural_candidates_reviewed']
    rows=[row for data,pin in deliveries for row in data['rows']]
    images=[im for data,pin in deliveries for im in data['images']]
    assert len(rows)==len({row['artwork_id'] for row in rows})==len({row['source_id'] for row in rows})
    assert len(images)==len({im['artwork_id'] for im in images})==len({im['sha256'] for im in images})
    row_by_id={row['artwork_id']:row for row in rows}
    for issue in quality['lifespan_or_qualified_creator']:
        row=row_by_id.get(issue['artwork_id'])
        assert row is None or row.get('reviewed_source_discrepancy'),'Unreviewed creator/date anomaly'
    for data,pin in deliveries:
        assert set(data['image_audit']['visual_sample_ids'])<=set(approved)|set(visual_holds)
        for row in data['rows']:
            assert row['confidence']>=.90
            if row.get('reviewed_source_discrepancy',{}).get('creation_date_unresolved'):
                assert row['action']=='create' and row['page']['reviewed_date_classification']=='unknown'
                assert s.source_date(row['page']) is None and row['page']['date'] is None
                assert row['work']['creation_year_start'] is None and row['work']['creation_year_end'] is None
                assert row['work']['date_precision']=='unknown' and row['work']['date_display']=='Unknown date'
                assert row['image_hold'] and row['artwork_id'] not in {im['artwork_id'] for im in images}
            assert row['page']['metadata']['artistUrl']==m.urlsplit(next(v['source']['url'] for v in pairs if v['artist']['id']==row['artist_id'])).path
            scheme=row.get('source_scheme','wikiart-artwork')
            if scheme=='wikiart-legacy-content-id':
                assert row['action']=='create' and row['page']['source_kind']=='artist_index_entry'
                entry=row['index_entry'];meta=row['page']['legacy_api_metadata']
                assert row['source_id']==str(meta['contentId']) and row['source_id'].isdigit()
                assert row['title']==entry['title']==meta['title']
                assert entry['source_date']==str(meta['yearAsString'])
                assert row['page']['date']==entry['date'] and row['image_hold']
                assert row['page']['metadata']['image'] is None and row['page']['metadata']['_id'] is None
                assert row['work']['work_type']=='unknown'
                assert row['work']['medium_text'] is None and row['work']['dimensions_text'] is None
                assert row.get('reviewed_source_discrepancy') and row['artwork_id'] not in {im['artwork_id'] for im in images}
                assert entry in r.load(RUN/'unlinked-index-entries.json.gz')
                api=r.load(RUN/'translations'/(row['artist_id']+'-en.json.gz'))
                assert any({k:v for k,v in item.items() if k!='image'}==meta for item in api['items'])
            else:
                assert scheme=='wikiart-artwork' and re.fullmatch('[0-9a-f]{24}',row['source_id'])
            if row['action']=='existing':assert row['artwork_id'] in data['preimages']
        for im in data['images']:
            row=row_by_id[im['artwork_id']];date=s.source_date(row['page'])
            assert date and date['creation_year_end']<=1970 and not row.get('has_image') and not row.get('image_hold')
            assert im['artwork_id'] not in data['held'] and im['artwork_id'] not in visual_holds
            assert im['rights_status']==row['rights_status'] and im['source_rights_label']==row['source_rights_label']
            assert im['rights_status']==('public_domain' if im['source_rights_label']=='Public domain' else ('unknown' if im['source_rights_label']=='Rights label not supplied' else 'restricted'))
            if im.get('source_display_placeholder'):assert approved.get(im['artwork_id'])==im['sha256']
            raw=Path(im['visual_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and r.sha(raw)==im['sha256']
            if row['action']=='existing':assert data['preimages'][im['artwork_id']]['artwork']['primary_media_id'] is None
    new=sum(row['action']=='create' for row in rows)
    positions_needed=sum(any(row['action']=='create' for row in data['rows'][start:start+40]) for data,pin in deliveries for start in range(0,len(data['rows']),40))
    with r.connect('production') as db:
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(m.COLLECTION,)).fetchone()['n']
        assert position+positions_needed<=100000
    result={'at':r.now(),'painters':expected_count,'overlap_with_previous_cohorts_or_otto_dix':0,'records':len(rows),'new_review_records':new,
        'existing_records':len(rows)-new,'images':len(images),'actual_rights_labels':dict(collections.Counter(im['rights_status'] for im in images)),
        'visual_samples_approved':len(approved),'visual_samples_held':len(visual_holds),'display_placeholder_images_individually_reviewed':sum(bool(im.get('source_display_placeholder')) for im in images),
        'maximum_derivative_bytes':max(im['bytes'] for im in images),'collection_position_before':position,'position_groups_needed':positions_needed,'remaining_position_groups':100000-position-positions_needed,'selection_position_policy':'Each transaction group shares one append-only display position. Existing ranks and membership are unchanged; position is nonunique by schema and does not cap artwork count.',
        'successful_cloud_backup':r.load(BACKUP/'cloud-backup.json')['id'],'checks':['Immutable selection and delivery pins','Artist and artwork source identity','Creation-date image scope','Source rights distinct from approval','No existing-image replacement','Full QA sample accounting','Unique delivery artwork IDs, source IDs and image checksums','Derivative byte bounds and checksums','Owner collection capacity'],'errors':[]}
    r.save(dest,result);print(json.dumps(result),flush=True)

if __name__=='__main__':preflight()
