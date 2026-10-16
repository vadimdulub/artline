"""MOMus selected collection context; real local catalogue read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='fbb86dfe-de37-5942-b762-0585ae753b31';IIDS=[IID]
s.IID,s.IIDS,s.PROTECT_IIDS=IID,IIDS,IIDS
RUN=m.RUN/'native/momus-20261011'
PREVIOUS=m.RUN/'native/jewish-20261010'
DISCOVERY=PREVIOUS/'next-source-discovery-001.json.gz'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/momus-20261011'
CP=PREVIOUS/'delivery-checkpoint-001.json'
CP_SHA='be7f3a689452611f89ced4a724d32818c36fa45961a0033e7a0a7e771575eea1'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
