#!/usr/bin/env python3
"""Recompute frozen comparisons and literal facts, without any database writes."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-fourth-identity-v2-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
def main():
    m=i.m;dest=i.RUN/'identity-recomputed-002.json';assert not dest.exists();cp=i.RUN/'native-candidates-001.json.gz';ip=i.RUN/'native-identity-002.json.gz';x=m.load(cp);y=m.load(ip)
    for dep in x['dependencies']+[x['parser_reference'],y['query_reference'],y['base_query_reference']]:i.checked(dep)
    assert y['candidate_reference']==i.ref(cp) and y['params']==i.params_for(x['rows'])
    for row in x['rows']:assert row==i.f.parse(row['index'],i.checked(row['source_reference']))
    assert i.comparisons(x['rows'],y['state'])==y['comparisons']
    m.save(dest,dict(at=m.now(),validator_reference=i.ref(Path(__file__).resolve()),candidate_reference=i.ref(cp),identity_reference=i.ref(ip),rows=len(x['rows']),literal_facts_reparsed_equal=True,comparisons_recomputed_equal=True,read_only=True))
    print(str(len(x['rows']))+' literal records and indexed comparisons recomputed identically',flush=True)
if __name__=='__main__':main()
