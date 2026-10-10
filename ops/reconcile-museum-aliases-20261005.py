#!/usr/bin/env python3
"""Reconcile three reviewed duplicate institutions, retaining source identities."""
import argparse,hashlib,importlib.util,json,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
RUN=r.RUN/'additional-museum-aliases';BACKUP=Path.home()/'Library/Application Support/Artline/backups/additional-museum-aliases-20261005'
OP='additional-museum-aliases-20261005';EDITOR='local-european-research'
PAIRS=[('wikimedia-museum-q154568','alte-pinakothek','https://www.pinakothek.de/en/alte-pinakothek','Alte Pinakothek in Munich; both records identify the same gallery, not Neue Pinakothek.'),('wikimedia-museum-q917820','london-museum','https://www.londonmuseum.org.uk/','Both records identify the London Museum institution and the same official domain; individual sites are not merged.'),('decolonization-centre-pompidou','spain-research-museum-q1895953','https://www.centrepompidou.fr/en/collection','Both records identify the Musée national d’art moderne collection at Centre Pompidou, Paris.')]
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+k))
def snapshot(db,alias,canonical):
 rows=db.execute('SELECT to_jsonb(i)row FROM institutions i WHERE slug=ANY(%s)ORDER BY slug',([alias,canonical],)).fetchall();inst={x['row']['slug']:x['row']for x in rows};assert len(inst)==2
 aid=inst[alias]['id'];cid=inst[canonical]['id'];assert inst[alias]['place_id']==inst[canonical]['place_id']
 def get(table,where,args):return [x['row']for x in db.execute('SELECT to_jsonb(t)row FROM '+table+' t WHERE '+where+' ORDER BY id',args).fetchall()]
 works=get('artworks','current_institution_id=%s',(aid,));holds=get('artwork_location_assertions',"institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(aid,));venues=get('institution_venues','institution_id=%s',(aid,))
 assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE institution_id=%s AND claim_type='display'LIMIT 1",(aid,)).fetchone()
 assert not db.execute('SELECT 1 FROM curated_collections c JOIN curated_collection_items ci ON ci.collection_id=c.id WHERE c.institution_id=%s LIMIT 1',(aid,)).fetchone()
 assert {x['id']for x in works}=={x['artwork_id']for x in holds},'Every moved work requires an accepted holding'
 return dict(institutions=inst,artworks=works,assertions=holds,venues=venues)
def plan():
 pairs=[]
 for alias,canonical,url,basis in PAIRS:
  raw,rc=r.capture(url,tag='additional-museum-identity',timeout=30);assert rc['status']==200
  targets={}
  for target in ['local','production']:
   with r.connect(target)as db:targets[target]=snapshot(db,alias,canonical)
   assert not targets[target]['institutions'][alias]['canonical_institution_id']
  pairs.append(dict(alias=alias,canonical=canonical,source=rc,basis=basis,targets=targets))
 r.save_gz(RUN/'plan.json.gz',pairs);print([(x['alias'],x['canonical'],len(x['targets']['local']['artworks']))for x in pairs])
def apply(target):
 path=RUN/'plan.json.gz';pairs=r.load(path);digest=hashlib.sha256(path.read_bytes()).hexdigest();r.save_gz(BACKUP/(target+'-preimages.json.gz'),[x['targets'][target]for x in pairs]);receipts=[]
 with r.connect(target,readonly=False)as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='3s'");db.execute('SELECT pg_advisory_xact_lock(202610053)')
  for p in pairs:
   old=p['targets'][target];alias=old['institutions'][p['alias']]['id'];canonical=old['institutions'][p['canonical']]['id'];ids=[x['id']for x in old['artworks']]
   db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',([alias,canonical],)).fetchall()
   cur=snapshot(db,p['alias'],p['canonical'])
   if cur['institutions'][p['alias']]['canonical_institution_id']==canonical:
    assert not cur['artworks'];continue
   assert cur==old,'Reviewed preimages changed; replan before applying'
   db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall()
   db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now()WHERE id=%s',(canonical,alias))
   db.execute('UPDATE institution_venues SET institution_id=%s WHERE institution_id=%s',(canonical,alias))
   db.execute("UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(canonical,alias))
   db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_by=%s,updated_at=now()WHERE id=ANY(%s::uuid[])',(canonical,EDITOR,ids))
   db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,%s,'authority_data',%s)ON CONFLICT(id)DO NOTHING",(uid('source'),OP,'Reviewed museum institution aliases',p['source']['url']))
   for entity in [alias,canonical]:
    note=p['basis']+' Original institution identity retained as an alias. Artwork metadata, images, editorial states, source provenance and owner selections are preserved. No current-display claim. Plan SHA-256 '+digest+'.'
    db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'institution',%s,'institution_identity',%s,%s,%s,%s,%s)",(uid(target+'/'+entity),entity,uid('source'),p['source']['url'],note,p['source']['retrieved_at'],EDITOR))
   after=[x['row']for x in db.execute('SELECT to_jsonb(a)row FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id',(ids,)).fetchall()];allowed={'current_institution_id','revision','updated_at','updated_by'}
   for before,new in zip(old['artworks'],after):
    assert {k:v for k,v in before.items()if k not in allowed}=={k:v for k,v in new.items()if k not in allowed};assert new['current_institution_id']==canonical and new['revision']==before['revision']+1
   receipts.append(dict(alias=p['alias'],canonical=p['canonical'],artworks=after))
 r.save_gz(BACKUP/(target+'-after.json.gz'),dict(plan_sha256=digest,repairs=receipts));print(target,'consolidated',len(receipts),'museum identities')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);args=p.parse_args()
 if args.command=='plan':plan()
 else:assert args.target;apply(args.target)
