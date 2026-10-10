#!/usr/bin/env python3
"""Nine existing Repin gaps with exact native object/version comparison."""
import argparse
import importlib.util
import gzip
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-repin-images-20261006'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-repin-physical-versions-v1'
f.IDS=['5eb77ac9-ab10-4518-94ee-b4a8e9268001','cd6d1886-f0b8-4e80-8948-0121167f4547','d6793c7f-d5e1-4881-8385-42013feff0d8','3b6d09c5-cb56-4d10-a83e-5ff517c3798c','12d6c39a-3067-48aa-a5d9-07b135066b53','a0ba8c5c-92a4-4395-844b-42cd98257aff','1c3bc019-78fd-48af-a47c-aa5f79299421','61a8ae7d-c91c-4689-afe1-137b81ff62d4','3d527db8-b89f-4154-9a22-6ebee3854deb']
f.MAX_SOURCE_OPTIONS=2
f.DATE_VARIANT_IDS=set(f.IDS)
f.SELECTION='Nine specific existing eligible Russian Museum gaps by Repin, with nineteen individually selected WikiArt pages and at most four physical-version alternatives per record. Native accessions, materials and exact photographs must distinguish studies, finished paintings and repeated sitter portraits. Differing or absent source dates remain separate evidence. No catalogue metadata changes or publication.'
r.ARTISTS['d0c0f71d-2d33-4775-9290-ee4029860a8e']=dict(qid='Q172911',native='repin_ie',label='Репин И. Е.',life='1844, Чугуев, Харьковской губ. – 1930, Куоккала близ Ленинграда',birth=1844,death=1930)

def source_options(c,options):
 choices={
  '3b6d09c5-cb56-4d10-a83e-5ff517c3798c':[214928,214929,214987],
  'd6793c7f-d5e1-4881-8385-42013feff0d8':[214941,214942,214940],
  'cd6d1886-f0b8-4e80-8948-0121167f4547':[215337,215338,215335,215336],
  '5eb77ac9-ab10-4518-94ee-b4a8e9268001':[214978,214981],
  '1c3bc019-78fd-48af-a47c-aa5f79299421':[215209,215036,215169],
 }
 if c['artwork_id'] not in choices:return options
 # The image filename is not this finished painting's canonical page slug.
 # Other numbered studies and sitter-title variants are explicit alternatives.
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes/ilya-repin.json.gz'
 data=path.read_bytes();index=json.loads(gzip.decompress(data));receipt=index['receipt']
 body=gzip.decompress((core.ROOT/receipt['body_path']).read_bytes())
 if core.sha(body)!=receipt['sha256'] or len(body)!=receipt['bytes'] or json.loads(body)!=index['items']:raise ValueError('Pinned Repin index changed')
 selected=[]
 for cid in choices[c['artwork_id']]:
  items=[i for i in index['items'] if i['contentId']==cid]
  if len(items)!=1:raise ValueError('Unique indexed version absent')
  i=items[0];slug='haulers-on-the-volga-1873' if cid==214987 else i['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg')
  selected.append(dict(page='https://www.wikiart.org/en/ilya-repin/'+slug,prior_index_lead=i))
 if any(o['prior_index_lead']['artistName']!='Ilya Repin' for o in selected):raise ValueError('Unexpected Repin version alternatives')
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=receipt,artwork_id=c['artwork_id'],options=selected,reason='Individually selected same-subject studies/portraits with numbered or translated title variants. These are competing physical versions; current pages and the exact native photograph decide selection.'))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

CONCORDANCES={
 ('3b6d09c5-cb56-4d10-a83e-5ff517c3798c','barge-haulers-on-the-volga-1-1870','Бурлаки на Волге1','Бурлаки на Волге'):'Exact oil study Ж-7928: frontal line of haulers, large sail behind them, steep right bank and matching lower-right dated inscription. Source title suffix 1 distinguishes this study from other versions; catalogue title is unchanged.',
 ('5eb77ac9-ab10-4518-94ee-b4a8e9268001','follow-me-satan-1895','Иди за мной, Сатано','«Иди за мною, Сатано»'):'Exact oil sketch Ж-2779: pale-robed figure beside a dark winged figure, red flames and matching rocks and lower-right inscription. The source uses мной while the native/catalogue title uses мною; retain both literal titles and the catalogue date uncertainty.',
 ('cd6d1886-f0b8-4e80-8948-0121167f4547','putting-a-propagandist-under-arrest-1-1879','Арест пропагандиста1','Арест пропагандиста'):'Exact graphite sheet Р-7869: foreground woman with headscarf, central standing man and child, seated figure at right, beam and window lines and lower-left 1879 signature. Source suffix 1 distinguishes this preliminary drawing from another drawing and the paintings; catalogue title is unchanged.',
 ('d6793c7f-d5e1-4881-8385-42013feff0d8','burlak-2-1870','Бурлак2','Бурлак'):'Exact oil study Ж-4055: standing cap-wearing hauler, pale harness over blue-green shirt, rope belt, hands, fence and lower-right 1870 signature. Source suffix 2 distinguishes this physical study from the pipe-smoking bust and other head study; catalogue title is unchanged.',
}
for (aid,slug,source_title,catalogue_title),note in CONCORDANCES.items():
 r.TITLE_CONCORDANCES[(aid,'https://www.wikiart.org/en/ilya-repin/'+slug,source_title,catalogue_title)]=note

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
