#!/usr/bin/env python3
"""Cite exact primary Finnish object matches; fill supported missing fields.

No creator life years, country, known creation year, holding or display claims
are overwritten. Undated works gain only explicitly stated museum bounds.
"""
import argparse,collections,contextlib,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-finnish-primary-followup.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;CORE=r.CORE;RUN=r.RUN;SOURCE='overnight-finnish-primary-object-review-20260913'
PLAN_NAME='application-plan.json';MANIFEST_NAME='application-manifest.json'
def additions(w,e):
 obj=e['primary_object'];updates={};notes=[]
 materials=[v['en'] for v in obj['materials'] if v.get('en')]
 if not w['medium_text'] and materials:updates['medium_text']='; '.join(materials)
 dims=[v for v in obj['dimensions'] if (v.get('measureType') or {}).get('en')=='artwork dimensions' and v.get('unit') and v.get('measurements')]
 if not w['dimensions_text'] and len(dims)==1:
  d=dims[0]
  if len(d['measurements']) in (2,3) and all(isinstance(v,(int,float)) and v>0 for v in d['measurements']):updates['dimensions_text']=' × '.join(str(v) for v in d['measurements'])+' '+d['unit']
 first=obj.get('yearFrom');last=obj.get('yearTo',first);prefix=obj.get('datePrefix') or {};prefix_text=prefix.get('en') or prefix.get('fi') or ''
 person=next(p for p in obj['people'] if p.get('role',{}).get('en')=='Artist')
 mirrored=first==person.get('birthYear') and last==person.get('deathYear')
 if w['date_precision']=='unknown' and first is not None and last is not None and not prefix_text and not mirrored:
  assert first<=last<=1970
  updates.update(creation_year_start=first,creation_year_end=last,date_precision='exact' if first==last else 'range',date_display=str(first) if first==last else f'{first}–{last}',research_candidate=False)
 elif w['date_precision']=='unknown':notes.append('Creation date stays unknown: missing/qualified source date or life-span-shaped museum bounds.')
 if prefix_text:notes.append('Museum date qualification retained in source evidence; existing dating not silently replaced: '+prefix_text)
 if e.get('copy_context'):notes.append('This object is the named maker\'s copy/study, not the original by the earlier artist; maker and title context preserved.')
 return updates,notes
def plan(target=None):
 if (RUN/PLAN_NAME).exists():return
 with contextlib.ExitStack() as stack:
  connections={t:stack.enter_context(m.m.r.base.connect(t=='production')) for t in ((target,) if target else ('local','production'))}
  return plan_connected(connections)
def plan_connected(connections):
 if (RUN/PLAN_NAME).exists():return
 assert (r.BASE/'finland/FI/round-20/delivery/verification.json').exists()
 entries=[];targets={t:{} for t in connections};holds=[]
 for n in range(1,21):
  d=json.loads((RUN/f'round-{n:02d}/research.json').read_text())
  for e in d['reviewed']:
   if e['decision']!='primary_identity_corroborated':continue
   receipts={t:r.BASE/'finland/FI'/f'round-{n:02d}'/'delivery/applied'/t/(e['qid']+'.json') for t in targets}
   if not all(p.exists() for p in receipts.values()):holds.append(dict(qid=e['qid'],reason='initial_import_identity_guard_held'));continue
   entry=dict(qid=e['qid'],round=n,evidence=e,targets={})
   for target,path in receipts.items():
    aid=json.loads(path.read_text())['artwork_id']
    db=connections[target]
    with db.transaction():
     db.execute('SET TRANSACTION READ ONLY');w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(aid,)).fetchone()['row'];assert w['status']=='review' and w['published_at'] is None
     assert m.m.accession_key(w['accession_number'])==m.m.accession_key(e['primary_object']['inventoryNumber'])
     person=next(p for p in e['primary_object']['people'] if p.get('role',{}).get('en')=='Artist')
     linked=db.execute("SELECT a.id::text,a.display_name,a.birth_year,a.death_year FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=%s AND aa.attribution_role='primary'",(aid,)).fetchall()
     assert len(linked)==1,(e['qid'],'not a single unqualified linked creator')
     artist=linked[0]
     authorities=db.execute("SELECT scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s",(artist['id'],)).fetchall()
     wiki_match=any(i['scheme']=='wikidata' and i['external_id']==e['creator_qid'] for i in authorities)
     museum_match=any(i['scheme']=='fng-person' and i['external_id']==str(person['id']) for i in authorities)
     assert wiki_match or museum_match,(e['qid'],'neither exact creator authority matches')
     if not wiki_match:
      assert r.namekey(artist['display_name'])==r.namekey(person.get('firstName','')+' '+person.get('familyName','')),(e['qid'],'museum creator name conflict')
      assert all(artist[k] is None or person.get(pk) is None or artist[k]==person[pk] for k,pk in [('birth_year','birthYear'),('death_year','deathYear')]),(e['qid'],'museum creator life conflict')
     entry.setdefault('creator_identity_checks',{})[target]=dict(artist_slug=db.execute('SELECT slug FROM artists WHERE id=%s',(artist['id'],)).fetchone()['slug'],wikidata_exact=wiki_match,fng_person_exact=museum_match,fng_person_id=str(person['id']),basis='Exact existing creator authority, with primary name and available life years checked for museum-only authority. No new artist identity inferred.')
     updates,notes=additions(w,e);entry['targets'][target]=dict(artwork_id=aid,slug=w['slug'],updates=updates,notes=notes);targets[target][e['qid']]=w
     owner=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='fng-object' AND external_id=%s",(str(e['primary_object']['objectId']),)).fetchone()
     assert not owner or owner['entity_id']==aid,(e['qid'],'Exact FNG object already belongs to another record; reconcile the physical-object duplicate before metadata planning')
   if len(targets)==2:assert entry['targets']['local']['slug']==entry['targets']['production']['slug'] and entry['targets']['local']['updates']==entry['targets']['production']['updates']
   entries.append(entry)
 for t,rows in targets.items():CORE.save_new(m.BACKUPS/('finnish-primary-'+t+'-preimages.json'),rows)
 first_target=next(iter(targets));CORE.save_new(RUN/PLAN_NAME,dict(at=CORE.now(),entries=entries,targets=targets,holds=holds));CORE.save_new(RUN/MANIFEST_NAME,dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/PLAN_NAME).read_bytes()),objects=len(entries),targets=list(targets),date_additions=sum('creation_year_start' in e['targets'][first_target]['updates'] for e in entries)));print('FNG primary metadata plan',len(entries),list(targets),flush=True)
def apply():
 raw=(RUN/PLAN_NAME).read_bytes();d=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/MANIFEST_NAME).read_text())['plan_sha256']
 for target in d['targets']:
  dest=RUN/(target+'-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   for e in d['entries']:
    t=e['targets'][target];aid=t['artwork_id'];old=d['targets'][target][e['qid']]
    with db.transaction():
     db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Finnish National Gallery: current primary object and material review','museum_api','https://kokoelma.kansallisgalleria.fi/api/v1/objects')
     if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
     current=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']
     # A separately verified exact-object consolidation increments revision
     # without changing artwork fields. Require every substantive field to
     # match the pinned preimage; never overwrite a concurrent content edit.
     audit_columns={'revision','updated_at','updated_by'}
     assert {k:v for k,v in current.items() if k not in audit_columns}=={k:v for k,v in old.items() if k not in audit_columns}
     updates=t['updates']
     if updates:db.execute(sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in updates)),(*updates.values(),m.m.ACTOR,aid))
     oid=str(e['evidence']['primary_object']['objectId']);found=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='fng-object' AND external_id=%s",(oid,)).fetchone()
     if found:assert found['entity_id']==aid
     else:m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='fng-object',external_id=oid,canonical_url=e['evidence']['object_url'],source_id=sid,retrieved_at=e['evidence']['primary_receipt']['retrieved_at']))
     m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='primary_object_metadata_review',source_record_id=oid,source_url=e['evidence']['object_url'],retrieved_at=e['evidence']['primary_receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=e['evidence'],updates=updates,notes=t['notes'],previous={k:old[k] for k in updates},policy='Country already independently reviewed; museum location is not a country claim. No display assertion imported.'),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY')
    for e in d['entries']:
     t=e['targets'][target];old=d['targets'][target][e['qid']];now=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(t['artwork_id'],)).fetchone()['row'];expected={**old,**t['updates']};ignore={'revision','updated_at','updated_by'};assert {k:v for k,v in now.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore}
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,primary_objects_verified=len(d['entries']),dates_added=sum('creation_year_start' in e['targets'][target]['updates'] for e in d['entries']),status='review',publication_unchanged=True));print(target,'FNG primary objects verified',len(d['entries']),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--target',choices=['local','production']);a=p.parse_args()
 if a.target:PLAN_NAME='application-plan-'+a.target+'.json';MANIFEST_NAME='application-manifest-'+a.target+'.json'
 plan(a.target) if a.command=='plan' else apply()
