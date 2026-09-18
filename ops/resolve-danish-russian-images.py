#!/usr/bin/env python3
"""Source-backed image-gap research for existing Danish/Russian catalogue works."""
import argparse,collections,hashlib,importlib.util,json,re,time,unicodedata,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,unquote,urlparse
import psycopg,requests
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-russian-image-gaps-20260913'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/danish-russian-image-gaps-20260913')
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
SESSION=requests.Session();SESSION.headers['User-Agent']='Artline/1.0 (https://github.com/vadimdulub/artline; selected public-domain artwork research)'

def save(path,data):core.save_new(path,data)
def norm(s):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',s.casefold()),re.UNICODE))
def fetch(url):
 key=core.sha(url.encode());p=RUN/'captures'/(key+'.json')
 if p.exists():return json.loads(p.read_bytes())
 for pausepath in (RUN/'pauses').glob('*.json'):
  pause=json.loads(pausepath.read_bytes())
  if urlparse(pause['url']).hostname!=urlparse(url).hostname:continue
  retry=pause.get('retry_after') or '60'
  delay=int(retry) if retry.isdigit() else 600
  if datetime.fromisoformat(pause['at'].replace('Z','+00:00')).timestamp()+delay>time.time():raise RuntimeError('Provider cooldown active; no request sent')
 time.sleep(1.3)
 r=SESSION.get(url,timeout=(15,90))
 if r.status_code in (429,502,503,504):
  save(RUN/'pauses'/(str(time.time_ns())+'.json'),{'url':url,'status':r.status_code,'retry_after':r.headers.get('Retry-After'),'at':core.now()})
  raise RuntimeError('Provider paused; inspect saved Retry-After before resuming')
 r.raise_for_status();assert len(r.content)<25_000_000
 d=r.json()
 if 'error' in d:
  save(RUN/'provider-errors'/(str(time.time_ns())+'.json'),{'url':url,'at':core.now(),'response':d,'retry_after':r.headers.get('Retry-After')})
  if d['error'].get('code')=='maxlag':save(RUN/'pauses'/(str(time.time_ns())+'.json'),{'url':url,'status':r.status_code,'retry_after':r.headers.get('Retry-After') or '60','at':core.now(),'error_code':'maxlag'})
  raise RuntimeError('Provider API error: '+d['error'].get('code','unknown'))
 save(p,r.content);save(p.with_suffix('.receipt.json'),{'url':r.url,'sha256':core.sha(r.content),'bytes':len(r.content),'retrieved_at':core.now()})
 return d

def audit():
 registry=json.loads((ROOT/'docs/research/danish-painters-20260913/painter-registry.json').read_bytes())
 rmanifest=json.loads((ROOT/'docs/research/russian-painters-20260913/combined-batch/manifest.json').read_bytes())
 rus=set()
 for c in rmanifest['chunks']:rus.update(json.loads((ROOT/'docs/research/russian-painters-20260913/combined-batch'/c['file']).read_bytes())['authors'])
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  with psycopg.connect(dsn,row_factory=dict_row) as db:
   db.execute('SET TRANSACTION READ ONLY')
   authors=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id) identifiers,
    (SELECT jsonb_agg(DISTINCT c.country_code) FROM artist_countries c WHERE c.artist_id=a.id AND c.country_code IN ('DK','RU')) countries
    FROM artists a WHERE a.status<>'archived' AND (EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id AND c.country_code IN ('DK','RU')) OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND ((e.scheme='smk-person' AND e.external_id=ANY(%s)) OR(e.scheme='wikidata' AND e.external_id=ANY(%s)))))""",(list(registry),sorted(rus))).fetchall()
   for a in authors:
    countries=set(a['countries'] or [])
    for e in a['identifiers'] or []:
     if e['scheme']=='smk-person' and e['id'] in registry:countries.add('DK')
     if e['scheme']=='wikidata' and e['id'] in rus:countries.add('RU')
    a['countries']=sorted(countries)
   rows=db.execute("""WITH selected AS MATERIALIZED(SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
    SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.primary_media_id::text,a.revision,i.slug institution,
    artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,artline_has_selection_evidence(a.id) selected,
    (SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id::text,'role',aa.attribution_role)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
    FROM selected s JOIN artworks a ON a.id=s.artwork_id LEFT JOIN institutions i ON i.id=a.current_institution_id ORDER BY a.id""",([a['id'] for a in authors],)).fetchall()
   byid={a['id']:a for a in authors}
   for w in rows:w['countries']=sorted({c for a in w['creators'] or [] for c in byid.get(a['id'],{}).get('countries',[])})
   summary={c:{'works':sum(c in w['countries'] for w in rows),'with_images':sum(c in w['countries'] and bool(w['primary_media_id']) for w in rows),'eligible_gaps':sum(c in w['countries'] and not w['primary_media_id'] and w['date_scope']=='eligible' and w['selected'] and w['status']!='archived' for w in rows),'painting_gaps':sum(c in w['countries'] and not w['primary_media_id'] and w['work_type']=='painting' and w['date_scope']=='eligible' and w['selected'] and w['status']!='archived' for w in rows)} for c in ('DK','RU')}
   save(RUN/(target+'-before.json'),{'at':core.now(),'artists':authors,'works':rows,'summary':summary});print(target,summary,flush=True)

def gaps():
 d=json.loads((RUN/'local-before.json').read_bytes())
 return d,[w for w in d['works'] if not w['primary_media_id'] and w['date_scope']=='eligible' and w['selected'] and w['status']!='archived' and len(w['creators'] or [])==1 and w['creators'][0]['role']=='primary']

def discover():
 d,works=gaps();wanted={c['id'] for w in works for c in w['creators']};qs={e['id']:a for a in d['artists'] if a['id'] in wanted for e in (a['identifiers'] or []) if e['scheme']=='wikidata'}
 # Explicit artist-ID scope; bounded discovery by museum-supported painters.
 # Fetching image metadata does not imply downloading their entire oeuvre.
 queryids=sorted(qs);allrows=[]
 for start in range(0,len(queryids),20):
  part=queryids[start:start+20]
  if start==400 and (RUN/'artist-discovery-partial-400.json').exists():
   save(RUN/'discovery-timeout-deferred.json',{'artists':part,'reason':'Original scoped query timed out at 90 seconds; defer this group without unbounded retries'});continue
  query='SELECT DISTINCT ?work ?creator ?image ?inventory ?collection ?date ?label WHERE { VALUES ?creator { '+ ' '.join('wd:'+q for q in part)+' } ?work wdt:P170 ?creator; wdt:P18 ?image. OPTIONAL { ?work wdt:P217 ?inventory. } OPTIONAL { ?work wdt:P195 ?collection. } OPTIONAL { ?work wdt:P571 ?date. } OPTIONAL { ?work rdfs:label ?label. FILTER(LANG(?label) IN ("en","ru","da")) } } ORDER BY ?work LIMIT 3000'
  try:data=fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
  except (RuntimeError,requests.RequestException) as error:
   save(RUN/('artist-discovery-partial-'+str(start)+'.json'),allrows);print('Discovery paused',str(error)[:200],flush=True);return
  rows=data['results']['bindings'];allrows.extend(rows)
  print('Artist discovery',min(start+20,len(queryids)),'/',len(queryids),'rows',len(rows),flush=True)
 save(RUN/'artist-discovery.json',allrows)

def backup():
 BACKUP.mkdir(parents=True,exist_ok=True)
 dump=BACKUP/'local-before.dump'
 if not dump.exists():subprocess.run(['pg_dump','-Fc','--no-owner','--no-acl','-d','postgres://127.0.0.1/artline','-f',str(dump)],check=True)
 subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
 cloud=BACKUP/'production-backup.json'
 if not cloud.exists():
  raw=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description=Danish and Russian selected image gap resolution 20260913','--format=json'])
  save(cloud,raw)
 b=json.loads(cloud.read_bytes())
 if not b:
  records=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=20','--format=json']))
  b=next(x for x in records if x.get('description')=='Danish and Russian selected image gap resolution 20260913')
  save(BACKUP/'production-backup-verification.json',b)
 b=b[0] if isinstance(b,list) else b;assert b['status']=='SUCCESSFUL',b.get('status')
 save(RUN/'backups.json',{'local':{'path':str(dump),'sha256':core.sha(dump.read_bytes()),'bytes':dump.stat().st_size},'production':{'id':b['id'],'status':b['status'],'instance':b['instance']}})
 print('Recovery backups verified',flush=True)

def match():
 spec=importlib.util.spec_from_file_location('catalogues',ROOT/'ops/research-wikimedia-catalogues.py');cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
 d,works=gaps();authors={a['id']:a for a in d['artists']}
 mapping=dict(cat.MAPPING)
 for w in works:
  if w['institution'] and re.fullmatch(r'wikimedia-museum-q\d+',w['institution']):mapping[w['institution']]=w['institution'].split('-')[-1].upper()
 qindex={};aindex=collections.defaultdict(list)
 for w in works:
  for e in w['identifiers'] or []:
   if e['scheme']=='wikidata':qindex[e['id']]=w
  for e in authors[w['creators'][0]['id']]['identifiers'] or []:
   if e['scheme']=='wikidata':aindex[e['id']].append(w)
 discovery=RUN/'artist-discovery.json'
 if not discovery.exists():discovery=max(RUN.glob('artist-discovery-partial-*.json'),key=lambda p:int(p.stem.rsplit('-',1)[-1]))
 grouped=collections.defaultdict(list)
 for row in json.loads(discovery.read_bytes()):grouped[row['work']['value'].rsplit('/',1)[-1]].append(row)
 preliminary={}
 for q,rows in grouped.items():
  if q in qindex:preliminary[q]=qindex[q];continue
  creators={x['creator']['value'].rsplit('/',1)[-1] for x in rows};collections_q={x['collection']['value'].rsplit('/',1)[-1] for x in rows if 'collection' in x};invs={norm(x['inventory']['value']) for x in rows if 'inventory' in x};titles={norm(x['label']['value']) for x in rows if 'label' in x};years={int(x['date']['value'][:4]) for x in rows if 'date' in x and re.match(r'^\d{4}-',x['date']['value'])}
  hits={}
  for aq in creators:
   for w in aindex.get(aq,[]):
    if mapping.get(w['institution']) not in collections_q:continue
    exact_inventory=bool(w['accession_number'] and norm(w['accession_number']) in invs)
    title_date=bool(norm(w['title']) in titles and len(norm(w['title']).split())>=3 and len(years)==1 and w['creation_year_start']==w['creation_year_end']==next(iter(years)))
    if exact_inventory or title_date:hits[w['id']]=w
  if len(hits)==1:preliminary[q]=next(iter(hits.values()))
 # Explicit limits before entity enrichment; prioritize existing painting gaps.
 selected=sorted(preliminary,key=lambda q:(preliminary[q]['work_type']!='painting',q))[:400]
 entities={}
 for q in selected:
  p=cat.RUN/'entities'/(q+'.json')
  if p.exists():entities[q]=json.loads(p.read_bytes())['entity']
 missing=[q for q in selected if q not in entities]
 for start in range(0,len(missing),20):
  part=missing[start:start+20]
  data=fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','format':'json','ids':'|'.join(part),'props':'labels|aliases|claims|sitelinks','languages':'en|ru|da|de|fr|mul','maxlag':5}));entities.update(data['entities'])
 matched=[];deferred=[]
 for q in selected:
  w=preliminary[q];e=entities[q];titles=cat.labels(e);images=cat.values(e,'P18');creators={x['id'] for x in cat.values(e,'P170')};aqs={x['id'] for x in authors[w['creators'][0]['id']]['identifiers'] or [] if x['scheme']=='wikidata'}
  try:
   assert len(creators)==1 and creators&aqs,'Creator identity conflict'
   assert len(images)==1,'Multiple or absent P18 files'
   direct=any(x['scheme']=='wikidata' and x['id']==q for x in w['identifiers'])
   accession=bool(w['accession_number'] and norm(w['accession_number']) in {norm(x) for x in cat.values(e,'P217')})
   collection=bool(mapping.get(w['institution']) in {x['id'] for x in cat.values(e,'P195')})
   date=cat.date(e);date_match=bool(date['eligible'] and date['first']==w['creation_year_start'] and date['last']==w['creation_year_end'])
   title_match=norm(w['title']) in {norm(t) for t in titles}
   assert direct or collection and (accession or title_match and date_match and len(norm(w['title']).split())>=3),'Work identity needs manual review'
   assert not date['eligible'] or not (date['last']<w['creation_year_start'] or date['first']>w['creation_year_end']),'Conflicting creation dates'
   basis='Exact existing Wikidata artwork identifier and creator' if direct else 'Exact museum accession and creator authority' if accession else 'Unique exact multilingual title, creator authority, creation date and museum collection'
   matched.append({'target':w,'commons_title':'File:'+images[0],'work_qid':q,'identity':{'basis':basis,'titles':titles,'entity':e,'wikipedia_articles':{k:v for k,v in e.get('sitelinks',{}).items() if k in ('enwiki','ruwiki','dawiki')},'discovery_capture':str(discovery.relative_to(ROOT))}})
  except (AssertionError,KeyError,ValueError) as error:deferred.append({'work_qid':q,'target':w['id'],'reason':str(error)})
 # More than one entity/file for the same catalogue work requires reconciliation.
 counts=collections.Counter(c['target']['id'] for c in matched)
 unique=[c for c in matched if counts[c['target']['id']]==1]
 unique.sort(key=lambda c:(not bool(c['identity']['wikipedia_articles']),c['target']['work_type']!='painting',c['work_qid']))
 suffix='' if discovery.name=='artist-discovery.json' else '-partial'
 save(RUN/('commons-new-matches'+suffix+'.json'),unique);save(RUN/('commons-match-deferred'+suffix+'.json'),deferred+[{'target':c['target']['id'],'reason':'Multiple work entities matched'} for c in matched if counts[c['target']['id']]>1]);print('New exact Commons candidates',len(unique),'of',len(selected),'Wikipedia articles',sum(bool(c['identity']['wikipedia_articles']) for c in unique),flush=True)

def wikipedia():
 candidates=json.loads((RUN/'commons-new-matches.json').read_bytes());groups=collections.defaultdict(list)
 for c in candidates:
  sites=c['identity']['wikipedia_articles']
  site=next((x for x in ('enwiki','ruwiki','dawiki') if x in sites),None)
  if site:groups[site].append((c,sites[site]['title']))
 results=[]
 for site,entries in groups.items():
  host=site.removesuffix('wiki')+'.wikipedia.org'
  for start in range(0,len(entries),10):
   part=entries[start:start+10]
   data=fetch('https://'+host+'/w/api.php?'+urlencode({'action':'query','format':'json','titles':'|'.join(t for c,t in part),'prop':'images|revisions','imlimit':500,'rvprop':'ids','maxlag':5}))
   pages={p['title']:p for p in data['query']['pages'].values()}
   normalized={n['from']:n['to'] for n in data['query'].get('normalized',[])}
   for c,title in part:
    page=pages.get(normalized.get(title,title),{});names={i['title'].replace('_',' ') for i in page.get('images',[])}
    results.append({'work_qid':c['work_qid'],'artwork_id':c['target']['id'],'article':'https://'+host+'/wiki/'+title.replace(' ','_'),'revision':page.get('revisions',[{}])[0].get('revid'),'commons_file':c['commons_title'],'file_listed_on_article':c['commons_title'].replace('_',' ') in names,'image_list_truncated':bool(data.get('continue'))})
 save(RUN/'wikipedia-image-confirmation.json',results);print('Wikipedia articles',len(results),'file usage confirmed',sum(x['file_listed_on_article'] for x in results),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','discover','backup','match','wikipedia']);a=p.parse_args();globals()[a.phase]()
