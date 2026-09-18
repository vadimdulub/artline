#!/usr/bin/env python3
"""Exact image evidence for independently selected Cleveland CC0 objects."""
import argparse,concurrent.futures,fcntl,importlib.util,json,re,time,unicodedata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse,unquote
s=importlib.util.spec_from_file_location('helpers',Path(__file__).with_name('overnight-mia-images.py'));helpers=importlib.util.module_from_spec(s);s.loader.exec_module(helpers);core=helpers.core;ro=helpers.ro
core.VERSION='overnight-cleveland-selected-cc0-v1';core.PROVIDERS['night-cleveland']='The Cleveland Museum of Art'
CC0='https://creativecommons.org/publicdomain/zero/1.0/';SLUG='cleveland-museum-of-art';SCHEME='european-cleveland-cleveland-museum-of-art-object';QUERY=helpers.QUERY.replace("e.scheme='mia-object'","e.scheme='"+SCHEME+"'")
def norm(value):
 text=''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold()) if not unicodedata.combining(c));return ' '.join(re.findall(r'[^\W_]+',text))
def primary_maker(o):
 rows=o.get('creators') or [];primary=[x for x in rows if x.get('role')=='artist' and x.get('qualifier')!='after']
 if len(primary)!=1:raise ValueError('Unique primary artist is not established')
 m=primary[0]
 if m.get('qualifier') or m.get('extent'):raise ValueError('Qualified primary attribution needs review')
 if any(x.get('role') not in ('artist','publisher','published by','printer','printed by','printer and publisher','author','after') for x in rows):raise ValueError('Other visual creator roles need review')
 if not isinstance(m.get('id'),int):raise ValueError('Native museum maker ID is absent')
 return m
def maker_name(m):
 name=re.split(r'\s*\(',m.get('description') or '',maxsplit=1)[0].strip()
 if not name or re.search(r'unknown|anonymous|unidentified|workshop|school of|attributed|after ',name,re.I):raise ValueError('Named primary creator requires separate attribution review')
 return name
def date_parts(o):
 lo=o.get('creation_date_earliest');hi=o.get('creation_date_latest');text=o.get('creation_date') or ''
 if not isinstance(lo,int) or not isinstance(hi,int) or isinstance(lo,bool) or isinstance(hi,bool) or not 1000<=lo<=hi<=1970:raise ValueError('Source creation interval outside scope or incomplete')
 if not text.strip() or re.search(r'\b(undated|unknown|before|after|not dated|possibly|or later|or earlier)\b|\?|\d{4}\s*[-–—]\s*$',text,re.I):raise ValueError('Original artwork date requires review')
 m=primary_maker(o);birth=m.get('birth_year') or '';death=m.get('death_year') or ''
 if re.fullmatch(r'\d{4}',birth) and re.fullmatch(r'\d{4}',death) and hi==int(death) and lo in (int(birth),int(birth)+15):raise ValueError('Source interval resembles artist lifespan or default activity range')
 approx=bool(re.search(r'\b(?:c\.|ca\.|circa|about|probably|early|mid|late)\b|\b(?:c\.|ca\.)\s*\d',text,re.I));precision=('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range')
 return lo,hi,precision,text
def source_match(c,o):
 if str(o.get('id'))!=c['external_id'] or o.get('accession_number')!=c['accession_number']:raise ValueError('Native object or accession identity differs')
 if norm(c['title'])!=norm(o.get('title')) or {'Painting':'painting','Drawing':'drawing','Print':'print'}.get(o.get('type'))!=c['work_type']:raise ValueError('Source title or artwork type differs')
 if o.get('legal_status')!='accessioned' or o.get('on_loan') is not False:raise ValueError('Museum ownership is not established')
 if o.get('record_type')!='object' or o.get('cover_accession_number'):raise ValueError('Multipart physical-object relationship needs review')
 parsed=urlparse(o.get('url') or '')
 if parsed.scheme!='https' or parsed.hostname not in ('clevelandart.org','www.clevelandart.org') or unquote(parsed.path).rstrip('/')!='/art/'+c['accession_number']:raise ValueError('Stable native museum page differs')
 m=primary_maker(o)
 if str(m['id'])!=c['artist_authority'] or c['roles']!=['primary'] or norm(maker_name(m)) not in {norm(n) for n in [c['artist']]+c['aliases']}:raise ValueError('Exact creator facts differ')
 if date_parts(o)!=(c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['date_display']):raise ValueError('Source artwork creation facts differ')
 if o.get('share_license_status')!='CC0' or o.get('copyright') or o.get('rights_and_reproductions'):raise ValueError('Exact image CC0 rights are missing or conflicting')
 im=(o.get('images') or {}).get('web') or {};url=im.get('url') or '';parsed=urlparse(url)
 if parsed.scheme!='https' or parsed.hostname!='openaccess-cdn.clevelandart.org' or unquote(parsed.path)!='/'+c['accession_number']+'/'+c['accession_number']+'_web.jpg':raise ValueError('Exact museum image resource mapping differs')
 if im.get('filename')!=c['accession_number']+'_web.jpg':raise ValueError('Museum primary image filename differs')
 return url,{'source_creator':maker_name(m),'source_maker_id':str(m['id']),'source_date_text':o['creation_date'],'source_year_start':c['creation_year_start'],'source_year_end':c['creation_year_end'],'holding':'accessioned; not a long-term loan','metadata_license':CC0}
original_attach=helpers.original_attach
def attach(db,im,target):
 url,_=source_match(im,im['raw']['object']);assert url==im['source_image_url']
 with db.transaction():
  rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
  if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('Target museum object identity differs')
  row=rows[0]
  if any(row[k]!=im[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type','artist_slugs','roles')):raise ValueError('Target source facts changed')
  if row['current_institution_id']!=im['institution_ids'][target]:raise ValueError('Target holding institution differs')
  if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
  outcome=original_attach(db,im,target)
  if outcome=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  return outcome
core.attach=attach
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=10000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();assert (a.run.parent/'backups.json').exists();lock=(a.run/'image-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=json.loads((a.run/'candidates.json').read_text())['candidates'];done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','failed')};todo=[c for c in rows if c['artwork_id'] not in done][:a.limit]
 for start in range(0,len(todo),50):
  if time.time()>=a.deadline:break
  group=todo[start:start+50]
  for c in group:source_match(c,c['raw']['object'])
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   for f in [pool.submit(core.worker,'night-cleveland',group[n::3],SimpleNamespace(run=a.run,prepare_only=True),None) for n in range(3)]:f.result()
  print(core.now(),'Cleveland selected images',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
