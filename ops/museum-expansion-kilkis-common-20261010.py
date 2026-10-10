"""Kilkis selected delivery context and bounded read-only snapshot helpers."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='4f3ac99d-d622-591d-8885-ac14362fbb50';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/kilkis-delivery-20261010';RESEARCH=m.RUN/'native/kilkis-review-20261010';DATED=m.RUN/'native/kilkis-20261010'
CP=m.RUN/'native/zongolopoulos-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='762dab88b21af3967713e342b39b16007228d6ec92b107e45700245f8ea60267'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json'
RESEARCH_SHA='b224245951d11814db9dcc2104b868f2b2600c7f7998c066097b4c6000a07f9e'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot

def research_verify():
    assert ref(CP)['sha256']==CP_SHA
    refs=[(RESEARCH_CP,RESEARCH_SHA)]
    outputs=[]
    for path,digest in refs:
        assert ref(path)['sha256']==digest
        cp=m.load(path)
        for pin in cp['artifacts']:checked(pin)
        for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
        outputs.append(dict(checkpoint=ref(path),artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts'])))
    return outputs
