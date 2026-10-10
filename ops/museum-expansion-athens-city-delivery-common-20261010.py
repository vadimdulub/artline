"""Selected Athens City delivery context; research evidence remains immutable."""
import hashlib
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='f575847e-47eb-59e4-b558-32d8723bc3c9';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/athens-city-delivery-20261010';RESEARCH=m.RUN/'native/athens-city-20261010'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/athens-city-delivery-20261010'
CP=m.RUN/'native/kilkis-delivery-20261010/delivery-checkpoint-001.json';CP_SHA='55a63267263c72d1edd4afc1c8ee0d369e692f4ec13f488331c91e65fc3e1e8b'
RESEARCH_CP=RESEARCH/'research-checkpoint-001.json';RESEARCH_SHA='4bbb9a000df2734d1609dac73899ac06ba6eb3d309e50deaf52b7ce309b9479d'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot

def research_verify():
    assert ref(CP)['sha256']==CP_SHA and ref(RESEARCH_CP)['sha256']==RESEARCH_SHA
    cp=m.load(RESEARCH_CP)
    for pin in cp['artifacts']:checked(pin)
    for pin in cp['external_artifacts']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256'],pin['path']
    return dict(checkpoint=ref(RESEARCH_CP),artifact_pins=len(cp['artifacts']),external_pins=len(cp['external_artifacts']))
