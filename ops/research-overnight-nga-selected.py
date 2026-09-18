#!/usr/bin/env python3
"""Select source metadata with a single explicit museum primary creator role."""
import argparse,csv,json,pathlib,collections,re,importlib.util
import psycopg
from psycopg.rows import dict_row
p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];run=a.run.resolve();r=run.parent;run.mkdir(exist_ok=True);s=importlib.util.spec_from_file_location('core',root/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
with (r/'nga/metadata/objects.csv').open() as f:objects={o['objectid']:o for o in csv.DictReader(f)}
with (r/'nga/metadata/constituents.csv').open() as f:people={o['constituentid']:o for o in csv.DictReader(f)}
by_artists=collections.defaultdict(list);roles=collections.Counter()
with (r/'nga/metadata/objects_constituents.csv').open() as f:
 for o in csv.DictReader(f):
  if o['roletype']=='artist':by_artists[o['objectid']].append(o);roles[(o['role'],o['prefix'],o['suffix'])]+=1
files=collections.defaultdict(list)
for f in json.loads((r/'nga/commons-file-index.json').read_text())['files']:
 m=re.search(r'\bNGA (\d+)\.(?:jpg|jpeg|png|tif|tiff)$',f['title'],re.I)
 if m:files[m[1]].append(f)
with (r/'nga/metadata/nga-published-images.csv').open() as f:open_ids={o['depictstmsobjectid'] for o in csv.DictReader(f) if o['openaccess']=='1' and o['viewtype']=='primary'}
with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
 artists=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,e.external_id,
 EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular
 FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='nga-constituent' WHERE a.status<>'archived'""").fetchall();artist_map={a['external_id']:a for a in artists}
 oldids={a['external_id'] for a in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme IN ('nga-object','european-nga-object')").fetchall()}
 held=collections.Counter();chosen=[]
 for oid,fs in files.items():
  if oid in oldids:held['Existing NGA ID']+=1;continue
  if len(fs)!=1:held['Multiple source files']+=1;continue
  o=objects.get(oid)
  if not o or o['accessioned']!='1' or o['isvirtual']!='0' or o['classification'] not in ('Painting','Drawing','Print','Watercolor') or oid not in open_ids:held['Object type/holding/open-primary-image not supported']+=1;continue
  cs=by_artists.get(oid,[])
  if len(cs)!=1 or cs[0]['role'] not in ('artist','painter','engraver','etcher') or cs[0]['prefix'] or cs[0]['suffix']:held['Unqualified single primary artist not supported']+=1;continue
  ar=artist_map.get(cs[0]['constituentid']);person=people.get(cs[0]['constituentid'])
  if not ar or not person:held['Existing artist authority not available']+=1;continue
  if any(re.fullmatch(r'\d{4}',person[k]) and ar[f] is not None and int(person[k])!=ar[f] for k,f in [('beginyear','birth_year'),('endyear','death_year')]):held['Creator life dates conflict']+=1;continue
  if person['constituenttype']!='individual' or person['forwarddisplayname']!=o['attribution']:held['Museum attribution conflict']+=1;continue
  m=re.fullmatch(r'\s*(?P<approx>(?:c\.|ca\.|circa|about|probably(?: c\.)?)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}|\d{2}))?\s*',o['displaydate'],re.I)
  if not m:held['Date wording needs review']+=1;continue
  lo=int(m['lo']);end=m['hi'] or m['lo'];hi=int(str(lo)[:2]+end) if len(end)==2 else int(end)
  if not (re.fullmatch(r'\d{4}',o['beginyear']) and re.fullmatch(r'\d{4}',o['endyear'])):held['Date bounds absent']+=1;continue
  blo,bhi=int(o['beginyear']),int(o['endyear'])
  if not 1000<=blo<=lo<=hi<=bhi<=1970:held['Date contradicts/crosses cutoff']+=1;continue
  if blo!=bhi and str(blo)==person['beginyear'] and str(bhi)==person['endyear']:held['Date mirrors creator lifespan']+=1;continue
  chosen.append({'object':o,'artist':ar,'creator':person,'creator_relation':cs[0],'commons_file':fs[0],
                 'creation_year_start':lo,'creation_year_end':hi,'date_precision':('circa' if lo==hi else 'circa_range') if m['approx'] else ('exact' if lo==hi else 'range')})
 chosen.sort(key=lambda c:(not c['artist']['popular'],c['object']['classification']!='Painting',c['artist']['display_name'],c['object']['objectid']))
 core.save_new(run/'source-candidates.json',chosen);core.save_new(run/'source-selection-report.json',{'at':core.now(),'selected':len(chosen),'popular':sum(c['artist']['popular'] for c in chosen),'types':dict(collections.Counter(c['object']['classification'] for c in chosen)),'held':held,'relationship_types':[[list(k),v] for k,v in roles.most_common(20)]})
 print('NGA new source leads',len(chosen),'popular',sum(c['artist']['popular'] for c in chosen),'types',dict(collections.Counter(c['object']['classification'] for c in chosen)),flush=True);print('Held',dict(held),flush=True)
