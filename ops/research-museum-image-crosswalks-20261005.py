#!/usr/bin/env python3
"""Bounded identifier research for existing illustrated museum leads."""
import argparse,importlib.util,json,time,re
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.PORT=55445;r.RUN=r.ROOT/'docs/research/museum-gaps-20261005'
KEYWORDS=['louvre','orsay','prado','uffizi','national gallery','hermitage','tretyakov','rijksmuseum','metropolitan','tate','moreau','picasso','versailles','carnavalet','thyssen','vatican','kunsthisto','boston','chicago','cleveland','pompidou','pushkin']

def snapshot():
 with r.connect()as db:
  rows=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,c.evidence_note::jsonb lead,
   COALESCE((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role,
    'identifiers',(SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=ar.id)))
    FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
   FROM citations c JOIN artworks a ON a.id=c.entity_id JOIN media_assets m ON m.id=a.primary_media_id
   WHERE c.entity_type='artwork' AND c.field_name='museum_location_lead_review' AND a.current_institution_id IS NULL
   AND a.status<>'archived' AND m.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa')
   AND a.creation_year_end<=1970 AND c.source_url LIKE 'https://www.wikiart.org/%%' ORDER BY a.id,c.id''').fetchall()
  selected={x['artwork']['id']:x for x in rows if any(word in x['lead'].get('reported_location','').casefold()for word in KEYWORDS)}
 r.save_gz(r.RUN/'selected-wikiart-museum-images.json.gz',list(selected.values()));print('Selected existing museum images',len(selected),flush=True)

def crosswalk():
 selected=r.load(r.RUN/'selected-wikiart-museum-images.json.gz');slugs=sorted({x['lead']['source_url'].split('/en/',1)[1]for x in selected if '/en/'in x['lead']['source_url']})
 for offset in range(0,len(slugs),40):
  dest=r.RUN/'wikiart-object-crosswalk'/f'{offset:04d}.json.gz'
  if dest.exists():continue
  query='''SELECT ?item ?wikiart ?creator ?collection ?inventory ?joconde ?ark ?met ?rijks ?nga ?image ?label WHERE { VALUES ?wikiart { '''+' '.join(json.dumps(v)for v in slugs[offset:offset+40])+''' } ?item wdt:P6002 ?wikiart .
 OPTIONAL { ?item wdt:P170 ?creator } OPTIONAL { ?item wdt:P195 ?collection } OPTIONAL { ?item wdt:P217 ?inventory }
 OPTIONAL { ?item wdt:P347 ?joconde } OPTIONAL { ?item wdt:P9394 ?ark } OPTIONAL { ?item wdt:P3634 ?met }
 OPTIONAL { ?item wdt:P350 ?rijks } OPTIONAL { ?item wdt:P2252 ?nga } OPTIONAL { ?item wdt:P18 ?image }
 OPTIONAL { ?item rdfs:label ?label FILTER(LANG(?label)="en") } }'''
  raw,receipt=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-selected-objects',timeout=45)
  if receipt['status']!=200:print('Deferred batch',offset,'HTTP',receipt['status'],flush=True);continue
  rows=[{k:v['value']for k,v in row.items()}for row in json.loads(raw)['results']['bindings']]
  r.save_gz(dest,{'rows':rows,'receipt':receipt});print('batch',offset,'/',len(slugs),'rows',len(rows),flush=True);time.sleep(1)


def titles():
 selected=r.load(r.RUN/'selected-wikiart-museum-images.json.gz')
 labels=set()
 for x in selected:
  name=x['artwork']['title']
  for title in [name,re.sub(r'\s*\([^)]*\)','',name).strip()]:
   labels.update([title,title[:1].lower()+title[1:]])
 labels=sorted(labels)
 for offset in range(0,len(labels),45):
  dest=r.RUN/'title-object-crosswalk'/f'{offset:04d}.json.gz'
  if dest.exists():continue
  query='SELECT ?item ?label ?creator ?collection ?inventory ?joconde ?ark ?met ?rijks ?nga ?image WHERE { VALUES ?label { '+' '.join(json.dumps(v)+'@en'for v in labels[offset:offset+45])+''' } ?item rdfs:label ?label . ?item wdt:P170 ?creator .
 OPTIONAL { ?item wdt:P195 ?collection } OPTIONAL { ?item wdt:P217 ?inventory }
 OPTIONAL { ?item wdt:P347 ?joconde } OPTIONAL { ?item wdt:P9394 ?ark } OPTIONAL { ?item wdt:P3634 ?met }
 OPTIONAL { ?item wdt:P350 ?rijks } OPTIONAL { ?item wdt:P2252 ?nga } OPTIONAL { ?item wdt:P18 ?image } }'''
  try:raw,receipt=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-selected-titles',timeout=45)
  except Exception as err:print('Deferred batch',offset,type(err).__name__,flush=True);continue
  if receipt['status']!=200:print('Deferred batch',offset,'HTTP',receipt['status'],flush=True);continue
  rows=[{k:v['value']for k,v in row.items()}for row in json.loads(raw)['results']['bindings']]
  r.save_gz(dest,{'rows':rows,'receipt':receipt});print('titles',offset,'/',len(labels),'rows',len(rows),flush=True);time.sleep(1)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['snapshot','crosswalk','titles']);args=p.parse_args();globals()[args.command]()
