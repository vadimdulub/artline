"""Chania selected delivery context and bounded read-only snapshot helpers."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='80780566-c37f-51e6-a861-f43c834027d8';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/chania-delivery-20261010';RESEARCH=m.RUN/'native/chania-20261010'
CP=m.RUN/'native/larissa-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='c070e8bf1ff48ebb542de210bb228f3236db5f42c539f56ed12120afd5f12376'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json'
RESEARCH_SHA='e4b9d345081aed5a1d1167b347d3472087291e2558e1c2fc1fa7f15a8629076a'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot

def research_verify():
    assert ref(CP)['sha256']==CP_SHA and ref(RESEARCH_CP)['sha256']==RESEARCH_SHA
    cp=m.load(RESEARCH_CP)
    for pin in cp['artifacts']:checked(pin)
    for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
    return dict(artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts']))
