"""Athens City research context; the real local catalogue remains read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='f575847e-47eb-59e4-b558-32d8723bc3c9';IIDS=[IID]
s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/athens-city-20261010'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/athens-city-20261010'
CP=m.RUN/'native/kilkis-delivery-20261010/delivery-checkpoint-001.json'
CP_SHA='55a63267263c72d1edd4afc1c8ee0d369e692f4ec13f488331c91e65fc3e1e8b'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
