#!/usr/bin/env python3
"""Fifteen individually selected Malevich and Filonov gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-malevich-filonov-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-modern-artists-20261007'
core.VERSION='local-wikiart-malevich-filonov-v1'
SELECTED={'74a1a347-528b-4063-89e2-ba89a4d74f9c': [219681, 219684, 219685, 219686], '91e64c96-5ade-44ee-bcee-f1ad6df8e5dd': [219681, 219684, 219685, 219686], 'b7db7df0-19f5-4325-a86d-5cb439e00ecb': [219681, 219684, 219685, 219686], '3f7b42f7-db3f-4b76-bb89-609843cfea52': [219906, 219905], '85a7b97b-13c8-4824-aefd-dbf4b277ab1d': [219674], '5d449a22-65e4-46fc-8ba0-8570022fa11c': [219927, 219657], '7ece1f91-488a-4960-8e73-28b47a993772': [219927, 219657], 'd46a1e7e-ec4b-4b63-8d29-dd2181e34301': [219751, 219750], 'de44472e-6a0e-4d11-8dfb-d811628ce6b3': [219831], '8841f95b-642f-407e-8192-37580c246855': [219698], '32056f42-d401-49a4-a938-3b6929091ff5': [219625], '011bd0c4-53b2-47e2-b4f5-638f7722817a': [219600], 'cfd5e33f-8999-4972-b73d-4fa30dea5544': [216239], 'a26dde14-e9ae-4cc4-a7f9-7cb3e54c3dfe': [216284], '5bd40a13-934a-4551-aeaf-fe7063d9f873': [216231, 216232]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':{'qid': 'Q208993', 'native': 'rerih_nk', 'label': 'Рерих Н. К.', 'life': '1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия', 'life_aliases': ['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'], 'birth': 1874, 'death': 1947},
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Fifteen eligible Malevich and Filonov exact-title leads, with one to four explicitly selected source alternatives per work. Distinct repeated-title inventories, source-date differences and unknown dates require individual native physical-version review. The two wider Suprematism leads remain separately pending.'
CONCORDANCES={('d46a1e7e-ec4b-4b63-8d29-dd2181e34301', 'https://www.wikiart.org/en/kazimir-malevich/peasants', 'Два крестьянина на фоне полей', 'Крестьяне'): "Individual literal title concordance for native Ж-9398: WikiArt 'Два крестьянина на фоне полей' and catalogue 'Крестьяне'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
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
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Untranslated index entries, abbreviated sitter names and different source wording caused the fuzzy shortlist to omit these specific candidates. Reject unrelated sitter names before downloads; title/name overlap is a lead, not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact native object and creator identity, current source metadata and individual visual comparison. Preserve date differences, unknown metadata, rights and review status. No publication or general title exception.'

r.ARTISTS.update({
 '12697a4b-c8f1-456b-ab95-50d00de023ed':dict(qid='Q130777',native='malevich_ks',label='Малевич К. С.',life='1879, Киев – 1935, Ленинград',birth=1879,death=1935),
 '9c436c3c-2576-405a-b2de-23afd3e47e13':dict(qid='Q466187',native='filonov_pn',label='Филонов П. Н.',life='1883, Москва – 1941, Ленинград',life_aliases=['1883, Москва — 1941, Ленинград','1882/3, Москва – 1941, Ленинград'],birth=1883,death=1941)
})

NATIVE_REFERENCE_ALIASES={'3f7b42f7-db3f-4b76-bb89-609843cfea52': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_ks_dve_muzhskie_figuri_nachalo_1930_h_zh_9476/4532_mainfoto_03.jpg', '5d449a22-65e4-46fc-8ba0-8570022fa11c': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_ks_zhenskiy_tors_1928_1929_zh_9467/5981_mainfoto_03.jpg', '74a1a347-528b-4063-89e2-ba89a4d74f9c': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_k.s._golova_krestyanina._nachalo_1930-h._zh-9399/14164_mainfoto_03.jpg', '7ece1f91-488a-4960-8e73-28b47a993772': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_k.s._zhenskiy_tors._19281929._zh-9386/14204_mainfoto_03.jpg', '85a7b97b-13c8-4824-aefd-dbf4b277ab1d': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_ks_devushki_v_pole_1928_1929_zh_9433/5977_mainfoto_03.jpg', '8841f95b-642f-407e-8192-37580c246855': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_k.s._peyzazh_s_pyatyu_domami._19281929._zh-9496/14198_mainfoto_03.jpg', 'cfd5e33f-8999-4972-b73d-4fa30dea5544': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/filonov_pn_kozel_1920_e_zh_9599/4579_mainfoto_03.jpg', 'd46a1e7e-ec4b-4b63-8d29-dd2181e34301': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/malevich_k.s._krestyane._okolo_1930._zh-9398_/11847_mainfoto_03.jpg'}
import inspect
_native_source=inspect.getsource(r.native_facts)
if core.sha(_native_source.encode())!='419e852939a2e561171018327156bd2bba040078a02e66074907871d1b729dbd':raise ValueError('Pinned native validator changed')
if _native_source.count(' aliases={\n')!=1:raise ValueError('Native alias insertion point changed')
_alias_lines=''.join('  '+repr(aid)+':'+repr(url)+',\n' for aid,url in NATIVE_REFERENCE_ALIASES.items())
exec(compile(_native_source.replace(' aliases={\n',' aliases={\n'+_alias_lines),__file__+'::native-reference-aliases','exec'),r.__dict__)

UNKNOWN_DATE_REVIEWS={'011bd0c4-53b2-47e2-b4f5-638f7722817a': {'page': 'https://www.wikiart.org/en/kazimir-malevich/apple-tree-in-blossom', 'wikiart_id': '57727342edc2cb3880c7ff6c', 'wikiart_title': 'Apple Tree in Blossom', 'page_sha256': 'cbd8fdd21b2a80018d4819367c594a9434a56df4ac945cd8da181e8a46409640', 'accession': 'Ж-9395', 'period': 'Около 1930', 'native_url': 'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh_9395/index.php', 'catalogue_date': {'creation_year_start': 1930, 'creation_year_end': 1930, 'date_precision': 'circa', 'date_display': 'Около 1930'}, 'note': 'WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual comparison identifies native Ж-9395, whose creation period is Около 1930. This object-specific museum evidence establishes pre-1971 eligibility. The catalogue retains Около 1930 and its existing numeric interval. WikiArt source year fields remain null; no source year or missing catalogue field was invented.'}}

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
