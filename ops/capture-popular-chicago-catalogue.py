#!/usr/bin/env python3
"""Capture popular-artist Chicago metadata; cached, bounded, no image downloads.

Explicit id ordering avoids unstable score-tied result pages. Stop at the
observed 10-page search boundary; mark partial coverage honestly.
"""
import argparse,importlib.util,json,sys,unicodedata,re,collections
from pathlib import Path
from urllib.parse import urlencode
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args();RUN=args.run
s=importlib.util.spec_from_file_location('campaign',ROOT/'ops/overnight-image-campaign.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core
f=core.Fetcher(RUN/'chicago/evidence')
def norm(s):return re.sub(r'[^\w]+',' ',''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))).strip()
def request(endpoint,params):
 u='https://api.artic.edu/api/v1/'+endpoint+'?'+urlencode({'params':json.dumps(params,separators=(',',':'))})
 d=f.metadata(u);receipt=json.loads((f.cache/(core.sha(u.encode())+'.receipt.json')).read_text());return d,receipt
if not (RUN/'popular-artists.json').exists():
 with m.read_only('postgres://localhost/artline') as db:
  rows=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
   ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
   (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid
   FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artist_discovery_selection s WHERE s.artist_id=a.id AND s.is_popular) ORDER BY display_name""").fetchall()
 core.save_new(RUN/'popular-artists.json',rows)
artists=json.loads((RUN/'popular-artists.json').read_text());total=0;summary=[]
FIELDS='id,title,alt_titles,artist_id,artist_ids,artist_title,artist_display,date_display,date_start,date_end,main_reference_number,artwork_type_title,classification_title,classification_titles,medium_display,dimensions,credit_line,is_public_domain,copyright_notice,image_id,department_title'
for i,a in enumerate(artists):
 output=RUN/'chicago/artists'/(a['slug']+'.json')
 if output.exists():
  saved=json.loads(output.read_text());total+=len(saved['works']);summary.append({k:saved[k] for k in ('artist_slug','match_count','total','complete')});continue
 names={norm(n) for n in [a['display_name'],*a['aliases']]};matches={};receipts=[]
 for term in [a['display_name'],*a['aliases'][:4]]:
  d,r=request('artists/search',{'q':term,'limit':20,'fields':'id,title,alt_titles,birth_date,death_date,is_artist,ulan_id'});receipts.append(r)
  for v in d['data']:
   corroborates=any(isinstance(a[k],int) and a[k]==v.get(src) for k,src in [('birth_year','birth_date'),('death_year','death_date')])
   contradicts=any(isinstance(a[k],int) and isinstance(v.get(src),int) and abs(a[k]-v[src])>2 for k,src in [('birth_year','birth_date'),('death_year','death_date')])
   if v.get('is_artist') is True and names&{norm(n) for n in [v['title'],*(v.get('alt_titles') or [])]} and corroborates and not contradicts:matches[v['id']]=v
  if matches:break
 works=[];pages=[];expected=0;complete=False
 if len(matches)==1:
  source=next(iter(matches.values()));page=1
  while True:
   d,r=request('artworks/search',{'query':{'term':{'artist_ids':source['id']}},'sort':[{'id':'asc'}],'limit':100,'page':page,'fields':FIELDS});pages.append(r)
   expected=d['pagination']['total']
   if total+expected>10000:raise SystemExit('Bounded API cap reached; use official metadata dump for a larger capture')
   works.extend(d['data'])
   if page>=d['pagination']['total_pages'] or page>=10:break
   page+=1
  assert len({o['id'] for o in works})==len(works)
  complete=len(works)==expected
 total+=len(works)
 saved={'at':core.now(),'artist':a,'artist_slug':a['slug'],'match_count':len(matches),'source_artists':list(matches.values()),'artist_captures':receipts,'pages':pages,'total':expected,'complete':complete,'works':works,'images_downloaded':0}
 core.save_new(output,saved);summary.append({k:saved[k] for k in ('artist_slug','match_count','total','complete')})
 print(i+1,'/100',a['display_name'],'exact artists',len(matches),'works',len(works),'aggregate',total,flush=True)
core.save_new(RUN/'chicago-capture-summary.json',{'at':core.now(),'artists':summary,'records':total,'images_downloaded':0})
