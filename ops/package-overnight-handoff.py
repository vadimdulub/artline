#!/usr/bin/env python3
"""Validate and package the dated metadata handoff, excluding raw image/dumps."""
import ast,csv,hashlib,importlib.util,json,re,zipfile
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE;ROOT=BASE/'chatgpt-handoff/final-20260914';ARCHIVE=ROOT.parent/'artline-research-20260914-chatgpt.zip'
def main():
 assert not ARCHIVE.exists(),'Preserve the delivered archive; use a new package phase for changed data'
 csv.field_size_limit(20000000);csv_checks={};ids=set();slugs=set();missing=[];exceptions={'wikimedia-artwork-q26997957','wikimedia-artwork-q27000045'};image_count=0;pending_images=0
 for path in sorted(ROOT.glob('*.csv')):
  count=0
  with path.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f);assert reader.fieldnames and len(set(reader.fieldnames))==len(reader.fieldnames)
   for row in reader:
    assert None not in row and all(v is not None for v in row.values()),(path,count,'column mismatch')
    for key,value in row.items():assert not value.lstrip().startswith(('=','+','-','@')) and not value.startswith(('\t','\r','\n')),(path,count,key,'formula-leading unescaped literal')
    if path.name.startswith('artwork_identity_index_'):
     assert row['local_artwork_id'] not in ids and row['artwork_slug'] not in slugs;ids.add(row['local_artwork_id']);slugs.add(row['artwork_slug'])
    if path.name=='artworks_added_active.csv':
     assert row['status']=='review' and row['artist_slugs']
     if not row['artist_country_codes']:assert row['artwork_slug'] in exceptions and all(c['role']=='formerly_attributed_to' for c in json.loads(row['creator_roles']))
     if not row['production_artwork_id']:missing.append(row['artwork_slug'])
    if path.name=='verified_selected_images.csv':
     image_count+=1;assert row['license_url'] and row['creator_credit'] and row['source_page_url'] and int(row['byte_size'])<=100000
     if row['production_upload_verified']=='false':pending_images+=1;assert not row['production_image_url']
    count+=1
  csv_checks[path.name]=dict(rows=count,sha256=CORE.sha(path.read_bytes()))
 assert len(ids)==len(slugs)==231630 and missing==['wikimedia-artwork-q21619670'];assert image_count==1535 and pending_images==29
 for path in ROOT.glob('*.json'):json.loads(path.read_text())
 for path in ROOT.glob('*.md'):
  for ref in re.findall(r'\]\(([^)]+)\)',path.read_text()):
   if not re.match(r'^[a-z]+://',ref) and not ref.startswith('#'):assert (path.parent/ref.split('#')[0]).exists(),(path,ref)
 scripts=[p for p in (m.x.ROOT/'ops').glob('*.py') if any(word in p.name for word in ('overnight','country','finnish','portuguese')) or p.name in ('apply-greek-primary-images.py','apply-wikimedia-catalogues.py','artline-db-access.py','import-michelangelo-frescoes.py')]
 for path in scripts:ast.parse(path.read_text(),filename=str(path))
 validation=dict(at=CORE.now(),csv_files=len(csv_checks),csv_checks=csv_checks,unique_artwork_identities=len(ids),selected_images=image_count,images_pending_production=pending_images,active_additions_missing_public_production_id=missing,expected_former_attribution_country_exceptions=sorted(exceptions),json_parsed=True,local_markdown_links_resolve=True,research_scripts_syntax_checked=len(scripts),test_scope='25 country counterexample tests and5 image-source tests passed separately; no database fixtures or test DB. Durable connection helper tested with a real read-only local query. Production reauthentication remains unresolved.')
 CORE.save_new(ROOT/'PACKAGE_VALIDATION.json',validation)
 files=[]
 for path in sorted(ROOT.iterdir()):
  assert path.is_file() and path.suffix in ('.csv','.json','.md'),path
  files.append(dict(name=path.name,bytes=path.stat().st_size,sha256=CORE.sha(path.read_bytes())))
 manifest=dict(at=CORE.now(),files=files,policy='Metadata, literal CSVs, reports, image-source links and audit receipts only. No database dumps, raw museum metadata exports, credentials or original/derivative image binaries. All additions remain in review. Local/prod differences are explicit.',local=dict(gross_added_artworks=2718,gross_added_creator_profiles=610,active_added_artworks=2707,verified_image_assets=1535,active_primary_images=1525,painter_duplicates=60,artwork_duplicates=438),production=dict(gross_added_artworks=2717,gross_added_creator_profiles=610,verified_uploaded_image_assets=1506,observed_active_primary_images=1496,painter_duplicates=56,artwork_duplicates=238,reauthentication_pending=True),country_scope_rounds=240,country_scope_rounds_verified_both=220,ten_main_countries_with_twenty_rounds_each=True,portugal=dict(research_rounds=20,prepared_candidates=74,explicit_holds=8,local_readonly_potential_additions=66,local_imported=0,production_imported=0))
 CORE.save_new(ROOT/'PACKAGE_MANIFEST.json',manifest)
 with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for path in sorted(ROOT.iterdir()):z.write(path,path.name)
 with zipfile.ZipFile(ARCHIVE) as z:
  assert z.testzip() is None
  for item in manifest['files']:assert CORE.sha(z.read(item['name']))==item['sha256']
 receipt=dict(at=CORE.now(),archive=str(ARCHIVE),bytes=ARCHIVE.stat().st_size,sha256=CORE.sha(ARCHIVE.read_bytes()),zip_crc_verified=True,manifest_entries_sha256_verified=True,files=len(files)+1,csv_files=len(csv_checks));CORE.save_new(ARCHIVE.with_suffix('.receipt.json'),receipt);print('Final handoff archive verified',json.dumps(receipt),flush=True)
if __name__=='__main__':main()
