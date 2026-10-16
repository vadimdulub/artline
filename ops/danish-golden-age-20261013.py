#!/usr/bin/env python3
"""Reconcile the source-backed Danish Golden Age creator set. Reads by default."""
import argparse, datetime, hashlib, importlib.util, json, subprocess, uuid
from pathlib import Path
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/danish-golden-age-20261013'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/danish-golden-age-20261013'
ACTOR='local-european-research'
MOVEMENT='a5417465-0c46-41f9-9c38-850e89eee512'
OP='danish-golden-age-20261013'
spec=importlib.util.spec_from_file_location('catalogue',ROOT/'ops/catalogue-expansion-20261008.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

SOURCES={
 'hirschsprung':('The Hirschsprung Collection — Danish Golden Age painters','collection_page','https://www.hirschsprung.dk/','https://www.hirschsprung.dk/en/collection/art/the-danish-golden-age-and-national-romanticism'),
 'nationalmuseum':('Nationalmuseum — The Danish Golden Age','collection_page','https://www.nationalmuseum.se/','https://www.nationalmuseum.se/en/dansk-guld%C3%A5lder'),
 'getty':('Getty — Beyond the Light: Identity and Place in Nineteenth-Century Danish Art','collection_page','https://www.getty.edu/','https://www.getty.edu/art/exhibitions/denmark/index.html'),
 'smk':('SMK Open — Danish museum object and person authorities','museum_api','https://open.smk.dk/','https://api.smk.dk/api/v1/art/field_info'),
 'petit-palais':('Petit Palais — Golden Age of Danish Painting 1801–1864','collection_page','https://www.petitpalais.paris.fr/','https://www.petitpalais.paris.fr/en/discover-programme/expositions/golden-age-danish-painting-1801-1864'),
}

# Closed identity set. Every row is joined by the existing unique SMK person ID,
# never by a fuzzy name. "core" is explicitly named by Golden Age collection
# sources; "associated" records documented exhibition/context inclusion.
ROSTER={
 '289_person':('core','hirschsprung'),'1117_person':('core','hirschsprung'),'181_person':('core','nationalmuseum'),
 '330_person':('core','hirschsprung'),'1166_person':('core','hirschsprung'),'254_person':('core','hirschsprung'),
 '1131_person':('core','hirschsprung'),'1008_person':('core','nationalmuseum'),'566_person':('core','nationalmuseum'),
 '259_person':('core','hirschsprung'),'1157_person':('core','hirschsprung'),'1162_person':('core','getty'),
 '231_person':('core','nationalmuseum'),'557_person':('core','getty'),'1115_person':('associated','getty'),
 '332_person':('associated','getty'),'699_person':('associated','getty'),'2851_person':('associated','nationalmuseum'),
 '564_person':('associated','nationalmuseum'),'238_person':('associated','nationalmuseum'),'333_person':('associated','hirschsprung'),
 '536_person':('associated','getty'),'1114_person':('associated','getty'),'1233_person':('associated','getty'),
 '33245_person':('associated','hirschsprung'),'604_person':('associated','getty'),'427_person':('associated','hirschsprung'),
 '285_person':('associated','hirschsprung'),'612_person':('associated','hirschsprung'),'1165_person':('associated','hirschsprung'),
 '292_person':('associated','hirschsprung'),'743_person':('associated','getty'),
}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def uid(value): return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/'+OP+'/'+value))
def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); raw=json.dumps(value,ensure_ascii=False,indent=2,default=str).encode()
 if path.exists(): assert path.read_bytes()==raw, 'Preserve pinned evidence: '+str(path)
 else: path.write_bytes(raw)
def source_id(key): return uid('source/'+key)

def capture():
 receipts=[]
 for key,(_,_,_,url) in SOURCES.items():
  raw,receipt=c.capture(url,pace=.8); receipts.append(dict(key=key,receipt=receipt,body_sha256=hashlib.sha256(raw).hexdigest()))
 save(RUN/'source-receipts-v2.json',dict(at=now(),sources=receipts));print('captured',len(receipts),'primary sources')

def snapshot():
 with c.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  movement=db.execute('SELECT to_jsonb(m) row FROM movements m WHERE id=%s',(MOVEMENT,)).fetchone()['row']
  rows=db.execute("""SELECT e.external_id,a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
   count(DISTINCT aa.artwork_id) works,count(DISTINCT aa.artwork_id) FILTER(WHERE w.primary_media_id IS NOT NULL) illustrated,
   EXISTS(SELECT 1 FROM artist_movements am WHERE am.artist_id=a.id AND am.movement_id=%s) linked
   FROM external_identifiers e JOIN artists a ON a.id=e.entity_id
   LEFT JOIN artwork_artists aa ON aa.artist_id=a.id LEFT JOIN artworks w ON w.id=aa.artwork_id AND w.status<>'archived'
   WHERE e.entity_type='artist' AND e.scheme='smk-person' AND e.external_id=ANY(%s)
   GROUP BY e.external_id,a.id ORDER BY e.external_id""",(MOVEMENT,list(ROSTER))).fetchall()
 assert len(rows)==len(ROSTER) and {r['external_id'] for r in rows}==set(ROSTER)
 result=dict(at=now(),movement=movement,artists=[dict(r) for r in rows],totals=dict(creators=len(rows),works=sum(r['works'] for r in rows),illustrated=sum(r['illustrated'] for r in rows),already_linked=sum(r['linked'] for r in rows)))
 save(RUN/'production-before.json',result);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'production-before.json',result)
 print(result['totals'])

def backup():
 rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=20','--format=json'],text=True))
 item=next((r for r in rows if r.get('description')=='Before Danish Golden Age movement expansion 20261013' and r.get('status')=='SUCCESSFUL'),None)
 assert item,'Cloud SQL backup is not successful yet'
 save(RUN/'cloud-backup.json',item);save(BACKUP/'cloud-backup.json',item);print('backup',item['id'],item['status'])

def apply():
 before=json.loads((RUN/'production-before.json').read_text());assert json.loads((RUN/'cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 expected={r['external_id']:r for r in before['artists']}
 with c.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='30s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute("SELECT a.id FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='smk-person' WHERE e.external_id=ANY(%s) ORDER BY a.id FOR SHARE",(list(ROSTER),)).fetchall()
  actual={r['external_id']:dict(r) for r in db.execute("""SELECT e.external_id,a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
   count(DISTINCT aa.artwork_id) works,count(DISTINCT aa.artwork_id) FILTER(WHERE w.primary_media_id IS NOT NULL) illustrated,
   EXISTS(SELECT 1 FROM artist_movements am WHERE am.artist_id=a.id AND am.movement_id=%s) linked
   FROM external_identifiers e JOIN artists a ON a.id=e.entity_id LEFT JOIN artwork_artists aa ON aa.artist_id=a.id
   LEFT JOIN artworks w ON w.id=aa.artwork_id AND w.status<>'archived' WHERE e.entity_type='artist' AND e.scheme='smk-person' AND e.external_id=ANY(%s)
   GROUP BY e.external_id,a.id ORDER BY e.external_id""",(MOVEMENT,list(ROSTER)))}
  assert actual==expected,'Concurrent creator/catalogue change'
  for key,(name,kind,base,_) in SOURCES.items():
   db.execute('INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',(source_id(key),OP+'-'+key,name,kind,base,OP))
  db.execute("UPDATE movements SET start_year=1801,end_year=1864,summary_md=%s,color_hex=coalesce(color_hex,'#8B6F47') WHERE id=%s",('Danish painting and drawing from the academy-centred culture associated with C.W. Eckersberg and the Copenhagen school. The core period is presented as 1801–1864; associated artists preserve broader, source-documented nineteenth-century context.',MOVEMENT))
  for person,(tier,source) in ROSTER.items():
   artist=actual[person]
   role='primary' if tier=='core' else 'associated'
   db.execute('INSERT INTO artist_movements(artist_id,movement_id,role) VALUES(%s,%s,%s) ON CONFLICT(artist_id,movement_id) DO UPDATE SET role=excluded.role',(artist['id'],MOVEMENT,role))
   note=dict(smk_person_id=person,display_name=artist['display_name'],classification=tier,interpretation=('Explicit Golden Age collection/exhibition artist.' if tier=='core' else 'Source-documented nineteenth-century Danish exhibition or collection context; associated classification does not assert every object was made within 1801–1864.'),all_artist_works_visible_under_unified_catalogue=True)
   db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    VALUES(%s,'artist',%s,%s,'danish_golden_age_association',%s,%s,%s,now(),%s) ON CONFLICT(id) DO NOTHING""",(uid('citation/'+person),artist['id'],source_id(source),person,SOURCES[source][3],json.dumps(note,ensure_ascii=False),ACTOR))
  db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
   VALUES(%s,'movement',%s,%s,'definition','1801-1864',%s,%s,now(),%s) ON CONFLICT(id) DO NOTHING""",(uid('movement-definition'),MOVEMENT,source_id('nationalmuseum'),SOURCES['nationalmuseum'][3],json.dumps({'period':'1801–1864','scope':'Golden Age core with separately marked associated nineteenth-century context'},ensure_ascii=False),ACTOR))
 after=[]
 with c.connect() as db:
  after=[dict(r) for r in db.execute("""SELECT a.id::text,a.slug,a.display_name,am.role,count(DISTINCT aa.artwork_id) works
   FROM artist_movements am JOIN artists a ON a.id=am.artist_id LEFT JOIN artwork_artists aa ON aa.artist_id=a.id
   WHERE am.movement_id=%s GROUP BY a.id,am.role ORDER BY a.display_name""",(MOVEMENT,))]
 assert len(after)==len(ROSTER)
 result=dict(at=now(),movement_id=MOVEMENT,artists=after,totals=dict(creators=len(after),works=sum(r['works'] for r in after),core=sum(r['role']=='primary' for r in after),associated=sum(r['role']=='associated' for r in after)))
 save(RUN/'production-applied.json',result);print(result['totals'])

EXHIBITIONS=[
 dict(key='golden-age-tour-2019',title='The Danish Golden Age',start='2019-02-28',end='2021-01-03',display='28 February 2019 – 3 January 2021',source='nationalmuseum',checklist='partial',
  occurrences=[('nationalmuseum-stockholm','Nationalmuseum','Stockholm','Sweden','SE','2019-02-28','2019-07-21'),('statens-museum-for-kunst','Statens Museum for Kunst (SMK)','Copenhagen','Denmark','DK','2019-08-24','2019-12-08'),(None,'Petit Palais','Paris','France','FR','2020-09-22','2021-01-03')],
  people=['289_person','1117_person','1166_person','181_person','1008_person','566_person','1131_person','330_person','259_person','231_person','557_person','699_person','2851_person','564_person','238_person']),
 dict(key='beyond-light-2023',title='Beyond the Light: Identity and Place in Nineteenth-Century Danish Art',start='2023-01-26',end='2023-08-20',display='26 January – 20 August 2023',source='getty',checklist='partial',
  occurrences=[('the-met','The Metropolitan Museum of Art','New York','United States','US','2023-01-26','2023-04-16'),('spain-research-museum-q731126','J. Paul Getty Museum','Los Angeles','United States','US','2023-05-23','2023-08-20')],
  people=['289_person','1117_person','181_person','1166_person','1131_person','1008_person','330_person','254_person','1157_person','231_person','332_person','699_person','1115_person','1162_person','536_person']),
]

def exhibition_plan():
 receipts={x['key']:x['receipt']|{'body_sha256':x['body_sha256']} for x in json.loads((RUN/'source-receipts-v2.json').read_text())['sources']}
 with c.connect() as db:
  artists={r['external_id']:dict(r) for r in db.execute("SELECT e.external_id,a.id::text,a.display_name FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='smk-person' AND e.external_id=ANY(%s)",(sorted({p for e in EXHIBITIONS for p in e['people']}),))}
  institutions={r['slug']:dict(r) for r in db.execute("SELECT id::text,slug,name FROM institutions WHERE slug=ANY(%s)",([o[0] for e in EXHIBITIONS for o in e['occurrences'] if o[0]],))}
  nearby=[dict(r) for r in db.execute("SELECT id::text,title,start_year,end_year FROM exhibitions WHERE normalized_title=ANY(%s)",([c.norm(e['title']) for e in EXHIBITIONS],))]
 assert not nearby,'Research plan must reconcile a newly concurrent exhibition'
 assert all(p in artists for e in EXHIBITIONS for p in e['people'])
 assert len(institutions)==len({o[0] for e in EXHIBITIONS for o in e['occurrences'] if o[0]})
 plan=dict(at=now(),exhibitions=EXHIBITIONS,artists=artists,institutions=institutions,receipts=receipts,interpretation={'touring_stops':'One exhibition identity with separate occurrences','checklists':'Participant lists are partial; no object is asserted as exhibited without checklist/object evidence','petit_palais_date_conflict':'Nationalmuseum touring page advertises through 3 January 2021; Petit Palais English page exposes a different end date. Preserve the conflict in occurrence evidence.'})
 save(RUN/'exhibition-plan.json',plan);save(BACKUP/'exhibition-plan.json',plan);print('planned',len(EXHIBITIONS),'exhibitions',sum(len(e['occurrences']) for e in EXHIBITIONS),'occurrences',sum(len(e['people']) for e in EXHIBITIONS),'participants')

def apply_exhibitions():
 p=json.loads((RUN/'exhibition-plan.json').read_text());assert json.loads((RUN/'cloud-backup.json').read_text())['status']=='SUCCESSFUL'
 with c.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='30s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101301)')
  assert not db.execute("SELECT 1 FROM exhibitions WHERE id=ANY(%s::uuid[])",([uid('exhibition/'+e['key']) for e in p['exhibitions']],)).fetchone()
  for e in p['exhibitions']:
   eid=uid('exhibition/'+e['key']);sid=uid('exhibition-source/'+e['key']);rc=p['receipts'][e['source']]
   db.execute("""INSERT INTO exhibitions(id,title,normalized_title,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'day','held',%s,'physical',%s,'review',%s)""",(eid,e['title'],c.norm(e['title']),e['start'],e['end'],int(e['start'][:4]),int(e['end'][:4]),e['display'],'Official organiser/archive pages document completed venue dates.',e['checklist'],OP))
   payload={'title':e['title'],'touring_occurrences':e['occurrences'],'participant_smk_ids':e['people'],'scope_note':p['interpretation']}
   db.execute("""INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(sid,eid,e['source'],e['key'],SOURCES[e['source']][3],rc['retrieved_at'],rc['url'],rc['sha256'],Jsonb(payload),Jsonb(p['interpretation'])))
   for n,o in enumerate(e['occurrences']):
    slug,venue,city,country,code,start,end=o;inst=p['institutions'].get(slug) if slug else None
    evidence={'official_source':SOURCES[e['source']][3],'touring_stop':True}
    if e['key']=='golden-age-tour-2019' and venue=='Petit Palais':evidence['date_conflict']=p['interpretation']['petit_palais_date_conflict']
    db.execute("""INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence)
     VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(uid('occurrence/'+e['key']+'/'+str(n)),eid,sid,inst['id'] if inst else None,venue,city,country,code,start,end,start+' – '+end,Jsonb(evidence)))
   for person in e['people']:
    artist=p['artists'][person]
    db.execute("""INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)
     VALUES(%s,%s,%s,%s,%s,'represented artist',%s,%s)""",(uid('participant/'+e['key']+'/'+person),eid,sid,artist['id'],artist['display_name'],person,Jsonb({'basis':'Artist explicitly named by official exhibition page/checklist or represented in the official web tour. Participant linkage does not assert every catalogue work was exhibited.'})))
  db.execute("INSERT INTO exhibition_source_coverage(id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,2019,2023,'partial',%s)",(uid('coverage/touring'),OP,SOURCES['nationalmuseum'][3],Jsonb({'scope':'Two major modern survey exhibitions and their five documented touring occurrences; historical SMK object-level exhibition histories remain an explicit continuation.'})))
 with c.connect() as db:
  result=dict(exhibitions=db.execute("SELECT count(*) n FROM exhibitions WHERE import_batch=%s",(OP,)).fetchone()['n'],occurrences=db.execute("SELECT count(*) n FROM exhibition_occurrences o JOIN exhibitions e ON e.id=o.exhibition_id WHERE e.import_batch=%s",(OP,)).fetchone()['n'],participants=db.execute("SELECT count(*) n FROM exhibition_participants p JOIN exhibitions e ON e.id=p.exhibition_id WHERE e.import_batch=%s",(OP,)).fetchone()['n'])
 assert result=={'exhibitions':2,'occurrences':5,'participants':30};save(RUN/'exhibitions-applied.json',dict(at=now(),**result));print(result)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['capture','snapshot','backup','apply','exhibition_plan','apply_exhibitions']);a=p.parse_args();globals()[a.phase]()
