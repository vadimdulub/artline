#!/usr/bin/env python3
"""Sixteen further selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-prints-landscapes-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-prints-landscapes-v1'
SELECTED={'d2cb8ab2-2475-4365-8c4f-26c831f0a14e': [230150], '2a52e013-41fe-42d2-864a-f459ee926184': [229706], '5ff4ff9b-166b-4c03-b7cb-3f44ba944bfc': [230152], '5d080189-6fae-4980-a5e6-651427977e90': [225630, 225631, 225632, 225629], '0b4decaf-e808-40c5-ac75-7d2717fc9b86': [237415], '16bc7d15-843f-4430-9d10-4d351d74ee43': [237431, 237372, 237373], '58c60d7c-de7e-414e-b214-ba24e82de22d': [226261], '805b0fce-87f2-48b3-8d01-fa7861a921ee': [225842], '524b4d27-f835-4002-b079-fb6fba8c639c': [226174, 225622], 'd1181247-1a22-48d6-b1e8-5989ed026cdf': [226168, 226174], '38a7b591-4a2f-4b98-85e0-c73a01949917': [225711, 225712, 225713, 225714], '34409d64-2c8f-4e68-b0a9-77df406d92dd': [229705], '03c70cd9-41ae-481c-80ce-5c2660d36e5c': [225719, 225720, 225721, 225722], '3f52caa1-144b-45a1-bf39-2c62ea7235aa': [225724, 225725, 225726], '826247bd-9eca-49b7-be5d-5bd2b61af372': [225981, 225982, 225983, 225984], '8749fd9a-a9ae-445d-9992-3e92225ffb70': [225630, 225631, 225632, 225629]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
r.ARTISTS['2ad50a57-bc3d-4c05-8c61-4312ff6b2967']=dict(qid='Q208993',native='rerih_nk',label='Рерих Н. К.',life='1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия',life_aliases=['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'],birth=1874,death=1947)
f.SELECTION='Sixteen existing eligible Russian Museum review artworks: eight print records and eight Roerich paintings. Select bounded source metadata before downloads, distinguish original drawings, printed designs and individual impressions, and compare landscape and stage-design versions. Preserve source statements and all catalogue facts.'
CONCORDANCES={('0b4decaf-e808-40c5-ac75-7d2717fc9b86', 'https://www.wikiart.org/en/valentin-serov/portrait-of-the-artist-a-p-ostroumova-lebedeva-1899', 'Портрет художницы А.П.Остроумовой-Лебедевой', 'Портрет А. П. Остроумовой-Лебедевой'): "Individual literal title concordance for native Гр.-39982: WikiArt 'Портрет художницы А.П.Остроумовой-Лебедевой' and catalogue 'Портрет А. П. Остроумовой-Лебедевой'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('16bc7d15-843f-4430-9d10-4d351d74ee43', 'https://www.wikiart.org/en/valentin-serov/portrait-of-l-n-andreev-1907', 'Портрет Л.Н.Андреева', 'Портрет писателя Л. Н. Андреева'): "Individual literal title concordance for native Гр.-44088: WikiArt 'Портрет Л.Н.Андреева' and catalogue 'Портрет писателя Л. Н. Андреева'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('2a52e013-41fe-42d2-864a-f459ee926184', 'https://www.wikiart.org/en/boris-kustodiev/alexei-tolstoy-the-adventures-of-nevzorov-or-ibikus-1925', 'Алексей Толстой. Похождение Невзорова, или ИБИКУС', 'Алексей Толстой. Похождение Невзорова, или ИБИКУС. Л.: ГИЗ'): "Individual literal title concordance for native Аф-43651: WikiArt 'Алексей Толстой. Похождение Невзорова, или ИБИКУС' and catalogue 'Алексей Толстой. Похождение Невзорова, или ИБИКУС. Л.: ГИЗ'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('34409d64-2c8f-4e68-b0a9-77df406d92dd', 'https://www.wikiart.org/en/boris-kustodiev/alexei-tolstoy-eccentrics-1925', 'Алексей Толстой. Чудаки', 'Алексей Толстой. Чудаки. М.; Л.: Изд. Л. Д. Френкель'): "Individual literal title concordance for native Аф-43652: WikiArt 'Алексей Толстой. Чудаки' and catalogue 'Алексей Толстой. Чудаки. М.; Л.: Изд. Л. Д. Френкель'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('5d080189-6fae-4980-a5e6-651427977e90', 'https://www.wikiart.org/en/nicholas-roerich/giantess-krimgerd-1915-2', 'Великанша Кримгерд', 'Великанша Кримгерд (Эдда)'): "Individual literal title concordance for native Гр.-41901: WikiArt 'Великанша Кримгерд' and catalogue 'Великанша Кримгерд (Эдда)'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('5ff4ff9b-166b-4c03-b7cb-3f44ba944bfc', 'https://www.wikiart.org/en/boris-kustodiev/poster-of-the-leningrad-society-bows-town-and-country-1925', 'Плакат Ленинградское Общество смычки города с деревней', 'Ленинградское общество смычки города с деревней'): "Individual literal title concordance for native Гр.Пл.-483: WikiArt 'Плакат Ленинградское Общество смычки города с деревней' and catalogue 'Ленинградское общество смычки города с деревней'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('826247bd-9eca-49b7-be5d-5bd2b61af372', 'https://www.wikiart.org/en/nicholas-roerich/kiss-the-earth-1912', 'Поцелуй земле', 'Поцелуй Земле. Действие 1-е'): "Individual literal title concordance for native Ж-1979: WikiArt 'Поцелуй земле' and catalogue 'Поцелуй Земле. Действие 1-е'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite.", ('d2cb8ab2-2475-4365-8c4f-26c831f0a14e', 'https://www.wikiart.org/en/boris-kustodiev/poster-for-the-freedom-loan-1917', 'Плакат Заем свободы', 'Плакат «Заемъ свободы»'): "Individual literal title concordance for native Гр.Луб.-3252: WikiArt 'Плакат Заем свободы' and catalogue 'Плакат «Заемъ свободы»'. Exact creator, dated native object and separately recorded image comparison establish the individually qualified identity; prints match the design only unless an individual impression is independently established. No general title normalization or catalogue rewrite."}
r.TITLE_CONCORDANCES.update(CONCORDANCES)
def source_options(c,options):
 result=[o for o in options if o['prior_index_lead']['contentId'] in SELECTED[c['artwork_id']]]
 assert {o['prior_index_lead']['contentId'] for o in result}==set(SELECTED[c['artwork_id']])
 aliases={204305:'portrait-of-captain-a-m-kostinich',204294:'portrait-of-alexander-bruloff-1827',204295:'portrait-of-alexander-bruloff'}
 if any(o['prior_index_lead']['contentId'] in aliases for o in result):
  url='https://www.wikiart.org/en/karl-bryullov/all-works/text-list';data,rc=r.capture(url,RUN/'metadata/canonical-pages/bryullov-list.html')
  links={urljoin(url,a['href']) for a in r.BeautifulSoup(data,'html.parser').select('a[href]')};updated=[]
  for o in result:
   cid=o['prior_index_lead']['contentId'];page='https://www.wikiart.org/en/karl-bryullov/'+aliases[cid] if cid in aliases else o['page']
   assert page in links
   updated.append(dict(o,page=page))
  core.save_new(RUN/'metadata/canonical-pages'/(c['artwork_id']+'.json'),dict(capture=rc,original_options=result,canonical_options=updated,reason='Literal canonical links from the current artist list; exact embedded image must independently match the selected pinned index. No generic filename normalization.'));result=updated
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_metadata_leads=options,selected_options=result,reason='Individually selected content IDs remove unrelated sitter-name similarities before source-page and visual review. Title similarity alone is not an identity decision.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
PRINT_IDS={'5ff4ff9b-166b-4c03-b7cb-3f44ba944bfc', '34409d64-2c8f-4e68-b0a9-77df406d92dd', '5d080189-6fae-4980-a5e6-651427977e90', '16bc7d15-843f-4430-9d10-4d351d74ee43', '2a52e013-41fe-42d2-864a-f459ee926184', 'd2cb8ab2-2475-4365-8c4f-26c831f0a14e', '0b4decaf-e808-40c5-ac75-7d2717fc9b86'}
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
