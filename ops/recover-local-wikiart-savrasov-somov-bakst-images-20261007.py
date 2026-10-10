#!/usr/bin/env python3
"""Twenty-three selected Savrasov, Somov and Bakst gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-savrasov-somov-bakst-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-next-artists-20261007'
core.VERSION='local-wikiart-savrasov-somov-bakst-v1'
SELECTED={'46524a04-77a6-40c3-8ef1-3a3ffbec2d43': [237229], 'da043e2b-2f14-42f9-a6bf-6497f5563ee6': [237238], '956cafdf-0f84-44bf-ba04-c0284127f294': [237053], 'a14116bb-5310-4d1f-b88e-d7317b5a3a2a': [237221], 'c1e47202-ea48-47e0-8865-82679d1b0e66': [237200], '3f9fa574-f943-4119-8dcf-3aa63ce66d58': [237030], '3eb91a80-41d8-4f54-ae6b-7573df1c4bed': [237208], 'd4823d64-b796-4bfb-a0b2-0a89c852b62b': [237101], 'dec51e46-a9e0-4f3f-a2aa-338b6b23f704': [237101], 'f8dbfc45-c34d-41e8-be3f-14955bdbed02': [237109], '64ac0e9c-0259-40ba-b398-f0310c96e489': [237093], '0827792e-4601-4653-82de-6584b6fb56a1': [237088], '0f5f88a4-32ca-4a27-9e5d-a036028cbd1a': [237062, 237064, 237072, 237065, 237073], 'c75d5bbf-b846-4760-9c89-d27ded4fa436': [237055], 'c5cd7165-8b87-493e-a390-fdc3f198927f': [237187], '0a1c6aae-5d90-4e18-aa52-5bd14595c353': [239264, 239265, 239266, 239263, 239267], 'a4a59827-c66f-43da-8ec3-e715686746f7': [239264, 239265, 239266, 239263, 239267], 'da89ebfe-39b8-480a-90c4-3a06ac516c9d': [239264, 239265, 239266, 239263, 239267], 'a4a2a171-ae78-4936-82e7-a94f4c8d1026': [239086], '30c360a6-27b4-44d8-bfa9-71220f116be1': [239301], '1b80ccd8-a5b5-493e-9abe-b2618c9f97b3': [239176, 239177], '4117735e-a651-4649-81a0-df6986db1f90': [239120, 239121, 239122], '5224389e-92d9-420d-aa92-ea2057d0e5c4': [188227]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=5
r.ARTISTS.update({'3ea9c74c-ebe7-44ff-933c-e48081f4e885': {'qid': 'Q353008', 'native': 'savrasov_ak', 'label': 'Саврасов А. К.', 'life': '12 (24) мая 1830, Москва — 1897, Москва', 'birth': 1830, 'death': 1897, 'life_aliases': ['12 [24] мая 1830, Москва — 1897, Москва']}, '492a20ac-5901-4624-9bf2-ed904fcda1e3': {'qid': 'Q433067', 'native': 'somov_ka', 'label': 'Сомов К. А.', 'life': '1869, Петербург – 1939, Париж', 'birth': 1869, 'death': 1939}, '2b407655-09cc-4688-9e44-df92ae4ac301': {'qid': 'Q214666', 'native': 'bakst_ls', 'label': 'Бакст Л. С.', 'life': '1866, Гродно – 1924, Париж', 'birth': 1866, 'death': 1924}})
f.SELECTION='Twenty-three eligible missing-image records by Savrasov, Somov and Bakst. Individually enumerated same-title options include five alternatives for Early Spring and each Somov self-portrait; this bound applies only to this operation. Current creator and native object review, bounded exact-title alternatives and individual source photograph comparisons required. Preserve all dates, unknown fields, holdings and review status.'
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
 if not 1<=len(result)<=5:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='All exact-title alternatives individually enumerated from the complete pinned source index. Five options are retained only for the specifically selected Early Spring and self-portrait records; other records have one to three. Title/date similarity is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'da043e2b-2f14-42f9-a6bf-6497f5563ee6': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/savrasov_ak_vid_na_moskovskiy_kreml_vesna_1873_zh2845/3105_mainfoto_03.jpg', 'c1e47202-ea48-47e0-8865-82679d1b0e66': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/savrasov_ak_zakat_nad_bolotom_1871_zh_5979/2693_mainfoto_03.jpg', '0a1c6aae-5d90-4e18-aa52-5bd14595c353': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._avtoportret._nachalo_1890-h._r-58447/19835_mainfoto_03.jpg', 'a4a59827-c66f-43da-8ec3-e715686746f7': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._avtoportret._1895._r-6565/19814_mainfoto_03.jpg', 'da89ebfe-39b8-480a-90c4-3a06ac516c9d': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._avtoportret._1898._r-6559/19732_mainfoto_03.jpg', 'a4a2a171-ae78-4936-82e7-a94f4c8d1026': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._bosket._1898-1899._r-8363/19731_mainfoto_03.jpg', '30c360a6-27b4-44d8-bfa9-71220f116be1': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/somov_ka_osmeyanniy_poceluy_1908_zh_2112/4550_mainfoto_03.jpg', '1b80ccd8-a5b5-493e-9abe-b2618c9f97b3': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._peyzazh_s_radugoy._1899._r-8492/19820_mainfoto_03.jpg', '4117735e-a651-4649-81a0-df6986db1f90': 'https://rusmuseumvrm.ru/data/collections/drawings/somov_k._a._feyerverk._1920._r-54768/19831_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

ENGLISH_TITLE_REVIEWS={'5224389e-92d9-420d-aa92-ea2057d0e5c4': {'page': 'https://www.wikiart.org/en/leon-bakst/self-portrait', 'wikiart_id': '57726e65edc2cb3880b6c7d6', 'wikiart_title': 'Self Portrait', 'catalogue_title': 'Автопортрет', 'note': "Individual English-title concordance for native Ж-2119: WikiArt 'Self Portrait' and catalogue 'Автопортрет'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The current source Original Title field remains absent; the separately captured translated index has the literal title Автопортрет. No current-page original-language field is invented.", 'source_index_title': 'Автопортрет', 'proof_sha256': '8725321c9869d074b6fc8ea588fee3902285a17f34177f4319af70b1271b7083'}}
r.BASIS='Exact existing native museum objects, creator authorities, selected current WikiArt pages and individually compared physical versions. One source page has no Original Title field; its literal English title, unchanged catalogue titles, checksum-pinned translated index title Автопортрет and visual evidence are individually reconciled. Preserve source date discrepancies, image framing, actual rights and unchanged catalogue metadata. Local image-only attachment; no publication or invented source fields.'
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

UNKNOWN_DATE_REVIEWS={'5224389e-92d9-420d-aa92-ea2057d0e5c4': {'page': 'https://www.wikiart.org/en/leon-bakst/self-portrait', 'wikiart_id': '57726e65edc2cb3880b6c7d6', 'wikiart_title': 'Self Portrait', 'page_sha256': '4f2a0ac20dcf048639df5faf47104c64612ecc533e1d587b8211deac178e2850', 'accession': 'Ж-2119', 'period': '1893', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh-2119/index.php', 'catalogue_date': {'creation_year_start': 1893, 'creation_year_end': 1893, 'date_precision': 'exact', 'date_display': '1893'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-2119, whose creation period is 1893. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1893 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

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
