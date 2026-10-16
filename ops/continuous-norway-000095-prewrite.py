#!/usr/bin/env python3
"""Read-only independent verification of exact batch-95 delivery attribution."""
import base64, fcntl, gzip, hashlib, importlib.util, io, json, re
from pathlib import Path
from urllib.parse import unquote_plus
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-norway-images-000095.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert 1<=len(images)<=12
ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images}
pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=b.h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
before=b.load(b.E/'oslo-bounded-gap-input.json.gz')['states'];assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
source=[];files=[];historical={}
pol=b.load(b.E/'norway-policy.json');raw=gzip.decompress((b.ROOT/pol['receipt']['body_path']).read_bytes());assert b.h.sha(raw)==pol['receipt']['sha256']
assert 'All works not labeled with copyright can be reproduced and published freely' in BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
assert pol['license_links']==['https://creativecommons.org/licenses/by/4.0/deed.en']
for row in [r for r in i.selected(b.B)['rows'] if r['artwork_id'] in expected]:
 aid=row['artwork_id'];im=expected[aid];rc=row['image']['receipt'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert b.h.sha(raw)==rc['sha256'] and rc['status']==200
 text=raw.decode();needle='createSSRApp(Components.SiteLayout, ';ssr,_=json.JSONDecoder().raw_decode(text[text.index(needle)+len(needle):]);c=ssr['child']['component'];obj=c['collectionItemImageComponent']['media'];photo=obj['images'][0]
 assert obj==row['image']['source'] and not obj['copyright'];assert obj['nmId']==row['accession_number']==before[aid]['artwork']['accession_number'];assert obj['producer']==row['creator_label']
 assert photo['photocredit']==row['photographer_credit'] and row['rights_status']=='cc_by'
 sp=BeautifulSoup(raw,'html.parser');assert sp.select_one('meta[property="og:image"]')['content']==im['source_image_url'];assert unquote_plus(im['source_image_url'])==unquote_plus(obj['iiifImageUrlTemplate'].format(photo['originalFile'],'1200',''))
 assert c['downloadImagesModalComponent']['media']==obj
 note=json.loads(row['identity_citation']['evidence_note']);nrc=note['receipt'];path=b.ROOT/nrc['body_path']
 if str(path) not in historical:
  hr=gzip.decompress(path.read_bytes());assert b.h.sha(hr)==nrc['sha256'];historical[str(path)]=json.loads(b'{'+hr+b'}')['hits']
 native=note['source_evidence'];assert native in historical[str(path)] and native['_id']==row['native_id'];assert note['plan_sha256']==row['plan_sha256']
 meta=native['_source']['MetaData'];assert meta['ObjectNumber']==[row['accession_number']]
 fields={}
 for dt in sp.select('.description-list dt'):
  dd=dt.find_next_sibling('dd')
  if dd:fields[dt.get_text(' ',strip=True).rstrip(':')]=dd.get_text(' ',strip=True)
 assert fields['Inventory no.']==row['accession_number'];years=[int(v) for v in re.findall(r'\b[12]\d{3}\b',fields['Creation date'])];assert min(years)==row['first'] and max(years)==row['last']<=1955
 dims=[]
 for d in meta['Dimensions']:
  if d.get('DimensionsCategory')!='Hovedmål' or d['DimensionsType'] not in ['Høyde','Bredde']:continue
  label={'Høyde':'Height','Bredde':'Width'}[d['DimensionsType']];mt=re.search(label+r':\s*([\d.,]+)\s*'+d['DimSizeUnit'],fields['Dimensions']);assert mt and float(mt.group(1).replace(',','.'))==float(str(d['DimensionNum']).replace(',','.'));dims.append(d)
 assert len(dims)==2
 assert b.h.norm(obj['title']) in {b.h.norm(t) for t in note['title_aliases']}
 source.append(dict(artwork_id=aid,inventory=row['accession_number'],native_id=row['native_id'],source_sha256=rc['sha256'],historical_source_sha256=nrc['sha256'],source_plan_sha256=row['plan_sha256'],policy_sha256=pol['receipt']['sha256'],physical_dimensions=dims,native_image=photo['originalFile'],image_copyright_label=obj['copyright'],credit=photo['photocredit'],license=b.LICENSE,same_physical_object=True))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert b.h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and b.h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:
  pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
  assert abs(pic.width/pic.height-float(photo['dimensions']['width'])/float(photo['dimensions']['height']))<.03
 files.append(dict(artwork_id=aid,path=im['path'],bytes=len(raw),sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,prepared_image_actually_viewed=True,original_separately_viewed=False))
b.save(b.E/'prewrite-source-verification.json',dict(at=b.h.now(),records=source,records_verified=len(source)))
b.save(b.E/'prewrite-file-verification.json',dict(at=b.h.now(),files=files,originals_outside_documents=True))

with b.connect() as db:
 live=b.h.snapshot(db,ids)
 for aid in ids:assert live[aid]==before[aid] and live[aid]['artwork']['primary_media_id'] is None
 collisions=db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall();assert not collisions
 for row in [r for r in i.selected(b.B)['rows'] if r['artwork_id'] in expected]:
  aid=row['artwork_id'];decision=next(d for d in review['decisions'] if d['artwork_id']==aid)
  assert decision['sha256']==expected[aid]['sha256'] and decision['viewed_individually'] and decision['decision']=='accept'
  assert row['plan_sha256']==json.loads(row['identity_citation']['evidence_note'])['plan_sha256']
b.save(b.E/'independent-prewrite-verification.json',dict(at=b.h.now(),selection_sha256=pin,visual_review_sha256=rv,individually_viewed=len(ids),source_verified=len(ids),files_verified=len(ids),live_null_primary_ids=ids,duplicate_hashes=0,unchanged_preimages=True))
print('Prewrite:',len(ids),'exact source objects, individually viewed files, rights and unchanged production gaps verified')
