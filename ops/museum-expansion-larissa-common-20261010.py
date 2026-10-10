"""Read-only Larissa delivery context; immutable research and production references."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

s=module('s','museum-expansion-kazantzakis-more-common-20261009.py')
prod=module('prod','catalogue-expansion-20261008.py')
m=s.m
IID='d843489b-7a33-5cbb-916a-4eecb0dac8b8'
IIDS=[IID];s.IIDS=IIDS;s.IID=IID;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/larissa-delivery-20261010'
RESEARCH=m.RUN/'native/larissa-20261010'
CP=m.RUN/'native/kazantzakis-more-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='a3bc1331a543ec266e70385db31f5384396ee54f273b0de1b612997bc4495c49'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json'
RESEARCH_SHA='593f52af993318a98fc5de549d43f9160608de9621ca8e5222cdec2d1e6ea8d1'
ref=s.ref;checked=s.checked;counts=s.counts

def snapshot(db,ids):
    out=s.snapshot(db,ids)
    mids=[v['id'] for v in out['media_assets']]
    out['media_rights_evidence']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_rights_evidence x WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id,id',(mids,))]
    return out

def research_verify():
    assert ref(CP)['sha256']==CP_SHA and ref(RESEARCH_CP)['sha256']==RESEARCH_SHA
    cp=m.load(RESEARCH_CP)
    for pin in cp['artifacts']:checked(pin)
    for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
    return dict(artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts']))
