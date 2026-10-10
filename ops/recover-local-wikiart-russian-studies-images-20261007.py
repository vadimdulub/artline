#!/usr/bin/env python3
"""Five existing Russian Museum drawings, distinguished from painted versions."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-studies-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-russian-drawing-studies-v1'
f.IDS=['b3739730-6844-4f6f-a8c3-5e85b7b4dff8','7157ac5d-1553-4765-a933-38f470262823','8169b974-ea78-4cc8-8495-7410700bc6de','de9593fe-0287-44b0-834b-8a9008773ec1','a4583426-82b1-4cf0-83e9-c02a39271d44']
f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=6
f.SELECTION='Five existing eligible Russian Museum review drawings: four Bryullov studies and Kustodiev Shrovetide. Select bounded metadata alternatives before downloads, distinguish physical sheets from finished paintings and other versions, preserve catalogue facts and actual rights evidence.'
CONCORDANCES={}

def source_options(c,options):
 aliases={
  204258:'in-a-harem-by-allah-s-order-underwear-should-be-changed-once-a-year-1-1835',
  204259:'in-a-harem-by-allah-s-order-underwear-should-be-changed-once-a-year-2',
  204260:'in-a-harem-by-allah-s-order-underwear-should-be-changed-once-a-year-3',
  204274:'mark-the-evangelist-1847',
 }
 if any(o['prior_index_lead']['contentId'] in aliases for o in options):
  url='https://www.wikiart.org/en/karl-bryullov/all-works/text-list';data,rc=r.capture(url,RUN/'metadata/canonical-pages/bryullov-list.html')
  links={urljoin(url,a['href']) for a in r.BeautifulSoup(data,'html.parser').select('a[href]')}
  updated=[]
  for o in options:
   cid=o['prior_index_lead']['contentId'];page='https://www.wikiart.org/en/karl-bryullov/'+aliases[cid]
   if page not in links:raise ValueError('Exact current source page link absent')
   updated.append(dict(o,page=page))
  core.save_new(RUN/'metadata/canonical-pages'/(c['artwork_id']+'.json'),dict(capture=rc,original_index_leads=options,options=updated,reason='Literal source-page links from the current artist list; image filenames include (1), while these four page slugs do not. No general filename normalization.'))
  return updated
 if c['artwork_id']!='a4583426-82b1-4cf0-83e9-c02a39271d44':return options
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes/boris-kustodiev.json.gz';data=path.read_bytes();d=json.loads(gzip.decompress(data));rc=d['receipt'];body=gzip.decompress((core.ROOT/rc['body_path']).read_bytes())
 if core.sha(body)!=rc['sha256'] or len(body)!=rc['bytes'] or json.loads(body)!=d['items']:raise ValueError('Pinned English index differs')
 selected=[]
 for cid in [230214,230215,230323,230212,230213]:
  rows=[x for x in d['items'] if x['contentId']==cid]
  if len(rows)!=1 or rows[0]['artistName']!='Boris Kustodiev' or rows[0]['completitionYear'] not in (1919,1920):raise ValueError('Selected Shrovetide study identity differs')
  i=rows[0];slug=i['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg')
  selected.append(dict(page='https://www.wikiart.org/en/boris-kustodiev/'+slug,prior_index_lead=i))
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=rc,artwork_id=c['artwork_id'],original_title_leads=options,options=selected,reason='Three selected 1919 scenes depict other compositions. Add the two individually selected 1920 Shrovetide versions to check for the native 1919 stage design. Preserve source/catalogue date differences; exact native sheet comparison decides identity.'))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
