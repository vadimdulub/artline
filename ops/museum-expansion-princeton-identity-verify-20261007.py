#!/usr/bin/env python3
"""Recompute frozen identity comparisons once; pin inputs for later delivery checks."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-princeton-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m
def main():
 candidate=i.RUN/'native-candidates-002.json.gz';identity=i.RUN/'native-identity-002.json.gz';dest=i.RUN/'identity-recomputed-001.json';assert not dest.exists()
 rows=m.load(candidate)['rows'];x=m.load(identity)
 for dep in [x['query_reference'],x['base_query_reference']]:i.f.checked(dep)
 assert x['candidate_reference']==i.ref(candidate) and x['params']==i.params_for(rows)
 assert x['comparisons']==i.comparisons(rows,x['state'])
 m.save(dest,dict(at=m.now(),validator_reference=i.ref(Path(__file__).resolve()),candidate_reference=i.ref(candidate),identity_reference=i.ref(identity),query_references=[x['query_reference'],x['base_query_reference']],comparisons_recomputed_equal=True,rows=len(rows),policy='Actual full recomputation of frozen comparisons and parameters. Subsequent checks pin these immutable inputs and separately requery live database preimages before writes; no repeated quadratic comparison calculation is needed.'))
 print(json.dumps(dict(comparisons_recomputed_equal=True,rows=len(rows))),flush=True)
if __name__=='__main__':main()
