#!/usr/bin/env python3
"""Reparse pinned Walters evidence and verify current artist authorities read-only."""
import importlib.util,json
from pathlib import Path

def module(name,filename):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
 result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def audit():
 report=module('report','report-local-image-recovery-20261006.py')
 w=module('native','recover-local-walters-native-images-20261006.py')
 r=module('reconciled','recover-local-walters-reconciled-images-20261006.py')
 panel=module('panel','recover-local-walters-reviewed-panel-image-20261006.py')
 checks=[];artists={};active_total=0
 for name in report.OPERATIONS:
  run=report.RUN.parent/name;receipt=run/'apply-receipt.json'
  if not receipt.exists():continue
  withdrawn={aid for p in run.glob('source-policy-correction*.json') for aid in json.loads(p.read_bytes())['artwork_ids']}
  attached={x['artwork_id'] for x in json.loads(receipt.read_bytes())['receipts'] if x['result']=='attached'}-withdrawn
  active_total+=len(attached)
  if not name.startswith('local-walters-'):continue
  wrapper=panel.w if name==panel.RUN.name else w if name in r.PRIOR else r.w
  if wrapper is r.w:r.RUN=run
  wrapper.RUN=run;wrapper.base.RUN=run
  for aid in sorted(attached):
   im=json.loads((run/'images'/(aid+'.json')).read_bytes())
   (panel.verify_image if wrapper is panel.w else wrapper.verify_image)(im)
   if 'creator_identity' in im:
    proof=im['creator_identity'];key=proof['artist_record']['id'];expected=(proof['artist_record'],proof['artist_identifiers'])
    if key in artists and artists[key]!=expected:raise ValueError('Artist snapshots disagree')
    artists[key]=expected
   facts=im['raw']['native_facts']
   checks.append(dict(artwork_id=aid,operation=name,source=im['page'],capture_sha256=im['raw']['native_capture']['sha256'],per_photo_cc0_verified=True,monochrome=facts['monochrome'],creator_qualification=facts.get('creator_qualification'),explicit_asset_concordance=bool(facts.get('native_asset_concordance')),qualified_view_label=im.get('view_label'),qualified_view_kind=im['raw'].get('view_scope_review',{}).get('kind'),creator_activity_dates_qualified=bool(im['raw'].get('creator_date_review'))))
 with report.base.connect() as db:
  ids=list(artists)
  actual={row['record']['id']:row['record'] for row in db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
  identifiers={aid:[] for aid in ids}
  for row in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall():identifiers[row['record']['entity_id']].append(row['record'])
  for aid,(expected,expected_ids) in artists.items():
   if actual[aid]!=expected or identifiers[aid]!=expected_ids:raise ValueError('Live artist authority differs')
 out=dict(at=report.core.now(),passed=True,verified=len(checks),basis='Reparsed pinned native museum captures with current validators; photograph-specific CC0 grants, source identities, credits and creator qualifications retained. No source page refetch in this audit.',recent_creator_copyright_guard_applied=True,unchanged_artist_authority_records=len(artists),qualified_creators=sum(bool(x['creator_qualification']) for x in checks),monochrome_sources=sum(x['monochrome'] for x in checks),asset_concordances=sum(x['explicit_asset_concordance'] for x in checks),checks=checks)
 out['explicitly_qualified_panel_views']=sum(bool(x['qualified_view_label']) and x['qualified_view_label'].startswith('Virgin panel only') for x in checks)
 out['explicitly_qualified_album_covers']=sum(x['qualified_view_kind']=='album_cover' for x in checks)
 out['creator_activity_date_reviews']=sum(x['creator_activity_dates_qualified'] for x in checks)
 path=report.RUN/('walters-source-audit-'+str(active_total)+'.json')
 if path.exists():path=report.RUN/'history'/(report.core.now().replace(':','-')+'-'+path.name)
 report.core.save_new(path,out);print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))

if __name__=='__main__':audit()
