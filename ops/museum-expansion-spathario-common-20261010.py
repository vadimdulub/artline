"""Spathario selected collection context; real local database read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='ecc56326-95ff-5063-9e7c-defe30001f0f';IIDS=[IID]
s.IID,s.IIDS,s.PROTECT_IIDS=IID,IIDS,IIDS
RUN=m.RUN/'native/spathario-20261010'
PREVIOUS=m.RUN/'native/war-20261010'
DISCOVERY=m.RUN/'native/nhm-20261010/next-source-discovery-001.json.gz'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/spathario-20261010'
CP=PREVIOUS/'delivery-checkpoint-001.json'
CP_SHA='a0ee3d529e59179bf7e4c2216d9933b358111e517f8db15547e6502bba33f6a5'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
