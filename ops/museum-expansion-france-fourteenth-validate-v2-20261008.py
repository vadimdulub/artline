"""Reparse immutable candidates and independently recompute supplemental comparisons."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-fourteenth-identity-v2-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
def main():
    m=i.m;dest=i.RUN/'identity-recomputed-002.json';assert not dest.exists()
    cp=i.RUN/'native-candidates-001.json.gz';ip=i.RUN/'native-identity-002.json.gz';x=m.load(cp);y=m.load(ip)
    for dep in x['dependencies']+[x['parser_reference'],y['query_reference'],y['base_query_reference'],y['underlying_query_reference'],y['notes_reference'],y['context_reference'],y['checkpoint_reference']]:i.checked(dep)
    assert y['candidate_reference']==i.ref(cp) and y['params']==i.params_for(x['rows'])
    for row in x['rows']:assert row==i.f.parse(row['index'],i.checked(row['source_reference']))
    augmented=i.augmented_rows(x['rows'])
    assert [r['comparison_only'] for r in augmented]==y['comparison_only_inputs']
    assert i.comparisons(x['rows'],y['state'])==y['comparisons']
    batch=m.load(i.RUN/'within-batch-identity-002.json.gz');expected=i.within_batch(x['rows'])
    for k,v in expected.items():assert batch[k]==v
    assert batch['identity_reference']==i.ref(ip)
    m.save(dest,dict(at=m.now(),validator_reference=i.ref(Path(__file__).resolve()),candidate_reference=i.ref(cp),identity_reference=i.ref(ip),rows=len(x['rows']),literal_facts_reparsed_equal=True,comparison_only_inputs_recomputed_equal=True,comparisons_recomputed_equal=True,within_batch_groups_recomputed_equal=True,read_only=True))
    print(json.dumps(dict(rows=len(x['rows']),recomputed_equal=True,database_writes=0,receipt=i.ref(dest))),flush=True)
if __name__=='__main__':main()
