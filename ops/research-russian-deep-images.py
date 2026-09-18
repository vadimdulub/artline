#!/usr/bin/env python3
"""Russian image research: exact identities, multiple sources, bounded downloads."""
import argparse,collections,importlib.util,json,re,subprocess,time,hashlib
from pathlib import Path
from urllib.parse import urlencode,urlparse
from datetime import datetime
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('base',ROOT/'ops/resolve-danish-russian-images.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
core=base.core;RUN=ROOT/'docs/research/russian-images-deep-20260913'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/russian-images-deep-20260913')
PREVIOUS=ROOT/'docs/research/danish-russian-image-gaps-20260913'
base.RUN=RUN;save=base.save;fetch=base.fetch;norm=base.norm

def audit():
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   artists=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id) identifiers
    FROM artists a WHERE a.status<>'archived' AND (EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id AND c.country_code='RU' AND c.relationship_type='cultural_affiliation') OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id='Q156426')) ORDER BY a.id""").fetchall()
   works=db.execute("""WITH selected AS MATERIALIZED(SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) UNION SELECT id FROM artworks WHERE object_form='icon' AND cultural_context ILIKE '%%Russian%%')
    SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.object_form,a.cultural_context,a.unlinked_creator_label,a.status,a.primary_media_id::text,a.revision,i.slug institution,
     artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,artline_has_selection_evidence(a.id) selected,
     (SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id::text,'role',aa.attribution_role)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
     (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
    FROM selected s JOIN artworks a ON a.id=s.artwork_id LEFT JOIN institutions i ON i.id=a.current_institution_id ORDER BY a.id""",([a['id'] for a in artists],)).fetchall()
   for w in works:w['countries']=['RU']
   summary={'artists':len(artists),'works':len(works),'with_images':sum(bool(w['primary_media_id']) for w in works),'eligible_gaps':sum(not w['primary_media_id'] and w['selected'] and w['date_scope']=='eligible' and w['status']!='archived' for w in works)}
   save(RUN/(target+'-before.json'),{'at':core.now(),'artists':artists,'works':works,'summary':summary});print(target,summary,flush=True)

def gaps():
 d=json.loads((RUN/'local-before.json').read_bytes());return d,[w for w in d['works'] if not w['primary_media_id'] and w['date_scope']=='eligible' and w['selected'] and w['status']!='archived']

def backup():
 BACKUP.mkdir(parents=True,exist_ok=True);dump=BACKUP/'local-before.dump'
 if not dump.exists():subprocess.run(['pg_dump','-Fc','--no-owner','--no-acl','-d','postgres://127.0.0.1/artline','-f',str(dump)],check=True)
 subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
 description='Russian artwork deep image research 20260913'
 request=BACKUP/'production-backup-request.json'
 if not request.exists():save(request,subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+description,'--format=json']))
 records=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=20','--format=json']))
 b=next(x for x in records if x.get('description')==description);assert b['status']=='SUCCESSFUL';save(BACKUP/'production-backup-verification.json',b)
 save(RUN/'backups.json',{'local':{'path':str(dump),'bytes':dump.stat().st_size,'sha256':core.sha(dump.read_bytes())},'production':b});print('Recovery backups verified',flush=True)

def accession_hint(w):
 if w.get('accession_number'):return w['accession_number']
 e=next((e for e in w['identifiers'] or [] if e['scheme']=='european-russian-session-museum-object'),None)
 if not e:return None
 part=e['id'].split('/')[-2].strip('_').lower()
 m=re.fullmatch(r'(zhb|zh|r|g|b|i|k)[_-](\d+)',part)
 if m:return {'zhb':'ЖБ','zh':'Ж','r':'Р','g':'Г','b':'Б','i':'И','k':'К'}[m[1]]+'-'+m[2]
 return None

def commons_search(deeper=False):
 d,g=gaps();authors={a['id']:a for a in d['artists']};queued={p.stem for p in (RUN/'images/selected/russian-deep-commons').glob('*.json')}
 output=RUN/'accession-deeper' if deeper else RUN
 if deeper:queued.update(w['id'] for w in json.loads((RUN/'accession-search-targets.json').read_bytes()))
 groups=collections.defaultdict(list)
 for w in g:
  if w['id'] in queued or w['institution']!='state-russian-museum' or len(w['creators'] or [])!=1 or w['creators'][0]['role']!='primary' or not accession_hint(w):continue
  groups[w['creators'][0]['id']].append(w)
 order=sorted(groups,key=lambda a:(-sum(w['work_type']=='painting' for w in groups[a]),authors[a]['display_name']))
 for works in groups.values():works.sort(key=lambda w:(w['work_type']!='painting',w['creation_year_start'],w['id']))
 targets=[];depth=0
 while len(targets)<1200:
  added=0
  for aid in order:
   if depth<len(groups[aid]):targets.append(groups[aid][depth]);added+=1
   if len(targets)==1200:break
  if not added:break
  depth+=1
 save(output/'accession-search-targets.json',targets);pages={}
 for start in range(0,len(targets),20):
  part=targets[start:start+20];query=' OR '.join('"'+accession_hint(w)+'"' for w in part)
  data=fetch('https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':50,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5}))
  pages.update(data.get('query',{}).get('pages',{}));save(output/'accession-search-batches'/(str(start).zfill(4)+'.json'),{'targets':[w['id'] for w in part],'query':query,'pages':data.get('query',{}).get('pages',{}),'truncated':bool(data.get('continue'))})
  print('Commons accession search',min(start+20,len(targets)),'/',len(targets),'unique files',len(pages),flush=True)
 save(output/'accession-search-files.json',pages)

def inventory_key(s):return re.sub(r'[^а-яa-z0-9]','',s.casefold().replace('ё','е'))
def museum_detail(url):
 key=core.sha(url.encode());old=ROOT/'docs/research/russian-painters-20260913/captures'/(key+'.html')
 p=RUN/'museum-captures'/(key+'.html')
 if p.exists():return BeautifulSoup(p.read_bytes(),'html.parser'),str(p.relative_to(ROOT))
 if old.exists():return BeautifulSoup(old.read_bytes(),'html.parser'),str(old.relative_to(ROOT))
 for pausepath in (RUN/'pauses').glob('*.json'):
  pause=json.loads(pausepath.read_bytes())
  if urlparse(pause['url']).hostname!=urlparse(url).hostname:continue
  retry=pause.get('retry_after') or '600';delay=int(retry) if retry.isdigit() else 600
  if datetime.fromisoformat(pause['at'].replace('Z','+00:00')).timestamp()+delay>time.time():raise RuntimeError('Museum cooldown active; no request sent')
 time.sleep(1.4);response=base.SESSION.get(url,timeout=(15,45))
 if response.status_code in (429,502,503,504):
  save(RUN/'pauses'/(str(time.time_ns())+'.json'),{'url':url,'at':core.now(),'status':response.status_code,'retry_after':response.headers.get('Retry-After')});raise RuntimeError('Museum source paused')
 response.raise_for_status();assert len(response.content)<6_000_000
 save(p,response.content);save(p.with_suffix('.receipt.json'),{'url':url,'sha256':core.sha(response.content),'retrieved_at':core.now()})
 return BeautifulSoup(response.content,'html.parser'),str(p.relative_to(ROOT))

def commons_match(deeper=False):
 output=RUN/'accession-deeper' if deeper else RUN
 targets=json.loads((output/'accession-search-targets.json').read_bytes());pages=json.loads((output/'accession-search-files.json').read_bytes())
 authors=json.loads((ROOT/'docs/research/russian-painters-20260913/selected-authors.json').read_bytes());audit=json.loads((RUN/'local-before.json').read_bytes());artist_byid={a['id']:a for a in audit['artists']};good=[];deferred=[]
 indexed=[]
 for page in pages.values():
  info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});text=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','');body=text+' '+json.dumps(meta,ensure_ascii=False)
  credit=meta.get('Artist',{}).get('value','');plain=BeautifulSoup(credit,'html.parser').get_text(' ',strip=True)
  indexed.append((page,body,credit,plain))
 for w in targets:
  hint=accession_hint(w);pattern=r'(?<![А-Яа-яA-Za-z0-9])'+re.escape(hint).replace(r'\-',r'[-– _]?')+r'(?!\d)';a=artist_byid[w['creators'][0]['id']];q=next((e['id'] for e in a['identifiers'] if e['scheme']=='wikidata'),None)
  source=authors.get(q)
  if not source:continue
  candidates=[]
  for page,body,credit,plain in indexed:
   if not re.search(pattern,body,re.I):continue
   if not re.search(r'Russian Museum|Русск(?:ий|ого|ом|ому) музе|rusmuseum',body,re.I):continue
   names={norm(source['name']),norm(source.get('native_name','')),norm(a['display_name'])}
   if q not in credit and norm(plain) not in names:continue
   candidates.append(page)
  if not candidates:continue
  e=next(e for e in w['identifiers'] if e['scheme']=='european-russian-session-museum-object')
  try:
   soup,capture=museum_detail(e['url']);txt=lambda sel:soup.select_one(sel).get_text(' ',strip=True) if soup.select_one(sel) else ''
   inv=txt('[title="Инвентарный номер"]');title=txt('.work__title');links=[a.get('href') for a in soup.select('.work__author a')]
   assert inventory_key(inv)==inventory_key(hint),'Museum inventory does not confirm search hint'
   assert norm(title)==norm(w['title']),'Detailed museum title conflict'
   assert len(links)==1 and source['url'].removeprefix('https://rusmuseumvrm.ru') in links,'Museum creator conflict'
   good.append({'target':w,'artist':a,'source_artist':source,'museum_inventory':inv,'museum_title':title,'museum_date':txt('.period'),'museum_capture':capture,'museum_author_links':links,'files':candidates,'identity_basis':'Exact accession confirmed on detailed official Russian Museum object page, matching creator authority and title; Commons file independently states accession, museum and creator.'})
  except (AssertionError,ValueError) as error:deferred.append({'artwork_id':w['id'],'reason':str(error)})
  if (len(good)+len(deferred))%10==0:print('New Commons object identities',len(good),'deferred',len(deferred),flush=True)
 save(output/'new-commons-identity-matches.json',good);save(output/'new-commons-identity-deferred.json',deferred);print('New exact image identities',len(good),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','backup','commons-search','commons-match']);p.add_argument('--deeper',action='store_true');a=p.parse_args()
 if a.phase in ('commons-search','commons-match'):globals()[a.phase.replace('-','_')](a.deeper)
 else:globals()[a.phase.replace('-','_')]()
