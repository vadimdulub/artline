import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000288.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
c=h.load(b.E/'global-title-collision-selection.json');d=h.load(b.E/'global-title-collision-evidence.json');decisions=[]
for row in c['rows']:
 for x in row['matches']:
  a=d['snapshots'][x['id']]['artwork']
  if row['source_id']=='1787224':reason='J.B.Sleper1948 paper print128x98mm with distinct Rijks accession; not anonymous16th/17th-century36x30cm wooden icon.'
  elif a['id']=='bbc161e1-f709-5ae2-9047-c97699472c85':reason='Walters44.648 is copper alloy/enamel28x24.5cm; not Berlin11317 tempera-on-wood25x18.5cm.'
  elif a.get('dimensions_text'):reason='Different documented dimensions '+a['dimensions_text']+' and independent source inventory/canonical identity; Berlin11317 is25x18.5x2.2cm. No matching SMB identity or source URL.'
  else:reason='Separate named-creator/date/source identity: '+str(a.get('unlinked_creator_label'))+'; '+str(a.get('date_display'))+'. Berlin11317 is anonymous18th-century wooden panel, not the named later works or1479/1563 works; source URLs and held labels retained.'
  decisions.append(dict(source_id=row['source_id'],other_artwork_id=a['id'],decision='distinct_physical_work',basis=reason))
b.save('global-title-collision-review.json',dict(at=h.now(),allowed_by_source={r['source_id']:[x['id'] for x in r['matches']] for r in c['rows']},decisions=decisions,existing_records_unchanged=True))
p=b.E.parent/'000285/booklet-visual-review.json';review=h.load(p)
for page in review['pages']:assert h.sha(Path(page['path']).read_bytes())==page['sha256']
b.save('prior-contextual-visual-evidence-verification.json',dict(at=h.now(),prior_review_path=str(p.relative_to(b.ROOT)),prior_review_sha256=h.sha(p.read_bytes()),immutable_copy_equal=(b.E/'booklet-visual-review.json').read_bytes()==p.read_bytes(),prior_page_image_hashes_verified=True,actually_viewed_this_batch=False,exact_object_matches_claimed=0))
b.save('attempt-reconciliation.json',dict(at=h.now(),own_application_receipts=[str(p.relative_to(b.ROOT)) for p in b.E.glob('**/applied*.json')],new_unique_operation=b.OP,prior_writes_before_plan=0,batch107_reconciled=True,previous_batch287_reconciled=True))
b.save('selection-editorial-review.json',dict(at=h.now(),discovered=10,selected_ids=b.SELECTED,decisions=[dict(source_id=oid,source_date=b.DATES[oid][0],range=list(b.DATES[oid][1:]),creator='anonymous; native actors empty',culture=b.native(oid)[0]['geography'],native_front=b.front(b.native(oid)[0])['id'],decision='eligible_same_inventory_panel') for oid in b.SELECTED],pending_ids=['1787213','1788063','1792494','1787403','1787249'],pending_basis='Remaining five captured notices reserved for next Berlin batch, including compound-frame and oklad/date precision review; no image downloaded for pending objects.'))
print('Source and global duplicate reviews pinned; no writes')
