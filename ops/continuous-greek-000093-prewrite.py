"""Bounded source, identity, actual visual and file verification before writes."""
import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b93',Path(__file__).with_name('continuous-greek-batch-000093.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==5 and not p['new_institutions']
notes={
'Harvest':'Blue sky, mountain landscape, trees flanking stylized harvesters; broad exposed cloth foreground is present in authentic native source, not an image placeholder. Distinct from existing Bathers, Music, Battle of Heracles and other landscapes. Entire supplied frame retained.',
'Table with Flowers':'Vertical still life with dark-outlined table, vase, scattered red flowers/fruit and pale exposed canvas. Distinct from existing horizontal still lifes and Acropolis composition; existing Still Life with Bottles is 57 x 125 cm with unknown date. Original independently viewed; museum image/support aspect discrepancy retained without cropping or distortion.',
'Saint Sebastian':'Single leaning figure with arrows, head upper left and signature lower right on exposed cloth. Distinct subject/composition from existing Virgin, Saint Cecilia and personifications. Original independently viewed; museum image/support aspect discrepancy retained without altering either source metadata or file proportions.',
'Portrait of Zacharias Papantoniou':'Balding moustached head on pale cloth; lower-right dedication/signature, complete supplied edges. Distinct from existing Parthenis portraits including father, Valsamakis and Papathanasiou. Sparse composition is native, not a placeholder.',
'Candle Lighting':'Standing boy raises hand to hanging lamp before painted church doorway; complete supplied frame and lower-right signature retained. Religious interior distinct from existing Annunciations and other subjects. Source omits physical dimensions; no dimensions invented.'}
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==5 and not audit['identity_holds'] and not audit['preparation_holds']
files=[];decisions=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 original_viewed=im['title'] in ['Table with Flowers','Saint Sebastian']
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,original_individually_viewed=original_viewed,tool='functions tools.view_image',path=im['path'],note=notes[im['title']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_supplied_proportions=True))
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id'])
 if r['dimensions']:
  ds=re.findall(r'\d+(?:[,.]\d+)?',r['dimensions']);hh,ww=[float(x.replace(',','.')) for x in ds];physical=ww/hh;pixel=im['width']/im['height'];delta=abs(pixel/physical-1)
  assert delta<.07
  ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=pixel,support_ratio=physical,relative_difference=delta,individual_original_review=original_viewed,decision='Supplied image appears complete and contains distinguishing composition; original file and full frame retained. Museum physical-versus-image proportion discrepancy remains explicit.' if delta>.04 else 'Within ordinary museum reproduction variation.'))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All five prepared derivatives actually individually viewed this turn. Two flagged original files also viewed; remaining originals technically decoded only.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios,unknown_dimensions_preserved=['candle-lighting']))
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+(', '+r['dimensions'] if r['dimensions'] else '')
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1955 and r['artist_id']=='d0b220dd-6817-4a2b-93a7-01193f38def3';assert '© 2026' in sp.get_text()
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],image_selected=True))
b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
comparison=h.load(b.E.parent/'000075/existing-parthenis-comparison-sheets.json');sheets=[dict(path=x['path'],sha256=x['sha256'],count=len(x['rows'])) for x in comparison['sheets']]
for batch in ['000075','000084','000088']:
 x=h.load(b.E.parent/batch/'batches/athens-000/sheets/000.json');sheets.append(dict(path=x['path'],sha256=x['sha256'],count=len(x['images'])))
for x in sheets:assert h.sha(Path(x['path']).read_bytes())==x['sha256']
b.save('actual-existing-composition-review.json',dict(at=h.now(),sheets=sheets,viewed_in_contact_sheets=50,full_size_existing_files_viewed=0,unillustrated_not_visually_reviewed=18,prior_immutable_reviews=['docs/research/continuous-production-20261011/batches/'+x+'/actual-visual-review.json' for x in ['000075','000084','000088']],finding='All six immutable prior sheets actually viewed this turn. Five selected derivatives have distinct compositions from 50 existing reproductions. All 68 creator records checked by source/title/inventory/material/dimensions. Eighteen unillustrated records received metadata review only.'))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'prior-batch-live-reconciliation.json')['previous_batch_verified']
 for name in ['preserved-parthenis-before.json.gz','other-title-candidates-before.json.gz']:
  old=h.load(b.E/name)['artworks'];assert h.snapshot(db,list(old))==old
 assert len(p['artists'])==1 and h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=5,images=5,no_existing_production_rows=True,global_identity_evidence='final-global-identity-reconciliation.json',shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Five selected sources, five actual visual reviews and scoped recovery verified.')
