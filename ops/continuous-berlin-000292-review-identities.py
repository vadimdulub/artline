import importlib.util
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
v=h.load(E/'global-identity-initial.json');ctx={x['id']:x for x in h.load(E/'collision-catalogue-context.json')['rows']};allowed={};decisions=[]
specific={'78be24b0':'Apsida45325 explicitly documents an in-situ Asinou narthex wall painting flanking the north doorway, with1332/earlier layers; not a portable30x23.5cm sixteenth-century Berlin panel. Original digital2006date retained as documentation only.', '826518d4':'Greek native300358 is25x19cm in raw source fields and held at Paros Ecclesiastical Museum; source17th-century date and viewed bust composition on dark background differ from full-length Berlin Michael in yellow rocky landscape. Existing image viewed with view_image; no metadata correction authorized.', 'd2a7f881':'Kykkos native guide figure60 identifies Michael of Cyprus,1782, separately from the sixteenth-century anonymous Berlin9354.', '662a7cdd':'WikiArt native57728a9dedc2cb388011a52e names Hildegard of Bingen; separate medieval manuscript tradition, not an eighteenth-century Russian panel. Existing unknown date preserved.'}
for r in v['records']:
 assert not r['native'] and not r['citations'];allowed[r['source_id']]=[x['id'] for x in r['title_collisions']]
 for x in r['title_collisions']:
  c=ctx[x['id']];basis=next((txt for key,txt in specific.items() if x['id'].startswith(key)),None)
  if not basis and x['dimensions_text']:basis='Distinct physical dimensions '+x['dimensions_text']+' versus Berlin '+str(r['dimensions'])+'; original medium, date, creator and independent native source retained in evidence.'
  if not basis:
   assert c['creator'];basis='Independent source identifies '+c['creator']+'; separate named Western/modern artwork rather than anonymous sixteenth-century Berlin icon. Source/date='+str(c['date_display'])+'; no existing unknown dates changed.'
  decisions.append(dict(source_id=r['source_id'],other_artwork_id=x['id'],decision='distinct_physical_work',basis=basis))
 for x in r['accession_collisions']:
  c=ctx[x['id']];assert c['creator'] in ['Hovsep Karalian','Shavarsh Hovhannisyan']
  decisions.append(dict(source_id=r['source_id'],other_artwork_id=x['id'],decision='independent_inventory_namespace',basis='Unrelated Armenian '+c['title']+' by '+c['creator']+', source date '+c['date_display']+'. A numeric inventory is not a global identifier; no Berlin source or object URL matches.'))
h.save(E/'global-title-collision-review.json',dict(at=h.now(),allowed_by_source=allowed,decisions=decisions,existing_records_unchanged=True,conditional_image_comparisons_required=['1788649']))
h.save(E/'selection-editorial-review.json',dict(at=h.now(),discovered=10,selected_ids=b.SELECTED,dates=b.DATES,date_review=b.DATE_REVIEW,anonymous_creators=True,selected_metadata_precedes_image_download=True,image_view_note='Four whole painted panels; multi-scene calendar and creation icon remain one work each. No later photograph date used as creation date.',pending_ids=['1787264','1787259','1720838','2291559','1791014','2388716'],pending_basis='Saved source notices require further identity/creator/image-version or rights review; no assertion that metadata must be blocked by an image gap.'))
print('Global identity collisions reviewed; four new metadata candidates cleared for image preparation')
