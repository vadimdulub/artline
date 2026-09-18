#!/usr/bin/env python3
"""Read-only duplicate leads. No same-name/title candidate is auto-deleted."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl,unquote
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def canonical_url(url):
 p=urlsplit(url or '');host=(p.hostname or '').lower().removeprefix('www.');return (host,unquote(p.path).rstrip('/'),tuple(sorted(parse_qsl(p.query,keep_blank_values=True))))

def entity_capture(q):
 # Historical immutable captures supply leads only; each proposed merge still
 # requires a fresh primary review. Do not erase old leads when a new campaign
 # uses its own capture directory.
 roots=[m.x.r.RUN/'entities',m.x.ROOT/'docs/research/overnight-countries-20260913/wikimedia/entities',m.x.ROOT/'docs/research/wikimedia-catalogue-scan-20260913/entities']
 return next((root/(q+'.json') for root in roots if (root/(q+'.json')).exists()),roots[0]/(q+'.json'))

def audit(target,phase):
 run=m.x.BASE/'duplicates'/phase;output_path=run/(target+'-audit.json')
 if output_path.exists():return
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='180s'")
  artists=m.artist_inventory(db)
  works=db.execute("""SELECT a.id::text,a.slug,a.title,a.alternate_title,a.normalized_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.object_form,a.current_institution_id::text,i.slug institution_slug,a.accession_number,a.status,a.revision,a.primary_media_id::text,ma.checksum_sha256,
   coalesce((SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id::text,'slug',p.slug,'name',p.display_name,'role',aa.attribution_role)) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators
   FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.status<>'archived'""").fetchall()
  authority=db.execute("SELECT e.entity_type,e.entity_id::text,e.scheme,e.external_id,e.canonical_url FROM external_identifiers e WHERE entity_type IN ('artist','artwork')").fetchall()
  # Scope citation evidence to active artwork records; ignore dataset-level
  # URLs as physical-object identity keys.
  citations=db.execute("""SELECT c.entity_id::text,c.field_name,c.source_record_id,c.source_url,s.slug source_slug FROM citations c JOIN artworks a ON a.id=c.entity_id JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND a.status<>'archived'""").fetchall()
  foreign_keys=db.execute("""SELECT conrelid::regclass::text table_name,confrelid::regclass::text references_table,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE contype='f' AND confrelid IN ('artworks'::regclass,'artists'::regclass) ORDER BY 1""").fetchall()
  counts={'active_artworks':len(works),'artists':len(artists),'authorities':len(authority),'artwork_citations':len(citations)}
 bywork={w['id']:w for w in works};byartist={a['id']:a for a in artists};leads=collections.defaultdict(list)
 def grouped(items,key):
  groups=collections.defaultdict(list)
  for row in items:
   k=key(row)
   if k:groups[k].append(row)
  return {k:v for k,v in groups.items() if len(v)>1}
 for key,group in grouped(works,lambda w:(w['institution_slug'],m.m.accession_key(w['accession_number'])) if w['institution_slug'] and w['accession_number'] and m.m.accession_key(w['accession_number']) not in ('0','UNKNOWN','N/A','NONE','-') else None).items():
  leads['same_institution_accession'].append({'institution':key[0],'accession_key':key[1],'works':group})
 incomplete_groups=collections.defaultdict(dict)
 for w in works:
  if not w['accession_number']:continue
  acc=m.m.accession_key(w['accession_number'])
  if acc in ('0','UNKNOWN','N/A','NONE','-'):continue
  for creator in w['creators']:
   if creator['role']=='primary':incomplete_groups[(creator['slug'],acc)][w['id']]=w
 for key,group in incomplete_groups.items():
  if len(group)>1 and any(w['institution_slug'] is None for w in group.values()) and any(w['institution_slug'] is not None for w in group.values()):leads['same_creator_inventory_missing_institution'].append(dict(artist_slug=key[0],accession_key=key[1],works=list(group.values())))
 for key,group in grouped(works,lambda w:w['checksum_sha256']).items():leads['same_image_sha256'].append({'sha256':key,'works':group})
 for key,group in grouped(works,lambda w:(w['institution_slug'],m.m.r.norm(w['title']),tuple(sorted(c['slug'] for c in w['creators'] if c['role']=='primary'))) if any(c['role']=='primary' for c in w['creators']) and w['institution_slug'] and w['title'] else None).items():
  leads['same_title_creator_institution'].append({'key':key,'works':group})
 for key,group in grouped([a for a in artists if a['status']!='archived'],lambda a:(m.f.names.namekey(a['display_name']),a['birth_year'],a['death_year']) if a['birth_year'] is not None and a['death_year'] is not None else None).items():leads['same_artist_name_closed_lifespan'].append({'key':key,'artists':group})
 source_objects=collections.defaultdict(set);url_examples={}
 artist_qids={e['external_id'] for e in authority if e['entity_type']=='artist' and e['scheme']=='wikidata'}
 checked_types=set(artist_qids)
 for row in [*authority,*citations]:
  if row.get('entity_type','artwork')!='artwork' or row['entity_id'] not in bywork:continue
  u=row.get('canonical_url') or row.get('source_url') or '';key=canonical_url(u)
  if key[0]=='wikidata.org':
   q=key[1].rsplit('/',1)[-1]
   if q not in checked_types and re.fullmatch(r'Q\d+',q):
    checked_types.add(q);path=entity_capture(q)
    if path.exists():
     e=json.loads(path.read_text())['entity']
     if any(v.get('id')=='Q5' for v in m.m.r.values(e,'P31') if isinstance(v,dict)):artist_qids.add(q)
   if q in artist_qids:continue
  # A creator-reconciliation citation can still point to an exact museum
  # object page. Retain that physical-object lead; only known person URLs
  # (such as the Wikidata artist identities above) are excluded.
  if not key[0] or key[1] in ('','/','/artworks','/collection','/collections') or key[1].endswith(('.csv','.json','.zip')):continue
  # Museum object pages/API object endpoints and exact Wikidata item URLs.
  german_object=(key[0]=='sammlung.staedelmuseum.de' and bool(re.match(r'^/(?:en/work|de/werk)/[^/]+$',key[1]))) or (key[0]=='kunsthalle-karlsruhe.de' and key[1].startswith('/kunstwerke/'))
  objectish=bool(german_object or re.search(r'/objects?/|/artwork/|/art/|/collection/|/collectie/|/notice/(?:joconde|palissy)/|/wiki/Q\d+$|^/2\d{7,}$',key[1],re.I) or any(k.lower() in ('object_number','objectid','artworkid') for k,v in key[2]))
  if not objectish:continue
  source_objects[key].add(row['entity_id']);url_examples[key]=u
 for key,ids in source_objects.items():
  if len(ids)>1:leads['same_object_source_url'].append({'url':url_examples[key],'canonical_key':key,'works':[bywork[i] for i in sorted(ids)]})
 museum_objects={(e['scheme'],e['external_id']):e['entity_id'] for e in authority if e['entity_type']=='artwork' and e['entity_id'] in bywork}
 for e in authority:
  if e['entity_type']!='artwork' or e['scheme']!='wikidata' or e['entity_id'] not in bywork:continue
  path=entity_capture(e['external_id'])
  if not path.exists():continue
  entity=json.loads(path.read_text())['entity']
  for prop,scheme in [('P9834','fng-object')]:
   for identifier in m.m.r.values(entity,prop):
    if not isinstance(identifier,str):continue
    other=museum_objects.get((scheme,identifier))
    if other and other!=e['entity_id']:leads['artwork_authority_crosswalk'].append(dict(wikidata=e['external_id'],museum_scheme=scheme,museum_object_id=identifier,works=[bywork[e['entity_id']],bywork[other]],entity_capture=str(path.relative_to(m.x.ROOT))))
 # Wikidata museum person crosswalks can expose two existing artist rows for
 # one identity even though every individual scheme has a uniqueness index.
 index=collections.defaultdict(set)
 for e in authority:
  if e['entity_type']=='artist':index[(e['scheme'],e['external_id'])].add(e['entity_id'])
 for e in authority:
  if e['entity_type']!='artist' or e['scheme']!='wikidata':continue
  path=entity_capture(e['external_id'])
  if not path.exists():continue
  entity=json.loads(path.read_text())['entity']
  canonical_qid=entity.get('id')
  if canonical_qid and canonical_qid!=e['external_id']:
   for other in index.get(('wikidata',canonical_qid),set())-{e['entity_id']}:
    if other in byartist and e['entity_id'] in byartist and byartist[other]['status']!='archived' and byartist[e['entity_id']]['status']!='archived':leads['artist_wikidata_redirect'].append({'old_wikidata':e['external_id'],'canonical_wikidata':canonical_qid,'artists':[byartist[e['entity_id']],byartist[other]],'entity_capture':str(path.relative_to(m.x.ROOT))})
  for prop,scheme in [('P2252','nga-constituent'),('P2174','moma-person'),('P2741','tate-person')]:
   for ident in m.m.r.values(entity,prop):
    if not isinstance(ident,str):continue
    if prop=='P2741':ident=ident.rsplit('-',1)[-1]
    for other in index.get((scheme,ident),set())-{e['entity_id']}:
     if other in byartist and e['entity_id'] in byartist and byartist[other]['status']!='archived' and byartist[e['entity_id']]['status']!='archived':leads['artist_authority_crosswalk'].append({'wikidata':e['external_id'],'museum_scheme':scheme,'museum_person_id':ident,'artists':[byartist[e['entity_id']],byartist[other]],'entity_capture':str(path.relative_to(m.x.ROOT))})
 report={'at':m.m.core.now(),'target':target,'phase':phase,'counts':counts,'lead_counts':{k:len(v) for k,v in leads.items()},'leads':dict(leads),'foreign_keys':foreign_keys,'policy':'Read-only leads. Same titles/names/images are not confirmed duplicates. Confirm physical/person identity and all dependent relationship preservation before a separate reviewed consolidation. Final audit must run after country imports.'}
 m.m.core.save_new(output_path,report);print(target,phase,'duplicate lead counts',report['lead_counts'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',choices=['local','production'],required=True);p.add_argument('--phase',default='preliminary');a=p.parse_args();audit(a.target,a.phase)
