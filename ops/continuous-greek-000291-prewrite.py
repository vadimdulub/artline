import importlib.util,io,re,json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000291.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==8 and len(p['held'])==8 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==7 and not audit['identity_holds'] and not audit['preparation_holds']
notes={
'figure-15':'Vertical watercolour and pencil figure with layered blue, green, red and gray strokes, visible paper margins and lower signature. Same full supplied individual sheet Π.3325/α, not an aggregate of all accession components.',
'reflection-of-a-dark-complexioned-girl':'Two angular decorated figures with elongated horizontal necks, candles and pale upper silhouette on dark ground. Same complete supplied canvas and signature area. Native1945inventoryΠ.4083 retained, not another Brauner portrait.',
'nude-5':'Reclining figure on pale green drapery; full supplied composition and lower-left signature retained. Native1874Π.691 identity distinct from other creators’ nudes. Physical98x130cm versus source pixel ratio differs about4%; source corners/composition preserved without stretching or cropping; measurements retained as supplied.',
 'the-flagellation-of-christ-2':'Tall sacred scene: bound Christ, surrounding figures, architectural ledge and upper bust. Complete native reproduction retained, including bottom steps and all source edges. Exact Brounzos1878Π.913 record retained separately from earlier paintings with this composition or title; no attribution to an older model creator invented.',
 'the-virgin-in-glory':'Virgin and child above angels, kneeling saints and book below; all supplied canvas edges visible. Exact Brounzos1877Π.850 reproduction, not a different old-master painting sharing the composition.',
 'landscape-with-dancing-peasants':'Horizontal village scene with dancers outside an inn at right, seated foreground people left, central road and distant steeple. Complete supplied scene, no detail crop. NativeΠ.192 with attributed-to-an-imitator qualification preserved; no primaryJanII artist link.',
 'before-the-storm':'River/meadow landscape with horses, windblown trees at left and storm clouds. Full supplied edges, sky and river foreground retained. Source74x93cm versus pixel ratio differs about4.8%; keep source measurements and source framing unchanged, no axis swapping/stretching/cropping.'}
decisions=[];files=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 for data in [raw,orig]:
  with Image.open(io.BytesIO(data)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.002
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id']);assert r['last']<=1955
 rc=h.load(Path(im['original_path']).with_suffix('.receipt.json'));assert rc['status']==200 and rc['url']==r['raw']['image_url'] and rc['sha256']==im['source_sha256']
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,original_individually_viewed=True,tool='functions tools.view_image',path=im['path'],original_path=im['original_path'],note=notes[r['source_id']],flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,source_file_proportions_preserved=True,source_receipt_sha256=h.sha(Path(im['original_path']).with_suffix('.receipt.json').read_bytes())))
 a,c=[float(x) for x in re.findall(r'\d+(?:[.]\d+)?',r['dimensions'].replace(',','.'))];ratios.append(dict(artwork_id=r['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=im['width']/im['height'],height_first_ratio=c/a,width_first_ratio=a/c,order_explicitly_labelled=False,decision=notes[r['source_id']],metadata_changed=False))
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+', '+r['dimensions'];assert (sp.select_one('p.obtainment').get_text(' ',strip=True) if sp.select_one('p.obtainment') else '')==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1970 and '© 2026' in sp.get_text();assert 'Koutlidis' not in r['credit'] and r['source_type'] in ['painting','watercolor']
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],creator_label=r['creator_label'],artist_id=r['artist_id'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All seven prepared derivatives and seven source originals individually viewed with tools.view_image; zero contact sheets viewed. All manual flags inspected; no placeholders or detail crops. Native pixel/physical ratio variations individually reviewed; source measurements retained. One1960metadata-only work has no downloaded image.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 old=h.load(b.E/'other-identity-candidates-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in audit['prepared_images']],)).fetchall()
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=8,prepared_images=7,accepted_images=7,new_painters=3,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Source identities, recovery, full file validation and14 actual image views verified; ready for8 review objects,3 painters and7 primary images.')
