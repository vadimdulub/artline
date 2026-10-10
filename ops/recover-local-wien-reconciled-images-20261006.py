#!/usr/bin/env python3
"""Two individual Wien Museum image matches with catalogue dates preserved."""
import argparse,importlib.util,json
from pathlib import Path

s=importlib.util.spec_from_file_location('wien',Path(__file__).with_name('recover-local-wien-followup-images-20261006.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
base=w.base;core=w.core
RUN=core.ROOT/'docs/research/local-wien-reconciled-images-20261006'
w.RUN=RUN;base.RUN=RUN
core.VERSION='local-wien-individually-reconciled-dates-v1'
w.REVIEWS={
 'Q6058798':('100686','Gustav Klimt (1862—1918)',
  'Exact stored inventory 100686, authority-linked museum object 102991, sole Klimt authorship, Pallas Athena title and 75 × 75 cm dimensions establish the object. Native date and painted inscription say 1898; the existing catalogue and authority say 1899. Retain this exact disagreement for editorial review while attaching only the independently licensed native photograph. No catalogue date or review status changes.'),
 'Q111165753':('10137','Ferdinand Georg Waldmüller (1793—1865)',
  'Exact German authority title Bautagelöhner erhalten ihr Frühstück, sole Waldmüller authorship, Wien Museum and the same 1859–1860 bounds identify the native painting. Authority dimensions are 53 × 44 cm, native 53.5 × 44 cm; the small height difference remains evidence. Native circa qualifier and source inventory 10137 are retained in the image evidence; existing range precision and missing inventory remain unchanged.'),
}
w.DATE_REVIEWS={'Q6058798':dict(stored_bounds=[1899,1899],native_bounds=[1898,1898],native_text='1898')}

def research():
 if not (RUN/'candidates.json').exists():
  original=json.loads((w.LEADS/'candidates.json').read_bytes())
  rows=[c for c in original['candidates'] if c['qid'] in w.REVIEWS]
  if len(rows)!=2:raise ValueError('Expected two reviewed objects')
  with base.connect() as db:
   for c in rows:
    row=db.execute("SELECT to_jsonb(a) record FROM artworks a WHERE a.id=%s AND a.primary_media_id IS NULL AND a.status='review' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)",(c['artwork_id'],)).fetchone()
    if not row or row['record']!=c['before_record']:raise ValueError('Candidate changed since review')
   baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
  core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows))
 w.research()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/w.PROVIDER).glob('*.json'):w.native_check(json.loads(path.read_bytes()))
  base.prepare(w.PROVIDER)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():w.native_check(im)
  base.verify()
