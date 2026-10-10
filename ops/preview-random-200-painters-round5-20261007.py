#!/usr/bin/env python3
"""Freeze an offline review of the fifth batch; this performs no cloud writes."""
import collections,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('round_five',ROOT/'ops/run-random-200-round5-20261007.py');x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;RUN=x.RUN

def main():
    approved,visual=x.d.visual_decisions()
    image_holds=r.load(RUN/'manual-image-holds.json')['held_artwork_ids']
    manual=r.load(RUN/'manual-identity-holds.json')['held_artwork_ids']
    cross=r.load(RUN/'cross-creator-image-audit.json')['held_artwork_ids']
    additional=r.load(RUN/'additional-image-reference-audit.json')['held_artwork_ids']
    resolutions=r.load(RUN/'duplicate-review-resolutions-v2.json')['approved']
    outcomes=[];all_images=[];all_rows=[]
    for data,pin in x.d.plans():
        artist=data['artist'];audit=r.load(RUN/'image-audits'/(artist['id']+'.json'))
        assert audit['selection_pin']==pin
        assert set(audit['visual_sample_ids'])<=set(approved)|set(visual)
        ids={row['artwork_id'] for row in data['rows'] if row['action'] in ['create','existing']}
        holds={**audit['held_artwork_ids'],**{aid:reason for aid,reason in visual.items() if aid in audit['visual_sample_ids'] and aid not in image_holds}}
        for aid,decision in resolutions.items():
            if aid in audit['held_artwork_ids'] and aid not in visual:
                assert r.load(RUN/'prepared-images'/(aid+'.json'))['sha256']==decision['sha256']
                holds.pop(aid,None)
        for extra in [cross,additional,manual]:holds.update({aid:reason for aid,reason in extra.items() if aid in ids})
        rows=[row for row in data['rows'] if row['action'] in ['create','existing'] and row['artwork_id'] not in holds]
        targets={row['artwork_id'] for row in x.d.image_rows(data)}-set(image_holds)-set(holds)
        images=[r.load(RUN/'prepared-images'/(aid+'.json')) for aid in targets]
        for im in images:
            assert im['outcome']=='prepared' and im['selection_pin']==pin
            raw=Path(im['visual_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and r.sha(raw)==im['sha256']
        all_images.extend(images);all_rows.extend(rows)
        outcomes.append({'artist':artist['display_name'],'artist_id':artist['id'],'source_entries':len(r.load(RUN/'indexes'/(artist['id']+'.json.gz'))['items']),'new_review_records':sum(row['action']=='create' for row in rows),'existing_source_matches':sum(row['action']=='existing' for row in rows),'images':len(images),'identity_holds':len(holds),'image_only_holds':sum(row['artwork_id'] in image_holds for row in rows)})
    assert len(outcomes)==200
    assert len(all_images)==len({im['artwork_id'] for im in all_images})==len({im['sha256'] for im in all_images})
    assert len(all_rows)==len({row['artwork_id'] for row in all_rows})==len({row['source_id'] for row in all_rows})
    totals={key:sum(row[key] for row in outcomes) for key in ['source_entries','new_review_records','existing_source_matches','images','identity_holds','image_only_holds']}
    assert totals['source_entries']==12690
    summary={'at':r.now(),'operation':x.m.OP,'status':'prepared_awaiting_google_cloud_reauthentication','production_written':False,'painters':200,'totals_before_fresh_production_conflict_check':totals,'actual_image_rights':dict(collections.Counter(im['rights_status'] for im in all_images)),'maximum_derivative_bytes':max(im['bytes'] for im in all_images),'quality_review_sha256':r.sha((RUN/'quality-final-review.json').read_bytes()),'painters_report':outcomes,'limitations':'Offline proposed counts. Fresh production snapshots, capacity check and pinned delivery plans must complete after Google Cloud sign-in. No catalogue or image upload has been performed by this batch. Concurrent production changes may reduce the final counts.'}
    r.save(RUN/'prepared-batch-review.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='painters_report'}),flush=True)
if __name__=='__main__':main()
