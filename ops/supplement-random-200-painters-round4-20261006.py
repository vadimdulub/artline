#!/usr/bin/env python3
"""Complete 200 named painters after a cultural category entered the fixed frame.

The original cohort and its held Aztec authority remain immutable. Select only
rank 201 in its original seeded ordering; no preference based on work counts,
image availability or research outcomes. Isolated receipts and scoped DB writes.
"""
import argparse,hashlib,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,ROOT/path);o=importlib.util.module_from_spec(sp);sp.loader.exec_module(o);return o
f=module('final','ops/finalize-random-200-painters-round4-20261006.py');x=f.x;d=x.d;s=x.s;m=x.m;r=x.r
MAIN=x.RUN;MAIN_BACKUP=x.BACKUP
OP=MAIN.name+'-named-painter-supplement';RUN=MAIN.parent/OP
BACKUP=MAIN_BACKUP.parent/OP;ORIGINALS=m.ORIGINALS.parent/OP
for obj in [f,x,d,s,m,r,m.q,d.d]:
 if hasattr(obj,'RUN'):obj.RUN=RUN
 if hasattr(obj,'BACKUP'):obj.BACKUP=BACKUP
 if hasattr(obj,'ORIGINALS'):obj.ORIGINALS=ORIGINALS
 if hasattr(obj,'OP'):obj.OP=OP
x.PRIOR_RUNS=x.PRIOR_RUNS+[MAIN]
def cohort():
 data=r.load(RUN/'cohort.json');assert len(data['painters'])==1
 assert data['painters'][0]['artist']['display_name']=='Marianne Stokes'
 return data['painters']
m.cohort=cohort

def bootstrap():
 if (RUN/'authorization.json').exists():return
 original=r.load(MAIN/'cohort.json');frame=r.load(MAIN/'sampling-frame.json')['frame']
 ordered=sorted(frame,key=lambda p:hashlib.sha256((original['seed']+'/'+p['artist']['id']).encode()).digest())
 assert ordered[:200]==original['painters'];chosen=ordered[200]
 assert chosen['artist']['display_name']=='Marianne Stokes'
 assert chosen['source']['url']=='https://www.wikiart.org/en/marianne-stokes'
 entity=r.load(MAIN/'creator-entity-review.json');assert entity['artist']['display_name']=='Aztec Art'
 r.save(RUN/'cohort.json',{'at':r.now(),'seed':original['seed'],'original_rank':201,'painters':[chosen],
  'method':'Next identity in the original SHA256 random ordering; fixes person/category eligibility only. Original 200 slots and all research outcomes preserved.','original_cohort_sha256':r.sha((MAIN/'cohort.json').read_bytes())})
 authorization=r.load(MAIN/'authorization.json')
 authorization.update(at=r.now(),painters=1,cohort_sha256=r.sha((RUN/'cohort.json').read_bytes()),
  continues='Complete the user-requested 200 named painters; original sample contained 199 named people and an incorrectly typed Aztec Art cultural authority.',
  original_authorization_sha256=r.sha((MAIN/'authorization.json').read_bytes()),
  rules=['Use original random rank 201, no outcome-driven resampling.','Original category slot is fully held and unchanged.','Same source, image, identity, date, review and production-preservation rules as the main batch.'])
 r.save(RUN/'authorization.json',authorization)
 r.save(BACKUP/'cloud-backup.json',r.load(MAIN_BACKUP/'cloud-backup.json'))
 r.save(RUN/'capture-cache.json',r.load(MAIN/'capture-cache.json'))
 print('Supplement frozen: Marianne Stokes, original rank 201',flush=True)

def research():
 bootstrap();m.snapshot();m.indexes();x.creator_leads();m.translations();m.pages();x.retry_pages();x.index_gaps();s.select();d.prepare();d.audits();d.sheets();x.cached_relationships()
 print('Supplement researched and prepared; manual reviews still required.',flush=True)

def audit():
 assert len(list((MAIN/'delivery-plans').glob('*.json.gz')))==200
 x.cross_creator_audit()
 review=module('review','ops/review-random-200-painters-round4-20261006.py')
 review.x=x;review.r=r;review.RUN=RUN
 review.scan(final=True);review.additional_image_audit()

def delivery():d.delivery_plans();x.preflight()
def upload():d.upload()
def apply():d.apply()
def verify():d.verify();f.verify()
def report():
 pair=cohort()[0]
 x.csv_file('selected-200-painters.csv',[{'rank':201,'artist':pair['artist']['display_name'],'artist_id':pair['artist']['id'],'wikiart_url':pair['source']['url']}])
 if not (RUN/'source-index-gaps.json').exists():r.save(RUN/'source-index-gaps.json',{'at':r.now(),'painters':[]})
 if not (RUN/'creator-lead-object-evidence.json.gz').exists():
  assert not r.load(RUN/'expanded-creator-leads.json')
  r.save_gz(RUN/'creator-lead-object-evidence.json.gz',{'at':r.now(),'records':{}})
 f.report()
 path=RUN/'report.html';page=path.read_text().replace('Another 200 painters — completed production import','Marianne Stokes — named-painter supplement').replace('200 painter outcomes','Painter outcome');path.write_text(page)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','audit','delivery','upload','apply','verify','report']);a=p.parse_args();globals()[a.phase]()
