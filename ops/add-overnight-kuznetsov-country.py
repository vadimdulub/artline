#!/usr/bin/env python3
"""Add explicitly documented Ukrainian affiliation without removing Russian."""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;ROOT=m.x.BASE/'country-context-corrections/kuznetsov-primary';SLUG='wikimedia-painter-q3341659';SOURCE='overnight-kuznetsov-primary-country-20260913'
def selected(db):return g.c.selected(db,[{'artist':{'slug':SLUG}}])[SLUG]
def run(target,apply):
 receipt=json.loads((ROOT/'receipt.json').read_text());raw=(ROOT/'museum.html').read_bytes();assert CORE.sha(raw)==receipt['sha256'];text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert 'русский и украинский' in text and '1850-1929' in text
 path=ROOT/(target+'-plan.json');dest=ROOT/(target+'-verified.json')
 if dest.exists():print(target,'already verified');return
 with m.m.r.base.connect(target=='production') as db:
  if not path.exists():
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY');old=selected(db);a=old['row'];assert a['status']=='review' and a['published_at'] is None and [a['birth_year'],a['death_year']]==[1850,1929]
    assert {'scheme':'wikidata','id':'Q3341659'} in old['authorities'];codes={c['country_code'] for c in old['countries'] if c['relationship_type']=='cultural_affiliation'};assert 'RU' in codes and 'UA' not in codes
   CORE.save_new(m.BACKUPS/'kuznetsov-country'/(target+'-preimage.json'),old);CORE.save_new(path,dict(at=CORE.now(),target=target,old=old,receipt=receipt,add='UA',preserve='RU and all original relationships, dates, fields, publication status'))
  data=json.loads(path.read_text());pin=CORE.sha(path.read_bytes());old=data['old'];aid=old['row']['id']
  if not apply:print(target,'country plan ready',pin);return
  with db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,));sid=m.m.source(db,SOURCE,'Simferopol Art Museum: explicit Russian and Ukrainian painter affiliation','authority_data','https://simhm.ru/')
   done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone()
   if not done:
    assert selected(db)==old
    note='Museum biography explicitly describes Nikolai Dmitrievich Kuznetsov (1850–1929) as Russian and Ukrainian. Nonexclusive cultural affiliation; preserve existing Russian affiliation. No birthplace, imperial citizenship, museum location or present-day border inference.'
    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'UA','cultural_affiliation',false,%s)",(aid,note))
    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id='kuznetsov-1850-1929',source_url=receipt['url'],retrieved_at=receipt['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,receipt=receipt,source_wording='русский и украинский портретный и жанровый живописец',review=note),ensure_ascii=False)))
    db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,aid))
  with db.transaction():
   db.execute('SET TRANSACTION READ ONLY');now=selected(db);ignore={'geography_review_state','revision','updated_at','updated_by'};assert {k:v for k,v in now['row'].items() if k not in ignore}=={k:v for k,v in old['row'].items() if k not in ignore};assert now['authorities']==old['authorities'];assert all(c in now['countries'] for c in old['countries']);assert len(now['countries'])==len(old['countries'])+1;assert {'RU','UA'}<={c['country_code'] for c in now['countries'] if c['relationship_type']=='cultural_affiliation'}
 CORE.save_new(dest,dict(at=CORE.now(),target=target,plan_sha256=pin,artist_slug=SLUG,added='UA',preserved='RU and every existing field/relationship; remains in review'));print(target,'Kuznetsov country verified',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--target',choices=['local','production'],required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();run(args.target,args.apply)
