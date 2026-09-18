#!/usr/bin/env python3
"""Four transliterated FNG person identities corroborated independently.

Museum object crosswalks and primary closed-life biographies distinguish these
people from namesakes. FNG numeric person IDs are not Wikidata P4177 UUIDs.
"""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;CORE=m.m.core;BASE=m.x.BASE;BACK=m.BACKUPS
CASES={'Q3341659':('399027','61774','Николай Дмитриевич Кузнецов',[1850,1929]),'Q1350341':('483521','60864','Максимов Василий Максимович',[1844,1911]),'Q127017':('394585','65410','Верещагин Василий Васильевич',[1842,1904]),'Q3372981':('395529','68376','Павла Сведомского',[1849,1904])}
def configure(target):
 c.RUN=BASE/'duplicates/fng-person-consolidation'/target;c.SOURCE='overnight-fng-person-primary-20260913';c.SOURCE_ROOT='https://kokoelma.kansallisgalleria.fi/';m.BACKUPS=BACK/'fng-person-consolidation'/target
def plan(target):
 configure(target)
 if (c.RUN/'plan.json').exists():return
 people=json.loads((BASE/'duplicates/fng-cross-country-person-review.json').read_text())['artists'];leads=json.loads((BASE/'duplicates/primary-crosswalk-0320/local-audit.json').read_text())['leads']['artwork_authority_crosswalk'];api=BASE/'finland/primary-api/objects.json';receipt=json.loads(api.with_name('objects.receipt.json').read_text());assert CORE.sha(api.read_bytes())==receipt['sha256'];objects={str(o['objectId']):o for o in json.loads(api.read_text())};entries=[]
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db)
  for q,(oid,pid,native,life) in CASES.items():
   f=BASE/'duplicates/fng-person-primary'/(q+'.html');raw=f.read_bytes();r=json.loads(f.with_suffix('.receipt.json').read_text());assert r['status']==200 and CORE.sha(raw)==r['sha256'];body=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert all(v in body for v in [native,*map(str,life)])
   obj=objects[oid];makers=[v for v in obj['people'] if v.get('role',{}).get('en')=='Artist'];assert len(makers)==1;maker=makers[0];assert str(maker['id'])==pid and not maker['attribution'] and [maker['birthYear'],maker['deathYear']]==life
   keep=next(a for a in people if {'scheme':'wikidata','id':q} in a['authorities']);old=next(a for a in people if {'scheme':'fng-person','id':pid} in a['authorities']);assert keep!=old
   lead=next(e for e in leads if e['museum_object_id']==oid);assert {a['creators'][0]['slug'] for a in lead['works']}=={keep['slug'],old['slug']}
   entity_path=Path(lead['entity_capture']);wiki=json.loads(entity_path.read_text());entity=wiki.get('entity',wiki);assert oid in m.m.r.values(entity,'P9834') and q in [v.get('id') for v in m.m.r.values(entity,'P170') if isinstance(v,dict)]
   rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([old['slug'],keep['slug']],))};a=rows[old['slug']];b=rows[keep['slug']];assert all(x['status']=='review' and x['published_at'] is None and x['entity_type']=='person' and [x['birth_year'],x['death_year']]==life for x in (a,b));assert not a['biography_md'] and not a['portrait_media_id'];assert not c.overlaps(db,a['id'],b['id'],deps)
   assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='fng-person' AND external_id=%s",(a['id'],pid)).fetchone();assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(b['id'],q)).fetchone()
   museum=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(a['id'],)).fetchall();assert museum
   evidence=dict(primary_url=r['url'],primary_person_facts=dict(receipt=r,native_name=native,life=life,fng_receipt=receipt,fng_person=maker,fng_object=obj,object_wikidata=lead['wikidata'],wikidata_capture=lead['entity_capture'],wikidata_sha256=CORE.sha(entity_path.read_bytes())),primary_preferred_biography=native+' '+str(life),country_code=None,basis='Independent current museum/exhibition biography and closed lifespan, reviewed transliteration, exact FNG person ID plus same physical-object P9834/P170 crosswalk corroborate one person. No name-only or P4177-to-numeric-ID match. Preserve all cultural affiliations, chronology, artwork links, assets and source assertions. Vereshchagin1842–1904 distinguished from Vasily1835–1909; PavelSvedomsky1849–1904 distinguished from Alexander1848–1911.')
   entries.append(dict(qid=q,old_slug=a['slug'],canonical_slug=b['slug'],evidence=evidence,targets={target:dict(old_id=a['id'],canonical_id=b['id'],old_signature=c.signature(a),canonical_signature=c.signature(b),overlaps=[],museum_creator_evidence=museum,dependencies=deps)}))
 CORE.save_new(c.RUN/'plan.json',entries);pin=CORE.sha((c.RUN/'plan.json').read_bytes());CORE.save_new(c.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=pin,confirmed_pairs=len(entries)));print(target,'FNG person plan',len(entries),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','apply','verify']);parser.add_argument('--target',choices=['local','production'],required=True);args=parser.parse_args();configure(args.target)
 if args.command=='plan':plan(args.target)
 else:getattr(c,args.command)(targets=(args.target,))
