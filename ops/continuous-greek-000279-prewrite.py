import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000279.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==11 and len(p['new_artists'])==3 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==5 and not audit['identity_holds'] and not audit['preparation_holds']
notes={
 'wildflowers-in-a-vase':'Red poppies and pale daisies in a clear round glass vase, scattered flowers on tabletop, pale curtain, signature lower right. Full supplied rectangular composition retained.',
 'vase-with-roses':'Pink roses in tall dark-blue vase with gold rim/base, fallen petal at left and signature lower right, pale folded curtain behind. Complete supplied vertical composition retained.',
 'almond-flowers-9035':'Flowering almond branches in a green vase with flowers scattered on tabletop, patterned cloth at lower left and signature lower right. Full supplied vertical image and edges retained.',
 'maroussi-2':'Grove with dark branching trunks, green and russet foliage and small yellow-hatted worker near center, vertical signature lower right. Full supplied canvas retained. This1950 inventory differs from the existing1958 Maroussi cypress composition by date,dimensions,collection and native identity.',
 'hydra-view-with-breakwater':'Light watercolor of terraced white buildings, hills, boats and figures along diagonal breakwater, blue and violet sea bands at bottom and signed1927 lower right. Whole supplied sheet preserved; distinct from the undated harbor-entrance notice.'
}
decisions=[];files=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(original)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id']);assert r['last']<=1955
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,original_individually_viewed=True,tool='functions tools.view_image',path=im['path'],original_path=im['original_path'],note=notes[r['source_id']]+' Original and derivative each actually viewed individually; genuine pictorial reproduction, not a placeholder. Source-defined approximate dates retained.',flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_supplied_proportions=True))
 nums=re.findall(r'\d+(?:[,.]\d+)?',r['dimensions']);assert len(nums)==2;hh,ww=[float(x.replace(',','.')) for x in nums];delta=abs((im['width']/im['height'])/(ww/hh)-1);assert delta<.05
 ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=im['width']/im['height'],support_ratio=ww/hh,relative_difference=delta,decision='Source physical/pixel proportions within5%; original and derivative visually checked, complete supplied composition and proportions retained. No metadata or geometry correction.'))
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+(', '+r['dimensions'] if r['dimensions'] else '');assert sp.select_one('p.obtainment').get_text(' ',strip=True)==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1970 and '© 2026' in sp.get_text()
 assert 'Koutlidis' not in r['credit'] and r['source_type'] in ['painting','watercolor']
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],creator_label=r['creator_label'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All5 prepared originals and all5 derivatives actually individually viewed with view_image. No contact sheet or unselected images claimed visually reviewed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 old=h.load(b.E/'other-identity-candidates-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
 assert not db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[])',([x['id'] for x in p['new_artists']],)).fetchall()
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=11,images=5,new_painters=3,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Eleven sources, five image pairs, three painter identities and scoped recovery verified.')
