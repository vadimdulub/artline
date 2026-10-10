#!/usr/bin/env python3
"""Twelve selected native museum gaps, with individual source/version review."""
import argparse,importlib.util,json,gzip
from pathlib import Path
from urllib.parse import urljoin,urlparse
s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-levitan-images-20261007'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
r.AUDIT=core.ROOT/'docs/research/local-wikiart-russian-additional-artists-20261007'
core.VERSION='local-wikiart-levitan-v1'
SELECTED={'644f3908-a910-414b-b4c2-cfad94b36e5e': [210324, 210325, 210326], '2b633435-6ff6-46dd-9851-8ea0857df1ee': [210210, 210211, 210212], 'd6f97c7d-5756-49ad-850a-e8b2a3da444b': [210306], '33b97fcd-abc5-450a-adcf-8b6404e382be': [210362], '4cd3dda6-82de-4a75-a9b1-d76863af97a3': [210039, 210254, 210267, 210269, 210411, 210255, 210256], '86d77717-4471-41db-866d-0dbf87e4bf9c': [210170, 210198, 210169], '8c20fc6f-b10f-45d8-842c-10388de7e965': [210092, 210093, 210094, 210095, 210098], '96bfb834-dc4f-4229-a105-993b745615fa': [210086, 210078, 210079, 210102, 210080, 210081, 210082, 210087, 210083, 210084, 210085], '7d717d84-3047-469f-abaa-75ab02ec6ccd': [210158, 210159, 210215, 210033, 210143], 'e96d578b-546f-4b55-9047-be8d36e8f165': [210294, 210293], 'afe15ca5-0fc4-4ab2-bbf6-56abb49794c3': [210419, 210431, 210432], 'e3f5a6c4-897b-487f-8889-fe0cce246bf0': [210419, 210431, 210432]}
f.IDS=list(SELECTED);f.DATE_VARIANT_IDS=set(f.IDS);f.MAX_SOURCE_OPTIONS=11

r.ARTISTS.update({'0d27b81a-f0c1-40c2-9f6e-c7a3cbc590af': {'qid': 'Q211356', 'native': 'levitan_ii', 'label': 'Левитан И. И.', 'life': '1860, село Кибарты, Литва – 1900, Москва', 'birth': 1860, 'death': 1900}})
f.SELECTION='Twelve remaining exact-title Russian Museum review artworks by Levitan, individually selected from pinned complete source indexes. Validate complete source index captures, native objects and exact physical versions before attachment. Preserve actual source dates, techniques, rights and unchanged catalogue data.'
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
  result.append(dict(page='https://www.wikiart.org/en/'+slug+'/'+name,prior_index_lead=item))
 if not 1<=len(result)<=11:raise ValueError('Unbounded individual source selection')
 core.save_new(RUN/'metadata/bounded-title-options'/(c['artwork_id']+'.json'),dict(original_fuzzy_options=options,selected_options=result,complete_index_pin=pin,reason='Individual editorial selection from the complete pinned same-creator source index. Individually selected titles from the scoped eight-artist metadata audit. Preserve all explicit date differences; a title lead is not a physical-version approval.'))
 return result
f.SOURCE_OPTION_TRANSFORM=source_options
r.BASIS='Exact existing Russian Museum inventory objects, verified Levitan creator authority, current WikiArt source pages and individual visual comparisons across same-title versions. Preserve dates, unknown metadata, rights and review status. No catalogue publication or biography change.'

PRINT_IDS={'96bfb834-dc4f-4229-a105-993b745615fa'}
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
