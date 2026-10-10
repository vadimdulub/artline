"""Athens City photograph selection after the verified135-artwork delivery."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

base=module('base','museum-expansion-athens-city-delivery-common-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID=base.IID;IIDS=[IID]
RUN=m.RUN/'native/athens-city-photographs-20261010'
PREVIOUS=m.RUN/'native/athens-city-delivery-20261010'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/athens-city-photographs-20261010'
CP=PREVIOUS/'delivery-checkpoint-001.json';CP_SHA='6f7061802080f49bd112a02f61e0d283a49dab9963e1801475b0afdd91244667'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
