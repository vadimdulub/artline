#!/usr/bin/env python3
"""Six existing Serov drawings: exact sheet review of undated WikiArt leads."""
import argparse
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-serov-undated-drawings-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-serov-undated-drawing-review-v1'
f.IDS=['09939d3f-5b6c-4362-b8cb-9786e3a08066','72ea4757-1e2e-4978-bc84-122aac52d5e7','f6c4e974-6b11-4053-b674-243c2b2bf59c','f11a2f68-2458-4cab-a512-5a8e8e5cb910','09fd9395-4925-4a27-9b35-b084bfa85f5e','2fe15ba0-34fd-42ec-9e28-01adaa8e7584']
f.DATE_VARIANT_IDS=set(f.IDS)
f.SELECTION='Six existing eligible Russian Museum Serov drawings with four individually selected undated WikiArt leads. Compare exact physical sheets with native inventory photographs, preserving missing source dates and all catalogue fields. No date may be inferred from a filename or the artist lifespan.'
r.ARTISTS['676b2231-17dd-4012-8b95-c57cef5f33b4']=dict(qid='Q217128',native='serov_v_a',label='Серов В. А.',life='1865, Петербург – 1911, Москва',birth=1865,death=1911)
CONCORDANCES={}
BAKST='f6c4e974-6b11-4053-b674-243c2b2bf59c'
BAKST_PAGE='https://www.wikiart.org/en/valentin-serov/portrait-of-leo-bakst'
BAKST_ID='577276c8edc2cb3880d291f9'
BAKST_PAGE_SHA='dc5cbcfbba57f55a71ce38f79e0a30d90885fbfb9a5d5c4a00188e89a74e28f4'
DATE_NOTE='WikiArt explicitly leaves the creation date unknown (structured year ?; no displayed Date field). Individual visual review identifies Russian Museum sheet Р-13438, dated Первая половина 1900-х (first half of the 1900s). This native object evidence establishes pre-1971 eligibility; the existing catalogue retains its coarser 1900–1909 interval and original date text. WikiArt source year fields remain null. No source year was invented and no catalogue date or unknown field was rewritten.'
r.BASIS='Exact existing Russian Museum object URL, accession, creator authority and title; current WikiArt original-language title, creator/object/photo identity and individual physical-sheet visual comparison. WikiArt creation date remains explicitly unknown. A frozen individual review of exact native sheet Р-13438 and its first-half-of-the-1900s date establishes pre-1971 scope without changing source or catalogue years. Actual rights labels and explicit user source approval remain separate. Local image-only attachment; no publication or independent copyright-holder permission asserted.'

def source_date_review(c,record,soup,rc,data):
 if (c['artwork_id'],rc['url'],record.get('_id'),record.get('year'))!=(BAKST,BAKST_PAGE,BAKST_ID,'?'):
  raise ValueError('Unknown source date has no individual native version/date approval')
 if core.sha(data)!=BAKST_PAGE_SHA or rc['sha256']!=BAKST_PAGE_SHA:
  raise ValueError('Individually reviewed undated source page changed')
 if any(li.find('s') and wiki.norm(li.find('s').get_text(' ',strip=True))=='date' for li in soup.select('.wiki-layout-artwork-info article > ul > li')):
  raise ValueError('Unknown source date presentation changed')
 catalogue=dict(creation_year_start=c['creation_year_start'],creation_year_end=c['creation_year_end'],date_precision=c['date_precision'],date_display=c['date_display'])
 if catalogue!=dict(creation_year_start=1900,creation_year_end=1909,date_precision='decade',date_display='Первая половина 1900-х'):
  raise ValueError('Reviewed catalogue creation scope changed')
 review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][BAKST]
 native=review['native_facts']
 if review['decision']!='continue_to_visual_review' or review['selected_page']!=BAKST_PAGE or review['wikiart_id']!=BAKST_ID:
  raise ValueError('Individual undated sheet identity approval absent')
 if (native['accession'],native['period'],native['capture']['url'])!=('Р-13438','Первая половина 1900-х','https://rusmuseumvrm.ru/data/collections/drawings/r-13438/index.php'):
  raise ValueError('Individual native date/object differs')
 p=RUN/'metadata/museum'/(BAKST+'.html');nd=p.read_bytes()
 if core.sha(nd)!=native['capture']['sha256'] or len(nd)!=native['capture']['bytes']:
  raise ValueError('Reviewed native date evidence changed')
 visual=[x for x in json.loads((RUN/'alternative-visual-review.json').read_bytes())['options'] if x['artwork_id']==BAKST and x['page']==BAKST_PAGE]
 if len(visual)!=1 or visual[0]['decision']!='approved' or visual[0]['selected_for_attachment'] is not True or visual[0]['visually_inspected'] is not True:
  raise ValueError('Exact undated physical-sheet comparison missing')
 for receipt in [visual[0]['private_source_download'],visual[0]['reference_capture']]:
  raw=Path(receipt['path']).read_bytes()
  if core.sha(raw)!=receipt['sha256'] or len(raw)!=receipt['bytes']:raise ValueError('Reviewed date/version photograph changed')
 expected=dict(artwork_id=BAKST,page=BAKST_PAGE,wikiart_id=BAKST_ID,page_sha256=BAKST_PAGE_SHA,source_structured_year='?',source_year_start=None,source_year_end=None,source_displayed_date=None,native_facts=native,catalogue_date=catalogue,conservative_eligibility_upper_bound=1909,scope_basis='Individually matched physical sheet and its explicit native creation period; the whole 1900s decade is before 1971. No exact creation year inferred.',version_note=review['reason'],source_download=visual[0]['private_source_download'],native_reference=visual[0]['reference_capture'],decision='eligible_exact_native_version',note=DATE_NOTE)
 proof=json.loads((RUN/'unknown-source-date-review.json').read_bytes())
 if proof!=expected:raise ValueError('Frozen individual native source-date review differs')
 return proof

wiki.SOURCE_DATE_REVIEW=source_date_review

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
