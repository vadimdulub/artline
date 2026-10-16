#!/usr/bin/env python3
"""Public source research while production reauthentication is pending."""
import importlib.util, json, collections
from pathlib import Path
from urllib.parse import urljoin
sp=importlib.util.spec_from_file_location('continuation',Path(__file__).with_name('creators-deep-continuation-20261011.py'))
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x);x.configure('thomas-theodor-heine')
source='https://www.wikiart.org/en/thomas-theodor-heine'
old=x.r.load(x.ROOT/'docs/research/low-count-200-painters-20261008/low-count-audit.json.gz')['painters']
pair=next(v for v in old if v.get('source') and v['source']['url']==source)
x.c.AID=pair['artist']['id']
raw,profile=x.c.capture(source);pair['profile_receipt']=profile
raw,rc=x.c.capture(source+'/all-works/text-list');items={}
for a in x.m.BeautifulSoup(raw,'html.parser').select('li a[href]'):
 if a['href'].startswith('/en/thomas-theodor-heine/'):
  title=a.get_text(' ',strip=True);ds=a.parent.get_text(' ',strip=True).removeprefix(title).strip(' ,');u=urljoin(source,a['href']);items[u]=dict(title=title,url=u,source_date=ds,date=x.m.dates.creation_date(ds))
raw,api=x.c.capture('https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl=thomas-theodor-heine&json=2');metadata=json.loads(raw)
x.r.save_gz(x.RUN/'source-indexes'/(x.c.AID+'.json.gz'),dict(outcome='indexed',items=list(items.values()),metadata=metadata,receipt=rc,metadata_receipt=api))
translations=collections.defaultdict(set)
for lang in ['ru','fr','de']:
 raw,trc=x.c.capture('https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl=thomas-theodor-heine&json=2');values=json.loads(raw)
 x.r.save_gz(x.RUN/(('russian-titles' if lang=='ru' else lang+'-titles')+'.json.gz'),dict(items=values,receipt=trc))
 for v in values:translations[str(v['contentId'])].add(x.q.norm(v.get('title')))
rows,held=x.b.source_candidates(pair)
for i,row in enumerate(rows,1):
 raw,rc=x.c.capture(row['source_url'],'page-captures');page=x.q.page_metadata(raw,rc)
 assert page['metadata']['artistUrl']=='/en/thomas-theodor-heine'
 assert x.q.image_key(page['metadata']['image'])==x.q.image_key(row['metadata']['image'])
 assert x.q.norm(page['metadata']['title'])==x.q.norm(row['work']['title'])
 row.update(page=page,wikiart_artwork_id=page['metadata']['_id'],translated_titles_checked=sorted(translations[row['source_id']]),selection_index=i)
 date=x.s.source_date(page);w=row['work']
 if date:w.update(date)
 else:
  w.update(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display='Unknown date');row['date_review']='No creation date established by the direct source; independent object research required.'
 w.update(alternate_title=page['fields'].get('Original Title') or None,medium_text=(page['fields'].get('Media') or page['fields'].get('Medium') or '').replace(' ,',',') or None,dimensions_text=page['fields'].get('Dimensions'))
 w['work_type']=x.s.kind(w['medium_text'])
 print(i,w['title'],w['date_display'],flush=True)
x.r.save_gz(x.RUN/'preliminary-research.json.gz',dict(pair=pair,rows=rows,held=held,source_index_count=len(items),metadata_count=len(metadata),at=x.r.now(),production_preflight_pending=True,limitation='Historical creator snapshot only; production creator identity, raw-label inventory and duplicate collisions must be freshly checked before writes. Public catalogue currently returns two linked works.'))
