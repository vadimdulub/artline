#!/usr/bin/env python3
"""Twenty-five individually selected Konchalovsky gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-konchalovsky-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-next-artists-20261007'
core.VERSION='local-wikiart-konchalovsky-v1'
SELECTED={'1a8531ba-84a3-4a40-be64-8b81a2d53aea': [263610], '8c1755f3-b116-4858-855a-93a364273ea4': [263617], 'd15945d1-4165-46ee-8a15-f79682243176': [263779], '4f3b8f06-9be2-4dca-93c6-4feea4abac2f': [263712], 'fdb88164-3bd4-443a-8230-4c5e9eafe833': [263798], '6dda2296-8184-4071-8478-6fbac1f62252': [263817], '5cedc5f7-494a-4051-adb5-dc27ed6bbfe7': [263646, 263647, 263648, 263649], '6748748a-24df-4cb6-a88e-7eaab3a97f0b': [263580, 263575], '3be9003f-c36b-44ec-80c9-a8e98b88359e': [263576], '27ca3034-edbe-4fc0-b4d1-cf9668003bea': [264167], '8603edfe-795e-41f5-816e-8442f80c7856': [264272], '8d4e58d8-0935-4018-824d-76a1f31832e4': [264243], 'e84830df-936c-4118-adda-6827f52f2286': [263908, 263909, 263910], '39f909cd-0c9e-4f1e-88de-5421f5236c6f': [263912], '0f18718b-44b4-4b52-ac78-4edfa284e607': [263907], '80f9a66a-6bc4-4a83-a83f-add35d32e025': [263918], '97fa02d9-77bc-4eda-83b9-19ff53a8ecd6': [263944], 'ced29429-3321-4e80-8cad-a6408e666104': [263964], '87029197-3d58-4d70-93be-7f20ccafb225': [264021], '755971a2-11f6-4e04-a6fa-4e6f8a2656ff': [264027], 'c5526876-282b-4bb7-8b2e-59c5081b1612': [264001], '8e4ce378-772b-4ca2-9ed3-d5aefb8d3bd7': [264141], 'aa57a554-402e-4421-a4e6-8473b2f9517a': [263719], '2537da59-99e2-488c-bd7e-9946d12e154f': [264129], '0388baed-fc68-4017-acc2-7b3df5778e63': [263808]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({'56f7387e-f5dc-424d-a6f9-150d8aefb9c8': {'qid': 'Q2626131', 'native': 'konchalovskiy._pp', 'label': 'Кончаловский П. П.', 'life': '1876, Славянск Харьковской губ. – 1956, Москва', 'birth': None, 'death': None}})
f.SELECTION='Twenty-five eligible missing-image Konchalovsky records. Unknown local artist birth/death fields stay null; literal native creator biography and QID provide independent identity evidence. Current creator and native object review, bounded exact-title alternatives and individual source photograph comparisons required. Preserve all dates, unknown fields, holdings and review status.'
CONCORDANCES={}
r.TITLE_CONCORDANCES.update(CONCORDANCES)
def source_options(c,options):
 audit=json.loads((r.AUDIT/'discovery.json').read_bytes());lead=next(x for x in audit['leads'] if x['work']['id']==c['artwork_id']);slug=lead['source_artist_slug']
 pin=next(x for x in audit['source_pins'] if x['path'].endswith('/ru-'+slug+'.json.gz'));raw=(core.ROOT/pin['path']).read_bytes()
 if core.sha(raw)!=pin['sha256']:raise ValueError('Pinned complete index changed')
 idx=json.loads(gzip.decompress(raw));body=gzip.decompress((core.ROOT/idx['receipt']['body_path']).read_bytes())
 if core.sha(body)!=idx['receipt']['sha256'] or len(body)!=idx['receipt']['bytes'] or json.loads(body)!=idx['items'] or idx['receipt']!=pin['source_receipt']:raise ValueError('Original index capture differs')
 result=[]
 for cid in SELECTED[c['artwork_id']]:
  matches=[i for i in idx['items'] if i['contentId']==cid]
  if len(matches)!=1:raise ValueError('Individually selected index item absent')
  item=matches[0];name=urlparse(item['image']).path.split('/')[-1].split('!',1)[0].removesuffix('.jpg')
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=4:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Exact-title candidates selected from the complete pinned same-creator index, including every listed same-title alternative. Similar titles and dates are leads only; current metadata and direct native/source comparison must establish the physical version.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'d15945d1-4165-46ee-8a15-f79682243176': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/konchalovskiy_p._p._gerkules_i_omfala._1928._zhs-1065/21634_mainfoto_03.jpg', '5cedc5f7-494a-4051-adb5-dc27ed6bbfe7': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/konchalovskiy_p._p._most._1911._zhs-953/24912_mainfoto_03.jpg', 'ced29429-3321-4e80-8cad-a6408e666104': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/konchalovskiy_p.p._portret_geroya_sovetskogo_soyuza_letchika_a.b.yumasheva._1941._zh-5601/14078_mainfoto_03.jpg', 'aa57a554-402e-4421-a4e6-8473b2f9517a': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/konchalovskiy_pp__semeyniy_portret_1911/2717_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
