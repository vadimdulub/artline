#!/usr/bin/env python3
"""Retain individually supplied editorial decisions; never writes the database."""
import argparse, importlib.util, json, sys
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m;RUN=w.RUN

def save(suffix, supplied):
    candidate=RUN/'native-candidates-006.json.gz';comparison=RUN/'native-comparisons-006.json.gz'
    rows={r['facts']['inventory']:r for r in m.load(candidate)['rows'] if r['state']=='candidate'}
    comps={r['source_id']:r for r in m.load(comparison)['records']}
    prior=[d for p in sorted(RUN.glob('editorial-reviewed-*.json.gz')) for d in m.load(p)['decisions']]
    used={d['inventory'] for d in prior};decisions=[]
    for inv,state,basis in supplied:
        assert inv not in used and inv in rows and len(basis)>60
        assert state in ['approved_review_only_addition','editorial_hold','existing_identity_review']
        used.add(inv);r=rows[inv]
        decisions.append(dict(source_id=r['source_id'],inventory=inv,state=state,confidence=.95 if state=='approved_review_only_addition' else None,basis=basis,facts=r['facts'],index=r['index'],source_reference=r['source_reference'],comparison=comps[r['source_id']],limitation='Official collection-page extraction documents the object and collection connection, not fresh display, custody or legal ownership. Editorial confidence is not a calibrated probability. Literal qualified creators stay unlinked; source narrative and uncertainty retained. No image approval or publication.'))
    m.save(RUN/f'editorial-reviewed-{suffix}.json.gz',dict(at=m.now(),decisions=decisions,candidate_reference=w.ref(candidate),comparison_reference=w.ref(comparison),policy='Individually reviewed source facts, narratives and existing-record leads. Provisional selection only; immutable import plan, fresh scope checks and transactional validation required before additions.'))
    print(json.dumps(dict(saved=len(decisions),approved=sum(d['state']=='approved_review_only_addition' for d in decisions),total_reviewed=len(prior)+len(decisions),total_approved=sum(d['state']=='approved_review_only_addition' for d in prior+decisions))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();save(a.suffix,json.load(sys.stdin))
