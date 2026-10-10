"""Jewish Museum of Greece selected collection context; real local catalogue read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='760b0104-19ee-5ad1-94f0-0ceb8dcea09e';IIDS=[IID]
s.IID,s.IIDS,s.PROTECT_IIDS=IID,IIDS,IIDS
RUN=m.RUN/'native/jewish-20261010'
PREVIOUS=m.RUN/'native/spathario-20261010'
DISCOVERY=PREVIOUS/'next-source-discovery-001.json.gz'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/jewish-20261010'
CP=PREVIOUS/'delivery-checkpoint-001.json'
CP_SHA='ee56868d8c16bae7ad6162d4b791d28bdbbcabaf2a0ce7792acae17d1cdb05a3'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
