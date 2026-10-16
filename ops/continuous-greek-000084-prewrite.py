#!/usr/bin/env python3
"""Source, global identity, visual review and complete file checks for batch 84."""
import importlib.util,io,json,subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b84',Path(__file__).with_name('continuous-greek-batch-000084.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==4 and not p['new_institutions']
notes={
'Portrait of Antonis Benakis':'Upright male sitter with moustache, light suit and hand at hip, top-left monogram; all supplied canvas edges retained. Distinct from Papanastasiou full-length light-suit portrait and Valsamakis bust. Native reproduction ratio is about 5.7 percent wider than published support ratio; visible supplied edges reviewed, no crop or aspect correction introduced.',
'Belle Epoque Lady [Portrait of Sophia Laskaridou]':'Full-length woman in dark dress and hat, hand at hip, closed parasol, top-left signature/date; complete supplied rectangular canvas edges. Distinct from seated Aristovouli and standing Julia Parthenis portraits in contact sheets.',
'Odeon of Herodes Atticus':'Wide view of arched classical stone theatre with trees and blue openings; complete supplied composition and lower-right signature visible. Distinct from geometric column/building in existing Epidauros.'}
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==3 and not audit['identity_holds'] and not audit['preparation_holds']
files=[];decisions=[];sources=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],note=notes[im['title']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_supplied_proportions=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All three prepared derivatives actually viewed individually in this turn. Originals technically decoded; no claim of separately viewing original files.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files))
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+', '+r['dimensions']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1970 and r['artist_id']=='d0b220dd-6817-4a2b-93a7-01193f38def3'
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],image_selected=r['last']<=1955))
b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
comparison=h.load(b.E.parent/'000075/existing-parthenis-comparison-sheets.json');sheets=[dict(path=x['path'],sha256=x['sha256'],count=len(x['rows'])) for x in comparison['sheets']];last=h.load(b.E.parent/'000075/batches/athens-000/sheets/000.json');sheets.append(dict(path=last['path'],sha256=last['sha256'],count=len(last['images'])))
for x in sheets:assert h.sha(Path(x['path']).read_bytes())==x['sha256']
b.save('actual-existing-composition-review.json',dict(at=h.now(),sheets=sheets,viewed_in_contact_sheets=44,full_size_existing_files_viewed=0,unillustrated_not_visually_reviewed=17,prior_review='docs/research/continuous-production-20261011/batches/000075/actual-existing-composition-review.json',finding='All four immutable prior sheets viewed again this turn. Three newly selected images have distinct compositions from the 44 existing reproductions. All 61 creator records also checked by source/title/inventory/material/dimensions; 14 possible overlaps/units remain held. Aphrodite has no selected or viewed image.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
 for name in ['preserved-parthenis-before.json.gz','aphrodite-global-collision-review.json']:
  old=h.load(b.E/name)['artworks'];assert h.snapshot(db,list(old))==old
 assert len(p['artists'])==1 and h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=4,images=3,no_existing_production_rows=True,global_identity_evidence='final-global-identity-reconciliation.json',shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Four source records, three individually viewed images and scoped recovery passed.')
