#!/usr/bin/env python3
"""Reconcile every SMK exhibition history in the closed Golden Age object scan."""
import argparse, collections, datetime, hashlib, importlib.util, json, re, uuid
from pathlib import Path
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/danish-golden-age-20261013';BACKUP=Path.home()/'Library/Application Support/Artline/backups/danish-golden-age-20261013';OP='danish-golden-age-smk-exhibitions-20261013';TODAY=datetime.date(2026,10,13)
s=importlib.util.spec_from_file_location('scan',ROOT/'ops/danish-golden-age-smk-complete-20261013.py');scan=importlib.util.module_from_spec(s);s.loader.exec_module(scan)
d=scan.dga
def uid(v):return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/'+OP+'/'+v))
def iso(v):return datetime.date.fromisoformat(v[:10]) if v else None
def root(v):return d.c.norm(re.sub(r'\s*\(\d+\)\s*$','',v or ''))
def save(p,x):d.save(p,x)

def plan():
 data=scan.load(RUN/'smk-complete-scan-v3.json.gz');objects={r['object_number']:r for r in data['records']}
 oids=sorted(objects)
 with d.c.connect() as db:
  links=collections.defaultdict(set)
  for start in range(0,len(oids),1000):
   batch=oids[start:start+1000]
   for r in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(scan.SCHEME,batch)):links[r['external_id']].add(r['entity_id'])
   for r in db.execute("SELECT accession_number,a.id::text FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug='statens-museum-for-kunst' AND accession_number=ANY(%s)",(batch,)):links[r['accession_number']].add(r['id'])
   for r in db.execute("SELECT a.accession_number,a.id::text FROM artworks a JOIN artwork_location_assertions l ON l.artwork_id=a.id JOIN institutions i ON i.id=l.institution_id WHERE i.slug='statens-museum-for-kunst' AND a.accession_number=ANY(%s)",(batch,)):links[r['accession_number']].add(r['id'])
   urls=[objects[x].get('source_url') or objects[x].get('raw',{}).get('frontend_url') for x in batch];urls=[x for x in urls if x]
   byurl={objects[x].get('source_url') or objects[x].get('raw',{}).get('frontend_url'):x for x in batch}
   for r in db.execute("SELECT canonical_url url,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) UNION SELECT source_url,entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,urls)):links[byurl[r['url']]].add(r['entity_id'])
  artists={r['external_id']:dict(r) for r in db.execute("SELECT e.external_id,a.id::text,a.display_name FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='smk-person' AND e.external_id=ANY(%s)",(list(d.ROSTER),))}
  inst=collections.defaultdict(list)
  for r in db.execute("SELECT id::text,slug,name FROM institutions WHERE status<>'archived'"):inst[d.c.norm(r['name'])].append(dict(r))
 rows=[];held=[]
 for oid,o in objects.items():
  for e in o.get('exhibitions',[]):
   if not e.get('exhibition') or not e.get('date_start'):
    held.append(dict(object_number=oid,reason='missing_title_or_start',source=e));continue
   matches=links[oid]
   if len(matches)!=1:
    held.append(dict(object_number=oid,reason='artwork_identity_'+('missing' if not matches else 'ambiguous'),source=e,candidates=sorted(matches)));continue
   start=iso(e['date_start']);end=iso(e.get('date_end'));venue=(e.get('venue') or '').strip() or None
   if end and start>end:held.append(dict(object_number=oid,reason='reversed_dates',source=e));continue
   rows.append(dict(object_number=oid,source_object_id=o.get('source_id') or o.get('raw',{}).get('id'),artwork_id=next(iter(matches)),person=o['person'],title=o.get('title') or o.get('raw',{}).get('titles',[{}])[0].get('title'),exhibition=e['exhibition'].strip(),root=root(e['exhibition']),start=str(start),end=str(end) if end else None,venue=venue,type=e.get('type')))
 # Cluster repeated/touring occurrences with the same normalized source title.
 byroot=collections.defaultdict(list)
 for r in rows:byroot[r['root']].append(r)
 groups=[]
 for key,items in sorted(byroot.items()):
  occurrences={ (x['exhibition'],x['start'],x['end'],x['venue']) for x in items};ordered=sorted(occurrences,key=lambda x:x[1]);clusters=[]
  for occurrence in ordered:
   start=iso(occurrence[1])
   if not clusters or (start-iso(clusters[-1][-1][1])).days>730:clusters.append([occurrence])
   else:clusters[-1].append(occurrence)
  for n,occ in enumerate(clusters):
   selected=[x for x in items if (x['exhibition'],x['start'],x['end'],x['venue']) in set(occ)];gkey=key+'/'+occ[0][1]+'/'+str(n)
   groups.append(dict(key=gkey,title=occ[0][0],alternate_titles=sorted({x[0] for x in occ if x[0]!=occ[0][0]}),occurrences=[dict(title=x[0],start=x[1],end=x[2],venue=x[3]) for x in occ],entries=selected))
 # The three translated 2019–2021 Golden Age stops belong to the curated tour.
 tour_id=d.uid('exhibition/golden-age-tour-2019');tour=[];remaining=[]
 for g in groups:
  if iso(g['occurrences'][0]['start']).year in (2019,2020) and re.search(r'guldalder|golden age',g['title'],re.I):tour.append(g)
  else:remaining.append(g)
 if tour:
  entries=[x for g in tour for x in g['entries']];occ=[x for g in tour for x in g['occurrences']]
  remaining.append(dict(key='existing-golden-age-tour',title='The Danish Golden Age',alternate_titles=sorted({g['title'] for g in tour}),occurrences=occ,entries=entries,existing_id=tour_id))
 groups=remaining
 with d.c.connect() as db:
  existing={}
  for g in groups:
   if g.get('existing_id'):
    row=db.execute('SELECT to_jsonb(e) row FROM exhibitions e WHERE id=%s',(g['existing_id'],)).fetchone();assert row;existing[g['key']]=row['row'];continue
   starts=[iso(x['start']) for x in g['occurrences']];ends=[iso(x['end']) or iso(x['start']) for x in g['occurrences']]
   matches=[x['row'] for x in db.execute("SELECT to_jsonb(e) row FROM exhibitions e WHERE normalized_title=%s AND status<>'archived' AND start_year<=%s AND end_year>=%s",(root(g['title']),max(x.year for x in ends),min(x.year for x in starts)))]
   if len(matches)==1:g['existing_id']=matches[0]['id'];existing[g['key']]=matches[0]
   elif len(matches)>1:
    held.append(dict(reason='ambiguous_existing_exhibition',group=g,candidates=[x['id'] for x in matches]));g['held']=True
 groups=[g for g in groups if not g.get('held')]
 with d.c.connect() as db:
  for g in groups:
   if not g.get('existing_id'):continue
   occurrence_rows=[dict(x) for x in db.execute('SELECT id::text,venue_label,start_date::text,end_date::text FROM exhibition_occurrences WHERE exhibition_id=%s',(g['existing_id'],))]
   for o in g['occurrences']:
    matches=[x for x in occurrence_rows if x['start_date']==o['start'] and x['end_date']==o['end'] and d.c.norm(x['venue_label'])==d.c.norm(o['venue'])]
    if len(matches)==1:o['existing_occurrence_id']=matches[0]['id']
 for g in groups:
  for o in g['occurrences']:
   candidates=inst[d.c.norm(o['venue'])] if o['venue'] else [];o['institution_id']=candidates[0]['id'] if len(candidates)==1 else None
   if len(candidates)>1:o['institution_ambiguity']=[x['id'] for x in candidates]
  g['entries']=list({(x['artwork_id'],x['object_number'],x['person'],x['title'],x['exhibition'],x['start'],x['end'],x['venue']):x for x in g['entries']}.values())
 plan=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),groups=groups,existing=existing,artists=artists,held=held,totals=dict(exhibitions=len(groups),new_exhibitions=sum(not g.get('existing_id') for g in groups),occurrences=sum(not o.get('existing_occurrence_id') for g in groups for o in g['occurrences']),entries=sum(len(g['entries']) for g in groups),artworks=len({x['artwork_id'] for g in groups for x in g['entries']}),held=len(held)))
 save(RUN/'smk-exhibition-plan-v2.json',plan);save(BACKUP/'smk-exhibition-plan-v2.json',plan);print(plan['totals'])

def apply():
 p=json.loads((RUN/'smk-exhibition-plan-v2.json').read_text());assert json.loads((RUN/'cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with d.c.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101302)')
  for key,before in p['existing'].items():
   now=db.execute('SELECT to_jsonb(e) row FROM exhibitions e WHERE id=%s FOR SHARE',(before['id'],)).fetchone()['row'];assert now==before,'Concurrent exhibition change'
  newids=[uid('exhibition/'+g['key']) for g in p['groups'] if not g.get('existing_id')]
  assert not db.execute('SELECT 1 FROM exhibitions WHERE id=ANY(%s::uuid[])',(newids,)).fetchone()
  for g in p['groups']:
   eid=g.get('existing_id') or uid('exhibition/'+g['key']);starts=[iso(x['start']) for x in g['occurrences']];ends=[iso(x['end']) or iso(x['start']) for x in g['occurrences']];lo=min(starts);hi=max(ends);state='held' if hi<=TODAY else 'uncertain'
   if not g.get('existing_id'):
    db.execute("""INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
     VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'day',%s,%s,'physical','partial','review',%s)""",(eid,g['title'],root(g['title']),Jsonb(g['alternate_titles']),lo,hi,lo.year,hi.year,str(lo)+' – '+str(hi),state,'Official SMK object exhibition histories; future/ongoing end dates remain uncertain.',OP))
   sid=uid('source/'+g['key']);payload={'source':'SMK Open object exhibition histories','group_key':g['key'],'occurrences':g['occurrences'],'object_count':len({x['object_number'] for x in g['entries']})};raw=json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()
   db.execute("""INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
    VALUES(%s,%s,'smk-open',%s,'https://api.smk.dk/api/v1/art/field_info',now(),'https://api.smk.dk/api/v1/art/search/',%s,%s,%s)""",(sid,eid,OP+'/'+g['key'],hashlib.sha256(raw).hexdigest(),Jsonb(payload),Jsonb({'grouping':'Same normalized source title and touring occurrences within 730 days; translated 2019 Golden Age titles manually reconciled.','participation':'Exact object history, not current display.'})))
   occurrence_ids={}
   for o in g['occurrences']:
    k=(o['title'],o['start'],o['end'],o['venue']);oid=o.get('existing_occurrence_id') or uid('occurrence/'+g['key']+'/'+json.dumps(k,ensure_ascii=False));occurrence_ids[k]=oid
    if o.get('existing_occurrence_id'):continue
    db.execute("""INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,start_date,end_date,date_display,evidence)
     VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(oid,eid,sid,o.get('institution_id'),o['venue'],o['start'],o['end'],o['start']+(' – '+o['end'] if o['end'] else ''),Jsonb({'source_title':o['title'],'institution_link_basis':'Exact unique normalized institution name' if o.get('institution_id') else 'Historical venue label preserved; institution unresolved.'})))
   people={x['person'] for x in g['entries']}
   for person in people:
    a=p['artists'][person];db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence) VALUES(%s,%s,%s,%s,%s,'represented artist',%s,%s)",(uid('participant/'+g['key']+'/'+person),eid,sid,a['id'],a['display_name'],person,Jsonb({'basis':'Exact SMK person identity on at least one object with this exhibition history.'})))
   for x in g['entries']:
    k=(x['exhibition'],x['start'],x['end'],x['venue']);end=iso(x['end']) if x['end'] else None;participation='exhibited' if end and end<=TODAY else 'catalogued'
    db.execute("""INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,title_label,creator_label,participation,evidence,match_basis)
     VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(uid('entry/'+g['key']+'/'+x['object_number']+'/'+x['start']+'/'+str(x['venue'])),eid,sid,occurrence_ids[k],x['artwork_id'],x['object_number'],x['title'],p['artists'][x['person']]['display_name'],participation,Jsonb({'smk_exhibition':x,'date_state':'completed' if participation=='exhibited' else 'future or ongoing at research date'}),'Exact SMK object number resolves to one active artwork; source object history names this exhibition and occurrence.'))
  db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,research_state,details) VALUES(%s,'smk-open','https://api.smk.dk/api/v1/art/search/','source_exhausted',%s)",(uid('coverage'),Jsonb({'scope':'Complete current Painting, Drawing and Print scan for 32 reconciled Danish Golden Age creator authorities','query_totals':{'Painting':4579,'Drawing':59930,'Print':24643},'held':p['totals']['held']})))
 with d.c.connect() as db:
  result=dict(exhibitions=db.execute("SELECT count(*) n FROM exhibitions WHERE import_batch=%s",(OP,)).fetchone()['n'],occurrences=db.execute("SELECT count(*) n FROM exhibition_occurrences o JOIN exhibition_source_records s ON s.id=o.source_record_id WHERE s.source_record_id LIKE %s",(OP+'/%',)).fetchone()['n'],entries=db.execute("SELECT count(*) n FROM exhibition_entries x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE s.source_record_id LIKE %s",(OP+'/%',)).fetchone()['n'],participants=db.execute("SELECT count(*) n FROM exhibition_participants x JOIN exhibition_source_records s ON s.id=x.source_record_id WHERE s.source_record_id LIKE %s",(OP+'/%',)).fetchone()['n'])
 assert result['occurrences']==p['totals']['occurrences'] and result['entries']==p['totals']['entries'];save(RUN/'smk-exhibitions-applied.json',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),**result));print(result)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);a=p.parse_args();globals()[a.phase]()
