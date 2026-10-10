#!/usr/bin/env python3
"""Six individually selected Roerich landscape gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-roerich-landscape-versions-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-title-variants-20261007'
core.VERSION='local-wikiart-roerich-landscape-versions-v1'
SELECTED={'d28da9a3-9eed-4d65-a6e7-a4b19a3f3a92': [226670], '4e84f32c-5aac-473d-8be4-53d64bee9aec': [226242, 225952], 'd7eb55ca-2dd8-4a66-a9e8-625a7edc636d': [225656], 'bbf0e5f2-fbfd-4d94-a4b6-ce5f4169ce31': [226090], '1bdda01d-d856-45c8-9b3a-a2e5f8639b3c': [226242, 225952], '34089c02-2787-418f-92b5-9e14dfa630a9': [226042, 225633, 226041]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=4
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':{'qid': 'Q208993', 'native': 'rerih_nk', 'label': 'Рерих Н. К.', 'life': '1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия', 'life_aliases': ['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'], 'birth': 1874, 'death': 1947},
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
 'd0c0f71d-2d33-4775-9290-ee4029860a8e':dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930),
 '86814786-f2e1-4ad8-b893-f03b046439b6':dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939),
})
f.SELECTION='Six eligible missing-image Roerich landscape records from the 76 revalidated remaining title-variant leads. Specific indexed landscapes, including untranslated entries, are individually selected for native version comparison; no source candidate implies an approved attachment.'
CONCORDANCES={('bbf0e5f2-fbfd-4d94-a4b6-ce5f4169ce31', 'https://www.wikiart.org/en/nicholas-roerich/lhasa-1942', 'Лхаса', 'Твердыня (Лхаса)'): "Individual literal title concordance for native Ж-7098: WikiArt 'Лхаса' and catalogue 'Твердыня (Лхаса)'. Exact creator, dated native object and separately recorded physical-version visual comparison establish this identity. No general title normalization or catalogue rewrite."}
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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
