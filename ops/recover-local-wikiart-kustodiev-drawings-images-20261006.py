#!/usr/bin/env python3
"""Nine existing Kustodiev drawings/paintings with native version comparison."""
import argparse
import importlib.util
import gzip
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-kustodiev-drawings-images-20261006'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-kustodiev-drawing-versions-v1'
f.IDS=['fd983725-b04b-43b0-89f9-c9eea4a1ab87','a0aeebb3-1875-43a0-9f08-11b434e23f73','0f41214f-988f-4c8a-8ecd-b9a5d9eeccea','f0a00cd7-1ece-4ccf-b896-638e7890213d','f53248c3-16e9-4f21-9c1e-94a49d24cd48','1edf2f5b-d227-49ae-ba0e-c8b2c523bb6b','bd443c71-29e0-4ee7-a4d0-bcc3e6849d49','93e85b4d-7de8-49d8-ba91-034e09091641','a10e4a2e-2e5b-47bf-885d-af7869ec9d27']
f.DATE_VARIANT_IDS={'1edf2f5b-d227-49ae-ba0e-c8b2c523bb6b','bd443c71-29e0-4ee7-a4d0-bcc3e6849d49','93e85b4d-7de8-49d8-ba91-034e09091641','a10e4a2e-2e5b-47bf-885d-af7869ec9d27'}
f.SELECTION='Nine existing eligible Russian Museum gaps by Kustodiev: seven drawings and two paintings. Select bounded current WikiArt alternatives, compare exact native photographs, distinguish physical drawings, prints and oil paintings, and preserve catalogue dates and unknown fields. No catalogue publication or metadata changes.'

def source_options(c,options):
 extra={'bd443c71-29e0-4ee7-a4d0-bcc3e6849d49':229971,'a10e4a2e-2e5b-47bf-885d-af7869ec9d27':230013,'1edf2f5b-d227-49ae-ba0e-c8b2c523bb6b':229930}
 if c['artwork_id'] not in extra:return options
 path=core.ROOT/'docs/research/production-wikiart-images-20261006/artist-indexes/boris-kustodiev.json.gz'
 data=path.read_bytes();index=json.loads(gzip.decompress(data));receipt=index['receipt'];body=gzip.decompress((core.ROOT/receipt['body_path']).read_bytes())
 if core.sha(body)!=receipt['sha256'] or len(body)!=receipt['bytes'] or json.loads(body)!=index['items']:raise ValueError('Pinned artist index changed')
 items=[i for i in index['items'] if i['contentId']==extra[c['artwork_id']]]
 if len(items)!=1 or items[0]['artistName']!='Boris Kustodiev':raise ValueError('Unique alternative identity absent')
 i=items[0];slug=i['image'].rsplit('/',1)[1].split('!',1)[0].removesuffix('.jpg');selected=options+[dict(page='https://www.wikiart.org/en/boris-kustodiev/'+slug,prior_index_lead=i)]
 reason='One additional balcony scene dated 1922, matching the native tea drawing’s year and balcony setting; visual comparison must distinguish the composition and physical artwork.' if c['artwork_id']=='1edf2f5b-d227-49ae-ba0e-c8b2c523bb6b' else 'One additional same-sitter work with a longer title and date matching the native object; current page and exact native photograph determine physical identity.'
 core.save_new(RUN/'metadata/bounded-version-options'/(c['artwork_id']+'.json'),dict(index=str(path.relative_to(core.ROOT)),index_sha256=core.sha(data),receipt=receipt,artwork_id=c['artwork_id'],options=selected,reason=reason))
 return selected
f.SOURCE_OPTION_TRANSFORM=source_options

CONCORDANCES={
 ('a10e4a2e-2e5b-47bf-885d-af7869ec9d27','portrait-of-f-f-notgaft-collector-1918','Портрет Ф.Ф.Нотгафта (Коллекционер)','Портрет Ф. Ф. Нотгафта'):'Exact mixed-media portrait РС-5917: collector in a pale robe holding a picture, surrounding framed works, piano, armchair, framed reverse and patterned floor all match the native photograph. Preserve the source parenthetical Коллекционер and the unchanged catalogue title.',
 ('bd443c71-29e0-4ee7-a4d0-bcc3e6849d49','portrait-of-a-sculptor-and-painter-d-s-stelletsky-1901','Портрет скульптора и живописца Д.С.Стеллецкого','Портрет Д. С. Стеллецкого'):'Exact oil portrait Ж-1885: bespectacled smiling artist leaning beside a large seated sculpture, lit sleeves and hand, dark studio and round table. The source title adds the sitter’s occupations; preserve both literal titles without changing the catalogue.',
}
for (aid,slug,source_title,catalogue_title),note in CONCORDANCES.items():
 r.TITLE_CONCORDANCES[(aid,'https://www.wikiart.org/en/boris-kustodiev/'+slug,source_title,catalogue_title)]=note

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
