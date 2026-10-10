#!/usr/bin/env python3
"""Fifteen selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-kuindzhi-versions-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-additional-artists-20261007'
core.VERSION='local-wikiart-kuindzhi-versions-v1'
SELECTED={'1657f1df-b0d5-4863-b8b4-9c5ad533325d': [236033, 236034, 236035, 236037, 236038, 236039, 236040, 236036, 236041, 236042], '28cf2865-85d6-47b1-813e-e0011d470071': [236033, 236034, 236035, 236037, 236038, 236039, 236040, 236036, 236041], '65894061-f139-456a-a070-baea47d5d86f': [236033, 236034, 236035, 236037, 236038, 236039, 236040, 236036, 236041], '32c95bff-b751-4e22-9d8e-2de801736d5c': [236075, 236076], '43ba7829-02a7-49c9-b3be-6bf2aa74b68c': [236075, 236076], '2eef3e76-8b36-4304-a5df-0928ab1334ff': [236205, 236206, 236207, 236203, 236204], '2a872ec4-c965-4037-8299-40c46f7a0e55': [236101], '111c7778-efd6-4f12-9c24-8c4e70c7dca9': [236065, 236066, 236067, 236060, 236061, 236062, 236063], '46511d20-ffe3-43f2-afb9-1acdb682df9d': [236110], 'f5189a5f-b030-4723-afa6-06ac656314ae': [236135], '2d8f0bca-db19-419b-b5f1-1ec1fdffb77e': [236045, 236046, 236047, 236048, 236050], '9cce5963-bb84-4d5e-91f6-b5e458bc9be0': [236140, 236141, 236138, 236139, 236049], '6fd081ce-d775-4688-9b50-8df2b58d0a69': [236156], '3c3611f7-91e6-47b4-a376-1db2090ca274': [236080, 236081, 236079], '982eac87-eeac-4663-9f13-1ed93aa7e9c2': [236080, 236081]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=9
r.ARTISTS.update({'f392b4f8-aaf3-4932-87e2-c7e43895712f': {'qid':'Q353628','native':'kuindzhi_ai','label':'Куинджи А. И.','life':'1842 (?), Мариуполь Екатеринославской губ. – 1910, Санкт-Петербург','birth':1842,'death':1910}})
f.SELECTION='Fifteen remaining exact-title Russian Museum review artworks by Kuindzhi, individually selected from pinned complete source indexes. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
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
  if cid==236033:name='a-birch-grove-1879'
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=10:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Individually selected titles from the scoped eight-artist metadata audit. Preserve all explicit date differences; a title lead is not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact existing Russian Museum inventory objects, verified Kuindzhi creator authority, current WikiArt source pages and individual visual comparisons across same-title versions. Preserve dates, unknown metadata, rights and review status. No catalogue publication or biography change.'

NATIVE_DIMENSION_REVIEW={'artwork_id': '9cce5963-bb84-4d5e-91f6-b5e458bc9be0', 'catalogue_dimensions': '12,5 x 18,5. И.: 11 x 17,7 (11,0 х 17,7 - бумага; 12,5 х 18,5 - картон)', 'native_dimensions': '11 x 17,7', 'native_accession': 'ЖБ-3', 'native_period': 'Этюд. 1900-1910', 'capture': {'at': '2026-10-07T01:23:59Z', 'bytes': 22637, 'path': 'docs/research/local-wikiart-kuindzhi-versions-images-20261007/metadata/museum/9cce5963-bb84-4d5e-91f6-b5e458bc9be0.html', 'sha256': 'e6abbae483dde16656ed6c9e373b083c28722d572d4a70b90170072b4b154427', 'url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-3/index.php'}, 'reason': 'The frozen catalogue distinguishes paper image 11 by 17.7 from backing cardboard 12.5 by 18.5 cm. The current native page supplies only 11 by 17.7 cm. Preserve both literal dimensional descriptions, including the existing backing measurements; exact inventory and all other native checks remain required.'}
_native_facts=r.native_facts
def native_facts(c):
 cfg=NATIVE_DIMENSION_REVIEW
 if c['artwork_id']!=cfg['artwork_id']:return _native_facts(c)
 if c['before_record']['dimensions_text']!=cfg['catalogue_dimensions']:raise ValueError('Individual catalogue dimension assertion changed')
 if json.loads((RUN/'native-dimension-review.json').read_bytes())!=cfg:raise ValueError('Individual dimension proof changed')
 import copy
 adapted=copy.deepcopy(c);adapted['before_record']['dimensions_text']=cfg['native_dimensions'];facts=_native_facts(adapted)
 if (facts['accession'],facts['period'],facts['capture'])!=(cfg['native_accession'],cfg['native_period'],cfg['capture']):raise ValueError('Individual dimensional object differs')
 facts['individual_dimension_review']=cfg
 return facts
r.native_facts=native_facts

UNKNOWN_DATE_REVIEWS={'46511d20-ffe3-43f2-afb9-1acdb682df9d': {'page': 'https://www.wikiart.org/en/arkhip-kuindzhi/lake-evening', 'wikiart_id': '5772768dedc2cb3880d1e5da', 'wikiart_title': 'Lake. Evening', 'page_sha256': '3ae6cd581f9b715abc6c5047a94e6d16e28bdf6af47347cab8e6a9e145ba511c', 'accession': 'Ж-6299', 'period': '1900-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh-6299/index.php', 'catalogue_date': {'creation_year_start': 1900, 'creation_year_end': 1909, 'date_precision': 'decade', 'date_display': '1900-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-6299, whose creation period is 1900-е. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1900-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, '982eac87-eeac-4663-9f13-1ed93aa7e9c2': {'page': 'https://www.wikiart.org/en/arkhip-kuindzhi/elbrus-in-the-daytime-1', 'wikiart_id': '5772768cedc2cb3880d1e3f8', 'wikiart_title': 'Elbrus in the daytime', 'page_sha256': 'ea0642fde85acdaf790efc819fc87868f6151a46d6d7fe3fc6df9491b8e5a245', 'accession': 'ЖБ-88', 'period': '1900-1910', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zhb-88/index.php', 'catalogue_date': {'creation_year_start': 1900, 'creation_year_end': 1910, 'date_precision': 'range', 'date_display': '1900-1910'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native ЖБ-88, whose creation period is 1900-1910. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1900-1910 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, 'f5189a5f-b030-4723-afa6-06ac656314ae': {'page': 'https://www.wikiart.org/en/arkhip-kuindzhi/portrait-of-ivan-kramskoi', 'wikiart_id': '5772768eedc2cb3880d1e76a', 'wikiart_title': 'Portrait of Ivan Kramskoi', 'page_sha256': '7ea2e9ca2063e1241c99a2d1546994bc84d86f2be150fcb02e03f569cad0bf64', 'accession': 'Р-30725', 'period': 'Из альбома рисунков. 1870-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/drawings/r-30725/index.php', 'catalogue_date': {'creation_year_start': 1870, 'creation_year_end': 1879, 'date_precision': 'decade', 'date_display': '1870-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Р-30725, whose creation period is Из альбома рисунков. 1870-е. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1870-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

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
