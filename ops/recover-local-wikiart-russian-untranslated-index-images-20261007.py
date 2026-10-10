#!/usr/bin/env python3
"""Twelve further selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-untranslated-index-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-untranslated-index-v1'
SELECTED={'b1f7cf95-5e32-4dd5-ac8a-6f306e659225': [215276], 'b0548b1b-4516-45c5-b79e-874180eb1f8e': [215227], 'a3f97b01-400e-43af-a0f8-8e94d191ecdc': [229849, 230308, 230249], 'ccadbc88-461b-4f2a-8b00-b36aa943e2c8': [214762, 214763, 214830], 'a7080a95-5ba5-4b49-8bf2-4edab2bb557f': [226144, 226145], 'b321ca5a-b081-42d8-a4ee-4cc16d66bb0d': [226653], '12c409a7-acc8-47d4-923c-5a56c2080fe2': [230245, 230246, 230251], 'd88ce259-f5d5-48d8-96fb-0c48556d9a8c': [214831, 214832, 214833], 'd4de59ca-ca3f-4fbc-9b2c-b903308473f6': [225900], '6eb8aefe-12a0-48d3-b54d-7ea10720d29b': [226159, 226160, 226161], 'a6793a02-d460-43ba-84e8-e5ff7029725d': [215266], '3adb7519-6f3f-4aef-b398-750a74aa7f96': [226837]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':{'qid': 'Q208993', 'native': 'rerih_nk', 'label': 'Рерих Н. К.', 'life': '1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия', 'life_aliases': ['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'], 'birth': 1874, 'death': 1947},
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Twelve existing eligible Russian Museum review artworks with individually selected full-index candidates, including untranslated index entries missed by Russian title lists. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
CONCORDANCES={('b1f7cf95-5e32-4dd5-ac8a-6f306e659225', 'https://www.wikiart.org/en/ilya-repin/portrait-of-the-lawyer-vladimir-spasovitch-1891', 'Портрет юриста', 'Портрет Владимира Спасовича'): "Individual literal title concordance for native Ж-4067: WikiArt 'Портрет юриста' and catalogue 'Портрет Владимира Спасовича'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
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
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Untranslated index entries, abbreviated sitter names and different source wording caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
ENGLISH_TITLE_REVIEWS={'6eb8aefe-12a0-48d3-b54d-7ea10720d29b': {'page': 'https://www.wikiart.org/en/nicholas-roerich/mohammed-on-mount-hira-1925', 'wikiart_id': '57727473edc2cb3880cc1e49', 'wikiart_title': 'Mohammed on mount Hira', 'catalogue_title': 'Пророк (Магомет на горе Хира)', 'note': "Individual English-title concordance for native Ж-7104: WikiArt 'Mohammed on mount Hira' and catalogue 'Пророк (Магомет на горе Хира)'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': '3d2b84ba8cdbe4bfa4d93c21cc36eb9b5c8aee8f7682619fdc4128437aac799e'}, 'a6793a02-d460-43ba-84e8-e5ff7029725d': {'page': 'https://www.wikiart.org/en/ilya-repin/portrait-of-the-composer-alexander-glazunov-1887', 'wikiart_id': '577272bdedc2cb3880c618d3', 'wikiart_title': 'Portrait of the Composer Alexander Glazunov', 'catalogue_title': 'Портрет Александра Глазунова', 'note': "Individual English-title concordance for native Ж-4014: WikiArt 'Portrait of the Composer Alexander Glazunov' and catalogue 'Портрет Александра Глазунова'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': '2fb85f2b20c4d320122a696faa1973caf4aeaa984f13304ac97fcbc406f604ed'}, 'b0548b1b-4516-45c5-b79e-874180eb1f8e': {'page': 'https://www.wikiart.org/en/ilya-repin/portrait-of-t-a-mamontova-1879', 'wikiart_id': '577272bcedc2cb3880c61683', 'wikiart_title': 'Portrait of T. A. Mamontova', 'catalogue_title': 'Портрет Татьяны Мамонтовой', 'note': "Individual English-title concordance for native Р-7845: WikiArt 'Portrait of T. A. Mamontova' and catalogue 'Портрет Татьяны Мамонтовой'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': '53c849bfe9d841f7faa006c2ff6047130af585d2f437957695b504d97ace51cb'}, 'b321ca5a-b081-42d8-a4ee-4cc16d66bb0d': {'page': 'https://www.wikiart.org/en/nicholas-roerich/snow-maiden-1912', 'wikiart_id': '57727488edc2cb3880cc3d57', 'wikiart_title': 'Snow Maiden', 'catalogue_title': 'Снегурочка', 'note': "Individual English-title concordance for native Ж-1968: WikiArt 'Snow Maiden' and catalogue 'Снегурочка'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': '15edc7e7a771bbf153ee375f60d886be0c53881f80aaf66c2a2165debcafe437'}, 'd4de59ca-ca3f-4fbc-9b2c-b903308473f6': {'page': 'https://www.wikiart.org/en/nicholas-roerich/in-a-monastery-1914', 'wikiart_id': '57727462edc2cb3880cba991', 'wikiart_title': 'In a monastery', 'catalogue_title': 'В монастыре', 'note': "Individual English-title concordance for native Ж-1981: WikiArt 'In a monastery' and catalogue 'В монастыре'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': 'aa65007596287bb8711683177a4cc9929d2d3d9b064a70ca4c45e807fd693508'}}
r.BASIS='Exact existing native museum objects, creator authorities, selected current WikiArt pages and individually compared physical versions. Five source pages have no Original Title field; their literal English titles, unchanged catalogue titles, checksum-pinned untranslated index entries and visual evidence are individually reconciled. Preserve source date discrepancies, image framing, actual rights and unchanged catalogue metadata. Local image-only attachment; no publication or invented source fields.'
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
 if core.sha(raw)!=pin['sha256']:raise ValueError('Pinned untranslated source index changed')
 index=json.loads(gzip.decompress(raw));body=gzip.decompress((core.ROOT/index['receipt']['body_path']).read_bytes())
 if core.sha(body)!=index['receipt']['sha256'] or len(body)!=index['receipt']['bytes'] or json.loads(body)!=index['items'] or index['receipt']!=pin['source_receipt']:raise ValueError('Untranslated source index capture differs')
 item=option['prior_index_lead']
 if item['title'] is not None or index['items'].count(item)!=1 or item['contentId'] not in SELECTED[aid]:raise ValueError('Exact untranslated index entry absent')
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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
