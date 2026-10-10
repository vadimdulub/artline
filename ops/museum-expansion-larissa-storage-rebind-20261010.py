"""Carry unchanged uploaded bytes into the schema-correct plan with full provenance."""
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('museum-expansion-larissa-reconciled-v2-20261010.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,c,m,RUN=b.a,b.c,b.m,b.RUN

def main():
    oldp=b.b.a.PLAN;old,digest0=b.b.a.validate_plan();new,digest=a.validate_plan()
    assert digest0=='145286e3507a7cb58c4eddfda1e560057e8cfcb96a59041c7898916b093dffd4'
    for key in ['records','holdings','images','before','before_counts','scoped_ids','prior_ids','prior_state','expected_counts']:
        assert old[key]==new[key],key
    uploaded=m.load(RUN/'storage-upload-001.json');assert uploaded['plan_sha256']==digest0 and len(uploaded['checks'])==205
    checks=[]
    for im,check in zip(new['images'],uploaded['checks']):
        assert check['media_id']==im['media_id'] and check['sha256']==im['sha256'] and check['path']==im['storage_path'] and check['plan_sha256']==digest0
        checks.append(dict(check,plan_sha256=digest,original_upload_plan_sha256=digest0))
    assert len({(v['artwork_id'],sid) for v in new['records'] for sid,url in a.identifier_values(v)})==184
    assert sum(len(v['facts']['source_ids']) for v in new['records'])==195
    m.save(RUN/'storage-upload-002.json',dict(at=m.now(),plan_sha256=digest,checks=checks,original_upload_reference=c.ref(RUN/'storage-upload-001.json'),old_plan_reference=c.ref(oldp),new_plan_reference=c.ref(a.PLAN),uploaded_bytes_unchanged=True,no_new_uploads=True,reason='Only the album database identifier representation changed; records, holdings, media IDs, paths, bytes and all source facts are identical.',script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(plan_sha256=digest,images_preserved=205,canonical_external_identifiers=184,source_records_preserved=195)),flush=True)

if __name__=='__main__':main()
