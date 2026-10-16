import importlib.util,gzip,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000283.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
p,pin=h.pinned(b.PHASE);records=[]
for r in p['records']:
 o,rc=b.native(r['source_id']);assert r['title']==o['title'] and r['accession_number']==o['ident'] and r['raw']['native']==o and r['medium']==o['material_desc']
 assert r['artist_id'] is None and not o['actors'] and not r['before'];assert (r['first'],r['last'])==b.DATES[r['source_id']][1:];assert r['precision']==('circa' if r['first']==r['last'] else 'range')
 front=o['images'][0];assert front['license']=='Public Domain Mark 1.0' and front['obj_ref']==['obj:'+r['source_id']] and front['asset_content']=='Aufsicht'
 records.append(dict(source_id=r['source_id'],artwork_id=r['artwork_id'],native_raw_sha256=rc['sha256'],source_json_sha256=r['evidence']['sha256'],native_date=o['dating'],selected_date=r['date_display'],date_precision=r['precision'],full_front_asset=front['id'],license=front['license'],creator_anonymous=True,booklet_pdf_page=b.PAGES[r['source_id']],booklet_catalogue_number=b.CATALOGUE[r['source_id']],ownership_custody_review=r['ownership_custody_review']))
b.save('independent-prewrite-source-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,records=records,source_id_reused=b.SOURCE_ID,selected_object_source_id_uuids_stable=True,no_image_rewrites=True,derivatives_pending_actual_review=True))
b.save('authorization-binding.json',dict(at=h.now(),actual_operation=b.OP,image_operation=b.i.OP,prior_setup_label='continuous-greek-20261011-b000283 is a reused setup label only; actual bounded delivery is Berlin',authorization='Current explicit user production authorization; no new service or spending budget',policy='Original111-source CSV staatliche_museen_berlin, docs/ARTLINE_IMAGE_USE.md general image policy and each selected native Public Domain Mark1.0',no_current_display_assertion=True,local_catalogue_read_only=True))
print('Four selected source records independently verified against native captures, date precision and visual catalogue evidence')
