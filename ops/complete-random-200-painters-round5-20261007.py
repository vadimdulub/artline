#!/usr/bin/env python3
"""Resume the authorized fifth batch after account sign-in and proxy startup."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def main():
    x=module('round_five','run-random-200-round5-20261007.py')
    assert x.r.load(x.RUN/'quality-final-review.json')['painters']==200
    x.d.delivery_plans()
    x.preflight()
    pre=x.r.load(x.RUN/'production-preflight.json')
    assert pre['painters']==200 and not pre['errors']
    x.d.upload()
    x.d.apply()
    assert len(list((x.RUN/'applied').glob('*.json')))==200
    x.d.verify()
    assert len(list((x.RUN/'verified').glob('*.json')))==200
    final=module('round_five_final','finalize-random-200-painters-round5-20261007.py')
    final.verify();final.report()
    check=module('round_five_check','check-random-200-painters-round5-20261007.py')
    check.main()

if __name__=='__main__':main()
