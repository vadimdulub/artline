#!/usr/bin/env python3
"""Discovery only: candidate creator/date comparisons, never fuzzy automatic links."""
import argparse,collections,difflib,importlib.util,re
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('deep',Path(__file__).with_name('museums-exactly-one-deep-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
d=m.d;RUN=m.RUN

def discover(wave):
 records=d.load(RUN/'waves'/wave/'source-verified.json.gz')['records']
 with d.connect()as db:
  authorities=db.execute("SELECT id::text,display_name,normalized_name,birth_year,death_year FROM artists WHERE status<>'archived'").fetchall()
  aliases=db.execute('SELECT artist_id::text,alias,normalized_alias FROM artist_aliases').fetchall()
 byid={x['id']:x for x in authorities};labels=collections.defaultdict(set)
 for x in authorities:labels[x['id']].add(x['normalized_name'])
 for x in aliases:labels[x['artist_id']].add(x['normalized_alias'])
 def creator_names(r):
  f=r['facts'];names={f.get('creator_label')or ''}
  rs=r['raw_source_record']
  if r['provider']=='artefact-native':
   for creator in rs['parsed']['index_candidate']['authors']:names.update(creator['title'].values())
  elif r['provider']=='wikidata-catalogue':
   for creator in rs['creators'].values():
    e=creator['entity'];names.update(v['value'] for v in e.get('labels',{}).values());names.update(v['value']for vs in e.get('aliases',{}).values()for v in vs)
  for name in list(names):
   if name.count(',')==1:
    parts=name.split(',');names.add(parts[1].strip()+' '+parts[0].strip())
  return {d.norm(n) for n in names if n}
 scope=[];matches={};lifes=[]
 for r in records:
  names=creator_names(r);hits=[]
  for aid,lab in labels.items():
   exact=names&lab
   # Transliteration/initial patterns are only comparison leads. They never
   # establish an automatic artist link or an accepted artwork identity.
   near=0
   if not exact:
    for n in names:
     for l in lab:
      nt=n.split();lt=l.split()
      if len(nt)>1 and len(lt)>1 and nt[-1]==lt[-1]:near=max(near,difflib.SequenceMatcher(None,n,l).ratio())
      if len(nt)>1 and any(len(t)==1 for t in nt) and nt[0]in lt:
       if all(any(w.startswith(t)for w in lt)for t in nt[1:]):near=max(near,.82)
   if exact or near>=.78:
    hits.append(dict(artist=byid[aid],basis='exact source name/alias'if exact else'transliteration/initial discovery only',source_names=sorted(names),similarity=round(near,3)))
    scope.append(dict(key=r['source_record_id'],artist=aid,first=r['facts']['first'],last=r['facts']['last']))
    ar=byid[aid]
    if exact and ((ar['birth_year']and r['facts']['last']<ar['birth_year'])or(ar['death_year']and r['facts']['first']>ar['death_year']+3)):
     lifes.append(dict(key=r['source_record_id'],facts=r['facts'],artist=ar,reason='source_date_outside_creator_life_review_required'))
  matches[r['source_record_id']]=hits
 with d.connect()as db:
  sql="""WITH wanted AS (SELECT * FROM jsonb_to_recordset(%s) w(key text,artist uuid,first integer,last integer))
  SELECT DISTINCT w.key,to_jsonb(a) artwork,aa.artist_id::text artist_id,ar.display_name
  FROM wanted w JOIN artwork_artists aa ON aa.artist_id=w.artist JOIN artists ar ON ar.id=aa.artist_id JOIN artworks a ON a.id=aa.artwork_id
  WHERE a.status<>'archived' AND (a.creation_year_start IS NULL OR (a.creation_year_start<=w.last+3 AND coalesce(a.creation_year_end,a.creation_year_start)>=w.first-3))
  ORDER BY w.key,aa.artist_id::text"""
  queryplan=db.execute('EXPLAIN (FORMAT JSON) '+sql,(Jsonb(scope),)).fetchone();rows=db.execute(sql,(Jsonb(scope),)).fetchall()
  ids=list({x['artwork']['id']for x in rows});evidence=[]
  for part in d.chunks(ids):
   evidence += db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(part,)).fetchall()
 source={x['source_record_id']:x for x in records};leads=[]
 for x in rows:
  r=source[x['key']];titles={r['facts']['title']};rs=r['raw_source_record']
  if r['provider']=='artefact-native':titles.update(rs['parsed']['index_candidate']['title'].values())
  elif r['provider']=='wikidata-catalogue':titles.update(v['value']for v in rs['entity'].get('labels',{}).values())
  def key(v):return re.sub(r'\b(a|an|the|painting)\b','',d.norm(v)).replace(' ','')
  a=x['artwork'];ratio=max(difflib.SequenceMatcher(None,key(t),key(v)).ratio()for t in titles for v in [a['title'],a['alternate_title']or''])
  if ratio>=.57:leads.append(dict(source_key=x['key'],source_title=r['facts']['title'],source_creator=r['facts']['creator_label'],source_date=r['facts']['date_display'],source_museum=r['museum']['name'],existing_id=a['id'],existing_title=a['title'],existing_date=a['date_display'],existing_museum=a['current_institution_id'],similarity=round(ratio,3)))
 out=RUN/'identity'/wave
 d.save(out/'discovery.json.gz',dict(at=d.now(),artists=authorities,aliases=aliases,creator_matches=matches,comparisons=rows,identifiers=evidence,life_conflicts=lifes,policy='All similarity scores are discovery only. No inferred artist relationship or artwork link is written.'))
 d.save(out/'query-plan.json',queryplan);d.save(out/'title-leads.json',leads)
 print('Reviewed',len(records),'candidate source works;',len(rows),'creator/date comparisons;',len(leads),'title leads;',len(lifes),'life conflicts')
 for x in leads:print(x['source_key'],x['source_title'],'=>',x['existing_id'],x['existing_title'],x['existing_date'],x['existing_museum'],x['similarity'],flush=True)
 for x in lifes:print('LIFE HOLD',x['key'],x['facts']['title'],x['facts']['date_display'],x['artist']['display_name'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('wave');x=p.parse_args();discover(x.wave)
