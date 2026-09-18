#!/usr/bin/env python3
"""Review previously unrepresented named SMK creators for selected eligible works."""
import argparse,collections,difflib,importlib.util,json,re,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('links',Path(__file__).with_name('reconcile-overnight-smk-creator-authorities.py'));links=importlib.util.module_from_spec(s);s.loader.exec_module(links);smk=links.smk;core=smk.core
COUNTRIES={'Dansk':'DK','Tysk':'DE','Hollandsk':'NL','Fransk':'FR','Italiensk':'IT','Svensk':'SE','Engelsk':'GB','Britisk':'GB','Belgisk':'BE','Schweizisk':'CH','Norsk':'NO','Østrigsk':'AT','Spansk':'ES','Polsk':'PL','Russisk':'RU','Græsk':'GR'}
def life_interval(p,kind):
 start=p.get(kind+'_date_start',[]);end=p.get(kind+'_date_end',[]);display=p.get(kind+'_date_prec',[])
 if len(start)!=1 or len(end)!=1 or not re.match(r'^\d{4}-',start[0]) or not re.match(r'^\d{4}-',end[0]):raise ValueError('Museum person lifespan interval unavailable')
 lo=int(start[0][:4]);hi=int(end[0][:4]);assert 900<=lo<=hi<=2026
 if display and len(display)!=1:raise ValueError('Conflicting lifespan display statements')
 text=display[0] if display else (str(lo) if lo==hi else str(lo)+'–'+str(hi));precision='exact' if lo==hi else 'range'
 if re.search(r'ca\.|circa|c\.',text,re.I):precision='circa' if lo==hi else 'circa_range'
 if re.search(r'før|efter|unknown|ukendt|\?',text,re.I):raise ValueError('Person life date needs editorial interpretation')
 return {'lo':lo,'hi':hi,'year':lo if lo==hi else None,'display':text,'precision':precision}
def identity_conflicts(person,people):
 names=links.variants({'creator':person['name'],'creator_forename':person.get('forename'),'creator_surname':person.get('surname')});surname=smk.norm(person.get('surname'));birth=life_interval(person,'birth');death=life_interval(person,'death');hits=[]
 for a in people:
  variants={smk.norm(n) for n in [a['display_name']]+a['aliases']};exact=bool(names&variants);same_life=a['birth_year'] is not None and a['death_year'] is not None and birth['lo']-2<=a['birth_year']<=birth['hi']+2 and death['lo']-2<=a['death_year']<=death['hi']+2
  similar=same_life and any(surname and surname in n or max((difflib.SequenceMatcher(None,n,v).ratio() for v in names),default=0)>.60 for n in variants)
  if exact or similar:hits.append({'artist_id':a['id'],'name':a['display_name'],'reason':'Exact name' if exact else 'Similar name and overlapping life dates'})
 return hits

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--creator-review',type=Path,required=True);p.add_argument('--limit',type=int,default=70);a=p.parse_args();r=a.run;r.mkdir(parents=True,exist_ok=True);previous=json.loads((a.creator_review/'plan.json').read_text());wanted={x['source_creator_id']:x for x in sorted(previous['held'],key=lambda c:-c.get('works',0)) if x.get('works',0)>=15 and not re.search(r'ubekendt|unknown|anonym|skole|school|værksted',x.get('source_creator',''),re.I)};wanted=dict(list(wanted.items())[:a.limit]);cap=json.loads((a.reference/'capture.json').read_text());objects=collections.defaultdict(list)
 with smk.ro('postgres://localhost/artline') as db:
  people=db.execute("SELECT a.id::text,a.display_name,a.birth_year,a.death_year,ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases FROM artists a WHERE a.status<>'archived'").fetchall();known={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='smk-person'").fetchall()}
 for receipt in cap['pages']:
  path=a.reference/'metadata'/(core.sha(receipt['url'].encode())+'.json');raw=path.read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['items']:
   try:
    maker=smk.primary_maker(o);pid=maker['creator_lref']
    if pid not in wanted or pid in known:continue
    lo,hi,precision,display=smk.date_parts(o);typ=smk.work_type(o)
    if o['object_number'] in cap['duplicate_accession_numbers'] or re.search(r'\b(verso|recto)\b',o['object_number'],re.I):continue
    title=next(t['title'] for t in o['titles'] if t.get('title'));c={'external_id':o['object_number'],'accession_number':o['object_number'],'source_api_id':o['id'],'title':title,'work_type':typ,'artist_authority':pid,'roles':['primary'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':display};smk.source_match(c,o)
    objects[pid].append({'source_object_id':o['object_number'],'source_record_url':o['frontend_url'],'work_type':typ,'maker':{k:v for k,v in maker.items() if k not in ('creator_history','notes')},'metadata_capture':receipt})
   except (ValueError,StopIteration):continue
 f=core.Fetcher(r/'person-metadata');rows=[];held=[]
 for n,(pid,works) in enumerate(sorted(objects.items(),key=lambda kv:-len(kv[1])),1):
  try:
   url='https://api.smk.dk/api/v1/person?id='+pid;data=f.metadata(url)
   if len(data.get('items',[]))!=1 or data['items'][0]['id']!=pid:raise ValueError('Person authority absent or ambiguous')
   person=data['items'][0];name=person.get('name','');first=person.get('forename','');last=person.get('surname','');names=links.variants({'creator':name,'creator_forename':first,'creator_surname':last})
   if not first or not last or 'MAKER' not in person.get('name_type',[]):raise ValueError('Named individual maker is not established')
   if any(not names&links.variants(w['maker']) for w in works):raise ValueError('Person and object creator names disagree')
   works=[w for w in works if w['source_object_id'] in person.get('works',[])]
   if not works:raise ValueError('Person authority does not corroborate any selected object')
   birth=life_interval(person,'birth');death=life_interval(person,'death')
   if birth['hi']>=death['lo']:raise ValueError('Overlapping or implausible lifespan intervals')
   conflicts=identity_conflicts(person,people)
   if conflicts:held.append({'source_creator_id':pid,'reason':'Possible existing painter; independent reconciliation required','matches':conflicts});continue
   codes=sorted({COUNTRIES[n] for n in person.get('nationality',[]) if n in COUNTRIES})
   if not codes:raise ValueError('Country affiliation needs further source interpretation')
   facts={k:person[k] for k in ['id','name','forename','surname','birth_date_start','birth_date_end','birth_date_prec','death_date_start','death_date_end','death_date_prec','nationality','name_type'] if k in person};aid=str(uuid.uuid5(uuid.NAMESPACE_URL,url));display=first+' '+last
   rows.append({'artist_id':aid,'slug':'smk-person-'+pid.removesuffix('_person'),'display_name':display,'sort_name':name,'normalized_name':smk.norm(display),'source_creator_id':pid,'source_record_url':url,'person_facts':facts,'birth':birth,'death':death,'countries':codes,'metadata_capture':json.loads((f.cache/(core.sha(url.encode())+'.receipt.json')).read_text()),'selected_source_objects':works,'image_candidates':len(works)})
  except ValueError as e:held.append({'source_creator_id':pid,'reason':str(e)})
  if n%10==0:print(core.now(),'New source creators reviewed',n,'selected',len(rows),'held',len(held),flush=True)
 core.save_new(r/'plan.json',{'at':core.now(),'records':rows,'held':held,'policy':'Only named museum creator authorities with documented country affiliations, source life intervals and eligible selected artworks. No images downloaded in this phase. Exact and similar existing identities are held; source date uncertainty retained.'});core.save_new(r/'plan-manifest.json',{'sha256':core.sha((r/'plan.json').read_bytes()),'count':len(rows)});print('New named artists selected',len(rows),'eligible candidate works',sum(c['image_candidates'] for c in rows),'held',len(held),flush=True)
if __name__=='__main__':main()
