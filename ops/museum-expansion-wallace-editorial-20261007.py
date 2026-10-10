#!/usr/bin/env python3
"""Retain explicit individual editorial decisions, without database writes."""
import argparse,importlib.util,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-wallace-refinement-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);m=r.m;RUN=r.RUN

def save(suffix,supplied):
 candidates=RUN/'native-candidates-003.json.gz';comparisons=RUN/'native-comparisons-003.json.gz';rows={x['facts']['inventory']:x for x in m.load(candidates)['rows'] if x['state']=='candidate'};cm={x['source_id']:x for x in m.load(comparisons)['records']}
 old=[d for p in sorted(RUN.glob('editorial-reviewed-*.json.gz')) for d in m.load(p)['decisions']];used={d['inventory'] for d in old};decisions=[]
 for inv,state,basis in supplied:
  assert inv in rows and inv not in used and len(basis)>60;used.add(inv);row=rows[inv]
  assert state in ['approved_review_only_addition','approved_existing_holding','editorial_hold']
  decisions.append(dict(source_id=row['source_id'],inventory=inv,state=state,confidence=.95 if state.startswith('approved_') else None,basis=basis,facts=row['facts'],index=row['index'],source_reference=row['source_reference'],comparison=cm[row['source_id']],limitation='Official museum object metadata and source-qualified attribution. Editorial confidence is not a calibrated probability. Preserve unknowns, source dates, versions and physical identity; collection connection does not establish current display, custody or legal ownership. No image/artist/publication approval.'))
 m.save(RUN/f'editorial-reviewed-{suffix}.json.gz',dict(at=m.now(),decisions=decisions,candidate_reference=r.f.ref(candidates),comparison_reference=r.f.ref(comparisons),policy='Individual editorial judgments, not database writes. Fresh scoped preflight, pinned plan and Library backup required before application.'))
 print(json.dumps(dict(saved=len(decisions),reviewed=len(old)+len(decisions),approved_additions=sum(d['state']=='approved_review_only_addition' for d in old+decisions),approved_existing=sum(d['state']=='approved_existing_holding' for d in old+decisions))),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);args=p.parse_args();save(args.suffix,json.load(sys.stdin))
