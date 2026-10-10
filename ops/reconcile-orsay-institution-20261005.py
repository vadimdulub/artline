#!/usr/bin/env python3
"""Consolidate the two verified identities of Musée d'Orsay without publishing.

M5060's official Ministry of Culture museum record names Musée d'Orsay, Paris,
and links to musee-orsay.fr. Preserve imported institution/venue/source IDs and
resolve their old URLs through canonical_institution_id. No object merging.
"""
import argparse,hashlib,importlib.util,json,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
RUN=r.RUN/'orsay-identity';BACKUP=Path.home()/'Library/Application Support/Artline/backups/museum-aliases-20261005'
OP='orsay-institution-reconciliation-20261005';EDITOR='local-european-research';URL='https://pop.culture.gouv.fr/notice/museo/M5060'
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+k))

def snapshot(db):
 institutions=db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE slug=ANY(%s)ORDER BY slug",(['joconde-m5060','musee-orsay'],)).fetchall();assert len(institutions)==2
 inst={x['row']['slug']:x['row']for x in institutions};alias=inst['joconde-m5060']['id'];canonical=inst['musee-orsay']['id']
 works=[x['row']for x in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE current_institution_id=%s ORDER BY id',(alias,)).fetchall()]
 assertions=[x['row']for x in db.execute("SELECT to_jsonb(h)row FROM artwork_location_assertions h WHERE institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL ORDER BY id",(alias,)).fetchall()]
 venues=[x['row']for x in db.execute('SELECT to_jsonb(v)row FROM institution_venues v WHERE institution_id=%s ORDER BY id',(alias,)).fetchall()]
 assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE institution_id=%s AND claim_type='display'LIMIT 1",(alias,)).fetchone(),'Display evidence needs separate venue reconciliation'
 assert not db.execute('SELECT 1 FROM curated_collection_items ci JOIN curated_collections c ON c.id=ci.collection_id WHERE c.institution_id=%s LIMIT 1',(alias,)).fetchone(),'Nonempty alias selections need separate merge'
 counts=db.execute('SELECT count(*) works,count(primary_media_id)images FROM artworks WHERE current_institution_id=%s AND status<>\'archived\'',(canonical,)).fetchone()
 return {'institutions':inst,'artworks':works,'assertions':assertions,'venues':venues,'canonical_counts':counts}

def plan():
 raw,receipt=r.capture(URL,tag='institution-identity-primary',timeout=30);assert receipt['status']==200
 text=raw.decode();assert 'M5060'in text and 'musee-orsay.fr'in text and 'Paris'in text
 targets={}
 for target in ['local','production']:
  with r.connect(target)as db:targets[target]=snapshot(db)
  snap=targets[target];assert not snap['institutions']['joconde-m5060']['canonical_institution_id']
  assert snap['institutions']['joconde-m5060']['place_id']==snap['institutions']['musee-orsay']['place_id']
  assert {x['id']for x in snap['artworks']}=={x['artwork_id']for x in snap['assertions']},'Every moved work needs its accepted holding assertion'
 r.save_gz(RUN/'plan.json.gz',{'targets':targets,'primary_source':receipt,'basis':'Identical official museum identity M5060, Paris, musee-orsay.fr; not a branch or an affiliated museum.'})
 print(json.dumps({k:{'works':len(v['artworks']),'existing_canonical_works':v['canonical_counts']['works']}for k,v in targets.items()}))

def apply(target):
 path=RUN/'plan.json.gz';data=r.load(path);before=data['targets'][target];digest=hashlib.sha256(path.read_bytes()).hexdigest();r.save_gz(BACKUP/(target+'-orsay-preimages.json.gz'),before)
 alias=before['institutions']['joconde-m5060']['id'];canonical=before['institutions']['musee-orsay']['id'];ids=[x['id']for x in before['artworks']]
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute('SELECT pg_advisory_xact_lock(202610053)')
  db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',([alias,canonical],)).fetchall()
  current=snapshot(db)
  if current['institutions']['joconde-m5060']['canonical_institution_id']==canonical:
   assert not current['artworks'];print(target,'already consolidated');return
  assert current==before,'Affected catalogue changed after preflight; preserve it and replan'
  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall()
  db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now()WHERE id=%s',(canonical,alias))
  db.execute('UPDATE institution_venues SET institution_id=%s WHERE institution_id=%s',(canonical,alias))
  db.execute("UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(canonical,alias))
  db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_by=%s,updated_at=now()WHERE id=ANY(%s::uuid[])',(canonical,EDITOR,ids))
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,%s,'authority_data',%s)ON CONFLICT(id)DO NOTHING",(uid('source'),OP,'French Ministry of Culture museum identity M5060',URL))
  for entity in [alias,canonical]:
   note='Museum identity reconciled with French Ministry of Culture record M5060: Musée d\'Orsay, Paris, official website musee-orsay.fr. The imported museum identity is retained as an alias; artwork dates, creators, images and review/publication states are preserved. Holdings do not establish current display. Plan SHA-256 '+digest+'.'
   db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'institution',%s,'institution_identity',%s,'M5060',%s,%s,%s,%s)ON CONFLICT(id)DO NOTHING",(uid(target+'/citation/'+entity),entity,uid('source'),URL,note,data['primary_source']['retrieved_at'],EDITOR))
  after=[x['row']for x in db.execute('SELECT to_jsonb(a)row FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id',(ids,)).fetchall()]
  allowed={'current_institution_id','revision','updated_at','updated_by'}
  for old,new in zip(before['artworks'],after):
   assert {k:v for k,v in old.items()if k not in allowed}=={k:v for k,v in new.items()if k not in allowed};assert new['current_institution_id']==canonical and new['revision']==old['revision']+1
  assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s LIMIT 1',(alias,)).fetchone()
 r.save_gz(BACKUP/(target+'-orsay-after.json.gz'),{'plan_sha256':digest,'artworks':after})
 print(target,'consolidated',len(after),'existing works; original identities, publication and images retained')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='plan':plan()
 else:assert args.target;apply(args.target)
