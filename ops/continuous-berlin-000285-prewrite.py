import importlib.util
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000285.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
p,pin=h.pinned(b.PHASE);rows=[]
refresh=h.load(b.E/'independent-source-refresh-verification.json');assert len(refresh['rows'])==3
for r in p['records']:
 o,rc=b.native(r['source_id']);assert r['title']==o['title'] and r['accession_number']==o['ident'] and r['raw']['native']==o and r['medium']==o['material_desc']
 assert r['artist_id'] is None and not o['actors'] and not r['before'];assert (r['first'],r['last'])==b.DATES[r['source_id']][1:];assert r['precision']==('exact' if r['first']==r['last'] else 'range')
 assert r['culture']==('; '.join(x['nameLine'] for x in o['geography']) or None)
 im=b.front(o);assert im['license']=='Public Domain Mark 1.0' and im['obj_ref']==['obj:'+r['source_id']] and im['asset_content']=='Aufsicht';assert im['id']==r['selected_image_asset_id']
 assert r['holding_confidence']>=.8 and r['holding_basis']==r['ownership_custody_review']
 rows.append(dict(source_id=r['source_id'],artwork_id=r['artwork_id'],native_raw_sha256=rc['sha256'],source_json_sha256=r['evidence']['sha256'],native_date=o['dating'],selected_date=r['date_display'],date_precision=r['precision'],full_front_asset=im['id'],license=im['license'],creator_anonymous=True,culture=r['culture'],ownership_custody_review=r['ownership_custody_review']))
b.save('independent-prewrite-source-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,records=rows,no_artist_invented=True,source_id_reused=b.SOURCE_ID,selected=3,fresh_native_metadata_verified=True))
b.save('authorization-binding.json',dict(at=h.now(),operation=b.OP,image_operation=b.i.OP,metadata_plan_sha256=pin,authorization='Current explicit source-backed production authorization, new artworks remain review',image_policy='Original111-source CSV Berlin entry, docs/ARTLINE_IMAGE_USE.md general policy, each selected native image Public Domain Mark1.0',user_approval_separate_from_source_rights=True,no_current_display_assertion=True,local_catalogue_connections=0,no_new_budget=True))
print('Three source identities, dates, anonymous creators, qualified geography and holdings independently verified')
