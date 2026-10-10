#!/usr/bin/env python3
"""Fifteen selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-four-artists-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-additional-artists-20261007'
core.VERSION='local-wikiart-russian-four-artists-v1'
SELECTED={'37f7ead2-6ea1-43cd-8083-de2ee5771055': [196968, 196969, 196972, 196973], '186c79ac-9b24-47e1-a025-fa0666456c95': [196485, 196486, 196583, 196614, 196608, 196633], '425312ef-a8cd-49ec-83f4-833c4b875842': [196574, 196575, 196576, 196577, 196599, 196579, 196605, 196586, 196587, 196584], 'dfaef9ba-4c3a-42d5-afa4-aa4981bb2c76': [196723], '7d34e018-225c-483a-9975-5796845e97ff': [196659, 196665], '2c87fc63-b969-4f8b-a1bf-63bda3e97a39': [196428, 196429, 196430], '3336eeb8-627d-4304-a094-7052ca404033': [196876], 'bce1fdf5-5782-4bf5-906e-8c7562e22a24': [228366, 228365], '65f04295-3c1b-4c18-b591-3ec1efb772c8': [249974, 249975], '132854f1-48a7-4422-95b8-30026af15e4a': [249844], '64e7532e-f8e7-484a-a17b-150ed1ba913d': [240937], '58744927-d2c3-406c-b3ee-1c3934a1a680': [240928], 'dbf983a5-949f-4e10-b2f1-7914a89bc24b': [240697], '38738652-4c11-4229-8697-d09fe4d30b54': [240700, 240701], 'ada80d33-aced-4dac-9bd8-69aa66d73026': [240860, 240861]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=7


r.ARTISTS.update({'0fbcd264-1ede-4d64-ad69-7f4bc33b9963': {'qid': 'Q181568', 'native': 'ayvazovsky_ik', 'label': 'Айвазовский И. К.', 'life': '1817, Феодосия — 1900, там же', 'birth': 1817, 'death': 1900}, 'a26d1473-2041-4049-b433-63a0ab9cdd4e': {'qid': 'Q215100', 'native': 'vrubel_ma', 'label': 'Врубель М. А.', 'life': '1856, Омск – 1910, Санкт-Петербург', 'birth': 1856, 'death': 1910}, '0931acb7-c3ce-410c-826a-4272a7b010cd': {'qid': 'Q318393', 'native': 'polenov_vd', 'label': 'Поленов В. Д.', 'life': '1844, Санкт-Петербург – 1927, усадьба Борок Тульской губ.', 'birth': 1844, 'death': 1927}, '7d6d8851-01f6-40fc-bc8f-461371f9ea6d': {'qid': 'Q110228', 'native': 'surikov_vi', 'label': 'Суриков В. И.', 'life': '1848, Красноярск – 1916, Москва', 'birth': 1848, 'death': 1916}})
f.SELECTION='Fifteen remaining exact-title Russian Museum review artworks by Aivazovsky, Vrubel, Polenov and Surikov, individually selected from pinned complete source indexes. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
CONCORDANCES={('7d34e018-225c-483a-9975-5796845e97ff', 'https://www.wikiart.org/en/ivan-aivazovsky/portrait-of-senator-alexander-ivanovich-kaznacheyev-1848', 'Портрет сенатора Александра Ивановича Казначеева', 'Портрет А. И. Казначеева'): "Individual literal title concordance for native Ж-1778: WikiArt 'Портрет сенатора Александра Ивановича Казначеева' and catalogue 'Портрет А. И. Казначеева'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
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
  if cid==196485:
   list_url='https://www.wikiart.org/en/ivan-aivazovsky/all-works/text-list';data,rc=r.capture(list_url,RUN/'metadata/canonical-pages/aivazovsky-list.html');links={urljoin(list_url,a['href']) for a in r.BeautifulSoup(data,'html.parser').select('a[href]')}
   canonical='https://www.wikiart.org/en/ivan-aivazovsky/constantinople-1856'
   if canonical not in links:raise ValueError('Exact canonical Aivazovsky page missing from current list')
   core.save_new(RUN/'metadata/canonical-pages/constantinople-1856.json',dict(capture=rc,content_id=cid,index_image=item['image'],canonical_page=canonical,reason='Literal current artist-list URL differs from the updated image filename; page/image identity is independently validated before selection.'))
   name='constantinople-1856'
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=10:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Individually selected titles from the scoped eight-artist metadata audit. Preserve all explicit date differences; a title lead is not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact existing Russian Museum inventory objects, four verified creator authorities, current WikiArt source pages and individual visual comparisons across same-title versions. Preserve dates, unknown metadata, rights and review status. No catalogue publication or biography change.'

NATIVE_REFERENCE_ALIASES={'37f7ead2-6ea1-43cd-8083-de2ee5771055': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/ayvazovskiy_ik_vid_konstantinopolya_1846_zh_1787/5517_mainfoto_03.jpg', '186c79ac-9b24-47e1-a025-fa0666456c95': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/ayvazovskiy_ik_konstantinopol_1882_zh_12119/5546_mainfoto_03.jpg', 'dfaef9ba-4c3a-42d5-afa4-aa4981bb2c76': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/ayvazovskiy_ik_morskoy_proliv_s_mayakom_1841_zh_7914/5537_mainfoto_03.jpg', '7d34e018-225c-483a-9975-5796845e97ff': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/ayvazovskiy_ik_portret_ai_kaznacheeva_1848_zh_1778/5507_mainfoto_03.jpg', '132854f1-48a7-4422-95b8-30026af15e4a': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/polenov_v._d._moskovskiy_dvorik._1902._zh-4210/18679_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

import copy
TRANSLATED_TITLES={'37f7ead2-6ea1-43cd-8083-de2ee5771055': {'page': 'https://www.wikiart.org/en/ivan-aivazovsky/view-of-constantinople-by-moonlight-1846', 'page_sha256': 'feb40fdc92e0b15efca81f91ae2c23f0790adf4277a01cc10d93d82377341cf9', 'wikiart_id': '57726fceedc2cb3880bbca25', 'wikiart_title': 'View of Constantinople by Moonlight', 'catalogue_title': 'Вид Константинополя', 'native_accession': 'Ж-1787', 'native_period': '1846'}}
_original_page_facts=wiki.page_facts
def translated_page_facts(c,data,rc):
 aid=c['artwork_id'];cfg=TRANSLATED_TITLES.get(aid)
 if not cfg:return _original_page_facts(c,data,rc)
 chosen=f.selected(c);review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][aid];native=r.native_facts(chosen)
 if native!=review['native_facts'] or review['decision']!='continue_to_visual_review':raise ValueError('Individual translated native version differs')
 if (native['accession'],native['period'],chosen['title'])!=(cfg['native_accession'],cfg['native_period'],cfg['catalogue_title']):raise ValueError('Translated native object changed')
 if (rc['url'],review['selected_page'],review['wikiart_id'],review['wikiart_title'])!=(cfg['page'],cfg['page'],cfg['wikiart_id'],cfg['wikiart_title']) or core.sha(data)!=cfg['page_sha256'] or rc['sha256']!=cfg['page_sha256']:raise ValueError('Frozen translated source page differs')
 soup=r.BeautifulSoup(data,'html.parser')
 if any(li.get_text(' ',strip=True).startswith('Original Title:') for li in soup.select('.wiki-layout-artwork-info article li')):raise ValueError('Original-title source presentation changed')
 proof=json.loads((RUN/'translated-title-review.json').read_bytes())[aid]
 if any(proof[k]!=v for k,v in cfg.items()) or proof['artwork_id']!=aid or proof['note']!=review['reason']:raise ValueError('Individual translated title proof differs')
 raw=(core.ROOT/proof['index_path']).read_bytes()
 if core.sha(raw)!=proof['index_sha256']:raise ValueError('Pinned Russian index differs')
 d=json.loads(gzip.decompress(raw));body=gzip.decompress((core.ROOT/d['receipt']['body_path']).read_bytes())
 if core.sha(body)!=d['receipt']['sha256'] or len(body)!=d['receipt']['bytes'] or json.loads(body)!=d['items'] or d['receipt']!=proof['receipt']:raise ValueError('Pinned Russian API capture differs')
 i=proof['item']
 if d['items'].count(i)!=1 or i!=chosen['prior_index_lead'] or (i['contentId'],i['title'],i['completitionYear'])!=(196973,'Вид Константинополя в лунном свете',1846):raise ValueError('Individual Russian expanded-title lead differs')
 visual=[v for v in json.loads((RUN/'alternative-visual-review.json').read_bytes())['options'] if v['artwork_id']==aid and v['page']==cfg['page']]
 if len(visual)!=1 or visual[0]['decision']!='approved' or visual[0]['selected_for_attachment'] is not True or visual[0]['visually_inspected'] is not True:raise ValueError('Translated-title physical version not approved')
 for image in [visual[0]['private_source_download'],visual[0]['reference_capture']]:
  b=Path(image['path']).read_bytes()
  if core.sha(b)!=image['sha256'] or len(b)!=image['bytes']:raise ValueError('Translated-title image comparison changed')
 adapted=copy.deepcopy(chosen);adapted.update(external_id=cfg['wikiart_id'],alternate_title=cfg['wikiart_title'])
 facts=r.original_facts(adapted,data,rc)
 if urlparse(facts['source_image_url']).path.split('!',1)[0]!=urlparse(i['image']).path.split('!',1)[0]:raise ValueError('Translated source photograph differs')
 facts.update(native_object_review=review,native_original_title=None,individual_title_concordance=proof)
 return facts
wiki.page_facts=translated_page_facts

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
