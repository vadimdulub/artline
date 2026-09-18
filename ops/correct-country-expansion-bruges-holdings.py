#!/usr/bin/env python3
"""Correct two distinct Bruges catalogue objects using their exact primary inventories."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('correct-country-expansion-reviewed-fields.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;C=f.C;B=f.B;RUN=B/'duplicates/bruges-distinct-objects';BACK=m.BACKUPS/'bruges-distinct-objects';E=B/'duplicates/seven-additional-objects/primary';Q='Q2745620';SLUG='wikimedia-museum-q2745620';NAME='Museu Nacional de Arte Contemporânea – Museu do Chiado'
def proposals():
 out=[]
 for q,key,acc,medium,dims,need in [('Q101800485','Lopes-Chiado','DEP1266 (48)','Oil on wood','22 × 32.5 cm',['DEP1266 (48)','Madeira','Alt. 22 x Larg. 32,5','Museu Nacional de Arte Contemporânea']),('Q101830207','Lopes-CAM','68P1169','Oil on canvas','73.5 × 54.5 cm',['68P1169','1908','Canvas Oil','73,5','54,5'])]:
  p=E/(key+'.review.json');ev=f.evidence(p);assert C.sha((E/(key+'.html')).read_bytes())==ev['data']['receipt']['sha256'];assert all(t in ev['data']['text'] for t in need)
  wiki=f.evidence(B/'wikimedia/entities'/(q+'.json'));entity=wiki['data']['entity'];assert entity['id']==q
  if q=='Q101800485':
   claims=json.dumps(entity);assert '202259' in claims,'ExactWikidataMatrizobjectpointerrequired'
  out.append(dict(key=q,type='artwork',slug='wikimedia-artwork-'+q.lower(),updates=dict(accession_number=acc,medium_text=medium,dimensions_text=dims),primary=ev,wikidata=wiki,correct_holding=q=='Q101800485'))
 return out

def plan():
 if (RUN/'plan.json').exists():return
 entries=proposals();inst=f.evidence(E/'MNAC-wikidata.json');e=inst['data']['data']['entities'][Q];assert e['id']==Q;assert any(x['mainsnak'].get('datavalue',{}).get('value',{}).get('id')=='Q45' for x in e['claims']['P17'])
 rc=json.loads((E/'MNAC-institution.receipt.json').read_text());assert C.sha((E/'MNAC-institution.html').read_bytes())==rc['sha256'];assert 'Museu Nacional de Arte Contempor' in (E/'MNAC-institution.html').read_text()
 targets={}
 for target in ('local','production'):
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');assert not db.execute('SELECT 1 FROM institutions WHERE wikidata_id=%s OR slug=%s',(Q,SLUG)).fetchone();targets[target]={}
   for x in entries:
    old=f.snapshot(db,x);w=old['row'];assert w['status']=='review' and not w['published_at'];assert not w['accession_number'] and not w['medium_text'] and not w['dimensions_text'];hold=[h for h in old['holdings'] if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by']];assert len(hold)==1 and hold[0]['institution_id']==w['current_institution_id'];assert not any(h['claim_type']=='display' and h['review_state']=='accepted' and not h['superseded_by'] for h in old['holdings']);assert len(old['creators'])==1 and old['creators'][0]['attribution_role']=='primary';assert db.execute("SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='PT'",(old['creators'][0]['artist_id'],)).fetchone();targets[target][x['key']]=old
  C.save_new(BACK/(target+'-preimages.json'),targets[target])
 for x in entries:
  keys=['slug','title','creation_year_start','creation_year_end','date_precision','status','accession_number'];assert [targets['local'][x['key']]['row'][k] for k in keys]==[targets['production'][x['key']]['row'][k] for k in keys]
 payload=dict(entries=entries,institution=dict(id=m.m.uid(m.x.SESSION_NAME+'/institution/'+Q),slug=SLUG,name=NAME,wikidata_id=Q,website_url='https://www.museuartecontemporanea.pt/',authority=inst,primary_receipt=rc),review='Two physically distinctpaintings:MNACDEP1266(48)oilwood22x32.5;CAM68P1169oilcanvas73.5x54.5. Exact current primary object sources supersede wrong secondary museum on first. Keep old assertion superseded, preserve all dates/creatorPT/media/review; no on-view assertion. No merger between works.')
 C.save_new(RUN/'plan.json',payload);pin=C.sha((RUN/'plan.json').read_bytes());C.save_new(RUN/'quality-review.json',dict(at=C.now(),approved=True,plan_sha256=pin,review=payload['review']));print('Bruges two objects and one missing institution planned',flush=True)

def apply():
 raw=(RUN/'plan.json').read_bytes();pin=C.sha(raw);d=json.loads(raw);qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin;i=d['institution']
 for target in ('local','production'):
  pre=json.loads((BACK/(target+'-preimages.json')).read_text())
  with m.m.r.base.connect(target=='production') as db:
   for e in d['entries']:
    dest=RUN/'applied'/target/(e['key']+'.json')
    if dest.exists():continue
    old=pre[e['key']];w=old['row'];rc=e['primary']['data']['receipt']
    with db.transaction():
     db.execute("SET LOCAL lock_timeout='30s'");db.execute("SET LOCAL statement_timeout='90s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(w['id'],));sid=m.m.source(db,m.x.SESSION_NAME+'-bruges-primary-correction','Primary catalogue distinction of two Bruges paintings','collection_page',rc['url']);done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s AND evidence_note LIKE %s",(w['id'],sid,e['key'],'%'+pin+'%')).fetchone()
     if not done:
      assert f.snapshot(db,e)==old
      if e['correct_holding']:
       found=db.execute('SELECT * FROM institutions WHERE wikidata_id=%s OR slug=%s',(Q,SLUG)).fetchall();assert not found or (len(found)==1 and str(found[0]['id'])==i['id'])
       db.execute("INSERT INTO institutions(id,slug,name,normalized_name,website_url,wikidata_id,kind,status,description) VALUES(%s,%s,%s,%s,%s,%s,'museum','review',%s) ON CONFLICT(id) DO NOTHING",(i['id'],SLUG,NAME,m.m.r.norm(NAME),i['website_url'],Q,'Museum identity confirmed by its official website and Portuguese national collection portal. Documented holdings do not assert current display.'))
       hid=m.m.uid(m.x.SESSION_NAME+'/holding-correction/'+e['key']);previous=next(h for h in old['holdings'] if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by']);note=json.dumps(dict(plan_sha256=pin,primary=e['primary'],supersedes=previous['id'],review=d['review']),ensure_ascii=False)
       m.m.r.base.insert(db,'artwork_location_assertions',dict(id=hid,artwork_id=w['id'],claim_type='holding',institution_id=i['id'],context='collection',source_id=sid,source_url=rc['url'],evidence_note=note,checked_at=rc['retrieved_at'],review_state='review'))
       db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s AND superseded_by IS NULL',(hid,previous['id']));db.execute("UPDATE artwork_location_assertions SET review_state='accepted' WHERE id=%s",(hid,));db.execute('UPDATE artworks SET current_location_text=%s,location_checked_at=%s,description_md=%s WHERE id=%s',(NAME,rc['retrieved_at'],'Bruges by Adriano de Sousa Lopes, documented in the MNAC catalogue as inventory DEP1266 (48). Oil on wood, 22 × 32.5 cm. Creation date remains under review; this is a museum connection, not a current-display claim.',w['id']))
      u=e['updates'];db.execute('UPDATE artworks SET accession_number=%s,medium_text=%s,dimensions_text=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(u['accession_number'],u['medium_text'],u['dimensions_text'],m.m.ACTOR,w['id']))
      m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=w['id'],field_name='primary_museum_object_correction',source_id=sid,source_record_id=e['key'],source_url=rc['url'],retrieved_at=rc['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,review=d['review'],primary=e['primary'],original_row=w,original_holdings=old['holdings'],institution=i if e['correct_holding'] else None),ensure_ascii=False)))
    C.save_new(dest,dict(at=C.now(),key=e['key'],slug=e['slug'],plan_sha256=pin));print(target,e['key'],'corrected',flush=True)

def verify():
 d=json.loads((RUN/'plan.json').read_text());out={}
 for target in ('local','production'):
  pre=json.loads((BACK/(target+'-preimages.json')).read_text());out[target]=[]
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for e in d['entries']:
    old=pre[e['key']];now=f.snapshot(db,e);assert all(now['row'][k]==v for k,v in e['updates'].items());assert now['creators']==old['creators'] and now['media']==old['media'];ignore=set(e['updates'])|{'revision','updated_at','updated_by'}
    if e['correct_holding']:
     ignore|={'current_institution_id','current_location_text','location_checked_at','description_md'};assert now['row']['current_institution_id']==d['institution']['id'];hid=m.m.uid(m.x.SESSION_NAME+'/holding-correction/'+e['key']);by={h['id']:h for h in now['holdings']};assert by[hid]['review_state']=='accepted' and by[hid]['institution_id']==d['institution']['id'];assert len(now['holdings'])==len(old['holdings'])+1
     for h in old['holdings']:
      expected={**h,'superseded_by':hid} if h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by'] else h;assert by[h['id']]==expected
    else:assert now['holdings']==old['holdings']
    assert {k:v for k,v in old['row'].items() if k not in ignore}=={k:v for k,v in now['row'].items() if k not in ignore};out[target].append(dict(slug=e['slug'],fields=e['updates'],institution_changed=e['correct_holding'],status=now['row']['status']))
 assert out['local']==out['production'];C.save_new(RUN/'verification.json',dict(at=C.now(),both_targets_verified=True,verified_records=2,new_institutions=1,targets=out));print('Bruges distinction verified both',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
