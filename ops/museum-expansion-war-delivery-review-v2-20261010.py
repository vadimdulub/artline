"""Correct two object_form values to observed schema; preserve cast/replica evidence."""
import copy,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-war-delivery-review-20261010.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
c,m,RUN,KEY,THALIA,ROILOS,AUTHORITIES,artist_link=(getattr(base,x) for x in ['c','m','RUN','KEY','THALIA','ROILOS','AUTHORITIES','artist_link'])

def build():
    records,holdings=base.build()
    for v in records:
        f=v['facts']
        if f['number'] in [184,185]:
            assert f['object_form'] in ['cast replica','stele (replica identity to review)'];f['object_form']=None
            f['source_facts']['review_notes'].append('Schema correction: object_form only permits icon or null. Cast/replica classification remains in work_type sculpture, description and preserved source_facts.object_form; no schema extension or source evidence loss.')
    assert all(v['facts']['object_form'] in [None,'icon'] for v in records)
    return records,holdings

def main():
    dest=RUN/'editorial-reviewed-002.json.gz';assert not dest.exists();previous=m.load(RUN/'editorial-reviewed-001.json.gz');rollback=m.load(RUN/'rolled-back-apply-001.json');assert rollback['new_records']==rollback['new_sources']==rollback['new_audits']==0 and rollback['preflight_unchanged']
    assert any(x['conname']=='artwork_object_form' and "'icon'" in x['definition'] for x in rollback['constraints'])
    records,holdings=build();old={v['facts']['number']:v for v in previous['records']}
    for v in records:
        n=v['facts']['number']
        if n not in [184,185]:assert v==old[n]
    result=copy.deepcopy(previous);result.update(at=m.now(),records=records,holdings=holdings,script_reference=c.ref(Path(__file__).resolve()))
    result['dependencies']+= [c.ref(RUN/'editorial-reviewed-001.json.gz'),c.ref(RUN/'rolled-back-apply-001.json')]
    result['review']['schema_correction']='Two sculpture object_form labels changed to null because database only permits icon or null. Cast/replica descriptions, sourcefacts and all other records/images unchanged. Original apply rolled back before any committed catalogue rows;90uploadedfiles remain reusable and unattached.'
    result['review']['prior_apply_rollback_verified']=True
    m.save(dest,result);print(json.dumps(dict(corrected_numbers=[184,185],new_records=len(records),unchanged_images=len(result['images']))),flush=True)

if __name__=='__main__':main()
