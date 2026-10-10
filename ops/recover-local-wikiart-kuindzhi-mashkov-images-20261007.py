#!/usr/bin/env python3
"""Sixteen selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-kuindzhi-mashkov-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-additional-artists-20261007'
core.VERSION='local-wikiart-kuindzhi-mashkov-v1'
SELECTED={'bc4b7d26-d595-40ee-8456-0b89d834d4ee': [236198], '56ce38ea-8c87-4f7c-89d4-029bbe5cbf5f': [236212], '54f61a95-c61c-4a88-a558-5e2549a834a7': [236174], 'b23a0439-3b73-405d-b463-ce4ac6a0c41c': [236099], '2066756c-0b41-4996-9d06-b4c5137cd161': [236183], 'f6a820de-36fc-4606-981d-594ccaaa9c04': [236064], '19c92984-395f-4db4-8f32-d4369ce8bb00': [236156], '77e2af71-b5de-4b78-a711-1a238b40ed0f': [236168], '99ed72b7-5dca-4327-b55b-6689204b48a8': [297563, 297597], 'af58e79d-5e02-4580-a8a7-566b7fb5a75f': [297536], 'e1846754-1f5c-4ebd-be99-87aab5b6c7ff': [297478], 'd73fcf2a-5371-4842-92ee-0cc7f26bd898': [297496], 'ba1f2b13-6061-4a0b-840a-9a1aeae0cb49': [297497], 'a62a7bdf-cd6a-4db3-bd76-43443740c5ac': [297498], 'b2f1af48-c5a0-4519-b103-e37be5faf42a': [297480], '9c3738e7-a7f4-47e3-96f6-86bf4f7275e5': [297469]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({'f392b4f8-aaf3-4932-87e2-c7e43895712f': {'qid': 'Q353628', 'native': 'kuindzhi_ai', 'label': 'Куинджи А. И.', 'life': '1842 (?), Мариуполь Екатеринославской губ. – 1910, Санкт-Петербург', 'birth': 1842, 'death': 1910}, '05bb9f7a-441d-490c-8c98-48b538e2eb88': {'qid': 'Q2704611', 'native': 'mashkov_ii', 'label': 'Машков И. И.', 'life': '1881, ст. Михайловская Саратовской губ. – 1944, Москва', 'birth': None, 'death': None}})
f.SELECTION='Sixteen existing eligible Russian Museum review artworks by Kuindzhi and Mashkov, individually selected from pinned complete source indexes. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
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
 if not 1<=len(result)<=3:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Individually selected titles from the scoped eight-artist metadata audit. Preserve all explicit date differences; a title lead is not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
NATIVE_TITLE_REVIEWS={'9c3738e7-a7f4-47e3-96f6-86bf4f7275e5': {'artwork_id': '9c3738e7-a7f4-47e3-96f6-86bf4f7275e5', 'museum_page': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1725/index.php', 'catalogue_title': 'Хлебы', 'native_title': 'Хлебы. Натюрморт', 'native_accession': 'ЖБ-1725', 'native_period': '1912', 'capture': {'at': '2026-10-07T00:53:40Z', 'bytes': 34144, 'path': 'docs/research/local-wikiart-kuindzhi-mashkov-images-20261007/metadata/museum/9c3738e7-a7f4-47e3-96f6-86bf4f7275e5.html', 'sha256': 'da157ef0e0c109893686b737452abc00b3cda7a48631c0fb226c99d6f0758792', 'url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1725/index.php'}, 'reason': 'Individual literal title concordance on the exact native inventory page: an added generic Still Life/Portrait term or singular begonia wording. Preserve the existing catalogue title and literal current native title separately. Creator, inventory, date, material, dimensions and individual image comparison remain required; no general title normalization.'}, 'ba1f2b13-6061-4a0b-840a-9a1aeae0cb49': {'artwork_id': 'ba1f2b13-6061-4a0b-840a-9a1aeae0cb49', 'museum_page': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1488/index.php', 'catalogue_title': 'Натюрморт с бегониями', 'native_title': 'Натюрморт с бегонией', 'native_accession': 'ЖБ-1488', 'native_period': '1911', 'capture': {'at': '2026-10-07T00:53:37Z', 'bytes': 30506, 'path': 'docs/research/local-wikiart-kuindzhi-mashkov-images-20261007/metadata/museum/ba1f2b13-6061-4a0b-840a-9a1aeae0cb49.html', 'sha256': 'a806d4fb125c016db677aadbd78d488c4b588f4051af7598a04c23f847bec44c', 'url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1488/index.php'}, 'reason': 'Individual literal title concordance on the exact native inventory page: an added generic Still Life/Portrait term or singular begonia wording. Preserve the existing catalogue title and literal current native title separately. Creator, inventory, date, material, dimensions and individual image comparison remain required; no general title normalization.'}, 'e1846754-1f5c-4ebd-be99-87aab5b6c7ff': {'artwork_id': 'e1846754-1f5c-4ebd-be99-87aab5b6c7ff', 'museum_page': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1240/index.php', 'catalogue_title': 'Дама с фазанами', 'native_title': 'Портрет дамы с фазанами', 'native_accession': 'Жб-1240', 'native_period': '1911', 'capture': {'at': '2026-10-07T00:53:35Z', 'bytes': 35077, 'path': 'docs/research/local-wikiart-kuindzhi-mashkov-images-20261007/metadata/museum/e1846754-1f5c-4ebd-be99-87aab5b6c7ff.html', 'sha256': '87283be2d8f5fcc29609b66ab1460ace4e532d237a9b8075e1ceb2c6bca28bc2', 'url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-1240/index.php'}, 'reason': 'Individual literal title concordance on the exact native inventory page: an added generic Still Life/Portrait term or singular begonia wording. Preserve the existing catalogue title and literal current native title separately. Creator, inventory, date, material, dimensions and individual image comparison remain required; no general title normalization.'}}
_native_facts=r.native_facts
def native_facts(c):
 cfg=NATIVE_TITLE_REVIEWS.get(c['artwork_id'])
 if cfg is None:return _native_facts(c)
 if c['title']!=cfg['catalogue_title'] or c['museum_page']!=cfg['museum_page']:raise ValueError('Individual native-title scope differs')
 stored=json.loads((RUN/'native-title-review.json').read_bytes())['artworks'][c['artwork_id']]
 if stored!=cfg:raise ValueError('Individual native-title proof changed')
 import copy
 adapted=copy.deepcopy(c);adapted['title']=cfg['native_title'];facts=_native_facts(adapted)
 if (facts['accession'],facts['period'],facts['capture'])!=(cfg['native_accession'],cfg['native_period'],cfg['capture']):raise ValueError('Individual native-title object evidence differs')
 facts['individual_native_title_concordance']=cfg
 return facts
r.native_facts=native_facts
r.BASIS='Exact existing Russian Museum inventory objects and two verified creator authorities, current selected WikiArt titles/images, preserved source/native/catalogue date and title assertions, and individual physical-version visual comparison. Local missing creator life fields remain null. Actual rights and user approval are separate. Local image-only attachment; no catalogue publication or biography changes.'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
