#!/usr/bin/env python3
"""Four primary-source field corrections, preserving rows, assets and review.

Plan after object consolidation so preimages reflect the latest relationships.
No title-based duplicate removal or automatic country inference is performed.
"""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
C=m.m.core;B=m.x.SESSION_BASE;RUN=B/'targeted-primary-corrections';BACK=m.BACKUPS/'targeted-primary-corrections'
def plain(v):return json.loads(json.dumps(v,default=str,ensure_ascii=False))
def evidence(path):
 d=json.loads(path.read_text());return dict(path=str(path),sha256=C.sha(path.read_bytes()),data=d)
def proposals():
 p=B/'poland-expansion/PL/round-05/delivery/polish-primary-v2/Q104558725.json';ev=evidence(p);o=ev['data']['object'];assert o['title']=='Portret Adama Potockiego (1822-1872)' and o['accession']=='131133 MNW'
 out=[dict(key='Potocki-sitter',type='artwork',slug='wikimedia-artwork-q104558725',updates=dict(title='Portrait of Adam Potocki (1822–1872)'),evidence=ev,receipt=ev['data']['receipt'],reason='Exact current Warsaw inventory131133MNWmakerStattlerand primary title identifyAdam,notArtur. Preserve original title as alternate and all chronology/country evidence. Reproduction unchanged.')]
 slug='europe-russian-session-museum-7fb485ae4e1c-record';p=next(B.glob('duplicates/inventory-second-pass/round-*/inventory-review/'+slug+'.json'));ev=evidence(p);r=ev['data']['reviews'][0];assert r['creator_label']=='Неизвестный художник' and r['inventory']=='Ж-3676' and C.sha(Path(r['capture']).read_bytes())==r['receipt']['sha256']
 out.append(dict(key='Tropinin-copy-maker',type='artwork',slug=slug,updates=dict(title=r['title'],accession_number=r['inventory'],medium_text=r['medium'],dimensions_text=r['dimensions'],unlinked_creator_label='Unknown painter (copy after Vasily Tropinin)'),remove_primary_creator_slug='vasily-tropinin-q434561',evidence=ev,receipt=r['receipt'],reason='Exact previously cited RussianMuseumЖ3676is unknown-paintercopyafterTropinin. Keep artwork and1830sdate; remove false primarycreatorlink, preserve archived relationship in citation/preimage. No named anonymous person or country inferred from museum.') )
 p=B/'duplicates/selected-primary/fng/404316.json';ev=evidence(p);out.append(dict(key='Genetz-creation-date',type='artwork',slug='wikimedia-artwork-q20792028',updates=dict(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display='Creation date under review',research_candidate=True),evidence=ev,receipt=ev['data']['receipt'],reason='Existing1885–1943creationrangeexactly repeats painterlifespan; objectdate is unresolved. Retain artwork,media,primaryholdingandall original assertions; no fabricated exact date.'))
 p=B/'wikimedia/entities/Q1354695.json';ev=evidence(p);e=ev['data']['entity'];assert e['labels']['mul']['value']=='Józef Mehoffer';out.append(dict(key='Mehoffer-shared-name',type='artist',qid='Q1354695',slug='wikimedia-painter-q1354695',updates=dict(display_name='Józef Mehoffer'),evidence=ev,receipt=ev['data']['receipt'],reason='Source has shared-language(mul)JózefMehofferlabel; previousGreekdisplaywas arbitrarydictionaryfallbackwhenEnglishmissing. PreserveGreeknameasalias; country/lifedates/publicationunchanged.'))
 return out

def snapshot(db,e):
 table='artworks' if e['type']=='artwork' else 'artists';w=db.execute('SELECT * FROM '+table+' WHERE slug=%s',(e['slug'],)).fetchone();assert w
 if e['type']=='artist':return plain(dict(row=w,aliases=db.execute('SELECT * FROM artist_aliases WHERE artist_id=%s ORDER BY id',(w['id'],)).fetchall(),authorities=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(w['id'],)).fetchall(),countries=db.execute('SELECT * FROM artist_countries WHERE artist_id=%s ORDER BY country_code,relationship_type',(w['id'],)).fetchall()))
 return plain(dict(row=w,creators=db.execute('SELECT aa.*,a.slug artist_slug FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=%s ORDER BY artist_id,attribution_role',(w['id'],)).fetchall(),media=db.execute('SELECT ma.* FROM media_assets ma JOIN artwork_media am ON am.media_id=ma.id WHERE am.artwork_id=%s ORDER BY ma.id',(w['id'],)).fetchall(),holdings=db.execute('SELECT * FROM artwork_location_assertions WHERE artwork_id=%s ORDER BY id',(w['id'],)).fetchall()))

def plan():
 if (RUN/'plan.json').exists():return
 assert (B/'serial-object-consolidation-completed.json').exists();entries=proposals();targets={}
 for target in ('local','production'):
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');targets[target]={}
   for e in entries:
    old=snapshot(db,e);w=old['row'];assert w['status']=='review' and w['published_at'] is None
    if e['key']=='Potocki-sitter':assert w['title']=='Childhood portrait of Artur Potocki' and w['accession_number']=='131133 MNW'
    if e['key']=='Tropinin-copy-maker':assert len(old['creators'])==1 and old['creators'][0]['artist_slug']==e['remove_primary_creator_slug'] and old['creators'][0]['attribution_role']=='primary' and not old['media'] and not w['accession_number']
    if e['key']=='Genetz-creation-date':assert (w['creation_year_start'],w['creation_year_end'])==(1885,1943)
    if e['type']=='artist':assert w['display_name']=='Γιούζεφ Μεχόφερ' and any(a['scheme']=='wikidata' and a['external_id']==e['qid'] for a in old['authorities']) and any(c['country_code']=='PL' for c in old['countries'])
    targets[target][e['key']]=old
  C.save_new(BACK/(target+'-preimages.json'),targets[target])
 for e in entries:
  fields=['slug','title','creation_year_start','creation_year_end','date_precision','accession_number','status'] if e['type']=='artwork' else ['slug','display_name','birth_year','death_year','status']
  assert [targets['local'][e['key']]['row'][k] for k in fields]==[targets['production'][e['key']]['row'][k] for k in fields]
 C.save_new(RUN/'plan.json',entries);pin=C.sha((RUN/'plan.json').read_bytes());C.save_new(RUN/'quality-review.json',dict(at=C.now(),approved=True,plan_sha256=pin,review='Four individually inspected primary-source corrections, exactsourceURLs and inventories, fullboth-targetpreimages, rows/assets/reviewpreserved. This is explicit scoped research QA; no fuzzy bulk edits.'));print('Four field corrections planned',flush=True)

def apply():
 raw=(RUN/'plan.json').read_bytes();pin=C.sha(raw);entries=json.loads(raw);qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
 for target in ('local','production'):
  pre=json.loads((BACK/(target+'-preimages.json')).read_text())
  with m.m.r.base.connect(target=='production') as db:
   for e in entries:
    dest=RUN/'applied'/target/(e['key']+'.json')
    if dest.exists():continue
    before=pre[e['key']];w=before['row'];table='artworks' if e['type']=='artwork' else 'artists'
    with db.transaction():
     db.execute("SET LOCAL lock_timeout='30s'");db.execute("SET LOCAL statement_timeout='90s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute('SELECT id FROM '+table+' WHERE id=%s FOR UPDATE',(w['id'],))
     sid=m.m.source(db,m.x.SESSION_NAME+'-targeted-field-corrections','Individually reviewed source corrections','collection_page',e['receipt']['url'])
     done=db.execute('SELECT 1 FROM citations WHERE entity_type=%s AND entity_id=%s AND source_id=%s AND source_record_id=%s AND evidence_note LIKE %s',(e['type'],w['id'],sid,e['key'],'%'+pin+'%')).fetchone()
     if not done:
      assert snapshot(db,e)==before;updates=dict(e['updates'])
      if 'title' in updates:
       updates['normalized_title']=m.m.r.norm(updates['title']);updates['alternate_title']=w['alternate_title'] or w['title']
      if e['type']=='artist':db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,'el','alternate') ON CONFLICT DO NOTHING",(w['id'],w['display_name'],m.m.r.norm(w['display_name'])))
      if e.get('remove_primary_creator_slug'):db.execute("DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(w['id'],before['creators'][0]['artist_id']))
      keys=list(updates);allowed={'title','normalized_title','alternate_title','accession_number','medium_text','dimensions_text','unlinked_creator_label','creation_year_start','creation_year_end','date_precision','date_display','research_candidate','display_name'};assert set(keys)<=allowed
      db.execute('UPDATE '+table+' SET '+','.join(k+'=%s' for k in keys)+',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',tuple(updates[k] for k in keys)+(m.m.ACTOR,w['id']))
      m.m.r.base.insert(db,'citations',dict(entity_type=e['type'],entity_id=w['id'],field_name='primary_field_correction',source_id=sid,source_record_id=e['key'],source_url=e['receipt']['url'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,review=e,original_row=w,original_creator_relationships=before.get('creators'),interpretation='Original artwork and assets remain; corrected assertions are separately sourced. Review/publicationstatusunchanged.'),ensure_ascii=False)))
    C.save_new(dest,dict(at=C.now(),key=e['key'],slug=e['slug'],plan_sha256=pin));print(target,e['key'],'corrected',flush=True)

def verify():
 entries=json.loads((RUN/'plan.json').read_text());out={}
 for target in ('local','production'):
  pre=json.loads((BACK/(target+'-preimages.json')).read_text());out[target]=[]
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for e in entries:
    old=pre[e['key']];now=snapshot(db,e);assert all(now['row'][k]==v for k,v in e['updates'].items());ignore=set(e['updates'])|{'revision','updated_at','updated_by'}
    if 'title' in e['updates']:ignore|={'normalized_title','alternate_title'};assert now['row']['alternate_title']==(old['row']['alternate_title'] or old['row']['title'])
    assert {k:v for k,v in old['row'].items() if k not in ignore}=={k:v for k,v in now['row'].items() if k not in ignore}
    if e['type']=='artist':assert now['authorities']==old['authorities'] and now['countries']==old['countries'] and all(a in now['aliases'] for a in old['aliases']) and any(a['alias']==old['row']['display_name'] for a in now['aliases'])
    else:
     assert now['media']==old['media'] and now['holdings']==old['holdings'];assert now['creators']==([] if e.get('remove_primary_creator_slug') else old['creators'])
    out[target].append(dict(key=e['key'],slug=e['slug'],updates=e['updates']))
 assert out['local']==out['production'];C.save_new(RUN/'verification.json',dict(at=C.now(),verified_records=len(entries),both_targets_verified=True,targets=out));print(len(entries),'corrections both verified',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
