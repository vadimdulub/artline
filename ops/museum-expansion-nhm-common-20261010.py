"""National Historical Museum research context; real local catalogue read-only."""
import importlib.util
from pathlib import Path

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

base = module('base', 'museum-expansion-larissa-common-v2-20261010.py')
s, prod, m = base.s, base.prod, base.m
IID = '5d1bc5d4-0e01-5e7b-8669-1411c393a158'
IIDS = [IID]
s.IID, s.IIDS, s.PROTECT_IIDS = IID, IIDS, IIDS
RUN = m.RUN / 'native/nhm-20261010'
PREVIOUS = m.RUN / 'native/asfa-20261010'
DISCOVERY = m.RUN / 'native/athens-city-photographs-20261010/next-source-discovery-001.json.gz'
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/nhm-20261010'
CP = PREVIOUS / 'delivery-checkpoint-001.json'
CP_SHA = '4e6f5c677827ef1eb87afee59f7345301c4ad88014fbe6c8e5166c3f6e72c76e'
ref, checked, counts, snapshot = base.ref, base.checked, base.counts, base.snapshot
