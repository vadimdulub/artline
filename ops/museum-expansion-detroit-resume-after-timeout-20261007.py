#!/usr/bin/env python3
"""Continue other selected objects after reviewing a non-HTTP transport timeout."""
import hashlib,importlib.util,json,time
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-detroit-resume-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.m;RUN=c.RUN
ERROR=RUN/'errors/object-005.json'
REVIEW=RUN/'timeout-review-001.json'
def gate():
 review=m.load(REVIEW);assert c.ref(ERROR)==review['error_reference'];error=m.load(ERROR)
 assert error['number']==5 and error['error'].startswith('ReadTimeout:')
 assert time.time()-c.epoch(error['at'])>=300
 assert sorted(p.name for p in (RUN/'errors').glob('*.json'))==['object-005.json'],'Another source failure needs separate review'
 for r in review['references']:assert c.ref(m.ROOT/r['path'])==r
 return dict(timeout_review_reference=c.ref(REVIEW),cadence_seconds=c.CADENCE_SECONDS,held_numbers=[5],no_retry=True)
def main():
 assert not REVIEW.exists();error=m.load(ERROR);assert error['error'].startswith('ReadTimeout:') and time.time()-c.epoch(error['at'])>=300
 m.save(REVIEW,dict(at=m.now(),error_reference=c.ref(ERROR),elapsed_since_timeout_seconds=round(time.time()-c.epoch(error['at']),1),references=[c.ref(c.QUEUE),c.ref(c.GATE),c.ref(Path(__file__).resolve()),c.ref(Path(c.__file__).resolve())],decision='Object5 remains uncaptured and unapproved. The observed failure was a45second read timeout without HTTP response; no new429 orRetry-After was received. After at least5minutes, proceed once to other already-selected public object URLs on the same host and same transport at no more than one request per25seconds. Do not retry object5, change transport, or bypass an access restriction. Stop on the next error.'))
 c.preflight=gate
 for row in m.load(c.QUEUE)['selected'][5:118]:
  path=RUN/'objects-001'/('object-%03d.json.gz'%row['number'])
  assert not path.exists()
  c.capture(row)
 print('Completed selected objects6 through118; object5 remains on hold',flush=True)
if __name__=='__main__':main()
