import importlib.util, hashlib, time, requests, collections, sys
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
missing={r['id'] for r in m.base.load(m.RUN/'local-final-unresolved-v3.json.gz')}
artists={q:r for r in m.base.load(m.RUN/'local-artists.json.gz') if r['id'] in missing for q in r['wikidata']}
links=collections.defaultdict(set)
for p in (m.RUN/'notable').glob('*.json'):
 for r in m.base.load(p)['results']['bindings']:
  a=r['artist']['value'].split('/')[-1];w=r['work']['value'].split('/')[-1]
  if a in artists:links[a].add(w)
entities={k:v for folder in ['entities','artist-entities','notable-gap-entities'] for p in (m.RUN/folder).glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()}
needed=sorted((set(links)|{w for ws in links.values() for w in ws})-set(entities))
for i in ([] if '--cached-only' in sys.argv else range(0,len(needed),25)):
 batch=needed[i:i+25];time.sleep(2)
 response=requests.get('https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(batch),'props':'claims|labels','languages':'en|fr|de|es|it|el|ru','format':'json'},headers={'User-Agent':'Artline/1.0 (selected painter notable-work research; artlines.org)'},timeout=45)
 if response.status_code==429:
  m.save('notable-gap-fetch-throttled.json',dict(at=m.base.now(),status=429,remaining=needed[i:],retry_after=response.headers.get('Retry-After')));break
 response.raise_for_status();data=response.json();assert 'error' not in data
 m.base.save(m.RUN/'notable-gap-entities'/(hashlib.sha256('|'.join(batch).encode()).hexdigest()+'.json'),data);entities.update(data['entities']);print('captured',i+len(batch),'/',len(needed),flush=True)
def values(e,p):return [c['mainsnak']['datavalue']['value'] for c in e.get('claims',{}).get(p,[]) if c.get('rank')!='deprecated' and 'datavalue' in c.get('mainsnak',{})]
ready=[];held=[]
for a,works in sorted(links.items()):
 candidates=[]
 for w in sorted(works):
  if w not in entities or a not in entities:
   held.append(dict(artist=a,work=w,reason='source_evidence_unavailable_after_rate_limit'));continue
  e=entities[w];claims=e.get('claims',{});creators=values(e,'P170');dates=values(e,'P571')
  notable=[c for c in entities[a].get('claims',{}).get('P800',[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('datavalue',{}).get('value',{}).get('id')==w]
  if not notable or any(c.get('qualifiers') for c in notable):
   held.append(dict(artist=a,work=w,reason='notable_statement_missing_or_qualified'));continue
  if len(creators)!=1 or creators[0].get('id')!=a or any(c.get('qualifiers') for c in claims.get('P170',[]) if c.get('rank')!='deprecated'):
   held.append(dict(artist=a,work=w,reason='creator_qualification'));continue
  years=sorted({int(d['time'][1:5]) for d in dates if d.get('precision',0)>=9 and d.get('time','').startswith('+')})
  if len(years)!=1 or any(d.get('precision',0)<9 for d in dates) or any(c.get('qualifiers') for c in claims.get('P571',[]) if c.get('rank')!='deprecated'):
   held.append(dict(artist=a,work=w,reason='date_unknown_range_or_qualification'));continue
  year=years[0]
  if year>1970:held.append(dict(artist=a,work=w,reason='after_1970',year=year));continue
  bounds={p:[int(v['time'][1:5]) for v in values(entities[a],p) if v.get('precision',0)>=9 and v.get('time','').startswith('+')] for p in ('P569','P570')}
  if (bounds['P569'] and year<min(bounds['P569'])+8) or (bounds['P570'] and year>max(bounds['P570'])):
   held.append(dict(artist=a,work=w,reason='creator_life_conflict'));continue
  title=next((e['labels'][l]['value'] for l in ['en','fr','de','es','it','el','ru'] if l in e.get('labels',{})),None)
  if not title:held.append(dict(artist=a,work=w,reason='missing_title'));continue
  artist=artists[a]
  candidates.append(dict(artist_id=artist['id'],artist_slug=artist['slug'],artist_name=artist['display_name'],artist_qid=a,work_qid=w,title=title,year=year,source_url='https://www.wikidata.org/wiki/'+w,entity_revision=e.get('lastrevid'),creator_life_evidence=bounds,collections=[v['id'] for v in values(e,'P195')],inventory=values(e,'P217'),types=[v['id'] for v in values(e,'P31')],notable_source='https://www.wikidata.org/wiki/'+a,notable_revision=entities[a].get('lastrevid'),image_files=values(e,'P18'),wikiart_ids=values(e,'P3467')))
 if candidates:
  candidates.sort(key=lambda r:(not r['image_files'],r['year'],r['work_qid']))
  ready.append(candidates[0])
m.save('notable-gap-selected-candidates.json.gz',ready);m.save('notable-gap-held.json.gz',held)
print('Selected notable candidates',len(ready),'held claims',dict(collections.Counter(r['reason'] for r in held)))
for r in ready:print(r['artist_name'],r['title'],r['year'],r['work_qid'],flush=True)
