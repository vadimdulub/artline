#!/usr/bin/env python3
"""Freeze completed, individually recorded review decisions before any delivery."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('round_six',ROOT/'ops/run-random-200-round6-20261007.py');x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;RUN=x.RUN

def main():
    quality=r.load(RUN/'quality-final-candidates.json');assert quality['painters']==200
    plans=list(x.d.plans());assert len(plans)==200
    byid={row['artwork_id']:row for data,pin in plans for row in data['rows'] if row['action'] in ['create','existing']}
    records={};identity={};image_holds={};leads=[];files={}
    for path in sorted((RUN/'editorial-review-decisions').glob('*.json')):
        data=r.load(path);files[str(path.relative_to(ROOT))]=r.sha(path.read_bytes())
        for aid,note in data['records'].items():
            assert aid in byid and aid not in records,('Repeated/unselected editorial decision',aid)
            row=byid[aid]
            assert note['source_url']==row['source_url']
            records[aid]={**note,'at':data['at'],'source_receipt':row['page']['receipt'],'decision_file':str(path.relative_to(ROOT)),'decision_file_sha256':files[str(path.relative_to(ROOT))]}
            if note.get('hold_record'):identity[aid]=note['reason']
            if note.get('image_hold_only'):image_holds[aid]=note['reason']
        leads.extend(data.get('related_leads',[]))
    assert not set(identity)&set(image_holds)
    for key in ['lifespan_or_qualified_creator','title_review_candidates','architectural_version_candidates']:
        missing=[v for v in quality[key] if v['artwork_id'] not in records]
        assert not missing,('Unreviewed quality flags',missing)
    approved,held=x.d.visual_decisions()
    batches=list((RUN/'visual-batches').glob('*.json'));assert len(batches)==len(list((RUN/'visual-reviews').glob('*.json')))
    for data,pin in plans:
        audit=r.load(RUN/'image-audits'/(data['artist']['id']+'.json'))
        assert set(audit['visual_sample_ids'])<=set(approved)|set(held)
    resolutions={};pair_reviews=[]
    for path in sorted((RUN/'duplicate-review-decisions').glob('*.json')):
        data=r.load(path);files[str(path.relative_to(ROOT))]=r.sha(path.read_bytes())
        for aid,value in data['approved'].items():
            assert aid not in resolutions
            assert value['sha256']==r.load(RUN/'prepared-images'/(aid+'.json'))['sha256']
            assert r.sha(Path(value['visual_evidence']).read_bytes())==value['sheet_sha256']
            resolutions[aid]=value
        pair_reviews.extend(data['pairs'])
    audited={tuple(sorted(g['ids'])) for path in (RUN/'image-audits').glob('*.json') for g in r.load(path)['duplicate_groups']}
    reviewed={tuple(sorted(v['artwork_ids'])) for v in pair_reviews}
    assert audited<=reviewed,('Unreviewed duplicate pairs',audited-reviewed)
    now=r.now()
    outputs={
      'reviewed-source-discrepancies.json':{'at':now,'records':records},
      'manual-identity-holds.json':{'at':now,'held_artwork_ids':identity,'scope':'Individually reviewed attribution/edition identities; no removal of existing records.'},
      'manual-image-holds.json':{'at':now,'held_artwork_ids':image_holds,'scope':'Keep named source metadata as review records while image/version/date scope remains unresolved; actual source rights are not the reason for these holds.'},
      'creator-conflict-relationship-leads.json':{'at':now,'rows':leads},
      'duplicate-review-resolutions-v2.json':{'at':now,'approved':resolutions,'scope':'Only hash-pinned, individually viewed pairs with equivalent titles, dates and composition can retain one canonical source record. All other duplicate/identity holds remain.'},
      'quality-final-review.json':{'at':now,'painters':200,'candidate_sha256':r.sha((RUN/'quality-final-candidates.json').read_bytes()),'all_title_and_architectural_candidates_reviewed':True,'lifespan_flags_reviewed':len(quality['lifespan_or_qualified_creator']),'title_flags_reviewed':len(quality['title_review_candidates']),'architectural_flags_reviewed':len(quality['architectural_version_candidates']),'visual_sheets_reviewed':len(batches),'visual_samples_approved':len(approved),'visual_samples_held':len(held),'source_notes':len(records),'identity_holds':len(identity),'image_only_holds':len(image_holds),'duplicate_pairs_reviewed':len(audited),'individual_review_files':files}}
    for name,value in outputs.items():r.save(RUN/name,value)
    print('Frozen review:',len(records),'source notes;',len(identity),'identity holds;',len(image_holds),'image-only holds;',len(batches),'visual sheets;',len(audited),'duplicate pairs',flush=True)
if __name__=='__main__':main()
