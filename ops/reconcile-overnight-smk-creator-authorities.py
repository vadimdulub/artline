#!/usr/bin/env python3
"""Match missing SMK creator IDs to existing painters with exact names and years."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('smk',ROOT/'ops/overnight-smk-selected-images.py');smk=importlib.util.module_from_spec(s);s.loader.exec_module(smk);core=smk.core
SOURCE='overnight-smk-creator-authorities-20260915'
def variants(m):
 names={m.get('creator','')};first=m.get('creator_forename');last=m.get('creator_surname')
 if first and last:names.add(first+' '+last)
 name=m.get('creator','')
 if name.count(',')==1:
  surname,given=name.split(',');names.add(given.strip()+' '+surname.strip())
 return {smk.norm(x) for x in names if x}
def research(run,reference):
 cap=json.loads((reference/'capture.json').read_text());assert cap['complete'];sources=collections.defaultdict(list)
 with smk.ro('postgres://localhost/artline') as db:
  people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
   ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
   (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid
   FROM artists a WHERE a.status<>'archived'""").fetchall()
  known={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='smk-person'").fetchall()}
 index=collections.defaultdict(dict)
 for a in people:
  for name in [a['display_name']]+a['aliases']:index[smk.norm(name)][a['id']]=a
 for receipt in cap['pages']:
  raw=(reference/'metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['items']:
   try:
    maker=smk.primary_maker(o)
    if maker['creator_lref'] in known:continue
    typ=smk.work_type(o);lo,hi,precision,display=smk.date_parts(o)
    if o['object_number'] in cap['duplicate_accession_numbers'] or re.search(r'\b(verso|recto)\b',o['object_number'],re.I):continue
    title=next(t['title'] for t in o['titles'] if t.get('title'));c={'external_id':o['object_number'],'accession_number':o['object_number'],'source_api_id':o['id'],'title':title,'work_type':typ,'artist_authority':maker['creator_lref'],'roles':['primary'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':display};smk.source_match(c,o)
    sources[maker['creator_lref']].append({'maker':{k:v for k,v in maker.items() if k not in ('creator_history','notes')},'source_record_url':o['frontend_url'],'source_object_id':o['object_number'],'metadata_capture':receipt})
   except (ValueError,StopIteration):continue
 selected=[];held=[]
 for pid,objects in sources.items():
  evidence=objects[0];maker=evidence['maker'];hits={}
  for name in variants(maker):hits.update(index[name])
  if len(hits)!=1:held.append({'source_creator_id':pid,'source_creator':maker['creator'],'works':len(objects),'reason':'Exact full name is absent or ambiguous'});continue
  artist=next(iter(hits.values()));birth=maker.get('creator_date_of_birth','');death=maker.get('creator_date_of_death','')
  if not re.match(r'^\d{4}-',birth) or not re.match(r'^\d{4}-',death) or (artist['birth_year'],artist['death_year'])!=(int(birth[:4]),int(death[:4])):
   held.append({'source_creator_id':pid,'source_creator':maker['creator'],'works':len(objects),'reason':'Both museum life years must match existing painter exactly'});continue
  if any(variants(x['maker'])!=variants(maker) or any(x['maker'].get(k)!=maker.get(k) for k in ('creator_date_of_birth','creator_date_of_death')) for x in objects):held.append({'source_creator_id':pid,'reason':'Native maker facts vary between source objects'});continue
  selected.append({'source_creator_id':pid,'artist':artist,'source_evidence':evidence,'eligible_missing_works':len(objects)})
 selected.sort(key=lambda c:-c['eligible_missing_works']);core.save_new(run/'plan.json',{'at':core.now(),'records':selected,'held':held});core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)});print('Selected exact museum creator links',len(selected),'associated works',sum(x['eligible_missing_works'] for x in selected),'held creator IDs',len(held),flush=True)
def review_people(run):
 data=json.loads((run/'plan.json').read_text());f=core.Fetcher(run/'person-metadata');out=[];held=[]
 for n,c in enumerate(data['records'],1):
  pid=c['source_creator_id'];u='https://api.smk.dk/api/v1/person?id='+pid
  try:
   d=f.metadata(u)
   if len(d.get('items',[]))!=1 or d['items'][0]['id']!=pid:raise ValueError('Exact person API record unavailable')
   p=d['items'][0];a=c['artist'];source=c['source_evidence']
   names=variants({'creator':p.get('name'),'creator_forename':p.get('forename'),'creator_surname':p.get('surname')})
   if not names&variants(source['maker']):raise ValueError('Person authority name disagrees with source object maker')
   if source['source_object_id'] not in p.get('works',[]):raise ValueError('Person authority does not list the corroborating artwork')
   birth={int(v[:4]) for v in p.get('birth_date_start',[]) if v[:4].isdigit()};death={int(v[:4]) for v in p.get('death_date_start',[]) if v[:4].isdigit()}
   if birth!={a['birth_year']} or death!={a['death_year']}:raise ValueError('Person authority life years differ or are incomplete')
   out.append({'source_creator_id':pid,'canonical_url':u,'source_object_id':source['source_object_id'],'person_facts':{k:p[k] for k in ['id','name','forename','surname','birth_date_start','birth_date_end','birth_date_prec','death_date_start','death_date_end','death_date_prec','nationality','name_type'] if k in p},'metadata_capture':json.loads((f.cache/(core.sha(u.encode())+'.receipt.json')).read_text())})
  except ValueError as e:held.append({'source_creator_id':pid,'reason':str(e)})
  if n%20==0:print(core.now(),'Person authority review',n,'verified',len(out),'held',len(held),flush=True)
 core.save_new(run/'person-verification.json',{'at':core.now(),'plan_sha256':core.sha((run/'plan.json').read_bytes()),'records':out,'held':held});print('Person records verified',len(out),'held',len(held),flush=True)

def apply(run,target):
 data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];records=data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;out=[]
 verified=json.loads((run/'person-verification.json').read_text());assert verified['plan_sha256']==core.sha((run/'plan.json').read_bytes());persons={c['source_creator_id']:c for c in verified['records']};records=[c for c in records if c['source_creator_id'] in persons]
 with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
  with db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260915)');db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'SMK: exact creator authority reconciliation','museum_api','https://api.smk.dk/api/v1/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,smk.METADATA_TERMS));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
   for c in records:
    a=c['artist'];pid=c['source_creator_id'];e=c['source_evidence'];m=e['maker'];matches=db.execute('SELECT id::text,slug,display_name,birth_year,death_year,status FROM artists WHERE slug=%s FOR UPDATE',(a['slug'],)).fetchall();assert len(matches)==1;actual=matches[0];assert actual['status']!='archived' and all(actual[k]==a[k] for k in ('display_name','birth_year','death_year'))
    names=[actual['display_name']]+[x['alias'] for x in db.execute('SELECT alias FROM artist_aliases WHERE artist_id=%s',(actual['id'],)).fetchall()];assert variants(m)&{smk.norm(x) for x in names};assert (actual['birth_year'],actual['death_year'])==(int(m['creator_date_of_birth'][:4]),int(m['creator_date_of_death'][:4]))
    ids=db.execute("SELECT entity_id::text,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND scheme='smk-person' AND external_id=%s",(pid,)).fetchall();assert not ids or (len(ids)==1 and ids[0]['entity_id']==actual['id']),'Native creator ID already belongs to another painter'
    path=backup/(target+'-'+pid+'-before.json')
    if not path.exists():core.save_new(path,{'artist':actual,'identifiers':ids})
    if not ids:
     db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'smk-person',%s,%s,%s,%s)",(actual['id'],pid,persons[pid]['canonical_url'],sid,persons[pid]['metadata_capture']['retrieved_at']))
     note={'native_creator_id':pid,'source_creator':m,'source_capture':e['metadata_capture'],'person_authority':persons[pid],'identity_review':'Exact source full name or existing alias and both birth/death years agree. Museum native ID checked for collisions; existing artist preserved. No biography, nationality or discovery-popularity value changed.'}
     db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artist',%s,%s,'museum_creator_authority',%s,%s,%s,%s,%s)",(actual['id'],sid,pid,e['source_record_url'],json.dumps(note,ensure_ascii=False),e['metadata_capture']['retrieved_at'],core.ACTOR))
    out.append({'artist_id':actual['id'],'source_creator_id':pid,'outcome':'existing' if ids else 'inserted'})
 core.save_new(run/(target+'-applied.json'),{'at':core.now(),'records':out});print(target,'creator links verified',len(out),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','review-people','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
 if a.phase=='research':research(a.run,a.reference)
 elif a.phase=='review-people':review_people(a.run)
 else:apply(a.run,a.target)
