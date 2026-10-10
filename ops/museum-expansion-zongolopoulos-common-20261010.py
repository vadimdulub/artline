"""Zongolopoulos selected delivery context and bounded read-only snapshot helpers."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='763803c5-3657-5d75-9cf8-9927a5c6a4de';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/zongolopoulos-delivery-20261010';RESEARCH=m.RUN/'native/zongolopoulos-20261010';DATED=m.RUN/'native/zongolopoulos-paintings-20261010'
CP=m.RUN/'native/theocharakis-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='36cd7e7b1ca4a9ce50552ca5fe2e819677dc5e35fddb3147632f6ba083cd57fb'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json'
RESEARCH_SHA='32b31e616cf63bd20a1edc62468fe01fb6c23fea9a8474e4b8aa91419402582e'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot

def research_verify():
    assert ref(CP)['sha256']==CP_SHA
    refs=[(RESEARCH_CP,RESEARCH_SHA),(DATED/'research-checkpoint-001.json','b62abdfbe4fa05e5309431b9e78baae7baea6859403f47f9a4d3d58ef060c49c')]
    outputs=[]
    for path,digest in refs:
        assert ref(path)['sha256']==digest
        cp=m.load(path)
        for pin in cp['artifacts']:checked(pin)
        for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
        outputs.append(dict(checkpoint=ref(path),artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts'])))
    return outputs
