#!/usr/bin/env python3
"""Twenty remaining selected Russian Museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-next-final-leads-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-next-artists-20261007'
core.VERSION='local-wikiart-russian-next-final-leads-v1'
SELECTED={'ffdc499d-de25-4109-9da2-ced51eacbee2': [264574, 297864, 297865, 297866], 'aa7c30c6-138f-4f4f-af93-b83e7bb4528b': [253034], '33ccce8c-67ed-4f0e-8a36-5cbf3aef83c6': [252951], 'b27b3796-ce9f-4d3c-a124-a9a60afd33a6': [252990], '1cba2c6f-e101-44f1-b6fb-c81ba149b5df': [252954], '970ac77a-e5d7-4eeb-a174-bcfa56c13b84': [252954], '10d5782b-e906-4a0a-a73a-decedb797cd5': [252955, 252956, 252957], '74bd5021-297a-4018-b614-3be10dd71b3d': [252955, 252956, 252957], '08a6a898-476a-45f8-8312-c18619f734a4': [241109], 'a5cdc454-86a2-4726-88de-e5690711bbca': [241106], '1859aae8-6142-4d4b-88e2-efdb373b9786': [241257], '2b8e7122-504f-4e9f-9468-09548716ee19': [241265], '3604f75b-0e08-43cb-949d-ee3def6f6a69': [241234, 241235], 'e06a2c51-3db0-4ecd-8944-ff3d3d1da1e7': [237789, 237788], '994489c3-23fb-4e37-a6e7-3378fa507f26': [190104], '29c837c9-0544-4540-b8b6-7beb4b0f17a7': [237513], '3c79c12f-cc08-4c10-9272-a774fdc5e23b': [237513], '643772ee-b969-4d3f-b63a-81fcecf28818': [195252, 195209, 195237, 195210], '7244d5c4-e5a0-430f-acd4-41792e536cb9': [195252, 195209, 195237, 195210], 'a8135509-f8d2-449a-aded-4261c6f9e856': [195243]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({'8a0471a0-2057-4581-ba13-8dc6619b96b7': {'qid': 'Q972018', 'native': 'dobuzhinskiy_mv', 'label': 'Добужинский М. В.', 'life': '1875, Новгород –1957, Нью-Йорк', 'birth': None, 'death': None}, 'f2d9b939-c731-4d52-ba93-a5338a5f1a40': {'qid': 'Q457976', 'native': 'ge_nn', 'label': 'Ге Н. Н.', 'life': '1831, Воронеж — 1894, хутор Ивановское Борзенского уезда Черниговской губ.', 'birth': 1831, 'death': 1894}, 'eae0e638-46d2-48a9-9184-ce689744916b': {'qid': 'Q434561', 'native': 'tropinin_va', 'label': 'Тропинин В. А.', 'life': '1776, дер. Карпово Чудовской волости Новгородской губ. – 1857, Москва', 'birth': 1776, 'death': 1857}, 'c45644cd-418c-49e5-8ffb-cdf923611bfd': {'qid': 'Q127017', 'native': 'vereschagin_vv', 'label': 'Верещагин В. В.', 'life': '1842, Череповец Новгородской губ. – 1904, Порт-Артур', 'birth': 1842, 'death': 1904}, '017b8272-39ce-424b-a3bf-4d2c86b5f363': {'qid': 'Q1095289', 'native': 'borisov_musatov_ve', 'label': 'Борисов-Мусатов В. Э.', 'life': '1870, Саратов – 1905, Таруса Калужской губ.', 'birth': 1870, 'death': 1905}, '86017b07-9804-4e56-92dc-e4e4e5e065b5': {'qid': 'Q204138', 'native': 'vasnecov_vm', 'label': 'Васнецов В. М.', 'life': '1848, село Лопиял Вятской губернии – 1926, Москва', 'birth': 1848, 'death': 1926}, 'a453d605-6758-4c46-9d87-27a55dc2b569': {'qid': 'Q262098', 'native': 'borovikovskiy_vl', 'label': 'Боровиковский В. Л.', 'life': '1757, Миргород –1825, Санкт-Петербург', 'birth': 1757, 'death': 1825}})
r.ARTISTS['eae0e638-46d2-48a9-9184-ce689744916b']['life_aliases']=['1780, дер. Карпово Чудовской волости Новгородской губ. – 1857, Москва']
f.SELECTION='Twenty remaining eligible missing-image leads across seven artists. Native creator, inventory, scope, exact source and individual physical-version comparison required. One current native creator conflict is held without any identity exception or image download. Unknown local creator fields, all dates, holdings and review status preserved.'
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
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='All exact-title alternatives enumerated from the complete pinned source index: one option per record except the three Death of Virginia versions for each of two native paintings. Native creator and exact physical-version review are required; title matching is only a lead.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'08a6a898-476a-45f8-8312-c18619f734a4': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/tropinin_v._a._gitarist._1839._zh-5230/19275_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

ENGLISH_TITLE_REVIEWS={'643772ee-b969-4d3f-b63a-81fcecf28818': {'page': 'https://www.wikiart.org/en/vladimir-borovikovsky/paul-i-1800', 'wikiart_id': '57726f70edc2cb3880ba9951', 'wikiart_title': 'Paul I', 'catalogue_title': 'Портрет Павла I', 'note': "Individual English-title concordance for native Ж-5015: WikiArt 'Paul I' and catalogue 'Портрет Павла I'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The current source Original Title field remains absent; the separately captured translated index has the literal title Павел I. No current-page original-language field is invented.", 'source_index_title': 'Павел I', 'proof_sha256': '706f0428611dc03e80ec0a0524bff4960b0f3a37106057049da302e824f7a1bc'}, '7244d5c4-e5a0-430f-acd4-41792e536cb9': {'page': 'https://www.wikiart.org/en/vladimir-borovikovsky/paul-i', 'wikiart_id': '57726f70edc2cb3880ba9961', 'wikiart_title': 'Paul I', 'catalogue_title': 'Портрет Павла I', 'note': "Individual English-title concordance for native Ж-3170: WikiArt 'Paul I' and catalogue 'Портрет Павла I'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The current source Original Title field remains absent; the separately captured translated index has the literal title Павел I. No current-page original-language field is invented.", 'source_index_title': 'Павел I', 'proof_sha256': '63a182b7f0e926ecc605666883242613f8d8896ba50ad0f907b069fa2440c5c4'}}
r.BASIS='Exact existing native museum objects, creator authorities, selected current WikiArt pages and individually compared physical versions. Two source pages have no Original Title field; its literal English title, unchanged catalogue titles, checksum-pinned translated index title Павел I and visual evidence are individually reconciled. Preserve source date discrepancies, image framing, actual rights and unchanged catalogue metadata. Local image-only attachment; no publication or invented source fields.'
original_page_facts=wiki.page_facts
def page_facts(c,data,rc):
 aid=c['artwork_id'];cfg=ENGLISH_TITLE_REVIEWS.get(aid)
 if cfg is None:return original_page_facts(c,data,rc)
 chosen=f.selected(c);review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][aid];native=r.native_facts(chosen)
 if native!=review['native_facts'] or review['decision']!='continue_to_visual_review':raise ValueError('Individual English/native object review changed')
 if (review['selected_page'],review['wikiart_id'],review['wikiart_title'],c['title'],review.get('individual_english_title_concordance'))!=(cfg['page'],cfg['wikiart_id'],cfg['wikiart_title'],cfg['catalogue_title'],cfg['note']):raise ValueError('Individual English-title concordance changed')
 if rc['url']!=cfg['page']:raise ValueError('Individually reviewed English source page differs')
 soup=r.BeautifulSoup(data,'html.parser')
 if any(li.get_text(' ',strip=True).startswith('Original Title:') for li in soup.select('.wiki-layout-artwork-info article li')):raise ValueError('English-only source presentation changed')
 proof=json.loads((RUN/'english-title-review.json').read_bytes())['artworks'][aid]
 if core.sha(core.encode(proof))!=cfg['proof_sha256']:raise ValueError('Individual English-title proof changed')
 if proof['source_capture']['sha256']!=core.sha(data) or proof['source_capture']['bytes']!=len(data) or rc['sha256']!=core.sha(data):raise ValueError('Reviewed English source capture changed')
 option=next(o for o in chosen['source_options'] if o['page']==cfg['page'])
 if proof['source_option']!=option or chosen['prior_index_lead']!=option['prior_index_lead'] or proof['native_facts']!=native or proof['note']!=cfg['note'] or proof['source_original_title'] is not None:raise ValueError('Reviewed English/native source identity changed')
 pin=proof['complete_index_pin'];raw=(core.ROOT/pin['path']).read_bytes()
 if core.sha(raw)!=pin['sha256']:raise ValueError('Pinned translated source index changed')
 index=json.loads(gzip.decompress(raw));body=gzip.decompress((core.ROOT/index['receipt']['body_path']).read_bytes())
 if core.sha(body)!=index['receipt']['sha256'] or len(body)!=index['receipt']['bytes'] or json.loads(body)!=index['items'] or index['receipt']!=pin['source_receipt']:raise ValueError('Untranslated source index capture differs')
 item=option['prior_index_lead']
 if item['title']!=cfg['source_index_title'] or proof['source_index_title']!=cfg['source_index_title'] or index['items'].count(item)!=1 or item['contentId'] not in SELECTED[aid]:raise ValueError('Exact translated index entry absent')
 matches=[v for v in json.loads((RUN/'alternative-visual-review.json').read_bytes())['options'] if v['artwork_id']==aid and v['page']==cfg['page']]
 if len(matches)!=1 or matches[0]['selected_for_attachment'] is not True or matches[0]['decision']!='approved' or matches[0]['visually_inspected'] is not True:raise ValueError('Exact English/native visual comparison absent')
 v=matches[0]
 if (proof['source_download'],proof['native_reference'],proof['version_note'])!=(v['private_source_download'],v['reference_capture'],review['reason']):raise ValueError('English/native comparison evidence changed')
 for image_rc in [proof['source_download'],proof['native_reference']]:
  payload=Path(image_rc['path']).read_bytes()
  if core.sha(payload)!=image_rc['sha256'] or len(payload)!=image_rc['bytes']:raise ValueError('English/native comparison image changed')
 adapted=dict(chosen,external_id=cfg['wikiart_id'],alternate_title=cfg['wikiart_title']);facts=r.original_facts(adapted,data,rc)
 if urlparse(facts['source_image_url']).path.split('!',1)[0]!=urlparse(item['image']).path.split('!',1)[0]:raise ValueError('Untranslated source photograph differs')
 facts.update(native_object_review=review,native_original_title=None,individual_english_title_concordance=proof)
 return facts
wiki.page_facts=page_facts

UNKNOWN_DATE_REVIEWS={'1859aae8-6142-4d4b-88e2-efdb373b9786': {'page': 'https://www.wikiart.org/en/vasily-tropinin/portrait-of-pavel-vasilyev', 'wikiart_id': '5772775eedc2cb3880d465bd', 'wikiart_title': 'Portrait of Pavel Vasilyev', 'page_sha256': '642a9fe7ac61467abf6fd3cd074c556d43d3de772f80778b6f7855a73991258d', 'accession': 'Ж-3669', 'period': '1830-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/zh-3669/index.php', 'catalogue_date': {'creation_year_start': 1830, 'creation_year_end': 1839, 'date_precision': 'decade', 'date_display': '1830-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-3669, whose creation period is 1830-е. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1830-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, 'a5cdc454-86a2-4726-88de-e5690711bbca': {'page': 'https://www.wikiart.org/en/vasily-tropinin/girl-with-a-candle', 'wikiart_id': '57727756edc2cb3880d45f8d', 'wikiart_title': 'Girl with a candle', 'page_sha256': '90e1665a2d186ce6522136e87bf097066d151d520caad9139dca93a6e2e32044', 'accession': 'Ж-5226', 'period': '1840-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/zh-5226/index.php', 'catalogue_date': {'creation_year_start': 1840, 'creation_year_end': 1849, 'date_precision': 'decade', 'date_display': '1840-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-5226, whose creation period is 1840-е. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1840-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, 'aa7c30c6-138f-4f4f-af93-b83e7bb4528b': {'page': 'https://www.wikiart.org/en/nikolai-ge/the-head-of-john-the-apostle', 'wikiart_id': '5772797fedc2cb3880db590a', 'wikiart_title': 'The head of John the Apostle', 'page_sha256': 'd462c3b381b799b172676240509a3f0a7e676c8ef9a0328573129a2dd8db730a', 'accession': 'Ж-4148', 'period': 'Этюд для картины «Тайная вечеря» (1863), находящейся в ГРМ. 1862-1863', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh-4148/index.php', 'catalogue_date': {'creation_year_start': 1862, 'creation_year_end': 1863, 'date_precision': 'range', 'date_display': '1862-1863'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-4148, whose creation period is Этюд для картины «Тайная вечеря» (1863), находящейся в ГРМ. 1862-1863. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1862-1863 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, '7244d5c4-e5a0-430f-acd4-41792e536cb9': {'page': 'https://www.wikiart.org/en/vladimir-borovikovsky/paul-i', 'wikiart_id': '57726f70edc2cb3880ba9961', 'wikiart_title': 'Paul I', 'page_sha256': 'd21e65196222428801a58abf68f29c728e2f4ab89bb9dbb18f81cfed526e83f9', 'accession': 'Ж-3170', 'period': '1800', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/18_19/zh_3170/index.php', 'catalogue_date': {'creation_year_start': 1800, 'creation_year_end': 1800, 'date_precision': 'exact', 'date_display': '1800'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-3170, whose creation period is 1800. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1800 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

def source_date_review(c,record,soup,rc,data):
 aid=c['artwork_id'];cfg=UNKNOWN_DATE_REVIEWS.get(aid)
 if not cfg or (rc['url'],record.get('_id'),record.get('year'))!=(cfg['page'],cfg['wikiart_id'],'?'):
  raise ValueError('Unknown source date has no individual native date/version approval')
 if core.sha(data)!=cfg['page_sha256'] or rc['sha256']!=cfg['page_sha256']:raise ValueError('Individually reviewed undated source page changed')
 if any(li.find('s') and wiki.norm(li.find('s').get_text(' ',strip=True))=='date' for li in soup.select('.wiki-layout-artwork-info article > ul > li')):raise ValueError('Unknown source date presentation changed')
 catalogue={k:c[k] for k in ['creation_year_start','creation_year_end','date_precision','date_display']}
 if catalogue!=cfg['catalogue_date']:raise ValueError('Reviewed catalogue creation scope changed')
 review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][aid];native=review['native_facts']
 if review['decision']!='continue_to_visual_review' or review['selected_page']!=cfg['page'] or review['wikiart_id']!=cfg['wikiart_id']:raise ValueError('Individual unknown-date version review absent')
 if (native['accession'],native['period'],native['capture']['url'])!=(cfg['accession'],cfg['period'],cfg['native_url']):raise ValueError('Native inventory/date differs')
 data_native=(RUN/'metadata/museum'/(aid+'.html')).read_bytes()
 if core.sha(data_native)!=native['capture']['sha256'] or len(data_native)!=native['capture']['bytes']:raise ValueError('Native date capture changed')
 matches=[v for v in json.loads((RUN/'alternative-visual-review.json').read_bytes())['options'] if v['artwork_id']==aid and v['page']==cfg['page']]
 if len(matches)!=1 or matches[0]['decision']!='approved' or matches[0]['selected_for_attachment'] is not True or matches[0]['visually_inspected'] is not True:raise ValueError('Exact undated version comparison missing')
 v=matches[0]
 for rc_image in [v['private_source_download'],v['reference_capture']]:
  b=Path(rc_image['path']).read_bytes()
  if core.sha(b)!=rc_image['sha256'] or len(b)!=rc_image['bytes']:raise ValueError('Individual date/version image changed')
 expected=dict(artwork_id=aid,page=cfg['page'],wikiart_id=cfg['wikiart_id'],page_sha256=cfg['page_sha256'],source_structured_year='?',source_year_start=None,source_year_end=None,source_displayed_date=None,native_facts=native,catalogue_date=catalogue,scope_basis='Individual exact-object visual comparison and the literal native creation period establish pre-1971 eligibility. Approximate dates and ranges remain approximate; no exact year is inferred.',version_note=review['reason'],source_download=v['private_source_download'],native_reference=v['reference_capture'],decision='eligible_exact_native_version',note=cfg['note'])
 proof=json.loads((RUN/'unknown-source-date-review.json').read_bytes())[aid]
 if proof!=expected:raise ValueError('Frozen individual date review differs')
 return proof
wiki.SOURCE_DATE_REVIEW=source_date_review


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
