#!/usr/bin/env python3
"""Reconcile source translations against bounded creator-specific artwork queries."""
import importlib.util,collections,re,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261009.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
code=sys.argv[1];folder=m.RUN/code;rows=m.load(folder/'source-records.json.gz');ap=m.load(folder/'artists-plan.json.gz');cross={};reviews=[];links={}
for a in ap['matches']:
 for w in a['works']:links[w['provider']+'/'+w['source_id']]=dict(verified_artist_id=a['artist_id'],creator_identity_basis='Unique verified museum creator name/alias; source attribution retained in evidence')
for a in ap['held']:
 for r in rows:
  if m.norm(r.get('creator_label'))==m.norm(a['name']):links[r['provider']+'/'+r['source_id']]=dict(creator_link_hold=True)
m.save(folder/'creator-links.json.gz',links)
with m.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 ids=sorted({a['artist_id'] for a in ap['matches']});artworks=[]
 for off in range(0,len(ids),100):
  artworks.extend(db.execute('SELECT a.id::text,a.title,a.alternate_title,a.current_institution_id::text,a.accession_number,a.creation_year_start,a.creation_year_end,a.work_type,aa.artist_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>%s',(ids[off:off+100],'archived')).fetchall())
 byartist=collections.defaultdict(list)
 for a in artworks:byartist[a['artist_id']].append(a)
 inst={x['slug']:str(x['id']) for x in db.execute('SELECT id,slug FROM institutions')}
 for r in rows:
  key=r['provider']+'/'+r['source_id'];aid=links.get(key,{}).get('verified_artist_id')
  if not aid:continue
  slug=m.museums()[r['museum']][0];iid=inst.get(slug,m.uid('museum/'+slug));titles={m.norm(r['title'])}
  for title in (r.get('alternate_title') or '').splitlines():titles.add(m.norm(re.sub(r'\s*\[[^]]*\]\s*$','',title)))
  # Official bilingual titles include an explicitly translated parenthesis.
  title=r['title'];match=re.fullmatch(r'(.+?) \(([^()]+)\)',title)
  if match:titles.update(m.norm(t) for t in match.groups())
  candidates=[a for a in byartist[aid] if m.norm(a['title']) in titles or (a['alternate_title'] and m.norm(a['alternate_title']) in titles)]
  if r.get('accession_number') and any(a['current_institution_id']==iid and m.norm(a['accession_number'])==m.norm(r['accession_number']) for a in byartist[aid]):continue
  if not candidates:continue
  possible=[]
  for a in candidates:
   if a['accession_number'] and r.get('accession_number') and m.norm(a['accession_number'])!=m.norm(r['accession_number']):continue
   if a['current_institution_id'] not in [None,iid]:continue
   if 'print' in r['source_type'].lower() or a['work_type']=='print':continue
   dates=(r.get('year_start'),r.get('year_end'))
   if dates[0] is not None and dates==(a['creation_year_start'],a['creation_year_end']):possible.append(a)
  generic=bool(re.fullmatch(r'self portrait|portrait|still life|untitled|landscape|nude|akt|bildnis|landschaft|stilleben|stillleben',m.norm(r['title'])))
  if len(possible)==1 and not generic:
   a=possible[0];cross[key]=dict(verified_existing_id=a['id'],crosswalk_basis='Unique existing creator plus exact official title/translation and matching creation bounds; inventory and holding do not conflict; prints and generic titles excluded.',crosswalk_before=a)
  elif possible:cross[key]=dict(editorial_hold='Creator-scoped title/date candidates require physical-version reconciliation',crosswalk_candidates=possible)
  reviews.append(dict(key=key,title=r['title'],creator=r['creator_label'],candidates=candidates,decision=cross.get(key,'Distinct inventory, holding, date or impression')))
m.save(folder/'source-identity-crosswalk.json.gz',cross);m.save(folder/'creator-scoped-identity-audit.json.gz',dict(scoped_artists=len(ids),scoped_artworks=len(artworks),reviews=reviews))
print('Reconciliation',code,len(artworks),'scoped works',len(cross),'decisions',sum('verified_existing_id' in v for v in cross.values()),'links',flush=True)
