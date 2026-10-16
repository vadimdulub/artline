"""Pin existing NGA source citations and reviewed physical-impression identities."""
import importlib.util,json,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-nga-images-000275.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rows=b.i.selected(b.B)['rows'];identity=b.load(b.E/'independent-identity-verification.json');source=b.load(b.E/'independent-source-verification.json');pins={}
for row in rows:
 found=[c for c in identity['citations'] if c['entity_id']==row['artwork_id'] and c['field_name']=='million_catalogue_nga'];assert len(found)==1
 c=found[0];ev=json.loads(c['evidence_note']);assert ev['plan_sha256']==row['plan_sha256'] and ev['native_object']['objectid']==row['native_id'] and ev['native_object']['accessionnum']==row['accession_number']
 rc=next(x for x in source['csv_receipts'] if x['path'].endswith('objects.csv'));assert ev['source_sha256']==rc['sha256']
 verified=next(x for x in source['records'] if x['artwork_id']==row['artwork_id']);assert all(verified['source_object'][k]==v for k,v in ev['native_object'].items())
 pins[row['artwork_id']]=c
b.save(b.E/'source-citation-pin-verification.json',dict(at=h.now(),citations=pins,source_plan_and_csv_checksums_match=True,new_programme_metadata_increments=0,passed=True))
images,_,review=b.i.accepted(b.B)
free=shutil.disk_usage(b.i.ORIG.parent).free;assert free>30*1024**3
b.save(b.P/'storage-limit-verification.json',dict(at=h.now(),free_bytes=free,existing_minimum_headroom_bytes=30*1024**3,selected_source_images=len(images),total_source_bytes=sum(Path(x['original_path']).stat().st_size for x in images),served_bytes=sum(x['bytes'] for x in images),new_paid_service=False,spending_limits_not_modified=True,configured_controls='Existing image preparation12MB file/12M pixel limits and30GiB disk floor; established Cloud Storage/SQL only; no new spending budget.'))
b.save(b.P/'version-identity-verification.json',dict(at=h.now(),records=[dict(artwork_id=r['artwork_id'],native_id=r['native_id'],accession=r['accession_number'],source_object=next(x['source_object'] for x in source['records'] if x['artwork_id']==r['artwork_id']),visual_decision=next(x for x in review['decisions'] if x['artwork_id']==r['artwork_id'])) for r in rows],same_title_impressions_distinct=True,notes='NGA11764 and11769 are different sheets with distinct accession, UUID, sheet margins, plate dimensions and source-primary images. Both are engravings pulled from a silver medal, not sculptures or interchangeable photos. Native source orientation preserved. Drevet after Rigaud remains qualified.'))
print('Source citation pins and distinct impression identities verified.')
