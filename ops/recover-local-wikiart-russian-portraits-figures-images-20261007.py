#!/usr/bin/env python3
"""Sixteen further selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-portraits-figures-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-russian-portraits-figures-v1'
SELECTED={'d532e171-ea3a-4bb5-bbe6-bf4eb615448f': [214686, 214780, 214685], '6eed328e-2ecf-41f3-a0b8-3bd6265b5a12': [214786], 'f801760b-1b57-4b52-be18-d56ac1e2a022': [214871, 214872, 214873], '4ca04900-e579-4f6f-8d98-2fbb746c1fd6': [215183], 'd31f8566-7bb3-4b30-81e7-31eadf86938b': [237418, 237417], '47fc3b3c-d3f8-4bc4-8d04-fbc78ed76ba3': [229991], 'f138c96c-45a0-4595-a8ed-ef9b30e1c6f7': [226289, 226290, 226291, 226292], '4ad8c467-81dd-4948-abbb-b1e6c8e1cca4': [215291, 215186, 215049], '8aa0bf1f-e898-4ed2-9bd0-d64e800cb1b7': [214784], '20d0f67f-1bec-4bd9-a022-500023b77c7b': [230222], 'ce509251-d9d0-456b-aae8-3223bc0fcb7c': [215059, 215087, 215080], 'f4c17656-8d24-420c-8f62-bb7b299e84ac': [215080, 215087, 215059], '8db5460d-15e0-4618-83eb-91b9967eadf1': [214735], '85aa71cb-627d-4dcd-8b1f-13de00c2dcfe': [229927, 229928], '9b894d2a-ee60-4453-bc00-3776c4c253e9': [214786], 'bd455176-fe8f-44a2-8b57-a4f353a33458': [214892]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
r.ARTISTS['2ad50a57-bc3d-4c05-8c61-4312ff6b2967']=dict(qid='Q208993',native='rerih_nk',label='Рерих Н. К.',life='1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия',life_aliases=['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'],birth=1874,death=1947)
f.SELECTION='Sixteen existing eligible Russian Museum review artworks with title or sitter-name variants. Select bounded metadata alternatives before downloads, distinguish native physical versions including drawings, painted studies, stage designs and paired subjects, preserve source statements and all catalogue facts.'
CONCORDANCES={('9b894d2a-ee60-4453-bc00-3776c4c253e9', 'https://www.wikiart.org/en/kuzma-petrov-vodkin/portrait-of-a-p-petrovoy-vodkin-artist-s-mother-1909', 'Портрет А.П.Петровой-Водкиной, матери художника', 'Портрет матери художника (Портрет А. П. Петровой-Водкиной)'): "Individual literal title concordance for native Ж-2396: WikiArt 'Портрет А.П.Петровой-Водкиной, матери художника' and catalogue 'Портрет матери художника (Портрет А. П. Петровой-Водкиной)'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('d532e171-ea3a-4bb5-bbe6-bf4eb615448f', 'https://www.wikiart.org/en/kuzma-petrov-vodkin/boys-1916', 'Мальчики', 'Три мальчика (Играющие мальчики)'): "Individual literal title concordance for native Р-57963: WikiArt 'Мальчики' and catalogue 'Три мальчика (Играющие мальчики)'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite.", ('f138c96c-45a0-4595-a8ed-ef9b30e1c6f7', 'https://www.wikiart.org/en/nicholas-roerich/ominous-1901-3', 'Зловещие', 'Вещие'): "Individual literal title concordance for native Р-1939: WikiArt 'Зловещие' and catalogue 'Вещие'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
r.TITLE_CONCORDANCES.update(CONCORDANCES)
def source_options(c,options):
 if c['artwork_id']=='d532e171-ea3a-4bb5-bbe6-bf4eb615448f':
  proof=json.loads((RUN/'metadata/boys-option-review.json').read_bytes());assert proof['artwork_id']==c['artwork_id'];options=proof['after']
 if c['artwork_id']=='9b894d2a-ee60-4453-bc00-3776c4c253e9':
  raw=(r.AUDIT/'discovery.json').read_bytes();d=json.loads(raw)
  donor=next(x for x in d['leads'] if x['work']['id']=='6eed328e-2ecf-41f3-a0b8-3bd6265b5a12')
  item=next(x for x in donor['candidates'] if x['contentId']==214786)
  assert donor['source_artist_slug']=='kuzma-petrov-vodkin' and item['title']=='Портрет А.П.Петровой-Водкиной, матери художника' and item['completitionYear']==1909
  from urllib.parse import urlparse
  slug=urlparse(item['image']).path.split('/')[-1].split('!',1)[0].removesuffix('.jpg')
  extra=dict(page='https://www.wikiart.org/en/kuzma-petrov-vodkin/'+slug,prior_index_lead=item)
  core.save_new(RUN/'metadata/individual-source-option-expansion.json',dict(artwork_id=c['artwork_id'],discovery_sha256=core.sha(raw),donor_artwork_id=donor['work']['id'],selected_item=item,prior_options=options,new_option=extra,reason='The complete pinned index supplies the explicitly named mother portrait of 1909. The fuzzy lead list returned wife portraits. Select this single same-creator, same-sitter, same-year metadata candidate before any source image download; native version matching remains required.'))
  options=[extra]
 result=[o for o in options if o['prior_index_lead']['contentId'] in SELECTED[c['artwork_id']]]
 assert {o['prior_index_lead']['contentId'] for o in result}==set(SELECTED[c['artwork_id']])
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_metadata_leads=options,selected_options=result,reason='Individually selected content IDs remove unrelated sitter-name similarities before source-page and visual review. Title similarity alone is not an identity decision.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
