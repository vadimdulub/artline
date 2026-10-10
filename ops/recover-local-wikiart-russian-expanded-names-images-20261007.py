#!/usr/bin/env python3
"""Twelve further selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-expanded-names-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-expanded-names-v1'
SELECTED={'6b71153e-0598-4815-a3e1-1d66f13d580a': [230110], '722b3de3-6183-4f0b-a3f6-bf8b0020057c': [237426], 'b7879f2b-e1ca-4ba7-8667-2c91cccccfd9': [237342, 237402], 'e31a9744-8445-404c-974b-dcb65c4ec8d5': [229788, 229789], '98e3e5a8-1b3e-4b6d-b9e6-89080f198af4': [229966], 'e4ffb723-e02a-447e-b78f-0597815d7056': [237425], '4c1ea354-6070-403f-b619-5954351e8f03': [215181], '5b7a75d2-8e03-4f93-9d52-2f9abcb93698': [215148], '14d572e7-4e69-476d-b0d6-4144a81e6237': [230126], 'dc8d1f5a-a422-4191-b2c9-532727274e3f': [230307, 230308], 'ca12a488-5186-4dfc-b73c-c8afcc97e0d5': [215182], '7599901d-9746-4d1e-bbdf-7b75d97f0b7b': [215234]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Twelve existing eligible Russian Museum review artworks with individually selected full-index candidates missed by fuzzy title lists. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
CONCORDANCES={('14d572e7-4e69-476d-b0d6-4144a81e6237', 'https://www.wikiart.org/en/boris-kustodiev/portrait-of-vasily-vasilyevich-mate', 'Портрет профессора гравирования В.В.Матэ', 'Портрет В. В. Матэ'): "Individual literal title concordance for native Ж-4360: WikiArt 'Портрет профессора гравирования В.В.Матэ' and catalogue 'Портрет В. В. Матэ'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('4c1ea354-6070-403f-b619-5954351e8f03', 'https://www.wikiart.org/en/ilya-repin/portrait-of-minister-of-ways-of-communication-and-member-of-state-council-prince-mikhail-1903', 'М.И.Хилков', 'Портрет князя Михаила Хилкова'): "Individual literal title concordance for native Ж-4024: WikiArt 'М.И.Хилков' and catalogue 'Портрет князя Михаила Хилкова'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('5b7a75d2-8e03-4f93-9d52-2f9abcb93698', 'https://www.wikiart.org/en/ilya-repin/portrait-of-ivan-stepanovich-panov-1867', 'ортрет художника Ивана Степановича Панова', 'Портрет Ивана Панова'): "Individual literal title concordance for native Ж-4041: WikiArt 'ортрет художника Ивана Степановича Панова' and catalogue 'Портрет Ивана Панова'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('6b71153e-0598-4815-a3e1-1d66f13d580a', 'https://www.wikiart.org/en/boris-kustodiev/portrait-of-the-commandant-of-the-mariinsky-palace-major-general-pavel-shevelev-1903', 'Портрет коменданта Мариинского дворца генерал-майора Павла Аркадьевича Шевелева', 'Портрет П. А. Шевелева'): "Individual literal title concordance for native Ж-1880: WikiArt 'Портрет коменданта Мариинского дворца генерал-майора Павла Аркадьевича Шевелева' and catalogue 'Портрет П. А. Шевелева'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('722b3de3-6183-4f0b-a3f6-bf8b0020057c', 'https://www.wikiart.org/en/valentin-serov/portrait-of-the-composer-alexander-serov-1889', 'Портрет композитора Александра Серова', 'Портрет А. Н. Серова'): "Individual literal title concordance for native Ж-4286: WikiArt 'Портрет композитора Александра Серова' and catalogue 'Портрет А. Н. Серова'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('7599901d-9746-4d1e-bbdf-7b75d97f0b7b', 'https://www.wikiart.org/en/ilya-repin/portrait-of-the-architect-philip-dmitrievich-hloboschin-1868', 'Портрет архитектора Филиппа Дмитриевича Хлобощина', 'Портрет Ф. Д. Хлобощина'): "Individual literal title concordance for native Ж-4053: WikiArt 'Портрет архитектора Филиппа Дмитриевича Хлобощина' and catalogue 'Портрет Ф. Д. Хлобощина'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('98e3e5a8-1b3e-4b6d-b9e6-89080f198af4', 'https://www.wikiart.org/en/boris-kustodiev/portrait-of-a-governor-general-of-finland-n-i-bobrikov-1903', 'Портрет генерал-губернатора Финляндии Н.И.Бобрикова', 'Портрет Н. И. Бобрикова'): "Individual literal title concordance for native Ж-1887: WikiArt 'Портрет генерал-губернатора Финляндии Н.И.Бобрикова' and catalogue 'Портрет Н. И. Бобрикова'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('b7879f2b-e1ca-4ba7-8667-2c91cccccfd9', 'https://www.wikiart.org/en/valentin-serov/portrait-of-prince-felix-yussupov-1903', 'Портрет князя Ф.Ф. Юсупова', 'Портрет князя Ф. Ф. Юсупова, графа Сумарокова-Эльстона'): "Individual literal title concordance for native Ж-4303: WikiArt 'Портрет князя Ф.Ф. Юсупова' and catalogue 'Портрет князя Ф. Ф. Юсупова, графа Сумарокова-Эльстона'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('ca12a488-5186-4dfc-b73c-c8afcc97e0d5', 'https://www.wikiart.org/en/ilya-repin/portrait-of-music-editor-and-patron-mitrofan-petrovich-belyayev-1886', 'Портрет музыкального деятеля М.П.Беляева', 'Портрет Митрофана Беляева'): "Individual literal title concordance for native Ж-4012: WikiArt 'Портрет музыкального деятеля М.П.Беляева' and catalogue 'Портрет Митрофана Беляева'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('dc8d1f5a-a422-4191-b2c9-532727274e3f', 'https://www.wikiart.org/en/boris-kustodiev/village-holiday-1910', 'Деревенский праздник (Осенний сельский праздник)', 'Деревенский праздник'): "Individual literal title concordance for native Ж-5511: WikiArt 'Деревенский праздник (Осенний сельский праздник)' and catalogue 'Деревенский праздник'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('e31a9744-8445-404c-974b-dcb65c4ec8d5', 'https://www.wikiart.org/en/boris-kustodiev/england-1926', 'Англия', 'Эскиз декорации III акта к пьесе Е. И. Замятина «Блоха». «Англия»'): "Individual literal title concordance for native Ж-11115: WikiArt 'Англия' and catalogue 'Эскиз декорации III акта к пьесе Е. И. Замятина «Блоха». «Англия»'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('e4ffb723-e02a-447e-b78f-0597815d7056', 'https://www.wikiart.org/en/valentin-serov/portrait-of-the-composer-alexander-glazunov-1899', 'Портрет композитора Александра Глазунова', 'Портрет А. Глазунова'): "Individual literal title concordance for native Гр.-40847: WikiArt 'Портрет композитора Александра Глазунова' and catalogue 'Портрет А. Глазунова'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
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
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Abbreviated or expanded sitter names and stage/holiday titles caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
UNKNOWN_DATE_REVIEWS={'14d572e7-4e69-476d-b0d6-4144a81e6237': {'page': 'https://www.wikiart.org/en/boris-kustodiev/portrait-of-vasily-vasilyevich-mate', 'wikiart_id': '5772757eedc2cb3880ce39b6', 'wikiart_title': 'Portrait of Vasily Vasilyevich Mate', 'page_sha256': '86ccb53776d9c2592b3cd717727dc4cae277940749418bd957ca6d3eda81760e', 'accession': 'Ж-4360', 'period': '1902', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh_4360/index.php', 'catalogue_date': {'creation_year_start': 1902, 'creation_year_end': 1902, 'date_precision': 'exact', 'date_display': '1902'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-4360, whose creation period is 1902. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains 1902 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}
PRINT_IDS=set(['e4ffb723-e02a-447e-b78f-0597815d7056'])
r.BASIS='Twelve individually matched existing Russian Museum objects and current WikiArt source pages. Preserve literal creator, object, version and date evidence, one individually reviewed unknown source date, one explicitly qualified lithographic design, actual rights and unchanged catalogue metadata. Local image-only attachment with no publication or individual print-impression identity asserted.'

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
