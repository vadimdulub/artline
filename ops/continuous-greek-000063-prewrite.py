#!/usr/bin/env python3
"""Independent source, global identity and every-file checks before batch 63 writes."""
import importlib.util,io,json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b63',Path(__file__).with_name('continuous-greek-batch-000063.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==7 and not p['new_institutions']
notes={
'Three faces':'Three half-length figures, central woman in red, man to right; complete supplied rectangular painting, no detail substitute.',
'Inspired by an Efronios Scene':'Full upright pencil/gouache sheet with two classical draped figures and lower-left inscription; paper and composition edges preserved.',
'Misery':'Dark interior, standing woman and seated man around table and window; full canvas, naturally dark image remains legible.',
'The Rabbin of Paris':'Bust portrait of bearded man in dark hat, signature upper left; supplied painting edges visible, no detail crop.',
'Lycabettus Hill':'Rocky hillside landscape with cypress trees and buildings; full horizontal composition, no borders cropped.'}
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==5 and not audit['identity_holds'] and not audit['preparation_holds']
decisions=[];files=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'];assert len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],note=notes[im['title']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_proportions=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All five prepared derivatives individually viewed in this turn. Originals technically decoded; no claim originals were visually viewed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files))
source=[]
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert r['creator_label']==sp.select_one('p.artist').get_text(' ',strip=True)
 assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+', '+r['dimensions']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1970
 assert r['artist_id']=='a65ed136-54ac-5a00-9d6a-5c77b02de019' or r['source_id']=='lycabettus-hill'
 source.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],creator_label=r['creator_label'],artist_id=r['artist_id']))
b.save('prewrite-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=source))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
 # Names and aliases were checked globally before retaining Kalligas object wording.
 assert not h.load(b.E/'kalligas-expanded-creator-search.json')['rows']
 b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=7,images=5,global_identity_evidence='final-global-identity-reconciliation.json',no_existing_production_rows=True,immutable_plan_backup=str(h.BACKUP/b.PHASE/'plan-preimages.json.gz'),shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Seven source records, five viewed files and global identity checks passed')
