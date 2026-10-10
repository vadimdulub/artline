#!/usr/bin/env python3
"""Sixteen individually selected Russian Museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-further-versions-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-further-artists-20261007'
core.VERSION='local-wikiart-russian-further-versions-v1'
SELECTED={'0ca9fbc9-260c-4b82-9940-79d37510c7cd': [203616, 203617, 203771], 'd374c9f3-cf7b-4ed8-b136-a7137ae51a22': [203705], 'dbf7a4da-8a16-4154-afed-2ce0db4bb148': [203705], 'c5067000-0dce-42ef-97ef-609071cc4685': [203586], '80603bc6-d6af-403f-8ed0-e041d4c179d9': [256575, 256577, 256573], '87c24e9f-41ac-4ccb-a03d-a5719006fb1e': [256575, 256577], 'fd4054b8-f49a-41b4-b20d-2f92eb3f084b': [256617], 'af7604fe-d149-4f94-a652-f9256f55cb37': [256488], 'bbfff33d-6aa6-4ac7-b923-91610bb81223': [256639, 267371], 'e50e0ad4-ddbd-4adf-ba37-2d5e7dbfdd50': [256639], 'c583d3a0-5301-4961-a9f5-ff34f5e834df': [256601], '5fab8504-abcc-4365-9236-fa5fde6f715a': [256651, 256653], '443fef56-cbc5-4ab9-a341-8d2979004a31': [270398], 'ac9bd0e7-04ca-4628-8f51-f3ff9e1dc1ea': [256431], '60b4ef6e-a593-42a9-ad69-109383173b7e': [256432], '871b1ebb-d87f-4ec4-b923-d985b18f0911': [256362]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({'2b3a8e63-6eac-411e-8eb5-7712ec2a84f3': {'qid': 'Q312024', 'native': 'bilibin_iy', 'label': 'Билибин И. Я.', 'life': '1876, поселок Тарховка близ Санкт-Петербурга — 1942, Ленинград', 'birth': 1876, 'death': 1942}, '9e183095-3611-46ad-ab97-662a77034157': {'qid': 'Q318427', 'native': 'nesterov_mv', 'label': 'Нестеров М. В.', 'life': '1862, Уфа – 1942, Москва', 'birth': 1862, 'death': 1942}, '06fbd151-c85c-415b-a91e-7dc31d5664bd': {'qid': 'Q248597', 'native': 'fedotov_pp', 'label': 'Федотов П. А.', 'life': '1815, Москва – 1852, Петербург', 'birth': 1815, 'death': 1852}, 'fd075e9d-98f9-46d4-a526-6a8c1dcb2364': {'qid': 'Q740592', 'native': 'makovskiy_ve', 'label': 'Маковский В. Е.', 'life': '1846, Москва – 1920, Петроград', 'birth': 1846, 'death': 1920}})
f.SELECTION='Sixteen eligible missing-image records across Bilibin, Nesterov, Fedotov and Makovsky. Current creator and native object review, bounded exact-title alternatives and individual source photograph comparisons required. Preserve all dates, unknown fields, holdings and review status.'
CONCORDANCES={('0ca9fbc9-260c-4b82-9940-79d37510c7cd', 'https://www.wikiart.org/en/ivan-bilibin/underwater-illustration-for-the-epic-volga-1928', 'Подводное царство. Иллюстрация к былине "Вольга"', 'Иллюстрация к былине "Вольга"'): 'Individual literal title concordance for native РС-4027: WikiArt \'Подводное царство. Иллюстрация к былине "Вольга"\' and catalogue \'Иллюстрация к былине "Вольга"\'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.'}
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
  name={203616: 'illustration-for-the-epic-volga-1902', 203617: 'illustration-for-the-epic-volga-1904', 203586: 'feast-of-prince-vladimir-1902'}.get(cid,name)
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=4:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Untranslated index entries, abbreviated sitter names and different source wording caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'5fab8504-abcc-4365-9236-fa5fde6f715a': 'https://rusmuseumvrm.ru/data/collections/drawings/nesterov_m._v._yunost_prepodobnogo_sergiya._1891._r-6188/25189_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

UNKNOWN_DATE_REVIEWS={'fd4054b8-f49a-41b4-b20d-2f92eb3f084b': {'page': 'https://www.wikiart.org/en/mikhail-nesterov/the-raising-of-lazarus', 'wikiart_id': '57727a24edc2cb3880ddb01c', 'wikiart_title': 'The Raising of Lazarus', 'page_sha256': 'f19d11d8b1a012a14a3fd3c3616fa70299f14ad3e699f244f258a8b69aaa71b1', 'accession': 'Р-40899', 'period': 'Эскиз росписи северной стены церкви во имя благоверного князя Александра Невского в Абастумане. 1898 - 1899', 'native_url': 'https://rusmuseumvrm.ru/data/collections/drawings/r-40899/index.php', 'catalogue_date': {'creation_year_start': 1898, 'creation_year_end': 1899, 'date_precision': 'range', 'date_display': '1898 - 1899'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Р-40899, whose creation period is Эскиз росписи северной стены церкви во имя благоверного князя Александра Невского в Абастумане. 1898 - 1899. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1898 - 1899 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

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
