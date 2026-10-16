import importlib.util,io,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000276.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);assert len(p['records'])==9 and len(p['new_artists'])==4 and not p['new_institutions']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==9 and not audit['identity_holds'] and not audit['preparation_holds']
notes={
 'the-holy-family-after-giulio-romano':'Mary with child, older woman and young John; Joseph in doorway, cradle and basket at bottom, cat at right. Entire supplied canvas reproduced. This is the1864 Louis d’Ambrosio copy, not a Giulio Romano original.',
 'portrait-of-a-lady-4':'Seated woman in rose-red dress, arm resting on chair, dark backdrop; whole supplied canvas retained. Distinct from the oval Eleni portrait and companion male portrait.',
 'portrait-of-eleni-m-negreponti':'Oval portrait of a dark-haired woman resting chin on hand. Museum-supplied red surround retained; oval outline complete and not cropped to rectangle.',
 'portrait-of-a-man-3':'Bearded seated man in black with medal, hands at lap, column at left; canvas edges visible. Same physical inventoryΠ.4118, distinct fromΠ.4119 female portrait.',
 'olive-trees':'Vertical watercolor of dark branching olive trunks and green foliage, signature at lower right. Full supplied paper composition retained; not the Maleas same-title horizontal work.',
 'portrait-of-nina-efkeidi-2356':'Round support with woman in left profile, dark hair and yellow background around head; entire circular edge and museum gray surround retained. Source supplies no dimensions; none inferred.',
 'dancing-hall-for-the-1st-act-of-the-opera-by-w-a-mozart-don-giovanni':'Crayon theatrical set design: grand double staircase, arches, chandeliers, crowd and curving upper outline; complete sheet and blue surround retained. Pictorial stage-design drawing, not a photograph of a constructed set.',
 'near-the-window':'Seated woman sewing beside tall sunlit window, draped white fabric across lap to floor, flowerpot at window and red-covered table at right. All source edges retained.',
 'self-portrait-4089':'Mustached painter with pipe, brush and palette facing easel, open white shirt. Full vertical canvas including signature area retained; not the other same-title inventories in Athens.'
}
decisions=[];files=[];sources=[];ratios=[]
for im in audit['prepared_images']:
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(original)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 r=next(r for r in p['records'] if r['artwork_id']==im['artwork_id']);note=notes[r['source_id']]
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,original_individually_viewed=True,tool='functions tools.view_image',path=im['path'],original_path=im['original_path'],note=note+' Original and derivative each individually viewed; authentic pictorial image, not a placeholder.',flags_reviewed=im['flags']))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,full_supplied_proportions=True))
 if r['dimensions']:
  nums=re.findall(r'\d+(?:[,.]\d+)?',r['dimensions']);assert len(nums)==2;hh,ww=[float(x.replace(',','.')) for x in nums];delta=abs((im['width']/im['height'])/(ww/hh)-1);assert delta<.07
  ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=r['dimensions'],pixel_ratio=im['width']/im['height'],support_ratio=ww/hh,relative_difference=delta,decision='Source physical/pixel proportions reviewed within7%; supplied complete original and derivative visually checked; no crop or metadata rewrite.'))
 else:ratios.append(dict(artwork_id=im['artwork_id'],dimensions_text=None,decision='No physical dimensions supplied; round support visually complete and source-to-derivative proportions unchanged.'))
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'] and date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert sp.select_one('p.description').get_text(' ',strip=True)==r['medium']+(', '+r['dimensions'] if r['dimensions'] else '');assert sp.select_one('p.obtainment').get_text(' ',strip=True)==r['credit']
 tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==r['raw']['image_url'];assert 0<r['first']<=r['last']<=1955 and '© 2026' in sp.get_text()
 sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],inventory=r['accession_number'],source_sha256=r['evidence']['sha256'],creation=r['date_display'],artist_id=r['artist_id'],creator_label=r['creator_label'],museum_credit=r['credit'],holding_confidence=r['holding_confidence'],ownership_not_asserted=True,current_display_not_asserted=True))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All9 prepared originals and all9 derivatives actually individually viewed with view_image. No contact sheet or unrelated existing image review claimed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('source-dimension-review.json',dict(at=h.now(),records=ratios));b.save('prewrite-source-verification.json',dict(at=h.now(),records=sources,plan_sha256=pin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
 old=h.load(b.E/'other-identity-candidates-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
 assert not db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[])',([x['id'] for x in p['new_artists']],)).fetchall()
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=9,images=9,new_painters=4,no_existing_production_rows=True,source_and_visual_checks_complete=True,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Nine sources and image pairs, four creator identities, global identities and scoped recovery verified.')
