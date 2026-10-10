"""ASFA museum research context; local catalogue remains read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='fe94f502-f226-56ad-89b1-e6a8fa4dd44e';IIDS=[IID];s.IID=IID;s.IIDS=IIDS;s.PROTECT_IIDS=IIDS
RUN=m.RUN/'native/asfa-20261010';PREVIOUS=m.RUN/'native/athens-city-photographs-20261010'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/asfa-20261010'
CP=PREVIOUS/'delivery-checkpoint-001.json';CP_SHA='583198eeb7fb961edf102cc4bcebc316610f31c12b79a4061d95fdf24ba5cadc'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
