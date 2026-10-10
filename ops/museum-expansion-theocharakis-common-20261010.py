"""Theocharakis selected delivery context and bounded read-only snapshot helpers."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='71238d8f-08c1-5637-9f68-b89d17dd9c62';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/theocharakis-delivery-20261010';RESEARCH=m.RUN/'native/theocharakis-20261010';DATED=m.RUN/'native/theocharakis-dated-20261010'
CP=m.RUN/'native/chania-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='6271b1b69d41f9aeb0f9aab4fc42b3478baae6cb9639e9c7e8993f69a0e671d8'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json'
RESEARCH_SHA='111102ce42532f27023cc3b2c22f580a547efc232896982933b4618b499dc8ba'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot

def research_verify():
    assert ref(CP)['sha256']==CP_SHA
    refs=[(RESEARCH_CP,RESEARCH_SHA),(DATED/'research-checkpoint-001.json','19104950752f9be76c22d8cbf159f569f38ad56ab5c78b24b807ba6e7a5423ec')]
    outputs=[]
    for path,digest in refs:
        assert ref(path)['sha256']==digest
        cp=m.load(path)
        for pin in cp['artifacts']:checked(pin)
        for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
        outputs.append(dict(checkpoint=ref(path),artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts'])))
    return outputs
