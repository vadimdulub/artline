#!/usr/bin/env python3
"""One further exact RKD-origin Commons reproduction; retain source credit."""
import argparse,importlib.util,json
from pathlib import Path

s=importlib.util.spec_from_file_location('rkd',Path(__file__).with_name('recover-local-commons-rkd-image-20261006.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
r.RUN=r.core.ROOT/'docs/research/local-commons-later-images-20261006';r.base.RUN=r.RUN
r.AID='8bc16a3c-45b7-5044-89f1-dce863ae8422';r.QID='Q105097974'
r.SOURCE_CREDIT_URL='https://rkd.nl/explore/images/242849'
r.NOTE='Exact Commons artwork Q105097974 and explicit PD-Art/PDM for a faithful two-dimensional reproduction of the seventeenth-century Gerrit Dou painting. RKD policy applies rights-holder permission requirements to copyright-protected material; it is not itself a blanket open licence. No photograph-specific contrary claim is present in the exact Commons source. Retain Commons public-domain basis, both RKD policy captures and the requested full RKD source credit. Do not treat RKD subscription/download availability as image-use permission.'
MONOCHROME='Source-provided archival monochrome reproduction; original painting colours are not represented.'
REVIEW=dict(monochrome=True,full_oval_composition=True,source_margins_preserved=True)

def verify_source(im):
 r.verify_source(im)
 if im['raw'].get('visual_source_review')!=REVIEW or MONOCHROME not in im['attribution_text']:raise ValueError('Reviewed monochrome source limitation omitted')

original_attach=r.base.m.attach
def attach(db,im,target):
 verify_source(im)
 return original_attach(db,im,target)
r.base.m.attach=attach

def verify():
 for im in r.base.prepared():verify_source(im)
 r.base.verify();im=r.base.prepared()[0]
 candidates=json.loads((r.RUN/'candidates.json').read_bytes())['candidates'];held=[]
 with r.base.connect() as db:
  row=db.execute('''SELECT m.rights_status,m.creator_credit,m.attribution_text,e.source_checksum,e.evidence_json FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s''',(im['media_id'],)).fetchone()
  if any(row[k]!=im[k] for k in ('rights_status','creator_credit','attribution_text')) or row['source_checksum']!=r.core.sha(r.core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored source evidence or monochrome attribution differs')
  for c in candidates:
   if c['artwork_id']==r.AID:continue
   if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held catalogue record changed')
   held.append(c['artwork_id'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 r.core.save_new(r.RUN/'source-rights-verification.json',dict(at=r.core.now(),passed=True,verified=1,complete_stored_evidence_verified=True,monochrome_limitation_retained=True,unchanged_held_artworks=held))
 r.core.save_new(r.RUN/'report.json',dict(at=r.core.now(),local_only=True,reviewed=len(candidates),attached=1,still_unattached=len(held),public_domain_attached=1,monochrome_attached=1,baseline_after=baseline,all_catalogue_metadata_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':
  path=r.RUN/'selected'/r.DIR/(r.AID+'.json')
  if not path.exists():r.research()
  im=json.loads(path.read_bytes())
  if im['raw'].get('visual_source_review')!=REVIEW:
   r.core.save_new(r.RUN/'history/before-monochrome-review/selected.json',path.read_bytes())
   im['raw']['visual_source_review']=REVIEW;im['attribution_text']+=' '+MONOCHROME
   verify_source(im);path.write_bytes(r.core.encode(im))
  else:verify_source(im)
 elif a.phase=='prepare':
  for path in (r.RUN/'selected'/r.DIR).glob('*.json'):verify_source(json.loads(path.read_bytes()))
  r.base.prepare(r.DIR)
 elif a.phase=='apply':r.base.apply()
 else:verify()
