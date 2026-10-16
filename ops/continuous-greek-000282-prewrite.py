import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000282.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==13 and len(p['new_artists'])==3 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==13 and not audit['identity_holds'] and not audit['preparation_holds']
notes={
'mystras-from-the-palace':'Pale palace walls with arched windows and blue scalloped clouds; signature1927 at lower left. Entire supplied horizontal composition retained.',
'hydra-kaminia':'Ochre terraced coastal settlement, deep blue sea at left, winding stairs and signature1927 at lower right. Entire supplied composition retained; distinct from earlier harbor and breakwater views.',
'ioanna-green-shadows':'Seated short-haired woman in lilac dress holding needlework, angular green facial shadows, signature1927 lower right. Full supplied vertical sheet retained.',
'portrait-of-a-woman-3':'Seated woman in sheer pale blouse and black skirt in a wicker chair, signature lower left. Full supplied vertical canvas retained.',
 'the-hill-of-mystras':'Terraced ochre hill with fortress at top, scattered trees and blue shadow contours, signature1927 lower right. Full supplied horizontal composition retained.',
'mystras-afentiko':'Multiple rounded church roofs with tall square tower at right, terraced hillside and trees. Original and derivative individually compared; same composition and edges. Physical/pixel ratio difference4.3% recorded without alteration.',
'mystras-the-church-of-saints-theodore-ayioi-theodoroi':'Pale church front with broad dome, dark arch below, adjacent ornate facade right and signature1927 lower right. Entire supplied horizontal composition retained.',
'girl-at-window':'Girl in profile leaning at open window, white dog on sill, pink flower and windblown petals. Entire supplied composition retained with blue sky and lower window edge.',
'portrait-of-the-artists-mother':'Woman in black high-neck dress with white lace, gold necklace and pendant, dark background and dated1880 signature below. Complete supplied canvas retained.',
'portrait-of-a-lady-15':'Young woman with black hat and coat and broad white collar; different from five existing portraits actually viewed. Original and derivative preserve the same supplied image, but source63x59cm implies a10.6% ratio discrepancy. Hold attachment pending native full-frame/dimension reconciliation; do not stretch image or correct metadata speculatively.',
'forest-2':'Vertical forest scene with dark trunks, mottled foliage, a pale path and signature lower right. Actual painted image, full supplied composition retained; ca.1955 kept approximate.',
'portrait-of-elia-demidof':'Dark-haired mustached man in a dark suit, left hand in pocket, right hand on balustrade; landscape behind. Complete supplied canvas retained.',
'harmony-3':'Abstract vertical composition of green, lavender, blue, red and yellow curved and angular shapes, signed1940 at lower right. Complete supplied canvas retained.'}
decisions=[];files=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(original)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id']);assert r['last']<=1955
 held=r['source_id']=='portrait-of-a-lady-15';original_viewed=r['source_id'] in ['mystras-afentiko','portrait-of-a-lady-15']
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='hold' if held else 'accept',viewed_individually=True,original_individually_viewed=original_viewed,tool='functions tools.view_image',path=im['path'],original_path=im['original_path'],note=notes[r['source_id']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,source_file_proportions_preserved=True,attachment_accepted=not held))
 hh,ww=[float(x.replace(',','.')) for x in re.findall(r'\d+(?:[,.]\d+)?',r['dimensions'])];delta=abs((im['width']/im['height'])/(ww/hh)-1);assert (delta<.05) if not held else (delta>.10)
 ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=im['width']/im['height'],support_ratio=ww/hh,relative_difference=delta,decision='held_native_dimensions_discrepancy' if held else 'accepted_source_proportions_preserved',metadata_correction=False))
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+(', '+r['dimensions'] if r['dimensions'] else '');credit=sp.select_one('p.obtainment');assert (credit.get_text(' ',strip=True) if credit else '')==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1970 and '© 2026' in sp.get_text();assert 'Koutlidis' not in r['credit'] and r['source_type'] in ['painting','watercolor']
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],creator_label=r['creator_label'],artist_id=r['artist_id'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All13 prepared derivatives individually viewed. Two originals individually viewed; other originals technically decoded only. Twelve images accepted; one image held. No contact sheets viewed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
comparisons=h.load(b.E/'bashkirtseff-composition-candidates.json')['rows'];viewed=[]
for r in comparisons:
 if r['title'] not in ['Portrait of a Young Girl','Self Portrait with Palette','Portrait of Madame X','Paris, Portrait of Irma','Georgette']:continue
 path=b.ROOT/'apps/web/public'/r['storage_path'].lstrip('/');assert h.sha(path.read_bytes())==r['checksum_sha256'];viewed.append(dict(r,path=str(path),viewed_individually=True))
b.save('bashkirtseff-actual-composition-review.json',dict(at=h.now(),records=viewed,decision='Five actually viewed existing portraits differ in sitter appearance, costume, orientation or composition from museumΠ.267. Maria portrait metadata accepted by native inventory; image held separately for source dimension discrepancy. Existing catalogue states preserved.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 old=h.load(b.E/'other-identity-candidates-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
 assert not db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[])',([x['id'] for x in p['new_artists']],)).fetchall()
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=13,prepared_images=13,accepted_images=12,new_painters=3,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Thirteen sources, thirteen visual reviews, twelve accepted images, three painter identities and scoped recovery verified.')
