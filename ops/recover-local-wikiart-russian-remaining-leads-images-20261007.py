#!/usr/bin/env python3
"""Thirteen remaining Russian Museum title leads: prints and undated works."""
import argparse
import copy
import gzip
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin,urlparse

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-remaining-leads-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-russian-remaining-title-leads-v1'
f.IDS=['f739aed7-9d3a-4e2e-bb53-ce05c8497148','2dd786e9-c014-4acc-81db-15c0ec736ecb','f85b9b13-e9ee-429e-bc13-51c0d7f42b90','e9690e4a-3fdf-4bcf-ad3c-5a412cc6304e','19fce6c4-7c8b-4fc5-97da-a5cd508509e4','dd463bf5-0c7a-4589-94b0-e8d9e7030328','1f667088-357b-4839-8b13-379e919435b5','bf8c8ebb-52fa-46dd-9ba2-306abd476496','027c5a45-4f79-4d70-83fa-3da7573ec857','577a657c-3203-4521-9432-09dda18ce817','6dd76b73-1972-4946-98b4-ed14cad2966f','d6b8915b-2c15-42cc-b559-d96b31f2287e','e540d03e-0a5c-46ae-8786-ef5387664e56']
f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=8
f.SELECTION='Thirteen existing eligible Russian Museum image gaps remaining in the bounded 91-title-lead discovery: nine prints, three paintings and one drawing. Select and compare individual source versions and native inventory photographs. Preserve source dates, unknown fields, actual rights, exact work/impression identity and catalogue review state.'
r.ARTISTS['676b2231-17dd-4012-8b95-c57cef5f33b4']=dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911)
CONCORDANCES={}

def source_options(c,options):
 if c['artwork_id']=='6dd76b73-1972-4946-98b4-ed14cad2966f':
  url='https://www.wikiart.org/en/karl-bryullov/all-works/text-list';data,rc=r.capture(url,RUN/'metadata/canonical-pages/bryullov-list.html')
  links=sorted({urljoin(url,a['href']) for a in r.BeautifulSoup(data,'html.parser').select('a[href]') if '/pheb-in-his-chariot' in a['href']})
  if not 1<=len(links)<=2:raise ValueError('Unexpected current Pheb alternative count')
  matches=[];captures=[]
  for page in links:
   body,prc=r.capture(page,RUN/'metadata/canonical-pages'/(core.sha(page.encode())[:20]+'.html'))
   tags=r.BeautifulSoup(body,'html.parser').select('.wiki-layout-painting-info-bottom[ng-init]')
   if len(tags)!=1:raise ValueError('Unique Pheb source metadata absent')
   record=json.loads(tags[0]['ng-init'].split('=',1)[1]);captures.append(dict(capture=prc,record=record))
   if urlparse(record['image']).path==urlparse(options[0]['prior_index_lead']['image']).path.split('!',1)[0]:matches.append(dict(options[0],page=page))
  if len(matches)!=1:raise ValueError('Exact indexed Pheb photograph has no unique current page')
  core.save_new(RUN/'metadata/canonical-pages'/(c['artwork_id']+'.json'),dict(artist_list_capture=rc,links=links,current_pages=captures,original_index_leads=options,options=matches,reason='Image filename has (1); exact current artist-list links and embedded image identity determine the page. No generic filename normalization.'))
  return matches
 extras={'f739aed7-9d3a-4e2e-bb53-ce05c8497148':[230189,230201],'1f667088-357b-4839-8b13-379e919435b5':[230214,230323]}
 if c['artwork_id'] not in extras:return options
 if c['creator_links'][0]['artist_id']!='0604627e-59cd-4203-82b2-9aa77423e5cc':raise ValueError('Selected creator changed')
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes/boris-kustodiev.json.gz';data=path.read_bytes();d=json.loads(gzip.decompress(data));rc=d['receipt'];body=gzip.decompress((core.ROOT/rc['body_path']).read_bytes())
 if core.sha(body)!=rc['sha256'] or len(body)!=rc['bytes'] or json.loads(body)!=d['items']:raise ValueError('Pinned English index differs')
 selected=list(options)
 for cid in extras[c['artwork_id']]:
  rows=[i for i in d['items'] if i['contentId']==cid]
  if len(rows)!=1 or rows[0]['artistName']!='Boris Kustodiev':raise ValueError('Unique current source identity absent')
  i=rows[0];slug=i['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg');selected.append(dict(page='https://www.wikiart.org/en/boris-kustodiev/'+slug,prior_index_lead=i))
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=rc,artwork_id=c['artwork_id'],original_title_leads=options,options=selected,reason='Individually selected additional English-index alternatives: a 1920 and an undated self-portrait, or the two other 1919 Shrovetide compositions. Native print comparison determines version identity; dates are not rewritten.'))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

UNKNOWN_DATE_REVIEWS={'f85b9b13-e9ee-429e-bc13-51c0d7f42b90': {'page': 'https://www.wikiart.org/en/boris-kustodiev/sunset', 'wikiart_id': '57727583edc2cb3880ce4196', 'wikiart_title': 'Sunset', 'page_sha256': 'f58da5cf486b69c6775d551ee26a2db8854109f7f9d27726fb2e657a1cab840b', 'accession': 'Ж-11160', 'period': 'Около 1917', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh-11160/index.php', 'catalogue_date': {'creation_year_start': 1917, 'creation_year_end': 1917, 'date_precision': 'circa', 'date_display': 'Около 1917'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-11160, whose creation period is Около 1917. This object-specific museum evidence establishes pre-1971 eligibility, with its original approximation or range preserved. The catalogue retains Около 1917 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, 'dd463bf5-0c7a-4589-94b0-e8d9e7030328': {'page': 'https://www.wikiart.org/en/boris-kustodiev/summer-landscape-with-women', 'wikiart_id': '57727583edc2cb3880ce4176', 'wikiart_title': 'Summer Landscape with Women', 'page_sha256': '5eaabf7bbd3e7ac4e0676b4f2b1f4e848920e1d76c3bdac84e85d9b5ec9e151b', 'accession': 'Р-57907', 'period': 'Эскиз. Конец 1910-х', 'native_url': 'https://rusmuseumvrm.ru/data/collections/drawings/r-57907/index.php', 'catalogue_date': {'creation_year_start': 1910, 'creation_year_end': 1919, 'date_precision': 'decade', 'date_display': 'Конец 1910-х'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Р-57907, whose creation period is Эскиз. Конец 1910-х. This object-specific museum evidence establishes pre-1971 eligibility, with its original approximation or range preserved. The catalogue retains Конец 1910-х and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, '577a657c-3203-4521-9432-09dda18ce817': {'page': 'https://www.wikiart.org/en/karl-bryullov/ruins-in-park', 'wikiart_id': '577270ffedc2cb3880c0248b', 'wikiart_title': 'Ruins in Park', 'page_sha256': 'ed3a26e6c1f488c93594f6c2f23e1132d8d83991285d8aecd106361cffbc9c0b', 'accession': 'Ж-3366', 'period': '1820-е', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/zh-3366/index.php', 'catalogue_date': {'creation_year_start': 1820, 'creation_year_end': 1829, 'date_precision': 'decade', 'date_display': '1820-е'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-3366, whose creation period is 1820-е. This object-specific museum evidence establishes pre-1971 eligibility, with its original approximation or range preserved. The catalogue retains 1820-е and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}, '6dd76b73-1972-4946-98b4-ed14cad2966f': {'page': 'https://www.wikiart.org/en/karl-bryullov/pheb-in-his-chariot', 'wikiart_id': '577270f6edc2cb3880bfb9d5', 'wikiart_title': 'Pheb in His Chariot', 'page_sha256': 'c98abe04bd3f6ab558e8d4321c90e9cb3b9d31cde0406594dfbbc0d8b3f8703a', 'accession': 'Ж-6547', 'period': '1846 (?)', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/17_19/zh-6547/index.php', 'catalogue_date': {'creation_year_start': 1846, 'creation_year_end': 1846, 'date_precision': 'circa', 'date_display': '1846 (?)'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-6547, whose creation period is 1846 (?). This object-specific museum evidence establishes pre-1971 eligibility, with its original approximation or range preserved. The catalogue retains 1846 (?) and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}
PRINT_IDS=set(['027c5a45-4f79-4d70-83fa-3da7573ec857', '19fce6c4-7c8b-4fc5-97da-a5cd508509e4', '2dd786e9-c014-4acc-81db-15c0ec736ecb', 'bf8c8ebb-52fa-46dd-9ba2-306abd476496', 'e9690e4a-3fdf-4bcf-ad3c-5a412cc6304e'])
r.BASIS='Exact existing native object and creator identity, current WikiArt title/object/image evidence and individual visual comparison. Four paintings/drawings match exact native objects with separately reviewed unknown source dates; five print records use explicitly qualified reproductions of matching printed designs without claiming identity of the individual museum impressions. Actual rights, source approval, source date uncertainty and unchanged catalogue metadata are preserved. Local image-only attachment; no publication or independently obtained copyright permission asserted.'

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

original_page_facts=wiki.page_facts
TRANSLATED_IDS={'577a657c-3203-4521-9432-09dda18ce817':204386,'6dd76b73-1972-4946-98b4-ed14cad2966f':204281}
def page_facts(c,data,rc):
 aid=c['artwork_id']
 if aid not in TRANSLATED_IDS:return original_page_facts(c,data,rc)
 chosen=f.selected(c);review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][aid];cfg=UNKNOWN_DATE_REVIEWS[aid]
 native=r.native_facts(chosen)
 if native!=review['native_facts'] or native['accession']!=cfg['accession'] or review['decision']!='continue_to_visual_review':raise ValueError('Individual translated native version differs')
 proof=json.loads((RUN/'translated-title-review.json').read_bytes())[aid]
 if (rc['url'],review['wikiart_id'],review['wikiart_title'])!=(cfg['page'],cfg['wikiart_id'],cfg['wikiart_title']) or proof['page']!=cfg['page'] or proof['page_sha256']!=core.sha(data):raise ValueError('Individual translated source identity differs')
 soup=r.BeautifulSoup(data,'html.parser')
 if any(li.get_text(' ',strip=True).startswith('Original Title:') for li in soup.select('.wiki-layout-artwork-info article li')):raise ValueError('Original-title source presentation changed')
 raw=(core.ROOT/proof['index_path']).read_bytes()
 if core.sha(raw)!=proof['index_sha256']:raise ValueError('Pinned Russian index differs')
 d=json.loads(gzip.decompress(raw));body=gzip.decompress((core.ROOT/d['receipt']['body_path']).read_bytes())
 if core.sha(body)!=d['receipt']['sha256'] or len(body)!=d['receipt']['bytes'] or json.loads(body)!=d['items'] or d['receipt']!=proof['receipt']:raise ValueError('Pinned Russian API capture differs')
 i=proof['item']
 if d['items'].count(i)!=1 or i!=chosen['prior_index_lead'] or (i['contentId'],i['title'],i['completitionYear'])!=(TRANSLATED_IDS[aid],chosen['title'],None):raise ValueError('Individual Russian title/image lead differs')
 adapted=copy.deepcopy(chosen);adapted.update(external_id=review['wikiart_id'],alternate_title=review['wikiart_title'])
 facts=r.original_facts(adapted,data,rc)
 if urlparse(facts['source_image_url']).path.split('!',1)[0]!=urlparse(i['image']).path.split('!',1)[0]:raise ValueError('Translated source photograph differs')
 facts.update(native_object_review=review,native_original_title=None,individual_title_concordance=proof)
 return facts
wiki.page_facts=page_facts

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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
