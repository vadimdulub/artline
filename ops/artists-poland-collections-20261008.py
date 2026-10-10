#!/usr/bin/env python3
"""Create source-backed creator authorities; reconcile names before catalogue planning."""
import importlib.util,collections,re,json,difflib,sys
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-poland-collections-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def plan():
 records=m.load(m.RUN/'poland/source-records.json.gz');groups=collections.defaultdict(list)
 for w in records:
  name=w.get('creator_label') or ''
  if len(name.split())<2 or re.search(r'qualified|attribut|anonymous|unknown|workshop|master|school|nieznan|;|/|\[|\?|\bMistrz\b',name,re.I):continue
  groups[m.norm(name)].append(w)
 raw,rc=r.Source().get('https://www.wikiart.org/en/artists-by-nation/polish',as_json=False);sp=BeautifulSoup(raw,'html.parser');pl={}
 for card in sp.select('li'):
  name=card.select_one('.artist-name a');info=card.select_one('.artist-short-info')
  if name and info and re.search(r'\bPolish\b',info.get_text()):pl[m.norm(name.get_text(' ',strip=True))]=dict(url='https://www.wikiart.org'+name['href'],caption=info.get_text(' ',strip=True),evidence=rc)
 with m.connect() as db:
  artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a')};aliases=list(db.execute('SELECT artist_id::text,alias FROM artist_aliases'))
  names=collections.defaultdict(set);tokens=collections.defaultdict(set);lasts=collections.defaultdict(set)
  for aid,a in artists.items():
   for n in [a['display_name']]+[x['alias'] for x in aliases if x['artist_id']==aid]:
    nn=m.norm(n);names[nn].add(aid);tokens[' '.join(sorted(nn.split()))].add(aid)
    if nn:lasts[nn.split()[-1]].add(aid)
  new=[];matches=[];held=[];countries=[];used={};aliasrows=[]
  for nn,works in sorted(groups.items()):
   label=works[0]['creator_label'];life=set()
   for w in works:
    for a in w['raw'].get('authors',[]):
     match=re.search(r'\((\d{4})\s*[-–]\s*(\d{4})\)',a.get('name') or '')
     if match and m.norm(r.clean(a['name']))==nn:life.add(tuple(map(int,match.groups())))
    source_label=w['raw'].get('author_label') or ''
    match=re.search(r'\((\d{4})\s*[-–]\s*(\d{4})\)',source_label)
    if match:life.add(tuple(map(int,match.groups())))
   exact=names[nn]|tokens[' '.join(sorted(nn.split()))]
   if len(exact)>1:held.append(dict(name=label,reason='Ambiguous existing exact/token name',ids=sorted(exact)));continue
   aid=next(iter(exact)) if exact else None
   if aid and artists[aid]['status']=='archived':held.append(dict(name=label,reason='Archived creator'));continue
   if aid and life and all(any(artists[aid].get(k) is not None and artists[aid][k]!=l[i] for i,k in enumerate(['birth_year','death_year'])) for l in life):
    held.append(dict(name=label,reason='Existing life dates conflict',id=aid,source_life=sorted(life)));continue
   if not aid:
    near=[x for x in lasts[nn.split()[-1]] if difflib.SequenceMatcher(None,nn,m.norm(artists[x]['display_name'])).ratio()>=.78 or any(artists[x].get('birth_year')==l[0] or artists[x].get('death_year')==l[1] for l in life)]
    if near:held.append(dict(name=label,reason='Possible existing name variant',ids=near));continue
    years=[v for w in works if w['date_decision'].startswith('within_cutoff') for v in [w['year_start'],w['year_end']]]
    if not years:held.append(dict(name=label,reason='No documented activity timeline'));continue
    lo,hi=min(years),max(years);lifebounds=next(iter(life)) if len(life)==1 else None
    # Do not invent biographies or life years from a work's date.
    if lifebounds and (lo<lifebounds[0] or hi>lifebounds[1]+1):lifebounds=None
    aid=m.uid('artist/'+nn)
    a=dict(id=aid,slug=m.OP+'-artist-'+m.sha(nn.encode())[:16],display_name=label,sort_name=label,normalized_name=nn,entity_type='person',birth_year=lifebounds[0] if lifebounds else None,death_year=lifebounds[1] if lifebounds else None,birth_display=str(lifebounds[0]) if lifebounds else None,death_display=str(lifebounds[1]) if lifebounds else None,birth_precision='exact' if lifebounds else None,death_precision='exact' if lifebounds else None,timeline_start_year=lifebounds[0] if lifebounds else lo,timeline_end_year=lifebounds[1] if lifebounds else hi,timeline_display=(str(lifebounds[0])+'–'+str(lifebounds[1])) if lifebounds else 'Documented works: '+str(lo)+'–'+str(hi),timeline_basis='life' if lifebounds else 'activity',status='review',created_by=m.ACTOR,updated_by=m.ACTOR)
    new.append(a);artists[aid]=a;names[nn].add(aid);tokens[' '.join(sorted(nn.split()))].add(aid);lasts[nn.split()[-1]].add(aid)
   else:
    used[aid]=artists[aid]
    if aid not in names[nn]:aliasrows.append(dict(id=m.uid('artist-alias/'+aid+'/'+nn),artist_id=aid,alias=label,normalized_alias=nn,language_code='pl',alias_type='alternate'));names[nn].add(aid)
   evidence=dict(artist_id=aid,name=label,works=[dict(provider=w['provider'],source_id=w['source_id'],url=w['source_url'],creation=w['date_display'],evidence=w['evidence']) for w in works],source_life=sorted(life))
   matches.append(evidence)
   if nn in pl:countries.append(dict(artist_id=aid,country_code='PL',relationship_type='cultural_affiliation',is_primary=False,note='Explicit Polish label in WikiArt national artist directory. '+pl[nn]['url']));evidence['country_evidence']=pl[nn]
   elif any(any(p.get('name')=='Polska' for p in w['raw'].get('createPlaces',[])) for w in works):
    countries.append(dict(artist_id=aid,country_code='PL',relationship_type='active',is_primary=False,note='Official museum creation-place field explicitly records Polska for a documented work. Does not infer citizenship or birthplace. '+next(w['source_url'] for w in works if any(p.get('name')=='Polska' for p in w['raw'].get('createPlaces',[])))))
  current={(str(x['artist_id']),x['country_code'],x['relationship_type']) for x in db.execute('SELECT * FROM artist_countries WHERE artist_id=ANY(%s::uuid[])',([v['artist_id'] for v in countries],))}
  countries=[x for x in countries if (x['artist_id'],x['country_code'],x['relationship_type']) not in current]
 p=dict(at=m.now(),new=new,matches=matches,held=held,existing=used,aliases=aliasrows,countries=countries)
 m.save(m.RUN/'artists-plan.json.gz',p);m.save(m.BACKUP/'artists-plan.json.gz',p);print('ARTISTS PLAN',dict(new=len(new),matches=len(matches),held=len(held),countries=len(countries)),flush=True)
def apply():
 p=m.load(m.RUN/'artists-plan-reviewed.json.gz');assert not(m.RUN/'artists-applied.json').exists();assert m.load(m.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
 p['existing']=m.load(m.RUN/'artists-concurrency-refresh.json.gz')['existing']
 with m.connect(True) as db,db.transaction():
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  actual={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(p['existing']),))};assert actual==p['existing']
  m.batch_insert(db,'artists',p['new']);m.batch_insert(db,'artist_aliases',p['aliases']);m.batch_insert(db,'artist_countries',p['countries'])
  sid=m.uid('artists-source');m.batch_insert(db,'sources',[dict(id=sid,slug=m.OP+'-creator-authorities',name='Polish museum and gallery creator authorities',source_type='collection_page',base_url='https://mnk.pl/',adapter_key=m.OP)])
  cites=[dict(id=m.uid('artist-citation/'+x['artist_id']+'/'+m.norm(x['name'])),entity_type='artist',entity_id=x['artist_id'],field_name='poland_creator_authority_20261008',source_id=sid,source_url=x['works'][0]['url'],evidence_note=json.dumps(dict(**x,policy='Existing metadata/publication preserved. New authorities in review; no nationality or biography inferred from museum location.'),ensure_ascii=False),retrieved_at=x['works'][0]['evidence']['retrieved_at'],created_by=m.ACTOR) for x in p['matches']]
  m.batch_insert(db,'citations',cites)
  assert db.execute('SELECT count(*) n FROM artists WHERE id=ANY(%s::uuid[]) AND status=%s AND published_at IS NULL',([a['id'] for a in p['new']],'review')).fetchone()['n']==len(p['new'])
 m.save(m.RUN/'artists-applied.json',dict(at=m.now(),new_artists=len(p['new']),matched_existing=len(p['matches'])-len(p['new']),poland_country_links=len(p['countries']),new_aliases=len(p['aliases']),held=len(p['held']),artist_ids=[x['artist_id'] for x in p['matches']],local_database_changes=0));print('ARTISTS APPLIED',len(p['new']),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
