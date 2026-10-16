"""Prewrite verification for the two individually viewed Roilos reproductions."""
import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b171',Path(__file__).with_name('continuous-greek-batch-000171.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==2 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==2 and not audit['identity_holds'] and not audit['preparation_holds']
notes={'Self-portrait':'Dark-haired mustached young man with white collar and black bow tie, three-quarter bust on dark brown background. The supplied canvas frame and proportions are complete. Original and derivative each individually viewed with tools.view_image; not a placeholder. Different creator, inventory and format from the six existing Athens self-portraits.', 'The Battle of Farsala':'Broad dusty cavalry scene, mounted officers at left and right, artillery wheel near center and signature lower right. Full supplied composition and all edges retained. Original and derivative each individually viewed with tools.view_image; not a placeholder. Subject differs from source-labelled charging Evzones and cavalry guard, with independent E.Koutlidis Foundation inventory Κ.433. No visual review of the four unillustrated War Museum objects is claimed.'}
decisions=[];files=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(original)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,original_individually_viewed=True,tool='functions tools.view_image',path=im['path'],original_path=im['original_path'],note=notes[im['title']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_supplied_proportions=True))
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id']);nums=re.findall(r'\d+(?:[,.]\d+)?',r['dimensions']);hh,ww=[float(x.replace(',','.')) for x in nums];delta=abs((im['width']/im['height'])/(ww/hh)-1);assert delta<.07
 ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=im['width']/im['height'],support_ratio=ww/hh,relative_difference=delta,decision='Museum source physical/pixel ratio discrepancy individually reviewed; supplied original and derivative both complete-frame. No crop and no dimensions rewrite.' if delta>.04 else 'Source proportions agree within ordinary rounding.'))
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+', '+r['dimensions'];assert sp.select_one('p.obtainment').get_text(' ',strip=True)==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1955 and r['artist_id']=='e17bd3cc-0953-5aa6-9e0e-00a16419379d';assert '© 2026' in sp.get_text()
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],ownership_not_asserted=True,current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All two prepared originals and all two derivatives actually individually viewed. Existing creator records and four War Museum source citations reviewed as metadata only; no claim to have viewed unavailable existing images.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 for name in ['preserved-roilos-scoped-before.json.gz','other-identity-candidates-before.json.gz']:
  old=h.load(b.E/name)['artworks'];assert h.snapshot(db,list(old))==old
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=2,images=2,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Two selected sources, originals/derivatives, global identities and scoped recovery verified.')
