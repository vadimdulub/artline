#!/usr/bin/env python3
"""Read-only verification and combined report for the selected local recovery."""
import collections
import csv
import importlib.util
import io
import json
from pathlib import Path
from PIL import Image

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
core=base.core
RUN=base.RUN.parent/'local-image-recovery-20261006'
OPERATIONS=[
 'local-commons-recovery-20261005','local-commons-khm-recovery-20261006',
 'local-commons-followup-recovery-20261006','local-commons-alternates-recovery-20261006',
 'local-academy-images-20261006','local-academy-followup-images-20261006',
 'local-academy-reconciled-images-20261006','local-commons-priority-followup-20261006',
 'local-academy-person-review-20261006','local-wien-native-image-20261006',
 'local-wien-followup-images-20261006',
 'local-academy-identity-followup-20261006','local-nga-native-images-20261006',
 'local-wien-reconciled-images-20261006',
 'local-academy-inventory-review-20261006','local-academy-verso-image-20261006',
 'local-commons-multiple-images-20261006','local-commons-photographer-alternate-20261006',
 'local-commons-warsaw-followup-20261006',
 'local-open-museum-priority-images-20261006','local-byzantine-commons-image-review-20261006',
 'local-commons-next-images-20261006',
 'local-walters-native-images-20261006',
 'local-walters-followup-images-20261006',
 'local-walters-later-images-20261006',
 'local-walters-midcentury-images-20261006','local-walters-reconciled-images-20261006',
 'local-walters-authority-followup-images-20261006','local-walters-authority-later-images-20261006',
 'local-walters-asset-concordance-images-20261006',
 'local-walters-authority-next-images-20261006',
 'local-byzantine-photographer-review-20261006',
 'local-byzantine-reviewed-face-image-20261006',
 'local-walters-reviewed-panel-image-20261006',
 'local-walters-authority-modern-images-20261006',
 'local-walters-authority-final-images-20261006',
 'local-cleveland-commons-images-20261006',
 'local-commons-later-images-20261006',
 'local-fng-native-images-20261006',
 'local-smk-native-image-20261006',
 'local-smk-current-images-20261006',
 'local-commons-additional-images-20261006',
 'local-rijks-native-images-20261006',
 'local-saam-native-audit-20261006',
 'local-rijks-followup-images-20261006',
 'local-chicago-native-images-20261006',
 'local-chicago-followup-images-20261006',
 'local-chicago-next-images-20261006',
 'local-chicago-download-recovery-20261006',
 'local-wikiart-approved-images-20261006',
 'local-wikiart-followup-images-20261006',
 'local-wikiart-crosswalk-images-20261006',
 'local-wikiart-reused-images-20261006',
 'local-wikiart-version-correction-images-20261006',
 'local-chicago-breadth-images-20261006',
 'local-wikiart-catalogue-review-images-20261006',
 'local-chicago-reviewed-authorities-20261006',
 'local-chicago-further-images-20261006',
 'local-chicago-further-authorities-20261006',
 'local-chicago-moronobu-image-20261006',
 'local-wikiart-papaloukas-images-20261006',
 'local-wikiart-russian-images-20261006',
 'local-wikiart-bathing-image-20261006',
 'local-wikiart-russian-followup-images-20261006',
 'local-wikiart-serov-roerich-images-20261006',
 'local-wikiart-petrov-vodkin-images-20261006',
 'local-wikiart-repin-images-20261006',
 'local-wikiart-kustodiev-drawings-images-20261006',
 'local-wikiart-serov-roerich-followup-images-20261006',
 'local-wikiart-russian-self-portraits-images-20261007',
 'local-wikiart-russian-studies-images-20261007',
 'local-wikiart-serov-undated-drawings-images-20261007',
 'local-wikiart-russian-remaining-leads-images-20261007',
 'local-wikiart-russian-title-variants-images-20261007',
 'local-wikiart-russian-further-title-variants-images-20261007',
 'local-wikiart-russian-more-title-variants-images-20261007',
 'local-wikiart-russian-additional-title-variants-images-20261007',
 'local-wikiart-russian-prints-landscapes-images-20261007',
 'local-wikiart-russian-portraits-figures-images-20261007',
 'local-wikiart-russian-expanded-names-images-20261007',
 'local-wikiart-russian-untranslated-index-images-20261007',
 'local-wikiart-kuindzhi-mashkov-images-20261007',
 'local-wikiart-kuindzhi-versions-images-20261007',
 'local-wikiart-levitan-images-20261007',
 'local-wikiart-shishkin-images-20261007',
 'local-wikiart-russian-four-artists-images-20261007',
 'local-wikiart-polenov-abbey-image-20261007',
 'local-wikiart-russian-further-studies-images-20261007',
 'local-wikiart-roerich-landscape-versions-images-20261007',
 'local-wikiart-benois-images-20261007',
 'local-wikiart-malevich-filonov-images-20261007',
 'local-wikiart-malevich-suprematism-images-20261007',
 'local-russian-commons-portrait-review-20261007',
 'local-wikiart-roerich-serov-final-leads-images-20261007',
 'local-wikiart-russian-subject-mismatch-review-20261007',
 'local-wikiart-russian-further-versions-images-20261007',
 'local-wikiart-russian-final-title-variants-images-20261007',
 'local-wikiart-konchalovsky-images-20261007',
 'local-wikiart-savrasov-somov-bakst-images-20261007',
 'local-wikiart-russian-next-final-leads-images-20261007',
 'local-chicago-more-images-20261007',
]

def report():
 artworks={};images={};operations={};withdrawals=[];unapproved_images=[];rejected_primaries=[];unusable_thumbnails=[]
 initial=json.loads((RUN.parent/'local-commons-recovery-20261005/candidates.json').read_bytes())['baseline']
 for name in OPERATIONS:
  run=RUN.parent/name
  candidates=json.loads((run/'candidates.json').read_bytes())['candidates']
  events=core.latest_events(run)
  rejection=run/'primary-image-rejection.json'
  if rejection.exists():rejected_primaries.append(json.loads(rejection.read_bytes()))
  tiny_review=run/'tiny-source-review.json'
  if tiny_review.exists():unusable_thumbnails.append((name,json.loads(tiny_review.read_bytes())))
  withdrawn={aid for p in run.glob('source-policy-correction*.json') for aid in json.loads(p.read_bytes())['artwork_ids']}
  withdrawn_images={p.stem:json.loads(p.read_bytes()) for p in (run/'images').glob('*.json') if p.stem in withdrawn}
  withdrawals.extend(withdrawn_images.values())
  visual=run/'visual-review.json'
  if visual.exists():
   for decision in json.loads(visual.read_bytes())['images']:
    path=run/'images'/(decision['artwork_id']+'.json')
    if decision['decision']!='approved' and path.exists():unapproved_images.append(json.loads(path.read_bytes()))
  receipt=run/'apply-receipt.json'
  attached={r['artwork_id'] for r in json.loads(receipt.read_bytes())['receipts'] if r['result']=='attached'}-withdrawn if receipt.exists() else set()
  for aid in attached:
   if aid in images:raise ValueError('Duplicate active attachment')
   images[aid]=json.loads((run/'images'/(aid+'.json')).read_bytes())
  operations[name]=dict(reviewed=len(candidates),attached=len(attached))
  for c in candidates:
   row=artworks.setdefault(c['artwork_id'],dict(artwork_id=c['artwork_id'],artist=c['artist'],title=c['title'],operations=[],source_results=[]))
   e=events.get(c['artwork_id'],{})
   row['operations'].append(name)
   row['source_results'].append(dict(operation=name,outcome='withdrawn_source_policy_hold' if c['artwork_id'] in withdrawn else 'attached' if c['artwork_id'] in attached else e.get('outcome','reviewed'),reason=e.get('reason') or e.get('policy',{}).get('finding','')))
 checks=[]
 with base.connect() as db:
  ids=list(images)
  current={r['artwork']['id']:r for r in db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence
    FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
    JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])''',(ids,)).fetchall()}
  links=collections.defaultdict(list)
  for r in db.execute('SELECT artwork_id::text,to_jsonb(aa) record FROM artwork_artists aa WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id',(ids,)).fetchall():links[r['artwork_id']].append(r['record'])
  identifiers=collections.defaultdict(list)
  for r in db.execute("SELECT entity_id::text,to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,)).fetchall():identifiers[r['entity_id']].append(r['record'])
  relations={(r['artwork_id'],r['media_id']):r['view_label'] for r in db.execute('SELECT artwork_id::text,media_id::text,view_label FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()}
  for aid,im in images.items():
   row=current[aid];m=row['media'];e=row['evidence']
   exclude={'primary_media_id','updated_at','updated_by','revision'}
   if {k:v for k,v in row['artwork'].items() if k not in exclude}!={k:v for k,v in im['before_record'].items() if k not in exclude}:raise ValueError('Catalogue metadata/status changed: '+aid)
   if links[aid]!=im['creator_links'] or identifiers[aid]!=im['identifiers']:raise ValueError('Identity links changed: '+aid)
   for field,expected in dict(id=im['media_id'],storage_path=im['path'],checksum_sha256=im['sha256'],license_url=im['policy_url'],creator_credit=im['creator_credit'],rights_status=im['rights_status'],source_page_url=im['page']).items():
    if m[field]!=expected:raise ValueError('Stored media differs: '+aid+' '+field)
   if e['source_image_url']!=im['source_image_url'] or e['policy_url']!=im['policy_url'] or (aid,im['media_id']) not in relations:raise ValueError('Source or image association differs')
   if im['provider'] in ('walters-native','byzantine-reviewed-face','fng-native','smk-current-native','rijks-native','chicago-native','wikiart-approved-local'):
    if m['attribution_text']!=im['attribution_text'] or e['source_checksum']!=core.sha(core.encode(im['raw'])) or e['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete image evidence or attribution differs')
   if im['provider']=='chicago-native':
    for key in ('creator_identity_review','catalogue_concordance_review'):
     review=im['raw'].get('native_facts',{}).get(key)
     if review and (review.get('decision')!='approved' or review['artwork_id']!=aid or review['note'] not in m['attribution_text']):raise ValueError('Individual Chicago identity/title review omitted')
   if im['provider']=='wikiart-approved-local':
    if im['raw']['user_source_approval']['target']!='local' or im['raw']['wikiart_facts']['rights_status']!=m['rights_status']:raise ValueError('Actual WikiArt rights or separate local source approval differs')
    if m['rights_status']!='public_domain' and (m['verified_at'] is not None or m['verified_by'] is not None):raise ValueError('User source approval represented as independent rights verification')
    facts=im['raw']['wikiart_facts']
    if facts['source_year_end'] is None:
     proof=facts.get('individual_source_date_review',{})
     if facts['source_year_start'] is not None or facts['source_metadata'].get('year')!='?' or proof.get('decision')!='eligible_exact_native_version' or not proof.get('note') or proof['note'] not in im['attribution_text']:raise ValueError('Unknown source date or individual native scope evidence lost')
   if im['raw'].get('print_design_review'):
    proof=im['raw']['print_design_review']
    if proof.get('match_level')!='printed_design' or proof.get('source_impression_identified') is not False or im.get('view_label')!='Printed design; individual impression unspecified':raise ValueError('Print-design scope misrepresented')
    if any(proof[k]!=im[k] for k in ('source_image_url','source_sha256','sha256','view_label','alt_text')) or proof['note'] not in im['attribution_text']:raise ValueError('Print-design source qualification lost')
   if im.get('view_label'):
    if m['alt_text']!=im['alt_text'] or relations[(aid,im['media_id'])]!=im['view_label']:raise ValueError('Qualified icon face label differs')
   elif im.get('alt_text') and m['alt_text']!=im['alt_text']:raise ValueError('Individual source-identity image label differs')
   data=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
   if core.sha(data)!=im['sha256'] or len(data)!=im['bytes'] or len(data)>100000:raise ValueError('Application bytes differ')
   if core.sha(Path(im['source_archive']).read_bytes())!=im['source_sha256']:raise ValueError('Archived source bytes differ')
   with Image.open(io.BytesIO(data)) as picture:picture.verify()
   checks.append(dict(artwork_id=aid,title=im['title'],artist=im['artist'],source_url=im['page'],image_path=im['path'],rights_status=im['rights_status'],bytes=len(data),sha256=im['sha256']))
  for im in withdrawals:
   if (core.ROOT/'apps/web/public'/im['path'].lstrip('/')).exists():raise ValueError('Withdrawn public file still present')
   row=db.execute('SELECT a.primary_media_id,m.rights_status,m.storage_path FROM artworks a JOIN media_assets m ON m.id=%s WHERE a.id=%s',(im['media_id'],im['artwork_id'])).fetchone()
   if row['primary_media_id']==im['media_id'] or row['rights_status']!='unknown' or row['storage_path'] is not None:raise ValueError('Withdrawal not enforced')
  for im in unapproved_images:
   if (core.ROOT/'apps/web/public'/im['path'].lstrip('/')).exists():raise ValueError('Unapproved public file still present')
   if core.sha(Path(im['source_archive']).read_bytes())!=im['source_sha256']:raise ValueError('Unapproved source archive differs')
   row=db.execute('SELECT primary_media_id::text FROM artworks WHERE id=%s',(im['artwork_id'],)).fetchone()
   if row['primary_media_id']==im['media_id']:raise ValueError('Unapproved image attached')
  for rejected in rejected_primaries:
   if (core.ROOT/'apps/web/public'/rejected['path'].lstrip('/')).exists():raise ValueError('Rejected primary public file still present')
   if core.sha(Path(rejected['source_archive']).read_bytes())!=rejected['source_sha256'] or core.sha(Path(rejected['private_derivative']).read_bytes())!=rejected['sha256']:raise ValueError('Rejected primary private evidence differs')
   if db.execute('SELECT 1 FROM media_assets WHERE storage_path=%s',(rejected['path'],)).fetchone():raise ValueError('Rejected primary unexpectedly attached')
  for name,review in unusable_thumbnails:
   rc=review['receipt'];aid=rc['artwork_id'];folder=core.ROOT/'apps/web/public/assets/artworks/imported'/name
   if list(folder.glob(aid+'-*')) or (RUN.parent/name/'images'/(aid+'.json')).exists():raise ValueError('Unusable native thumbnail prepared publicly')
   if core.sha(Path(rc['source_archive']).read_bytes())!=rc['sha256']:raise ValueError('Unusable native source evidence differs')
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 data=dict(at=core.now(),local_only=True,distinct_artworks_reviewed=len(artworks),new_images_attached=len(images),reviewed_without_attachment=len(artworks)-len(images),baseline_after=baseline,operations=operations,rights_status_counts=dict(collections.Counter(im['rights_status'] for im in images.values())),max_derivative_bytes=max(im['bytes'] for im in images.values()),all_files_and_live_database_links_verified=True,all_catalogue_metadata_creator_links_and_identifiers_preserved=True,withdrawn_source_images=len(withdrawals),withdrawn_public_files_absent=True,http_verification=dict(status='partial',limitation='Earlier per-operation HTTP checks passed; recent checks timed out on the existing Next.js server. Recent attachments have complete file/database verification but lack a completed HTTP receipt; see their operation-specific verification reports.'),remaining_catalogue_work=True)
 # Preserve prior checkpoint reports before replacing the latest combined view.
 data.update(unapproved_prepared_images=len(unapproved_images),unapproved_public_files_absent=True,unapproved_source_archives_preserved=True)
 data.update(rejected_primary_images=len(rejected_primaries),rejected_primary_public_files_absent=True,rejected_primary_source_archives_preserved=True)
 data.update(unusable_native_thumbnails=len(unusable_thumbnails),unusable_native_thumbnails_remain_private=True)
 data.update(walters_complete_stored_evidence_verified=True,walters_creator_qualifications_retained=sum(bool(im['raw'].get('native_facts',{}).get('creator_qualification')) for im in images.values() if im['provider']=='walters-native'))
 data.update(baseline_before=initial,catalogue_total_net_change=baseline['total']-initial['total'],catalogue_missing_net_change_outside_this_recovery=baseline['missing']-(initial['missing']-len(images)))
 data.update(images_attached_with_unknown_catalogue_dates_preserved=sum(im['before_record']['date_precision']=='unknown' for im in images.values()),qualified_icon_face_evidence_verified=any(im['provider']=='byzantine-reviewed-face' for im in images.values()))
 data.update(explicitly_qualified_views=sum(bool(im.get('view_label')) for im in images.values()),explicitly_qualified_icon_views=sum(bool(im.get('view_label')) and im.get('object_form')=='icon' for im in images.values()),explicitly_qualified_album_covers=sum(im['raw'].get('view_scope_review',{}).get('kind')=='album_cover' for im in images.values()))
 data.update(native_title_discrepancies_retained=sum(bool(im['raw'].get('source_identity_review') or im['raw'].get('native_facts',{}).get('catalogue_concordance_review')) for im in images.values()))
 data.update(chicago_individual_creator_reviews_verified=sum(bool(im['raw'].get('native_facts',{}).get('creator_identity_review')) for im in images.values() if im['provider']=='chicago-native'),chicago_individual_qualified_attributions_retained=sum(bool(im['raw'].get('native_facts',{}).get('creator_identity_review',{}).get('qualification')) for im in images.values() if im['provider']=='chicago-native'))
 data.update(wikiart_images_under_explicit_user_source_approval=sum(im['provider']=='wikiart-approved-local' for im in images.values()),wikiart_actual_rights_preserved_separately_from_user_approval=True)
 data.update(wikiart_images_with_unknown_source_dates_preserved=sum(im['provider']=='wikiart-approved-local' and im['raw']['wikiart_facts']['source_year_end'] is None for im in images.values()),qualified_print_design_reproductions=sum(bool(im['raw'].get('print_design_review')) for im in images.values()))
 listener=RUN/'http-listener-check-20261006.json'
 if listener.exists():
  data['http_verification']['latest_listener_check']=json.loads(listener.read_bytes())
  if data['http_verification']['latest_listener_check']['listener_detected'] is False:
   data['http_verification']['limitation']='Earlier per-operation HTTP checks passed; subsequent requests timed out. The latest read-only check found no local TCP listener on port 3000; no service was started and no new HTTP delivery requests were made. All attached files and database links are verified, but recent attachments still lack completed HTTP receipts.'
 for name in ['report.json','attached-images.csv','artwork-outcomes.csv']:
  old=RUN/name
  if old.exists():core.save_new(RUN/'history'/(core.sha(old.read_bytes())[:16]+'-'+name),old.read_bytes())
 (RUN/'report.json').write_bytes(core.encode(data))
 with (RUN/'attached-images.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(sorted(checks,key=lambda r:(r['artist'],r['title'])))
 outcomes=[]
 for aid,row in artworks.items():
  row.update(outcome='attached' if aid in images else 'held_for_further_review',operations='; '.join(row['operations']),source_results=json.dumps(row['source_results'],ensure_ascii=False));outcomes.append(row)
 with (RUN/'artwork-outcomes.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['artwork_id','artist','title','outcome','operations','source_results']);w.writeheader();w.writerows(outcomes)
 print(json.dumps(data,indent=2))

if __name__=='__main__':report()
