#!/usr/bin/env python3
"""Reconcile legacy WikiArt references against actual current artwork pages."""
import argparse,collections,concurrent.futures,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlsplit,urljoin
s=importlib.util.spec_from_file_location('images',Path(__file__).with_name('illustrated-300k-20261011.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;r=m.m
RUN=i.RUN/'wikiart';SIZE=250
def inputs():
 dest=RUN/'inputs.json.gz'
 if dest.exists():return m.load(dest)
 with r.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  rows=db.execute("SELECT a.id::text artwork_id,to_jsonb(a) artwork,to_jsonb(e) external,aa.artist_id::text,ar.display_name artist_name FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN artwork_artists aa ON aa.artwork_id=a.id AND aa.attribution_role='primary' JOIN artists ar ON ar.id=aa.artist_id WHERE e.entity_type='artwork' AND e.scheme='wikiart-legacy-content-id' AND a.status<>'archived' AND a.primary_media_id IS NULL AND a.creation_year_end<=1955 AND e.canonical_url LIKE 'https://www.wikiart.org/en/%%' ORDER BY ar.display_name,a.id").fetchall()
  counts=collections.Counter(row['artwork_id'] for row in rows);rows=[row for row in rows if counts[row['artwork_id']]==1];ids=list({row['artist_id'] for row in rows})
  profiles=collections.defaultdict(list);aliases=collections.defaultdict(list)
  for e in db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) AND scheme='wikiart-artist'",(ids,)):profiles[e['entity_id']].append(e['canonical_url'])
  for alias in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])',(ids,)):aliases[alias['artist_id']].append(alias['alias'])
 for row in rows:row.update(profiles=profiles[row['artist_id']],aliases=aliases[row['artist_id']])
 held={}
 # Existing individually documented component/identity decisions remain effective.
 for name in ['manual-image-holds.json','manual-identity-holds.json']:
  path=m.ROOT/'docs/research/wikiart-500-painters-20261011'/name
  if path.exists():held.update(m.load(path)['held_artwork_ids'])
 out=dict(at=m.now(),rows=[row for row in rows if row['artwork_id'] not in held],previous_individual_holds={row['artwork_id']:held[row['artwork_id']] for row in rows if row['artwork_id'] in held})
 i.saved(dest,out);print('Legacy WikiArt candidates',len(out['rows']),flush=True);return out
def select(index):
 batch='wikiart-'+str(index).zfill(3);dest=i.folder(batch)/'selection.json.gz'
 if dest.exists():return
 candidates=inputs()['rows'][index*SIZE:(index+1)*SIZE];assert candidates,'No more source candidates'
 def one(row):
  path=RUN/'research'/(row['artwork_id']+'.json')
  if path.exists():return m.load(path)
  out=dict(artwork_id=row['artwork_id'],source_url=row['external']['canonical_url'])
  try:
   url=row['external']['canonical_url'];i.d.core.provider_rate_slot('www.wikiart.org');page=r.wiki_fields(url);out['page']=page;a=row['artwork']
   assert urlsplit(url).path.rstrip('/')==urlsplit(urljoin(url,page['metadata']['paintingUrl'])).path.rstrip('/'),'Page now identifies a different artwork URL'
   assert page['date'] and page['date']['last']<=1955,'Current source date unknown or outside established image scope'
   assert page['date']['last']==a['creation_year_end'] and (a['creation_year_start'] is None or page['date']['first']==a['creation_year_start']),'Legacy and current source creation dates differ; individual version review required'
   assert m.norm(page['title']) in {m.norm(a['title']),m.norm(a.get('alternate_title'))},'Current title differs from stored title/translation'
   expected=url.rsplit('/',1)[0];assert page['artist_url'].rstrip('/')==expected,'Current creator profile differs from existing artwork URL'
   assert expected in {p.rstrip('/') for p in row['profiles'] if p} or m.norm(page['creator']) in {m.norm(x) for x in [row['artist_name'],*row['aliases']]},'Current source creator lacks verified catalogue identity'
   metadata=page['metadata']['image'];display=page['image_url'];assert re.fullmatch(r'uploads\d*\.wikiart\.org',urlsplit(metadata).hostname or ''),'Unexpected source image host'
   placeholder=display=='https://uploads.wikiart.org/Content/images/FRAME-600x480.jpg'
   if not placeholder:assert urlsplit(metadata).path.split('!')[0]==urlsplit(display).path.split('!')[0],'Displayed and artwork-metadata images identify different files'
   image_url=metadata if placeholder else display;assert re.fullmatch(r'uploads\d*\.wikiart\.org',urlsplit(image_url).hostname or '')
   prepared=dict(artwork_id=row['artwork_id'],native_id=row['external']['external_id'],current_source_id=page['source_id'],title=a['title'],creator_label=page['creator'],source_url=url,accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='wikiart',expected_museum_id=a['current_institution_id'],expected_primary_artist_id=row['artist_id'],rights_status=page['rights_status'],rights_label=page['rights_label'],rights_basis=page['rights_basis']+' User approval reaffirmed for the current image expansion; actual source labels retained.',image=dict(native_url=metadata,image_url=image_url,source=page,receipt=page['receipt']),plan_path=str(path),plan_sha256=page['receipt']['sha256'],manual_visual_required=placeholder,identity_confidence=.97,identity_basis='The existing legacy source URL resolves to this explicit current WikiArt artwork ID. Exact current artwork URL, stored title/translation, literal creation date and verified creator profile/name agree. Legacy numeric ID is retained as original evidence, not falsely equated to the current object ID; known current-object duplicates are held.')
   out.update(state='matched',row=prepared)
  except Exception as exc:out.update(state='held',reason=type(exc).__name__+': '+str(exc)[:500])
  return i.saved(path,out)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,candidates))
 rows=[out['row'] for out in results if out['state']=='matched'];held=[out for out in results if out['state']!='matched'];native_counts=collections.Counter(row['current_source_id'] for row in rows);url_counts=collections.Counter(row['image']['native_url'] for row in rows)
 with r.connect() as db:
  existing=collections.defaultdict(set)
  for e in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",([row['current_source_id'] for row in rows],)):existing[e['external_id']].add(e['entity_id'])
 valid=[]
 for row in rows:
  if native_counts[row['current_source_id']]>1 or url_counts[row['image']['native_url']]>1 or existing[row['current_source_id']]-{row['artwork_id']}:held.append(dict(artwork_id=row['artwork_id'],reason='Current native WikiArt object or image already identifies another catalogue record; reconcile object identity before attaching'))
  else:valid.append(row)
 i.saved(dest,dict(at=m.now(),batch=batch,provider='wikiart',rows=valid,held=held,selection_basis='Existing unillustrated legacy references independently reconciled to current native WikiArt pages, exact creator and literal dates. No rights-label exclusion. Known different-object and repeated-image identities held.'))
 i.saved(i.folder(batch)/'pin.json',dict(sha256=m.sha(dest.read_bytes())));print(batch,'matched',len(valid),'held',len(held),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--index',type=int,default=0);a=p.parse_args();select(a.index)
