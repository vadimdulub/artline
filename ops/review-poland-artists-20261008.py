#!/usr/bin/env python3
"""Editorial creator review: collective/qualified labels, aliases, official biographies."""
import importlib.util,re,json,collections
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-poland-collections-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
p=m.load(m.RUN/'artists-plan.json.gz');profiles={m.norm(x['name']):x for x in m.load(m.RUN/'artist-biographical-research.json.gz') if 'error' not in x};works=m.load(m.RUN/'poland/source-records.json.gz')
hold=['Bracia Łopieńscy','Katarzyna Kobro , Bolesław Utkin','malarz z kręgu Lukasa Cranacha Starszego','Monogramista IHM','Ubizi Giovanni Malusardi Spiridione (autor)','Jan Chrzciciel starszy Lampi','F. Michalski','Chateaubourg de']
mapnames={'Per st. Krafft':'d78efcca-1a77-4648-946c-8fbd8b761ee3','Stanisław von Chlebowski':'3dce6661-9d88-45f1-b7c5-b9d90d6f93bb'}
removed={a['id'] for a in p['new'] if a['display_name'] in hold};mapped={a['id']:mapnames[a['display_name']] for a in p['new'] if a['display_name'] in mapnames}
p['new']=[a for a in p['new'] if a['id'] not in removed and a['id'] not in mapped]
p['matches']=[x for x in p['matches'] if x['artist_id'] not in removed]
p['countries']=[x for x in p['countries'] if x['artist_id'] not in removed]
p['held'] += [dict(name=n,reason='Editorial review: collective, qualified or incomplete creator label, or existing duplicate authority conflict; retain object-level source wording') for n in hold]
with m.connect() as db:
 for x in p['matches']:
  if x['artist_id'] in mapped:
   x['artist_id']=mapped[x['artist_id']];a=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(x['artist_id'],)).fetchone()['v'];p['existing'][a['id']]=a;x['identity_resolution']='Same recorded life dates and explicit translated name/elder qualifier; name-order and language variant reviewed.'
   p['aliases'].append(dict(id=m.uid('artist-alias/'+a['id']+'/'+m.norm(x['name'])),artist_id=a['id'],alias=x['name'],normalized_alias=m.norm(x['name']),language_code='pl',alias_type='alternate'))
 for x in p['countries']:x['artist_id']=mapped.get(x['artist_id'],x['artist_id'])
 for a in p['new']:
  profile=profiles.get(m.norm(a['display_name']))
  if not profile:continue
  bio=profile['bio_excerpt'];birth=re.search(r'(?:\b[Uu]r\.|[Uu]rodzon[ay])\s+[^.!?]{0,90}?\b(1[89]\d{2})\b',bio);death=re.search(r'(?:\bzm\.|zmar[łl][a]?)\s+[^.!?]{0,90}?\b([12]\d{3})\b',bio,re.I)
  if birth and death:
   lo,hi=int(birth[1]),int(death[1]);activity=[v for w in works if m.norm(w.get('creator_label'))==m.norm(a['display_name']) and w['date_decision'].startswith('within_cutoff') for v in [w['year_start'],w['year_end']]]
   if lo<=hi and all(lo<=y<=hi+1 for y in activity):
    a.update(birth_year=lo,death_year=hi,birth_display=str(lo),death_display=str(hi),birth_precision='exact',death_precision='exact',timeline_start_year=lo,timeline_end_year=hi,timeline_display=str(lo)+'–'+str(hi),timeline_basis='life')
 for x in p['matches']:
  profile=profiles.get(m.norm(x['name']))
  if profile:
   x['official_profile']=dict(url=profile['url'],evidence=profile['evidence'],factual_sentences=profile['factual_sentences'])
   bio=profile['bio_excerpt'];cities=r'(?:Warszaw\w*|Krakow\w*|Kraków|Poznan\w*|Poznań|Wrocław\w*|Łodz\w*|Łódź|Gdańsk\w*|Katowic\w*)'
   active=re.search(r'(?:studi\w*|prac\w*|mieszk\w*|profesor\w*|wykład\w*)[^.!?]{0,180}'+cities,bio,re.I)
   if active:p['countries'].append(dict(artist_id=x['artist_id'],country_code='PL',relationship_type='active',is_primary=False,note='Official artist biography explicitly documents study/work/residence in a named city in Poland; not citizenship. '+profile['url']));x['poland_activity_basis']=active[0]
  relevant=[w for w in works if m.norm(w.get('creator_label'))==m.norm(x['name'])]
  located=next((w for w in relevant if any(v.get('name') in ['Polska','Warszawa','Kraków','Poznań','Wrocław','Łódź','Gdańsk','Katowice'] for v in w['raw'].get('createPlaces',[]))),None)
  if located:p['countries'].append(dict(artist_id=x['artist_id'],country_code='PL',relationship_type='active',is_primary=False,note='Museum explicitly documents creation in '+', '.join(v['name'] for v in located['raw']['createPlaces'])+'. Country placement uses modern geography; no citizenship/birthplace inferred. '+located['source_url']))
 current={(str(x['artist_id']),x['country_code'],x['relationship_type']) for x in db.execute('SELECT * FROM artist_countries WHERE artist_id=ANY(%s::uuid[])',([x['artist_id'] for x in p['countries']],))}
 unique={}
 for x in p['countries']:
  k=x['artist_id'],x['country_code'],x['relationship_type']
  if k not in current:unique[k]=x
 p['countries']=list(unique.values())
p['reviewed_at']=m.now();p['review_basis']='Source creator roles checked; named people only. Multi-author and workshop labels retained unlinked; existing ambiguous Lampi authorities not merged. Source life evidence reviewed against documented work activity.'
m.save(m.RUN/'artists-plan-reviewed.json.gz',p);m.save(m.BACKUP/'artists-plan-reviewed.json.gz',p)
print('Reviewed artists',len(p['new']),'new;',len(p['countries']),'Poland links;',len(p['matches'])-len(p['new']),'existing',flush=True)
