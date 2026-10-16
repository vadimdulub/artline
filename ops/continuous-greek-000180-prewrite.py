"""Prewrite verification for the two individually viewed Roilos reproductions."""
import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b171',Path(__file__).with_name('continuous-greek-batch-000180.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==4 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==4 and not audit['identity_holds'] and not audit['preparation_holds']
notes={'The Pharmacist Dicopoulos':'Seated elderly man in dark hat and coat; spoon and jar at left and paper in his lower hand. Full source edges retained in original and derivative. Both individually viewed; actual portrait, no placeholder.', 'The Lady with the Black Veil':'Woman with black veil and lace collar holding a green fan; coat of arms in upper left. Complete supplied rectangle and proportions retained; original and derivative individually viewed.', 'Self-Portrait':'Bearded painter-priest in dark cap beside religious painting, holding inscribed sheet; palette and brushes at right. Full composition, lower garment and source edges retained. Both individually viewed. Separate inventory Π.2978 from other artists’ same-title portraits.', 'Elisabeth Moutzan-Martinegko':'Young woman with blue ribboned headdress, light shawl and striped bodice, holding a closed book. Original and derivative individually viewed; full supplied frame retained.'}
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
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+', '+r['dimensions'];assert (sp.select_one('p.obtainment').get_text(' ',strip=True) if sp.select_one('p.obtainment') else '')==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1955 and r['artist_id']==b.NEW_ARTIST;assert '© 2026' in sp.get_text()
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],ownership_not_asserted=True,current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All four originals and all four derivatives actually individually viewed with tools.view_image. No visual review claimed for held or existing catalogue objects.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 for name in ['preserved-ionian-scoped-before.json.gz']:
  old=h.load(b.E/name)['artworks'];assert h.snapshot(db,list(old))==old
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=4,images=4,new_painters=1,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Four selected sources, originals/derivatives, globally reconciled painter and scoped recovery verified.')
