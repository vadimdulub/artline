#!/usr/bin/env python3
"""Correct seven individually reviewed short-life imports; local DB stays read-only."""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('bulk',Path(__file__).with_name('million-bulk-import-20261010.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);m=b.m
RUN=m.RUN/'lifetime-followup-20261011/activity-review';BACKUP=m.BACKUP/'lifetime-followup-20261011/activity-review'
ACTIVITY={
 '94e0264d-d4c7-52df-a0bb-46ae9a51c9d0':(1482,1514,'active 1482–1514','https://www.slam.org/collection/constituents/37147/','Saint Louis Art Museum explicitly labels Johann Otmar as active 1482–1514, identifies Augsburg as a place of activity and Reutlingen as birthplace. The Met 1502–1514 range is not a lifespan. Death-year alternatives remain unresolved.'),
 'bc41fe69-89bd-54ae-b3c1-de72067dee28':(1830,1840,'active 1830–1840','https://www.npg.org.uk/collections/search/person/mp93696/j-erxleben','National Portrait Gallery catalogue search result explicitly labels J. Erxleben active 1830–1840 and associates him with Prince Albert lithographs. The full page returned 403 and was not retried. The Met 1830–1842 label is retained as conflicting source evidence, not birth/death.'),
 'e6c2836b-1b69-523e-babb-b94983981469':(1520,1532,'active c. 1520–1532','https://www.getty.edu/vow/ULANFullDisplay?find=&nation=Brazilian&role=photoengraver%2C+photographer%2C+photographers%2C+photography+studio%2C+photogravurist%2C+photojournalist%2C+photolithographer%2C+photomontagist&subjectid=500031634','Getty ULAN 500031634 identifies the Italian woodcutter Francesco de Nanto. Its preferred biography says active 1532; its RKD biography supplies active c. 1520–1532. Neither supports the imported 1519–1528 lifespan. Object/impression dates remain unchanged.'),
 'abaf7c22-73bf-52af-973a-0ca6bf33d8a6':(1677,1678,'active c. 1677–1678','https://online.kunstsammlungen-coburg.de/downloads/kupferstichkabinett-liste-stecher.pdf','Kunstsammlungen der Veste Coburg engraver register, November 2022, PDF page 143, explicitly labels Benjamin Recknagel active around 1677/1678. Rijks imports supply c. 1680–1690 in person endpoints and in both object dates. The person endpoints are contradicted by documented earlier activity; no birth/death dates are asserted. The later print dates remain unchanged.')
}
UNRESOLVED={
 'cda34952-b26c-57f3-b01b-65553ec28a26':('https://www.nga.gov/artists/11577-baye-m-yancey','Baye M. Yancey: the undifferentiated NGA date label 1935–1942 exactly repeats the date range of the Index of American Design drawing Quilt Square. No independently documented birth or death was found. Withdraw the imported life interpretation; do not relabel the ambiguous range as a proven activity period.'),
 '69b9cd82-46ff-519f-9df8-1aa8b99aca56':('https://www.nga.gov/artists/46562-domenico-de-rossi','Domenico de Rossi: NGA supplies 1627–1640 without birth/death qualifiers and associates the name with a 1640/1645 print and later publications. Homonymous Rossi publishers require further authority reconciliation. Withdraw the unsupported thirteen-year lifespan without substituting another Rossi biography.'),
 '4677547a-94d3-5557-b559-c5d6788df156':('https://www.nga.gov/artists/51908-william-grotecloss','William Grotecloss: NGA supplies 1865–1872 without birth/death qualifiers and attributes an 1860s photograph of a commercial photographic gallery to him. The short range does not establish a seven-year life. Related Grotecloss names in library catalogues need individual reconciliation; no new lifespan is inferred.')
}
IGNORE={'updated_at','updated_by','revision'}
def related(db,ids):
 works=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) ORDER BY a.id',(ids,))]
 links=[r['v'] for r in db.execute('SELECT to_jsonb(aa) v FROM artwork_artists aa WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',(ids,))]
 return dict(artworks=works,creator_links=links)
def plan():
 if (RUN/'plan.json').exists():return
 snapshot=m.load(m.RUN/'lifetime-followup-20261011/short-life-snapshot-001.json.gz');rows=[]
 for aid,before in snapshot['artists'].items():
  update={k:None for k in ['birth_year','death_year','birth_display','death_display','birth_precision','death_precision']}
  if aid in ACTIVITY:
   lo,hi,label,url,reason=ACTIVITY[aid];update.update(active_start_year=lo,active_end_year=hi,activity_display=label,timeline_start_year=lo,timeline_end_year=hi,timeline_display=label,timeline_basis='activity')
  else:
   url,reason=UNRESOLVED[aid];works=[w for w in snapshot['works'] if w['artist_id']==aid and w['status']!='archived'];lo=min(w['creation_year_start'] for w in works);hi=max(w['creation_year_end'] for w in works)
   update.update(active_start_year=None,active_end_year=None,activity_display=None,timeline_start_year=lo,timeline_end_year=hi,timeline_display=f'Documented works {lo}–{hi}; lifespan unresolved',timeline_basis='estimated')
  rows.append(dict(artist_id=aid,before=before,update=update,source_url=url,reason=reason,source_method='Individual editorial review of official museum/authority web results and original captured museum metadata on 11 October 2026; observations are paraphrases, not archived HTML.'))
 m.save(RUN/'plan.json',dict(at=m.now(),rows=rows));m.save(RUN/'pin.json',dict(sha256=m.sha((RUN/'plan.json').read_bytes())))
def apply():
 plan();p=m.load(RUN/'plan.json');pin=m.load(RUN/'pin.json')['sha256'];assert pin==m.sha((RUN/'plan.json').read_bytes());ids=[r['artist_id'] for r in p['rows']]
 if (RUN/'applied.json').exists():return
 # Do not invalidate an already prepared live import's artist preconditions.
 for path in (m.RUN/'rijks').glob('*/plan.json.gz'):
  if not (path.parent/'full-verification.json').exists():assert not (set(ids)&set(m.load(path)['existing_artist_preconditions'])),'Affected artist is in a live import plan'
 with m.m.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  before={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))};objects=related(db,ids)
  completed=db.execute("SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])",([m.uid('life-activity-review/'+aid) for aid in ids],)).fetchone()['n']
  if completed:
   assert completed==len(ids);backup=m.load(BACKUP/'before.json.gz');assert related(db,ids)==backup['related']
   for row in p['rows']:assert all(before[row['artist_id']][k]==v for k,v in row['update'].items())
  else:
   for row in p['rows']:assert before[row['artist_id']]==row['before'],'Artist changed since individual review'
   m.save(BACKUP/'before.json.gz',dict(at=m.now(),artists=before,related=objects,plan_sha256=pin))
   sid=m.uid('source/lifetime-activity-review')
   db.execute("INSERT INTO sources(id,slug,name,source_type,adapter_key) VALUES(%s,%s,%s,'manual',%s) ON CONFLICT(id) DO NOTHING",(sid,m.OP+'-lifetime-activity-review','Individual review of museum artist date evidence',m.OP))
   for row in p['rows']:
    aid=row['artist_id'];update=row['update']
    b.n.copy_rows(db,'citations',[dict(id=m.uid('life-activity-review/'+aid),entity_type='artist',entity_id=aid,field_name='million_lifetime_activity_review',source_id=sid,source_record_id=aid,source_url=row['source_url'],evidence_note=json.dumps(dict(plan_sha256=pin,review=row),ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
    statement=sql.SQL('UPDATE artists SET {} ,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in update))
    db.execute(statement,[*update.values(),m.ACTOR,aid])
   assert related(db,ids)==objects
   after={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))}
   for row in p['rows']:
    aid=row['artist_id'];assert all(after[aid][k]==v for k,v in before[aid].items() if k not in row['update'] and k not in IGNORE)
    assert all(after[aid][k]==v for k,v in row['update'].items())
   db.commit()
 m.save(RUN/'applied.json',dict(at=m.now(),artists=ids,activity_corrections=len(ACTIVITY),ambiguous_lifespans_withdrawn=len(UNRESOLVED),plan_sha256=pin));print('Applied seven individually reviewed artist timeline corrections',flush=True)
def verify():
 p=m.load(RUN/'plan.json');ids=[r['artist_id'] for r in p['rows']];backup=m.load(BACKUP/'before.json.gz')
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');actual={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))}
  for row in p['rows']:
   aid=row['artist_id'];assert all(actual[aid][k]==v for k,v in row['update'].items());assert all(actual[aid][k]==v for k,v in backup['artists'][aid].items() if k not in row['update'] and k not in IGNORE)
  assert related(db,ids)==backup['related'];assert db.execute("SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])",([m.uid('life-activity-review/'+aid) for aid in ids],)).fetchone()['n']==len(ids)
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']
 m.save(RUN/'verification.json',dict(at=m.now(),artists=len(ids),artist_ids=ids,unchanged_artworks=len(backup['related']['artworks']),creator_links_unchanged=True,local_readonly_counts=local,local_baseline_equal=True));print('Verified seven artist corrections; all related artworks and creator links unchanged',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['plan','apply','verify']);args=ap.parse_args();globals()[args.action]()
