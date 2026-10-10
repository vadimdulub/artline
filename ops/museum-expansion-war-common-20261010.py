"""Athens War Museum context; selected production work, real local catalogue read-only."""
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

base=module('base','museum-expansion-larissa-common-v2-20261010.py')
s,prod,m=base.s,base.prod,base.m
IID='a4b7823c-f659-5413-9766-60c2306d8844';IIDS=[IID]
s.IID,s.IIDS,s.PROTECT_IIDS=IID,IIDS,IIDS
RUN=m.RUN/'native/war-20261010'
PREVIOUS=m.RUN/'native/nhm-20261010'
DISCOVERY=PREVIOUS/'next-source-discovery-001.json.gz'
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/war-20261010'
CP=PREVIOUS/'delivery-checkpoint-001.json'
CP_SHA='9cfd59401cd4d758e484a803d24700a144c853f63e6a8f87e7ea5659bade5655'
ref,checked,counts,snapshot=base.ref,base.checked,base.counts,base.snapshot
