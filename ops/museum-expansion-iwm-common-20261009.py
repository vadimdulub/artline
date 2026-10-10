"""Lightweight Imperial War Museums evidence and read-only snapshot helpers.

SQL preserves the established full-row snapshot contract without recursively
importing every historical wave. No historical scripts or evidence are changed.
"""
import hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(z);z.loader.exec_module(m)
RUN=m.RUN/'native/iwm-holdings-20261009';IIDS=['9028a907-87f9-5ef4-97da-1328fee34706','e147c124-583e-58d9-876f-d98f7ed0b5e2'];IID=IIDS[0];NETWORK=IIDS[1];QID='Q749808';QIDS={IID:QID,NETWORK:'Q23315190'};PROTECT_IIDS=IIDS;CP=m.RUN/'native/royal-holdings-20261009/delivery-checkpoint-001.json'
def ref(p):return dict(path=str(p.resolve().relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def checked(v):
 p=m.ROOT/v['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],v['path'];return p
def snapshot(db,ids):
 queries={
 'artworks':'SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',
 'artists':'SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',
 'media':'SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',
 'identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
 'citations':"SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
 'assertions':'SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id'}
 out={k:[v['row'] for v in db.execute(sql,(ids,))] for k,sql in queries.items()};out['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(IIDS,))];mids=sorted({v['media_id'] for v in out['media']}|{v['primary_media_id'] for v in out['artworks'] if v['primary_media_id']});out['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];return out
def counts(db):return {iid:db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(iid,)).fetchone() for iid in IIDS}
def digest_rows(rows):
 h=hashlib.sha256();count=0
 for row in rows:h.update(json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()+b'\n');count+=1
 return dict(rows=count,sha256=h.hexdigest())
def prior_state(db,ids):
 out=snapshot(db,ids);iids=sorted({v['current_institution_id'] for v in out['artworks'] if v['current_institution_id']}|set(IIDS));out['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(iids,))];return {k:digest_rows(v) for k,v in out.items()}
def statements(e,p):return [v for v in e['claims'].get(p,[]) if v['rank']!='deprecated']
def value(v):return v['mainsnak']['datavalue']['value']
def one(e,p):
 vs=statements(e,p);assert len(vs)==1 and vs[0]['mainsnak']['snaktype']=='value','nonunique/unknown '+p;return vs[0]
def val(e,p):return value(one(e,p))
def qual(v,p):
 vs=v.get('qualifiers',{}).get(p,[]);assert len(vs)==1 and vs[0]['snaktype']=='value';return vs[0]['datavalue']['value']
def year(v):
 assert v['calendarmodel']=='http://www.wikidata.org/entity/Q1985727' and v['precision']>=9 and v['before']==v['after']==0 and re.fullmatch(r'\+\d{4}-\d\d-\d\dT00:00:00Z',v['time']);return int(v['time'][1:5])
def creation(v):
 qs=set(v.get('qualifiers',{}));assert not qs-{'P1319','P1326','P1480'};circa='P1480' in qs
 if circa:assert qual(v,'P1480')['id']=='Q5727902'
 if qs&{'P1319','P1326'}:assert {'P1319','P1326'}<=qs;first=year(qual(v,'P1319'));last=year(qual(v,'P1326'));precision='circa_range' if circa else 'range'
 else:first=last=year(value(v));precision='circa' if circa else 'exact'
 assert 100<=first<=last<=1970;return first,last,precision
def references(v,p):return [snak['datavalue']['value'] for ref in v.get('references',[]) for snak in ref.get('snaks',{}).get(p,[]) if snak.get('snaktype')=='value']
