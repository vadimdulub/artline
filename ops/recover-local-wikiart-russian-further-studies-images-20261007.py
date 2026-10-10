#!/usr/bin/env python3
"""Twelve further selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-further-studies-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-further-studies-v1'
SELECTED={'2bb6fbd3-571c-47b1-ab86-9968840e5705': [214988, 214989, 214990], '780a64be-0242-4cb4-8187-dbb01f88f2f9': [229895], '5b489f1d-0ab4-476a-9fb6-c98a24f21520': [215308, 215311, 214967, 215309], '65f84a9c-d80d-4a35-a3e5-c8ad72906036': [229734, 229991, 229827], '1b428e83-90cc-4aef-a157-91c4f09c6f36': [215347], 'aad5c193-98b1-4f08-8ae5-6550b5ff923c': [204234], 'd3204a13-6021-4f36-8375-a6c9e0ddd48f': [215145], '5ff58e3c-83d1-4d2e-8a63-97eff78ec49c': [215173], '4c0885fd-1a41-4527-afb3-5cfebd585dad': [214817], 'c41c04e3-3c62-4612-8418-1522f9bee1f4': [204281], '2d5720de-8ed7-4b45-a615-1542264015a0': [214784], '16d48950-c5da-4c34-a271-31a394b93df9': [214846, 214847, 214848, 214855]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':{'qid': 'Q208993', 'native': 'rerih_nk', 'label': 'Рерих Н. К.', 'life': '1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия', 'life_aliases': ['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'], 'birth': 1874, 'death': 1947},
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Twelve remaining eligible Russian Museum records selected after read-only revalidation of 88 pending title-variant leads. Specific portraits, figure studies, illustration designs, mythological works and still lifes require individual exact-version comparison. Source-index candidates do not approve attachment.'
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
  if cid in {204234,204281}:
   canonical={204234:'death-of-inessa-de-castro-morganatic-wife-of-portuguese-infant-don-pedro',204281:'pheb-in-his-chariot'}[cid]
   list_url='https://www.wikiart.org/en/karl-bryullov/all-works/text-list';data,rc=r.capture(list_url,RUN/'metadata/canonical-pages/bryullov-list.html');links={urljoin(list_url,a['href']) for a in r.BeautifulSoup(data,'html.parser').select('a[href]')};page='https://www.wikiart.org/en/karl-bryullov/'+canonical
   if page not in links:raise ValueError('Exact canonical Bryullov source page absent from current artist list')
   core.save_new(RUN/'metadata/canonical-pages'/(str(cid)+'.json'),dict(capture=rc,index_content_id=cid,index_image=item['image'],canonical_page=page,reason='Literal current artwork href differs from image filename suffix (1); exact source metadata/image identity must still pass.'))
   name=canonical
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=4:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Untranslated index entries, abbreviated sitter names and different source wording caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

NATIVE_REFERENCE_ALIASES={'16d48950-c5da-4c34-a271-31a394b93df9': 'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._natyurmort._na_stole._1936._rs-24643/11265_mainfoto_03.jpg', '1b428e83-90cc-4aef-a157-91c4f09c6f36': 'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._lezhaschaya_devushka._1871._r-7815/19969_mainfoto_03.jpg', '2bb6fbd3-571c-47b1-ab86-9968840e5705': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._golovi_muzhchin._18731875._zh-4057/19877_mainfoto_03.jpg', '2d5720de-8ed7-4b45-a615-1542264015a0': 'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._zhenskiy_portret._dva_naturschika._1906._r-49285/11127_mainfoto_03.jpg', '4c0885fd-1a41-4527-afb3-5cfebd585dad': 'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._sidyaschaya_naturschica._1913._r-49542/11135_mainfoto_03.jpg', '5b489f1d-0ab4-476a-9fb6-c98a24f21520': 'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_veri_repinoy_v_detstve._1882._r-7814/19966_mainfoto_03.jpg', '5ff58e3c-83d1-4d2e-8a63-97eff78ec49c': 'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_marii_arcibushevoy._1880._r-7939/20221_mainfoto_03.jpg', '780a64be-0242-4cb4-8187-dbb01f88f2f9': 'https://rusmuseumvrm.ru/data/collections/drawings/kustodiev_b._m._eskiz_kostyumov_k_komedii_a._n._ostrovskogo_ne_bilo_ni_grosha_da_vdrug_altin._1917._/39261_mainfoto_03.jpg', 'd3204a13-6021-4f36-8375-a6c9e0ddd48f': 'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_fiziologa_ivana_tarhanova._1906._r-60389/20228_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

ENGLISH_TITLE_REVIEWS={'5ff58e3c-83d1-4d2e-8a63-97eff78ec49c': {'page': 'https://www.wikiart.org/en/ilya-repin/portrait-of-maria-artsybasheva-1880', 'wikiart_id': '577272b9edc2cb3880c61333', 'wikiart_title': 'Portrait of Maria Artsybasheva', 'catalogue_title': 'Портрет Марии Арцыбушевой', 'note': 'Individual English-title concordance: WikiArt Portrait of Maria Artsybasheva (1880), a null Russian index title and an absent Original Title field identify native Р-7939, Портрет Марии Арцыбушевой, through the matching dated portrait, drawing marks, autograph and rounded dimensions. Preserve absent source fields; no general title fallback or catalogue change.', 'proof_sha256': 'fd58fcc7c52754ba3a025d1ed29afc17a817f083c1e5b99156b95ee8b7868919'}}
r.BASIS='Exact existing native museum objects, creator authorities, selected current WikiArt pages and individually compared physical versions. One source page has no Original Title field; its literal English title, unchanged catalogue title, checksum-pinned untranslated index entries and visual evidence are individually reconciled. Preserve source date discrepancies, image framing, actual rights and unchanged catalogue metadata. Local image-only attachment; no publication or invented source fields.'
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
