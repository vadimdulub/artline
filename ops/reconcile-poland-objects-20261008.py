#!/usr/bin/env python3
"""Conservative creator-scoped duplicate checks against works outside museum scopes."""
import importlib.util,collections,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.load(m.RUN/'poland/source-records.json.gz');ap=m.load(m.RUN/'artists-plan-reviewed.json.gz');creators={m.norm(x['name']):x['artist_id'] for x in ap['matches']};cross={};reviews=[]
with m.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 ids=sorted(set(creators.values()));artworks=[]
 for off in range(0,len(ids),100):
  artworks.extend(db.execute('SELECT a.id::text,a.title,a.current_institution_id::text,a.accession_number,a.creation_year_start,a.creation_year_end,a.work_type,aa.artist_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>%s',(ids[off:off+100],'archived')).fetchall())
 byartist=collections.defaultdict(list)
 for a in artworks:byartist[a['artist_id']].append(a)
 inst={x['slug']:str(x['id']) for x in db.execute('SELECT id,slug FROM institutions')}
 for r in rows:
  aid=creators.get(m.norm(r.get('creator_label')))
  if not aid:continue
  slug=m.museums()[r['museum']][0];iid=inst.get(slug,m.uid('museum/'+slug));titles={m.norm(r['title'])}
  for title in r['raw'].get('otherTitles',[]):
   if title.get('name'):titles.add(m.norm(title['name']))
  candidates=[a for a in byartist[aid] if m.norm(a['title']) in titles]
  # Existing same-museum inventories are handled by the main plan.
  if r.get('accession_number') and any(a['current_institution_id']==iid and m.norm(a['accession_number'])==m.norm(r['accession_number']) for a in byartist[aid]):continue
  if not candidates:continue
  key=r['provider']+'/'+r['source_id'];possible=[]
  for a in candidates:
   if a['accession_number'] and r.get('accession_number') and m.norm(a['accession_number'])!=m.norm(r['accession_number']):continue
   if a['current_institution_id'] not in [None,iid]:continue
   if r['source_type']=='print' or a['work_type']=='print':continue # Different impressions are distinct.
   dates=(r.get('year_start'),r.get('year_end'))
   if dates[0] is not None and dates==(a['creation_year_start'],a['creation_year_end']):possible.append(a)
  generic=bool(re.fullmatch(r'autoportret|self portrait|portrait|portret|martwa natura|still life|bez tytulu|untitled|pejzaz|landscape|akt|nude',m.norm(r['title'])))
  if len(possible)==1 and not generic:
   a=possible[0];cross[key]=dict(verified_existing_id=a['id'],crosswalk_basis='Unique existing creator plus exact source title/alternate title and matching explicit creation bounds; existing inventory and holding do not conflict; prints and generic titles excluded.',crosswalk_before=a)
  elif possible:
   cross[key]=dict(editorial_hold='Creator-scoped existing title/date candidates require physical-version reconciliation; not duplicated automatically',crosswalk_candidates=possible)
  reviews.append(dict(key=key,title=r['title'],creator=r['creator_label'],candidates=candidates,decision=cross.get(key,'Distinct inventory, holding, date or print impression; source-native record retained')))
m.save(m.RUN/'poland/source-identity-crosswalk.json.gz',cross);m.save(m.RUN/'poland/creator-scoped-identity-audit.json.gz',dict(scoped_artists=len(ids),scoped_artworks=len(artworks),reviews=reviews))
print('Creator-scoped reconciliation',len(artworks),'works',len(cross),'decisions',sum('verified_existing_id' in v for v in cross.values()),'links',flush=True)
