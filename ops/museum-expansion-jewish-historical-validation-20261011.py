"""Read-only verification of completed W134 against preserved historical policies."""
import hashlib,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-jewish-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,r,RUN,PLAN,REVIEW,sha=a.c,a.m,a.r,a.RUN,a.PLAN,a.REVIEW,a.sha

def historical_checked(pin):
    rows={x['logical_path']:x for x in m.load(RUN/'historical-policy-reconciliation-001.json')['rows']}
    if pin['path'] not in rows:return c.checked(pin)
    row=rows[pin['path']];assert pin==row['inherited_pin']
    historical=row['plan_used_byte_copy'];assert sha(historical['path'])==pin['sha256']==historical['sha256']
    assert sha(row['current_observed_byte_copy']['path'])==row['current_pin']['sha256']
    return Path(historical['path'])

def validate_plan():
    p=m.load(PLAN);digest=sha(PLAN);assert p['review_reference']==c.ref(REVIEW)
    for pin in p['evidence']:historical_checked(pin)
    for pin in p['external_evidence']:assert sha(pin['path'])==pin['sha256'],pin['path']
    review=m.load(REVIEW);rebuilt,holdings=r.build();assert rebuilt==p['records']==review['records'] and not holdings
    assert len(p['records'])==140 and len(p['images'])==131 and len(p['prior_ids'])==2798
    assert sum(len(v['facts']['source_ids']) for v in p['records'])==143
    assert len({v['artwork_id'] for v in p['records']})==140
    assert len({s for v in p['records'] for s in v['facts']['source_ids']})==143
    assert len({x['sha256'] for x in p['images']})==131 and {x['artwork_id'] for x in p['images']}<={v['artwork_id'] for v in p['records']}
    assert sum(v['facts']['first'] is None for v in p['records'])==5
    assert sum(v['facts']['first'] is not None and v['facts']['last']>1970 for v in p['records'])==1
    for im in p['images']:
        assert im['first'] is not None and im['last']<=1955 and im['date_policy_passed'] and im['bytes']<=100000
        assert sha(im['prepared_path'])==im['sha256'] and sha(im['original_reference']['path'])==im['original_reference']['sha256'] and im['rights_status']=='restricted' and im['rights_label']=='In Copyright (InC)'
    return p,digest
