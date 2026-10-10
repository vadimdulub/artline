#!/usr/bin/env python3
"""Nine further Serov/Roerich gaps with exact native version comparison."""
import argparse
import copy
import importlib.util
import gzip
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-serov-roerich-followup-images-20261006'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-serov-roerich-further-versions-v1'
f.IDS=['48c5424a-8209-4305-a308-ee52dc9499a9','b3abc0f1-27f5-47ec-bac3-c1cf5fa80c2e','928c3dbb-a672-44c3-917b-f504466918a7','db27356f-3805-4a7d-9bed-f6d991e936d9','d3dc6c1c-ad91-4c49-a482-2ace94085cde','067e54e1-e72b-4e31-936a-8ec85fe97890','ea932359-c34c-4969-9da6-92df0da4c2f2','c052cf28-7406-4839-9357-bd6c123d738d','8e811e60-cde7-4f07-ad16-b83cc07e03ee']
f.DATE_VARIANT_IDS=set(f.IDS)
f.SELECTION='Nine existing eligible Russian Museum image gaps by Roerich and Serov. Same-title candidates have differing source dates and require exact native physical-version comparison. Keep artwork metadata, unknown fields and review status unchanged; source dates and source approval remain separate evidence.'
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':dict(qid='Q208993',native='rerih_nk',label='Рерих Н. К.',life='1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия',life_aliases=['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'],birth=1874,death=1947),
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
})

def source_options(c,options):
 extras={
  'c052cf28-7406-4839-9357-bd6c123d738d':('valentin-serov',[237375]),
  'd3dc6c1c-ad91-4c49-a482-2ace94085cde':('nicholas-roerich',[226375,226376]),
  '928c3dbb-a672-44c3-917b-f504466918a7':('nicholas-roerich',[225888,225893]),
  'b3abc0f1-27f5-47ec-bac3-c1cf5fa80c2e':('nicholas-roerich',[226767,226529]),
 }
 if c['artwork_id'] not in extras:return options
 slug,content_ids=extras[c['artwork_id']]
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes'/(slug+'.json.gz')
 data=path.read_bytes();index=json.loads(gzip.decompress(data));receipt=index['receipt'];body=gzip.decompress((core.ROOT/receipt['body_path']).read_bytes())
 if core.sha(body)!=receipt['sha256'] or len(body)!=receipt['bytes'] or json.loads(body)!=index['items']:raise ValueError('Pinned artist index changed')
 selected=list(options)
 for cid in content_ids:
  items=[i for i in index['items'] if i['contentId']==cid]
  if len(items)!=1 or items[0]['artistName']!=c['artist']:raise ValueError('Unique alternative identity absent')
  i=items[0];filename=i['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg')
  selected.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+filename,prior_index_lead=i))
 reason='One additional Simonovich portrait dated 1880; the exact native photograph must decide sitter and physical artwork identity.' if slug=='valentin-serov' else 'Two individually selected same-subject study/version alternatives; current source metadata and exact native photograph determine physical identity.'
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=receipt,artwork_id=c['artwork_id'],options=selected,reason=reason))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

CONCORDANCES={
 ('c052cf28-7406-4839-9357-bd6c123d738d','portrait-of-lialia-adelaida-simonovich-1880','Ляля (Аделаида Яковлевна) Симонович','Портрет А. Я. Симонович'):
 'The source names the sitter Lialia (Adelaida Yakovlevna) Simonovich; the catalogue uses her initials. This literal concordance applies only to the visually matched childhood portrait Ж-1733, 1880, with identical head, ear, gaze, white ruffled collar and clothing folds. Preserve both titles.'
}
for (aid,slug,source_title,local_title),note in CONCORDANCES.items():
 r.TITLE_CONCORDANCES[(aid,'https://www.wikiart.org/en/valentin-serov/'+slug,source_title,local_title)]=note

CAMP='d3dc6c1c-ad91-4c49-a482-2ace94085cde'
CAMP_PAGE='https://www.wikiart.org/en/nicholas-roerich/polovtsian-camp-1914-1'
CAMP_NOTE='Individual editorial translation: Polovtsian camp corresponds to Половецкий стан. The English WikiArt page has no Original Title field; no Russian source title is invented. The reviewed photograph matches the exact native set design Ж-1983, including two flags, patterned tents, three smoke columns and hill contours. WikiArt dates it 1914; the native and catalogue date 1909 remains unchanged. Strong yellow/red source colour differences are preserved.'
r.BASIS='Exact existing Russian Museum object URL, accession, creator authority and title; current WikiArt creator/object/photo identity and individual physical-version visual comparison. Original-language titles are verified, with literal sitter-name concordance for Ж-1733 and individually recorded English/Russian editorial translation for Ж-1983, whose source has no Original Title field. Native dates/materials and actual source rights remain separate from unchanged catalogue metadata and explicit user source approval. Local image-only attachment; no publication or independent copyright-holder permission asserted.'
original_page_facts=wiki.page_facts
def page_facts(c,data,rc):
 if c['artwork_id']!=CAMP:return original_page_facts(c,data,rc)
 chosen=f.selected(c);review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][CAMP]
 native=r.native_facts(chosen)
 if native!=review['native_facts'] or native['accession']!='Ж-1983' or review['decision']!='continue_to_visual_review':raise ValueError('Individual camp native version differs')
 proof=json.loads((RUN/'camp-title-concordance.json').read_bytes())
 if (rc['url'],review['wikiart_id'],review['wikiart_title'],chosen['title'])!=(CAMP_PAGE,'5772747cedc2cb3880cc2c21','Polovtsian camp','Половецкий стан'):raise ValueError('Individual camp title identity differs')
 if proof['page']!=CAMP_PAGE or proof['page_sha256']!=core.sha(data) or proof['note']!=CAMP_NOTE or review.get('individual_title_concordance')!=CAMP_NOTE:raise ValueError('Reviewed camp source or translation differs')
 soup=r.BeautifulSoup(data,'html.parser')
 if any(li.get_text(' ',strip=True).startswith('Original Title:') for li in soup.select('.wiki-layout-artwork-info article li')):raise ValueError('Source original-title presentation changed')
 index=(core.ROOT/proof['index_path']).read_bytes()
 if core.sha(index)!=proof['index_sha256']:raise ValueError('Pinned English index differs')
 d=json.loads(gzip.decompress(index));body=gzip.decompress((core.ROOT/d['receipt']['body_path']).read_bytes())
 if core.sha(body)!=d['receipt']['sha256'] or len(body)!=d['receipt']['bytes'] or json.loads(body)!=d['items'] or d['receipt']!=proof['receipt']:raise ValueError('English API capture differs')
 item=proof['item']
 if d['items'].count(item)!=1 or item!=chosen['prior_index_lead'] or (item['contentId'],item['title'],item['completitionYear'])!=(226376,'Polovtsian camp',1914):raise ValueError('Individual English source title/date differs')
 adapted=copy.deepcopy(chosen);adapted.update(external_id=review['wikiart_id'],alternate_title=review['wikiart_title'])
 facts=r.original_facts(adapted,data,rc)
 if r.urlparse(facts['source_image_url']).path.split('!',1)[0]!=r.urlparse(item['image']).path.split('!',1)[0]:raise ValueError('Individual camp photograph differs')
 facts.update(native_object_review=review,native_original_title=None,individual_title_concordance=proof)
 return facts
wiki.page_facts=page_facts

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
