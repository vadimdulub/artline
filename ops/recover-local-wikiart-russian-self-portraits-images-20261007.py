#!/usr/bin/env python3
"""Six existing Russian Museum self-portrait drawings, reviewed individually."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-self-portraits-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-russian-self-portraits-v1'
f.IDS=['230b7e15-4007-49af-9344-99269433d965','85330fe8-b0df-4195-b118-da808ea268ad','bbbebb8b-7cad-4f52-8c3a-bd59ffe66c06','e4bfef6e-c1a0-459e-8799-e3e9f4b4f605','4773071a-2dfe-4d6a-ad72-e91c699b7637','efd8276d-88b9-49df-a494-b79aa3935698']
f.DATE_VARIANT_IDS=set(f.IDS)
f.MAX_SOURCE_OPTIONS=7
f.SELECTION='Six existing eligible Russian Museum self-portrait drawings by Kustodiev, Bryullov and Serov. Bounded same-subject source alternatives are selected from captured artist indexes before downloads. Exact native composition and physical-version comparison decide attachment. Preserve catalogue metadata, unknown fields and review state.'
r.ARTISTS['676b2231-17dd-4012-8b95-c57cef5f33b4']=dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911)
CONCORDANCES={
 ('230b7e15-4007-49af-9344-99269433d965','self-portrait-1904-1','Автопортрет. 1902.jpg','Автопортрет'):
 'Individual title concordance for Р-53189: the source Original Title literally contains Автопортрет. 1902.jpg, a filename-like suffix. The explicit source Date and exact native drawing are 1904. Preserve the literal field as an anomaly; do not infer a 1902 creation date or normalize other source titles.',
 ('e4bfef6e-c1a0-459e-8799-e3e9f4b4f605','self-portrait-1904','Автопортрет. 1902.jpg','Автопортрет'):
 'Individual title concordance for Р-49273: the source Original Title literally contains Автопортрет. 1902.jpg, a filename-like suffix. The explicit source Date and exact native drawing are 1904. Preserve the literal field as an anomaly; do not infer a 1902 creation date or normalize other source titles.',
 ('85330fe8-b0df-4195-b118-da808ea268ad','self-portrait-1914','Автопортрет. 1902.jpg','Автопортрет'):
 'Individual title concordance for Р-8127: the source Original Title literally contains Автопортрет. 1902.jpg, a filename-like suffix. The explicit source Date and exact native drawing both state 1910–1914. Preserve the literal field as an anomaly; do not infer a 1902 creation date or normalize other source titles.',
 ('bbbebb8b-7cad-4f52-8c3a-bd59ffe66c06','self-portrait-1918','Автопортрет. 1902.jpg','Автопортрет'):
 'Individual title concordance for РС-801: the source Original Title literally contains Автопортрет. 1902.jpg, a filename-like suffix. The explicit source Date, visible inscription and exact native drawing are 1918. Preserve the literal field as an anomaly; do not infer a 1902 creation date or normalize other source titles.',
}
for (aid,slug,source_title,local_title),note in CONCORDANCES.items():
 r.TITLE_CONCORDANCES[(aid,'https://www.wikiart.org/en/boris-kustodiev/'+slug,source_title,local_title)]=note

def source_options(c,options):
 choices={
  '230b7e15-4007-49af-9344-99269433d965':('boris-kustodiev',[230194,230195,230196]),
  'e4bfef6e-c1a0-459e-8799-e3e9f4b4f605':('boris-kustodiev',[230194,230195,230196]),
  '85330fe8-b0df-4195-b118-da808ea268ad':('boris-kustodiev',[230191,230197,230188,230192,230198]),
  'bbbebb8b-7cad-4f52-8c3a-bd59ffe66c06':('boris-kustodiev',[230200]),
  '4773071a-2dfe-4d6a-ad72-e91c699b7637':('karl-bryullov',[204389,204390,204391,204392,204393,204394]),
  'efd8276d-88b9-49df-a494-b79aa3935698':('valentin-serov',[237452,237453,237454,237455,237456,237451]),
 }
 slug,ids=choices[c['artwork_id']]
 artist,artist_id={
  'boris-kustodiev':('Boris Kustodiev','0604627e-59cd-4203-82b2-9aa77423e5cc'),
  'karl-bryullov':('Karl Bryullov','366c4612-1b9a-4240-8749-ab9512e2d390'),
  'valentin-serov':('Valentin Serov','676b2231-17dd-4012-8b95-c57cef5f33b4'),
 }[slug]
 if c['creator_links'][0]['artist_id']!=artist_id:raise ValueError('Selected creator changed')
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes'/(slug+'.json.gz')
 data=path.read_bytes();index=json.loads(gzip.decompress(data));receipt=index['receipt'];body=gzip.decompress((core.ROOT/receipt['body_path']).read_bytes())
 if core.sha(body)!=receipt['sha256'] or len(body)!=receipt['bytes'] or json.loads(body)!=index['items']:raise ValueError('Pinned artist index differs')
 selected=[]
 for cid in ids:
  items=[i for i in index['items'] if i['contentId']==cid]
  if len(items)!=1 or items[0]['artistName']!=artist:raise ValueError('Unique self-portrait identity absent')
  item=items[0];filename=item['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg')
  selected.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+filename,prior_index_lead=item))
 reason='Individually selected dated self-portrait alternatives. Kustodiev uses the native year/range; Serov uses six dated versions because no source index entry states native 1883. Exact physical-version review still required.'
 if slug=='karl-bryullov':reason='The three nearer-date Bryullov candidates do not depict native unfinished drawing Р-2225. Extend this single record to the other three indexed dated self-portraits before concluding that it remains unmatched; preserve all earlier evidence.'
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=receipt,artwork_id=c['artwork_id'],original_title_leads=options,options=selected,reason=reason))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
