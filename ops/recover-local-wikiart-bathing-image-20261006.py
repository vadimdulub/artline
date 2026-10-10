#!/usr/bin/env python3
"""Exact alternate WikiArt painting after the same-titled graphic was rejected."""
import argparse
import copy
import gzip
import importlib.util
import json
import uuid
from pathlib import Path

s=importlib.util.spec_from_file_location('russian',Path(__file__).with_name('recover-local-wikiart-russian-images-20261006.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
wiki,base,core=r.wiki,r.base,r.core
PARENT=r.RUN
RUN=core.ROOT/'docs/research/local-wikiart-bathing-image-20261006'
r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-bathing-alternate-v1'
AID='92b7b4c7-4f0a-495c-94e0-015b53e60db4'
PAGE='https://www.wikiart.org/en/boris-kustodiev/bathing-1921'
CONCORDANCE='Exact oil painting ЖС-569 visually compared: seated figure, birch trunk, townscape, red rug and second bather. Keep both source titles and unchanged catalogue title.'

def snapshot():
 if (RUN/'candidates.json').exists():return
 c=copy.deepcopy(next(x for x in json.loads((PARENT/'candidates.json').read_bytes())['candidates'] if x['artwork_id']==AID))
 with base.connect() as db:
  current=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(AID,)).fetchone()['record']
  if current!=c['before_record'] or current['primary_media_id']:raise ValueError('Local gap changed')
  wiki.chicago.authority_unchanged(db,c)
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 index=core.ROOT/'docs/research/production-wikiart-images-20261006/translated-indexes/ru-boris-kustodiev.json.gz';raw=index.read_bytes();d=json.loads(gzip.decompress(raw));rc=d['receipt'];body=gzip.decompress((core.ROOT/rc['body_path']).read_bytes())
 if core.sha(body)!=rc['sha256'] or len(body)!=rc['bytes'] or json.loads(body)!=d['items']:raise ValueError('Prior alternate metadata changed')
 matches=[x for x in d['items'] if r.urlparse(x['image']).path.split('!',1)[0]=='/images/boris-kustodiev/bathing-1921.jpg']
 if len(matches)!=1 or matches[0]['title']!='Купание' or matches[0]['completitionYear']!=1921:raise ValueError('Alternate metadata identity differs')
 core.save_new(RUN/'alternative-metadata-lead.json',dict(index_path=str(index.relative_to(core.ROOT)),index_sha256=core.sha(raw),receipt=rc,item=matches[0]))
 c.update(page=PAGE,prior_index_lead=matches[0])
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=[c],selection='One existing oil painting, previously held for a different graphic version; alternate WikiArt title/composition individually reviewed. No catalogue metadata updates.'))
 # Reuse same-session, checksum-pinned native object and creator evidence.
 for relative in ['museum/'+AID+'.html','museum/'+AID+'.receipt.json','authors/kustodiev_bm.html','authors/kustodiev_bm.receipt.json']:
  core.save_new(RUN/'metadata'/relative,(PARENT/'metadata'/relative).read_bytes())
 for p in (PARENT/'metadata').glob('*.json'):core.save_new(RUN/'metadata'/p.name,p.read_bytes())
 for p in (PARENT/'metadata/reference-images').glob(AID+'.json'):core.save_new(RUN/'metadata/reference-images'/p.name,p.read_bytes())
 data=(PARENT/'metadata/bathing-alternate.html').read_bytes();oldrc=json.loads((PARENT/'metadata/bathing-alternate.receipt.json').read_bytes())
 if oldrc['url']!=PAGE or core.sha(data)!=oldrc['sha256'] or len(data)!=oldrc['bytes']:raise ValueError('Alternate page capture changed')
 p=RUN/'metadata/pages'/(AID+'.html');newrc=dict(oldrc,requested_url=PAGE,redirects=[],path=str(p.relative_to(core.ROOT)),reused_capture=oldrc)
 core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),newrc)
 review=copy.deepcopy(json.loads((PARENT/'metadata-identity-review.json').read_bytes())['artworks'][AID])
 review.update(wikiart_id='5772756eedc2cb3880ce21b6',wikiart_title='Bathing',individual_title_concordance=CONCORDANCE,reason='Full visual comparison confirms the alternative oil painting; title difference remains explicit.',source_fields=['Original Title: Купание','Date: 1921'])
 core.save_new(RUN/'metadata-identity-review.json',dict(at=core.now(),artworks={AID:review}))
 prior=json.loads((PARENT/'images'/(AID+'.json')).read_bytes())
 core.save_new(RUN/'previous-rejected-version.json',prior)
 core.save_new(RUN/'reused-download.json',(PARENT/'metadata/bathing-alternate-image.json').read_bytes())
 docs=[]
 for source in ('AGENTS.md','docs/ARTLINE_IMAGE_USE.md'):
  data=(core.ROOT/source).read_bytes();capture='metadata/authorization/'+Path(source).name;core.save_new(RUN/capture,data);docs.append(dict(source_path=source,capture=capture,sha256=core.sha(data)))
 core.save_new(RUN/'source-authorization.json',dict(at=core.now(),source='WikiArt',target='local',record_actual_rights_separately=True,documents=docs,user_instruction='see new md file - wiki art is fully approved',scope='Exact alternative image for existing Russian Museum oil painting; preserve old rejected source evidence and both titles.'))
 print('Snapshotted exact alternate oil painting',flush=True)

r.snapshot=snapshot

def prepare():
 im=json.loads((RUN/'selected'/wiki.PROVIDER/(AID+'.json')).read_bytes());wiki.verify_image(im)
 receipt=json.loads((RUN/'reused-download.json').read_bytes());data=Path(receipt['path']).read_bytes()
 if core.sha(data)!=receipt['sha256'] or len(data)!=receipt['bytes'] or receipt['url']!=im['source_image_url']:raise ValueError('Reviewed alternate original differs')
 archive=base.ARCHIVE/'source-images'/RUN.name/(AID+'-'+receipt['sha256'][:16]+'.image');core.save_new(archive,data)
 result,width,height,quality=core.compress(data);digest=core.sha(result);path='/assets/artworks/imported/'+RUN.name+'/'+AID+'-'+digest[:16]+'.jpg'
 core.save_new(core.ROOT/'apps/web/public'/path.lstrip('/'),result)
 im.update(path=path,sha256=digest,bytes=len(result),width=width,height=height,jpeg_quality=quality,source_sha256=receipt['sha256'],source_bytes=len(data),source_archive=str(archive),downloaded_at=receipt['at'],response_headers=receipt['headers'],transform='Full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
 im['raw']['reused_source_download']=receipt
 core.save_new(RUN/'images'/(AID+'.json'),im);base.prepare('contact-sheets-only')

def verify():
 r.verify()
 im=base.prepared()[0];receipt=json.loads((RUN/'reused-download.json').read_bytes())
 if im['raw']['reused_source_download']!=receipt or core.sha(Path(receipt['path']).read_bytes())!=im['source_sha256']:raise ValueError('Original download reuse evidence changed')
 prior=json.loads((RUN/'previous-rejected-version.json').read_bytes())
 if (core.ROOT/'apps/web/public'/prior['path'].lstrip('/')).exists():raise ValueError('Rejected graphic returned to serving')
 with base.connect() as db:
  if db.execute('SELECT 1 FROM media_assets WHERE id=%s',(prior['media_id'],)).fetchone():raise ValueError('Rejected graphic has a database attachment')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':snapshot();wiki.research(1)
 elif a.phase=='apply':base.apply()
 else:globals()[a.phase]()
