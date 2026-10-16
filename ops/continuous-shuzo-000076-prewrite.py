#!/usr/bin/env python3
import importlib.util,io,json,gzip
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-shuzo-000076.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==6 and not audit['identity_holds'] and not audit['preparation_holds']
notes={
'6261':'Charcoal female portrait; entire paper sheet visible with upper corner inscriptions and adjacent color calibration card. Full supplied photograph retained.',
'16859':'Tall willow-and-kingfisher painting, bird at left and lower inscription; all painting edges visible, mount and calibration labels M1758 retained.',
'16862':'Tall hanging scroll with fruit branch below calligraphy; source M1761 label matches museum inventory crosswalk. Entire painted paper, mount and calibration context retained.',
'16863':'Narrow flowering branch/chestnut composition under calligraphy, literal source title Hermit in Autumn Mountain retained. M1762 label matches museum record. Full painted sheet and supplied photographic context retained.',
'16865':'Tall branch with two orange persimmons, pale leaves and upper-right inscription. M1764 native label. Complete painted sheet, supplied mount and calibration context retained.',
'16866':'Tall pale figure composition, figure below center and inscription upper left, M1765 native label. All painted silk edges visible; faint original tones and photographic context retained.'}
files=[];decisions=[];sources=[]
for im in audit['prepared_images']:
 r=next(x for x in p['records'] if x['artwork_id']==im['artwork_id']);raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 for data,expected in [(raw,(im['width'],im['height'])),(orig,tuple(im['original_dimensions']))]:
  with Image.open(io.BytesIO(data)) as pic:pic.verify()
  with Image.open(io.BytesIO(data)) as pic:pic.load();assert pic.size==expected
 assert abs(im['width']/im['height']-im['original_dimensions'][0]/im['original_dimensions'][1])<.01
 decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],note=notes[r['source_id']],flags_reviewed=im['flags'],physical_ratio_review='Museum dimensions concern painted support; native photograph includes mounting/background/calibration cards. Supplied composition and proportions preserved, no crop or warp.'))
 files.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=im['bytes'],complete_decode=True,original_complete_decode=True,full_frame=True,actually_viewed=True))
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'];sp=BeautifulSoup(raw,'html.parser');section=sp.get_text(' ',strip=True).split('検索トップ')[-1].split('1．コレクション')[0]
 assert all(x in section for x in [r['accession_number'],r['raw']['original_title'],r['dimensions'],'Public Domain','岸田劉生',str(r['first'])])
 source=next(x for x in h.load(b.E/'shuzo-kishida-rows.json') if x['id']==r['raw']['shuzo_id']);assert source['title']['en']==r['title'] and source['accessionNumber']==r['accession_number'] and source['url']==r['source_url'] and source['yearLabel']['en']==r['date_display']
 assert r['first']==r['last'] and r['last']<=1970 and r['artist_id']==b.NEW_ARTIST and r['raw']['medium'][0]['ja'] in section
 sources.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],source_sha256=r['evidence']['sha256'],shuzo_capture_sha256=r['shuzo_receipt']['sha256'],title=r['title'],original_title=r['raw']['original_title'],date=r['date_display'],inventory=r['accession_number'],source_image_url=r['raw']['image_url'],rights='Public Domain'))
review=dict(at=h.now(),batch_quality_decision='accept',decisions=decisions,scope='All six prepared derivatives viewed individually in this turn. Original files fully decoded; no claim of separately viewing originals. Museum calibration cards/background retained because full supplied frame is required.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files));b.save('prewrite-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=sources))
rc=h.load(b.E/'shuzo-artist-A1293-capture.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
for s in ['岸田劉生','KISHIDA Ryūsei','1891-06-23','1929-12-20','60362067','500121267','Q3021493']:assert s in text
with h.connect() as db:
 assert not h.snapshot(db,[r['artwork_id'] for r in p['records']]);cr=b.creator_matches(db);assert not cr['matches'] and not cr['authority_matches']
 for r in p['records']:assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED'
b.save('authorization.json',dict(at=h.now(),scope='User explicitly authorized source-backed production painters, artworks, authentic images and museum holdings; no further approval required. Batch 76 only.',source_policy='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',rights='Native Aichi image-specific Public Domain statements and museum commercial-use terms; user authorization recorded separately, not a licence.',shuzo='Registry metadata-discovery-only rule preserved: source images obtained only after resolving selected records to explicit native Aichi reuse evidence.'))
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=6,new_artist=1,new_institution=1,images=6,shared_lock='artline-curated-ingestion',all_global_identity_checks_passed=True,local_catalogue_connections=0,source_verification='prewrite-source-verification.json',file_verification='prewrite-file-verification.json',visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),recovery='local-recovery-verification.json'))
print('Six records and individually viewed images verified; one new source-backed painter.')
