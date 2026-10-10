#!/usr/bin/env python3
"""Seventeen remaining Russian Museum title-variant gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-final-title-variants-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-final-title-variants-v1'
SELECTED={'3d9f4d6e-342f-47de-93c9-ae8b38bdfa77': [214852, 214850, 214854, 214851], '82b5600c-a24c-4649-a0f4-80e829cc0e45': [215088, 215156], '91318c57-dea9-4db5-abce-01acf75346e3': [204299], 'f8d14111-9b4b-4a66-8cf7-d809edc8f56f': [204412], '956d97c2-016d-47cf-a60f-823d550ff3cc': [226154, 225491], '75e9242f-32ed-4d64-8f3a-b2b50f735b72': [214939, 215025], '6cda28a3-6e5c-4f3c-9382-807cf0364f69': [204299], 'f500f272-8762-45a2-8ca5-5e570b68ef63': [225323, 226832, 226829, 226881], '72606a79-20fd-4f36-b24d-3d091ac4817f': [204298], '06f8fdb6-d659-4023-9ee5-9ae93e78cd12': [225842, 226975, 225838], '045706b3-6921-46e4-9eac-3f0836ed67c4': [225842, 225854], '42d84b3a-0d04-4d14-8a9e-63e00d661fea': [225847, 225846, 225838], '6a83ca33-3675-4c3e-a7fc-879e0de2eab7': [225847, 225846, 225838], '03fc2aa0-2bf5-4b95-8372-1615c2a9edec': [225560, 226334], '8fcc3a23-c1dc-46f8-a680-cb9638ebeb4e': [215276], '7ebd00d3-92af-4808-b992-740c7bf8ba02': [225829, 226217, 227117], 'b07bd677-aa7b-4f22-a580-f0edd5feebbc': [226418]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':{'qid': 'Q208993', 'native': 'rerih_nk', 'label': 'Рерих Н. К.', 'life': '1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия', 'life_aliases': ['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'], 'birth': 1874, 'death': 1947},
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Seventeen remaining eligible existing records in the 222-lead title-variant queue. Individually selected complete-index alternatives prioritize matching subject or expanded title. One to four options per record; wrong named sitter and incompatible panel format require metadata exclusion before image download. Preserve catalogue identities, dates, unknown fields and review status.'
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
  name={204299: 'portrait-of-an-unknown-woman-in-a-turban', 204298: 'portrait-of-an-unknown'}.get(cid,name)
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=4:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Untranslated index entries, abbreviated sitter names and different source wording caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'82b5600c-a24c-4649-a0f4-80e829cc0e45': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_trudovika._1907._zh-5539/19899_mainfoto_03.jpg', '8fcc3a23-c1dc-46f8-a680-cb9638ebeb4e': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_ottona_rihtera._19011903._zh-4039/19937_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

ENGLISH_TITLE_REVIEWS={'03fc2aa0-2bf5-4b95-8372-1615c2a9edec': {'page': 'https://www.wikiart.org/en/nicholas-roerich/earth-paternoster-1907', 'wikiart_id': '57727454edc2cb3880cb946d', 'wikiart_title': 'Earth paternoster', 'catalogue_title': 'Заклятие земное', 'note': "Individual English-title concordance for native Ж-1966: WikiArt 'Earth paternoster' and catalogue 'Заклятие земное'. Exact creator, pinned source and native object, and separately recorded visual comparison establish this version. The source Original Title field and untranslated index title remain absent; no original-language title is invented.", 'proof_sha256': 'd24856efe79fae8f280da4dc6f43fab967d22bf97edb47801857e91ac4b1fb59'}}
r.BASIS='Exact existing native museum objects, creator authorities, selected current WikiArt pages and individually compared physical versions. One source page has no Original Title field; its literal English title, unchanged catalogue titles, checksum-pinned untranslated index entries and visual evidence are individually reconciled. Preserve source date discrepancies, image framing, actual rights and unchanged catalogue metadata. Local image-only attachment; no publication or invented source fields.'
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
