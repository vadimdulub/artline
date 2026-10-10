#!/usr/bin/env python3
"""Recompute frozen comparisons and preserve additional cross-language title leads."""
import importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-princeton-followup-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=i.m;RUN=i.RUN
PATTERNS={3:r'pont|bridge|touque',7:r'prairie|pr[ée] |meadow|printemps|spring',12:r'chien|dog|mort|dead',13:r'trouville',34:r'tig[er]|tigr|lion|leopard',54:r'alp|mont|mount|snow|neige|glac|chamon|st\.? cerg',59:r'quoddy|head|coast|maine'}
def main():
    candidate=RUN/'native-candidates-001.json.gz';identity=RUN/'native-identity-001.json.gz';dest=RUN/'identity-recomputed-001.json';assert not dest.exists();rows=m.load(candidate)['rows'];x=m.load(identity)
    for dep in [x['query_reference']]+x['query_references']:i.checked(dep)
    assert x['candidate_reference']==i.ref(candidate) and x['params']==i.params_for(rows) and x['comparisons']==i.comparisons(rows,x['state'])
    by={a['id']:a for a in x['state']['artworks']};out=[]
    for row,cmp in zip(rows,x['comparisons']):
        n=row['number']
        if n not in PATTERNS:continue
        rs=[by[aid] for aid in cmp['creator_pool_ids'] if re.search(PATTERNS[n],by[aid]['title']+' '+(by[aid]['alternate_title'] or ''),re.I)]
        out.append(dict(number=n,source_id=row['source_id'],pattern=PATTERNS[n],rows=rs))
    m.save(RUN/'additional-title-context-001.json.gz',dict(at=m.now(),identity_reference=i.ref(identity),query_reference=i.ref(Path(__file__).resolve()),results=out,policy='Additional literal-title leads selected from the complete creator scope, including French subject vocabulary. Similarity is not identity; unresolved close versions remain held.'))
    m.save(dest,dict(at=m.now(),validator_reference=i.ref(Path(__file__).resolve()),candidate_reference=i.ref(candidate),identity_reference=i.ref(identity),query_references=[x['query_reference']]+x['query_references'],comparisons_recomputed_equal=True,rows=len(rows),policy='Full recomputation completed. Subsequent review pins these frozen inputs; database preflight independently requeries live identity state.'))
    print(json.dumps(dict(comparisons_recomputed_equal=True,rows=len(rows),additional_leads=sum(len(v['rows']) for v in out))),flush=True)
if __name__=='__main__':main()
