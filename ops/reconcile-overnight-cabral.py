#!/usr/bin/env python3
"""Two distinct Cabral paintings: correct accession, named maker and Spanish country.

Primary museums disagree about the maker's birth year. Store that uncertainty;
do not merge the two works on an erroneous Wikimedia inventory number.
"""
import argparse,importlib.util,json,uuid
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;RUN=m.x.BASE/'spain/primary-cabral';SOURCE='overnight-cabral-primary-reconciliation-20260913'
NAME='Manuel Cabral y Aguado Bejarano';SLUG='wikimedia-painter-q9027667';PID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/overnight-cabral/Q9027667'))
PRADO='https://www.museodelprado.es/coleccion/artista/cabral-y-aguado-bejarano-manuel/915b2b5f-ae17-4771-b8ee-7545dd961dc4'
CERES='https://ceres.mcu.es/pages/ResultSearch?MuseumsRolSearch=16&MuseumsSearch=&hipertextSearch=1&search=simpleSelection&simpleSearch=0&txtSimpleSearch=Cabral+Aguado+y+Bejarano%2C+Manuel'
CASES={'Q110835393':('Baile en un salón','DO0952P'),'Q110835410':('Baile en una caseta de feria','DO0953P')}

def plan():
 if (RUN/'metadata-plan.json').exists():return
 evidence={}
 for name in ['ceres-provider-results.json','prado-provider-results.json','thyssen-person.html']:
  f=RUN/name;raw=f.read_bytes();evidence[name]=dict(path=str(f.relative_to(m.x.ROOT)),sha256=CORE.sha(raw))
 assert 'Pintor español' in (RUN/'prado-provider-results.json').read_text()
 for title,acc in CASES.values():assert title in (RUN/'ceres-provider-results.json').read_text() and acc in (RUN/'ceres-provider-results.json').read_text()
 targets={}
 for target in ['local','production']:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   assert not db.execute("SELECT 1 FROM artists WHERE normalized_name LIKE '%cabral%'").fetchone()
   assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='wikidata' AND external_id='Q9027667'").fetchone()
   works={}
   for q,(title,acc) in CASES.items():
    w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',('wikimedia-artwork-'+q.lower(),)).fetchone()['row']
    assert w['status']=='review' and w['published_at'] is None and w['title']==title and w['unlinked_creator_label']==NAME and not w['primary_media_id']
    assert w['accession_number']=='DO0952P' and w['date_precision']=='unknown'
    assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(w['id'],)).fetchone()
    assert db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=%s AND institution_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(w['id'],w['current_institution_id'])).fetchone()
    works[q]=w
   targets[target]=works
  CORE.save_new(m.BACKUPS/('cabral-'+target+'-preimages.json'),works)
 for q in CASES:assert all(targets['local'][q][k]==targets['production'][q][k] for k in ['slug','title','accession_number','date_precision','unlinked_creator_label'])
 data=dict(at=CORE.now(),targets=targets,evidence=evidence,country='ES',country_basis='Prado explicitly describes a Spanish painter and Spanish school. This is cultural affiliation, not museum location or birthplace.',birth_review='Prado and Sevilla museum give1828; Carmen Thyssen gives1827. No single birth_year is asserted. Timeline lower bound1827 is explicitly estimated from the documented alternative, not an exact birth year.',object_review='Two different compositions and exact distinct museum titles. Current CER.es identifies salón DO0952P and caseta DO0953P, circa1860, oil on canvas. Preserve the old erroneous DO0952P assertion in this evidence. Source provider captures are labeled as such because origin HTTP requests were rejected/rate-limited.')
 CORE.save_new(RUN/'metadata-plan.json',data);CORE.save_new(RUN/'metadata-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'metadata-plan.json').read_bytes()),new_painters=1,existing_artworks=2));print('Cabral plan1 painter,2 existing paintings',flush=True)

def apply():
 raw=(RUN/'metadata-plan.json').read_bytes();d=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'metadata-manifest.json').read_text())['plan_sha256']
 for target in ['local','production']:
  dest=RUN/(target+'-metadata-verified.json')
  if dest.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Cabral: Prado, Carmen Thyssen and Sevilla museum identity review','collection_page',PRADO)
    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(PID,sid,'%'+pin+'%')).fetchone()
    if not done:
     assert not db.execute("SELECT 1 FROM artists WHERE normalized_name LIKE '%cabral%'").fetchone()
     m.m.r.base.insert(db,'artists',dict(id=PID,slug=SLUG,display_name=NAME,sort_name='Cabral y Aguado Bejarano, Manuel',normalized_name=m.m.r.norm(NAME),entity_type='person',birth_year=None,death_year=1891,birth_display='1827 or 1828',death_display='1891',birth_precision='unknown',death_precision='exact',timeline_start_year=1827,timeline_end_year=1891,timeline_display='born 1827 or 1828; died 1891',timeline_basis='estimated',biography_md='Spanish painter of genre scenes, history paintings and portraits. Primary museums disagree on his birth year: the Prado and Sevilla catalogue give 1828; the Carmen Thyssen museum gives 1827. Identity, country and the two distinct Sevilla paintings are corroborated; the birth year remains unresolved.',geography_review_state='classified',status='review',created_by=m.m.ACTOR,updated_by=m.m.ACTOR))
     person=json.loads((m.m.r.RUN/'entities/Q9027667.json').read_text())['entity']
     for alias in sorted(set(m.m.r.labels(person))):db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(PID,alias,m.m.r.norm(alias)))
     m.m.r.base.insert(db,'artist_countries',dict(artist_id=PID,country_code='ES',relationship_type='cultural_affiliation',is_primary=True,note=d['country_basis']))
     m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=PID,scheme='wikidata',external_id='Q9027667',canonical_url='https://www.wikidata.org/wiki/Q9027667',source_id=sid,retrieved_at=d['at']))
     for field,url in [('geography',PRADO),('biography','https://www.carmenthyssenmalaga.org/en/artista/manuel-cabral-aguado-bejarano')]:m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=PID,source_id=sid,field_name=field,source_record_id='Q9027667',source_url=url,retrieved_at=d['at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,country_basis=d['country_basis'],birth_review=d['birth_review'],sources=d['evidence']),ensure_ascii=False)))
     for q,(title,acc) in CASES.items():
      old=d['targets'][target][q];assert db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(old['id'],)).fetchone()['row']==old
      db.execute("UPDATE artworks SET accession_number=%s,creation_year_start=1860,creation_year_end=1860,date_precision='circa',date_display='c. 1860',medium_text='Oil on canvas',research_candidate=false,unlinked_creator_label=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(acc,m.m.ACTOR,old['id']))
      m.m.r.base.insert(db,'artwork_artists',dict(artwork_id=old['id'],artist_id=PID,attribution_role='primary',attribution_note='Exact primary museum creator and title; two companion works remain distinct.'))
      m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=old['id'],source_id=sid,field_name='primary_object_metadata_review',source_record_id=acc,source_url=CERES,retrieved_at=d['at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,object_review=d['object_review'],previous=old,sources=d['evidence']),ensure_ascii=False)))
   with db.transaction():
    db.execute('SET TRANSACTION READ ONLY');person=db.execute('SELECT * FROM artists WHERE id=%s',(PID,)).fetchone();assert person['birth_year'] is None and person['death_year']==1891 and person['status']=='review' and person['published_at'] is None
    assert db.execute("SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='ES' AND relationship_type='cultural_affiliation'",(PID,)).fetchone()
    for q,(_,acc) in CASES.items():
     old=d['targets'][target][q];w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(old['id'],)).fetchone()['row'];updates=dict(accession_number=acc,creation_year_start=1860,creation_year_end=1860,date_precision='circa',date_display='c. 1860',medium_text='Oil on canvas',research_candidate=False,unlinked_creator_label=None);expected={**old,**updates};ignore={'revision','updated_at','updated_by'};assert {k:v for k,v in w.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore}
     assert db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s',(w['id'],PID)).fetchone()
  CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,new_painters=1,existing_artworks_reconciled=2,country='ES',birth_uncertainty_preserved=True));print(target,'Cabral reconciled and verified',flush=True)

def images():
 a.RUN=RUN/'images'
 if not (a.RUN/'application-plan.json').exists():
  ims=[];targets={t:[] for t in ['local','production']}
  for q,(title,acc) in CASES.items():
   d=json.loads((RUN/(q+'-commons.json')).read_text());page=next(iter(d['data']['query']['pages'].values()));info=page['imageinfo'][0];meta=info['extmetadata'];assert meta['LicenseShortName']['value']=='Public domain' and meta['Copyrighted']['value']=='False'
   raw=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/cabral',q+'.original').read_bytes();receipt=json.loads((RUN/(q+'-image-receipt.json')).read_text());assert CORE.sha(raw)==receipt['sha256'];enc,w,h,quality=CORE.compress(raw);sha=CORE.sha(enc);path='/assets/artworks/imported/cabral/'+q.lower()+'-'+sha[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),enc);credit=m.image_review.image_credit(meta)
   im=dict(key=q,media_id=m.m.uid('cabral-image/'+q+'/'+sha),path=path,sha256=sha,bytes=len(enc),width=w,height=h,quality=quality,title=title,artist=NAME,page=info['descriptionurl'],provider_name='Wikimedia Commons',source_slug='overnight-cabral-selected-images-20260913',source_name='Cabral: selected rights-reviewed Commons reproductions',source_root='https://commons.wikimedia.org/',source_image_url=info['url'],rights_status='public_domain',license_label='Public domain',license_url='https://creativecommons.org/publicdomain/mark/1.0/',creator_credit=credit,attribution_text=f'{NAME}. {title}. {credit}. Wikimedia Commons, public domain. Full-frame resize and JPEG compression.',download=receipt,checked_at=CORE.now(),identity=dict(choice=dict(page=page,receipt=d['receipt']),identity_basis='Actual image review: salon composition has a dancer in a closed room; fair-booth composition has open curtains and gate in distance, matching primary CER.es description. Exact maker/title/museum agree. Incorrect Commons accession for caseta is superseded by primary DO0953P; distinct DO0952P is not merged. Per-file PD-Art/PD-old-auto-expired deathyear1891.'))
   ims.append(im)
   for target in targets:
    with m.m.r.base.connect(target=='production') as db,db.transaction():
     db.execute('SET TRANSACTION READ ONLY');work=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE slug=%s',('wikimedia-artwork-'+q.lower(),)).fetchone()['row'];assert work['accession_number']==acc and not work['primary_media_id'] and work['status']=='review' and work['creation_year_end']==1860;targets[target].append(dict(key=q,work=work))
  for target,rows in targets.items():CORE.save_new(m.BACKUPS/('cabral-images-'+target+'-preimages.json'),rows)
  CORE.save_new(a.RUN/'application-plan.json',dict(at=CORE.now(),images=ims,targets=targets,qa='Both actual full-frame images inspected; distinct compositions and primary identities approved.'))
  CORE.save_new(a.RUN/'application-manifest.json',dict(plan_sha256=CORE.sha((a.RUN/'application-plan.json').read_bytes()),images=2))
 a.apply();a.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','images']);args=p.parse_args();globals()[args.command]()
