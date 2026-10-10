#!/usr/bin/env python3
"""Eight selected Serov/Roerich gaps with exact native physical-version checks."""
import argparse
import copy
import gzip
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-serov-roerich-images-20261006'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-serov-roerich-physical-versions-v1'
r.BASIS='Exact existing Russian Museum object URL, accession, creator authority and title; current WikiArt creator/object/photo identity and individual physical-version visual comparison. Original-language title is verified on the source page, or for the specifically reviewed Rite of Spring via its checksum-pinned Russian WikiArt index entry for the exact same image. Native dates/materials and actual source rights remain separate from unchanged catalogue metadata and explicit user source approval. Local image-only attachment; no publication or independent copyright-holder permission asserted.'
f.IDS=['609732ee-c625-4584-9dda-0e447145dcbb','97b0b1a3-4029-43ca-b091-40e8b3337c82','8103f611-837b-40ca-8023-5d1072313b77','2c9e4d8b-d94a-4dc0-92bc-10bf534cfc51','4fed8a9d-7e08-4e60-86e6-c7e457b2debb','823e789d-3702-4e94-85a1-abb1f600ffed','6b9923af-25d7-40ca-b812-a43dcb19ee9c','88b53694-8e3e-40a2-b48b-21b04ad19d29']
f.MAX_SOURCE_OPTIONS=5
f.SELECTION='Eight existing eligible Russian Museum review records by Serov and Roerich. Same-title/year WikiArt leads, at most five metadata options per object, remain unapproved until exact physical-version visual comparison. Preserve catalogue facts and actual source rights separately from user approval.'
r.ARTISTS.update({
 '2ad50a57-bc3d-4c05-8c61-4312ff6b2967':dict(qid='Q208993',native='rerih_nk',label='Рерих Н. К.',life='1874, Санкт-Петербург – 1947, Нагар, долина Кулу, Индия',life_aliases=['1874, Санкт-Петербург — 1947, Нагар, долина Кулу, Индия'],birth=1874,death=1947),
 '676b2231-17dd-4012-8b95-c57cef5f33b4':dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911),
})

RITE='97b0b1a3-4029-43ca-b091-40e8b3337c82'
RITE_PAGE='https://www.wikiart.org/en/nicholas-roerich/the-rite-of-spring-1945-1'
original_page_facts=wiki.page_facts
def page_facts(c,data,rc):
 if c['artwork_id']!=RITE:return original_page_facts(c,data,rc)
 chosen=f.selected(c);review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][RITE]
 native=r.native_facts(chosen)
 if native!=review['native_facts'] or native['accession']!='Ж-7093' or review['decision']!='continue_to_visual_review':raise ValueError('Individual Rite native version differs')
 proof=json.loads((RUN/'rite-title-concordance.json').read_bytes())
 if (rc['url'],review['wikiart_id'],review['wikiart_title'],chosen['title'])!=(RITE_PAGE,'57727491edc2cb3880cc4a77','The Rite of Spring','Весна священная'):raise ValueError('Individual title identity differs')
 if proof['page']!=RITE_PAGE or proof['page_sha256']!=core.sha(data):raise ValueError('Reviewed English source differs')
 soup=r.BeautifulSoup(data,'html.parser')
 if any(li.get_text(' ',strip=True).startswith('Original Title:') for li in soup.select('.wiki-layout-artwork-info article li')):raise ValueError('Source original-title presentation changed')
 index=(core.ROOT/proof['index_path']).read_bytes()
 if core.sha(index)!=proof['index_sha256']:raise ValueError('Pinned translated index differs')
 d=json.loads(gzip.decompress(index));body=gzip.decompress((core.ROOT/d['receipt']['body_path']).read_bytes())
 if core.sha(body)!=d['receipt']['sha256'] or len(body)!=d['receipt']['bytes'] or json.loads(body)!=d['items'] or d['receipt']!=proof['receipt']:raise ValueError('Translated API capture differs')
 item=proof['item']
 if d['items'].count(item)!=1 or item!=chosen['prior_index_lead'] or (item['title'],item['completitionYear'])!=('Весна Священная',1945):raise ValueError('Russian source title/date differs')
 adapted=copy.deepcopy(chosen);adapted.update(external_id=review['wikiart_id'],alternate_title=review['wikiart_title'])
 facts=r.original_facts(adapted,data,rc)
 if r.urlparse(facts['source_image_url']).path.split('!',1)[0]!=r.urlparse(item['image']).path.split('!',1)[0]:raise ValueError('Translated-title photograph differs')
 facts.update(native_object_review=review,native_original_title=None,individual_title_concordance=proof)
 return facts
wiki.page_facts=page_facts

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
