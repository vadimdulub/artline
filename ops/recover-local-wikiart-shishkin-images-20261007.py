#!/usr/bin/env python3
"""Twelve selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-shishkin-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-additional-artists-20261007'
core.VERSION='local-wikiart-shishkin-v1'
SELECTED={'d1b51936-b61e-4060-b896-967e15272e96': [228769, 228512], '1428c9cf-8bef-4c3e-8966-781be2ba773e': [228924, 228925], '009a7542-a4b0-419c-9842-38810cb9d57f': [228552, 228553], '8aee64b9-1f90-42d7-a46d-e8180597522c': [228736, 228737], 'd92d7064-8059-48f8-9d0b-602e77cc6366': [228736, 228737], 'dc1f321e-c8b4-40ba-aa5c-c688b9a420ac': [228736, 228737], 'c4179ef2-66c9-45c2-bab4-368f3f2e9d55': [228825, 228826], '55687f9d-2508-4b7f-8604-247dbfe492a4': [228836], '9eae6deb-160c-4e8e-8821-7b11618ebf02': [228934, 228935, 228936], '49ffa67f-4cb0-4aaf-a082-d3f3ac641923': [228650, 228651, 228652, 228653, 228654, 228655, 228656, 228657, 228658, 228659, 228660, 228661, 228662, 228663, 228664, 228665, 228666], 'bb08c698-0047-49a0-a3a0-1a06bfc249cf': [228870, 228872, 228873, 228874, 228875, 228876, 228879, 228880, 228881], '32290f44-ecdb-4d1b-bf3f-4d9d98bfed41': [228891, 228892, 228893]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=17


r.ARTISTS.update({'e27d4c11-eece-486b-bc33-b3da37129c56': {'qid': 'Q193064', 'native': 'shishkin_ii', 'label': 'Шишкин И. И.', 'life': '1832, Елабуга – 1898, Санкт-Петербург', 'birth': 1832, 'death': 1898}})
f.SELECTION='Twelve remaining exact-title Russian Museum review artworks by Shishkin, individually selected from pinned complete source indexes. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
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
 if not 1<=len(result)<=17:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Individually selected titles from the scoped eight-artist metadata audit. Preserve all explicit date differences; a title lead is not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact existing Russian Museum inventory objects, verified Shishkin creator authority, current WikiArt source pages and individual visual comparisons across same-title versions. Preserve dates, unknown metadata, rights and review status. No catalogue publication or biography change.'

NATIVE_REFERENCE_ALIASES={'8aee64b9-1f90-42d7-a46d-e8180597522c': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18762/30535_mainfoto_03.jpg', 'd92d7064-8059-48f8-9d0b-602e77cc6366': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18767/30536_mainfoto_03.jpg', 'dc1f321e-c8b4-40ba-aa5c-c688b9a420ac': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18768/30538_mainfoto_03.jpg', 'c4179ef2-66c9-45c2-bab4-368f3f2e9d55': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18936/30543_mainfoto_03.jpg', '49ffa67f-4cb0-4aaf-a082-d3f3ac641923': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18958/30550_mainfoto_03.jpg', '32290f44-ecdb-4d1b-bf3f-4d9d98bfed41': 'https://rusmuseumvrm.ru/data/collections/engraving/gr-18093/30530_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

PRINT_IDS={'32290f44-ecdb-4d1b-bf3f-4d9d98bfed41'}
original_version=r.version
def version(im,approved=False):
 original_version(im,approved)
 if im['artwork_id'] not in PRINT_IDS:return
 matches=[x for x in json.loads((RUN/'print-design-review.json').read_bytes())['images'] if x['artwork_id']==im['artwork_id']]
 if len(matches)!=1:raise ValueError('Individual print-design scope absent')
 proof=matches[0]
 if any(proof[k]!=im[k] for k in ('source_sha256','sha256','source_image_url','view_label','alt_text')):raise ValueError('Print-design view or image changed')
 if proof['match_level']!='printed_design' or proof['source_impression_identified'] is not False or proof['native_work_type']!='print' or im['work_type']!='print':raise ValueError('Print-design match misrepresented as individual impression')
 native=r.native_facts(im)
 if (proof['native_inventory'],proof['native_medium'])!=(native['accession'],native['medium']):raise ValueError('Print-design native medium/inventory differs')
 if proof!=im['raw'].get('print_design_review') or proof['note'] not in im['attribution_text']:raise ValueError('Print-design limitation omitted')
 if im.get('view_label')!='Printed design; individual impression unspecified':raise ValueError('Print-design scope label changed')
 wiki.chicago.verify_view(im)
r.version=version

UNKNOWN_DATE_REVIEWS={'9eae6deb-160c-4e8e-8821-7b11618ebf02': {'page': 'https://www.wikiart.org/en/ivan-shishkin/stones-1', 'wikiart_id': '5772751cedc2cb3880cd8d74', 'wikiart_title': 'Stones', 'page_sha256': 'b1cce973cafa2dd46ef67a661c048d62bf97e36a8b2323f68c7aae55cea50213', 'accession': 'Ж-2805', 'period': 'Этюд. 1890-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh-2805/index.php', 'catalogue_date': {'creation_year_start': 1890, 'creation_year_end': 1899, 'date_precision': 'decade', 'date_display': '1890-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-2805, whose creation period is Этюд. 1890-е. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1890-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

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
