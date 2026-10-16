#!/usr/bin/env python3
"""Separate one evidenced nineteenth-century engraver from a later namesake."""
import argparse,importlib.util,json,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('frey',Path(__file__).with_name('million-lifetime-corrections-20261011.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;n=f.n
RUN=m.RUN/'lifetime-followup-20261011/sharpe-review';BACKUP=m.BACKUP/'lifetime-followup-20261011/sharpe-review'
AID='34d4a661-63ce-5bc1-9ea8-67971f196a5e';OLD='d666e1be-4ef2-5bc6-aae6-d9ccae4a99d0';NEW=m.uid('artist/lifetime-review/charles-william-sharpe-1818-1899');QID='Q57979966'
SID=m.uid('source/sharpe-identity-review');SLUG='charles-william-sharpe-1818-1899';URL='https://wellcomecollection.org/concepts/bsef73s2'
def snapshot(db):
 f.AID=AID
 return dict(object=f.snapshot(db),old_artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(OLD,)).fetchone()['v'],old_artist_identifiers=[r['v'] for r in db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(OLD,))])
def plan():
 if (RUN/'plan.json').exists():return
 with m.m.connect() as db:
  before=snapshot(db)
  assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artist' AND external_id=ANY(%s)",([QID,'bsef73s2'],)).fetchall()
  assert not db.execute('SELECT id FROM artists WHERE normalized_name=%s AND birth_year=1818 AND death_year=1899',(m.norm('Charles William Sharpe'),)).fetchall()
 source=next(r for r in m.load(m.RUN/'rijks/06000-06500/plan.json.gz')['new_artworks'] if r['artwork_id']==AID)
 person=dict(constituentid='bsef73s2',forwarddisplayname='Charles William Sharpe',preferreddisplayname='Sharpe, Charles William',displaydate='1818–1899',wikidataid=QID,constituenttype='individual')
 aid,reason,artist=n.artist_plan(person,[source],{}, {}, {},'wellcome','wellcome-concept');assert artist and artist['birth_year']==1818 and artist['death_year']==1899
 artist.update(id=NEW,slug=SLUG)
 evidence=dict(method='Official collection/authority pages read with web research on 11 October 2026; editorial paraphrases, not raw page copies.',sources=[
  dict(url=URL,observation='Wellcome identifies Charles William Sharpe as a British engraver, 1818–1899, associated with The Art Journal. Its explicit Wikidata link is Q57979966.'),
  dict(url='https://www.nationaltrustcollections.org.uk/object/286689',observation='National Trust object 286689, Raising the Maypole, explicitly identifies its engraver as Charles William Sharpe, Birmingham 1818–1899; print published in 1862.'),
  dict(url=source['source_url'],observation='Captured Rijks native metadata names Charles William Sharpe on the print dated 16 October 1854, inventory RP-P-OB-73.047. The person authority wrongly supplies died 1955 and Q21463861. Only this object-level link is corrected.'),
  dict(url='https://artcollection.dcms.gov.uk/person/sharpe-charles-william/',observation='Search result corroborated 1818–1899. A later full-page request returned 403; no retry or bypass. Not required for the correction.')],decision='The dated 1854 print matches the documented nineteenth-century engraver. Preserve the later namesake and original Rijks person identifier without reassignment; preserve source conflict in the object citation.',editorial_confidence=0.97)
 m.save(RUN/'plan.json',dict(at=m.now(),before=before,artist=artist,source=source,evidence=evidence));m.save(RUN/'pin.json',dict(sha256=m.sha((RUN/'plan.json').read_bytes())))
def apply():
 plan();p=m.load(RUN/'plan.json');pin=m.load(RUN/'pin.json')['sha256'];assert pin==m.sha((RUN/'plan.json').read_bytes())
 if (RUN/'applied.json').exists():return
 with m.m.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(AID,));before=snapshot(db)
  done=db.execute('SELECT id FROM citations WHERE id=%s',(m.uid('sharpe-review/object'),)).fetchone()
  if not done:
   assert before==p['before'];links=before['object']['creators'];assert len(links)==1 and links[0]['artist_id']==OLD and links[0]['attribution_role']=='primary'
   assert before['object']['artwork']['creation_year_start']==1854 and (before['old_artist']['birth_year'],before['old_artist']['death_year'])==(1881,1955)
   assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artist' AND external_id=ANY(%s)",([QID,'bsef73s2'],)).fetchall()
   assert not db.execute('SELECT id FROM artists WHERE id=%s OR slug=%s OR (normalized_name=%s AND birth_year=1818 AND death_year=1899)',(NEW,SLUG,m.norm('Charles William Sharpe'))).fetchall()
   m.save(BACKUP/'before.json.gz',before)
   db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,adapter_key) VALUES(%s,%s,%s,'authority_data',%s,%s)",(SID,m.OP+'-sharpe-identity-review','Wellcome and National Trust: Sharpe identity review',URL,m.OP))
   n.copy_rows(db,'artists',[p['artist']])
   n.copy_rows(db,'external_identifiers',[dict(id=m.uid('sharpe-review/identifier/'+scheme),entity_type='artist',entity_id=NEW,scheme=scheme,external_id=value,canonical_url=url,source_id=SID,retrieved_at=m.now()) for scheme,value,url in [('wellcome-concept','bsef73s2',URL),('wikidata',QID,'https://www.wikidata.org/wiki/'+QID)]])
   n.copy_rows(db,'citations',[dict(id=m.uid('sharpe-review/'+kind),entity_type=kind if kind=='artist' else 'artwork',entity_id=NEW if kind=='artist' else AID,field_name='million_lifetime_identity_review',source_id=SID,source_record_id='bsef73s2' if kind=='artist' else '200399321',source_url=URL if kind=='artist' else p['source']['source_url'],evidence_note=json.dumps(dict(plan_sha256=pin,evidence=p['evidence'],original_native_creators=p['source']['creators'],previous_creator_links=links),ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR) for kind in ['artist','object']])
   db.execute("UPDATE artwork_artists SET artist_id=%s,attribution_note=%s WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(NEW,'Individually reviewed 11 October 2026: nineteenth-century engraver Charles William Sharpe (1818–1899), supported by Wellcome bsef73s2 and National Trust 286689; original conflated Rijks authority retained in citation.',AID,OLD))
   after=snapshot(db);assert after['old_artist']==before['old_artist'] and after['old_artist_identifiers']==before['old_artist_identifiers'];assert all(after['object'][k]==before['object'][k] for k in ['artwork','media','identifiers']);assert after['object']['creators'][0]['artist_id']==NEW
   db.commit()
  else:assert before['object']['creators'][0]['artist_id']==NEW
 m.save(RUN/'applied.json',dict(at=m.now(),new_artist_id=NEW,artwork_id=AID,old_artist_id=OLD,plan_sha256=pin));print('Created the verified 1818–1899 engraver and corrected one artwork link',flush=True)
def verify():
 p=m.load(RUN/'plan.json');before=m.load(BACKUP/'before.json.gz')
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=snapshot(db);a=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(NEW,)).fetchone()['v']
  assert all(a[k]==v for k,v in p['artist'].items());assert after['old_artist']==before['old_artist'] and after['old_artist_identifiers']==before['old_artist_identifiers']
  assert all(after['object'][k]==before['object'][k] for k in ['artwork','media','identifiers']);expected=dict(before['object']['creators'][0],artist_id=NEW);actual=after['object']['creators'][0]
  assert len(after['object']['creators'])==1 and all(actual[k]==v for k,v in expected.items() if k!='attribution_note')
  assert db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])',([m.uid('sharpe-review/'+k) for k in ['artist','object']],)).fetchone()['n']==2
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']
 public=[]
 for path in ['/api/backend/v1/artists/'+SLUG,'/api/backend/v1/artists/'+SLUG+'/works/'+AID]:
  started=time.monotonic();r=requests.get('https://artlines.org'+path,timeout=(15,60));r.raise_for_status();data=r.json();assert 'Charles William Sharpe' in r.text
  if path.endswith(SLUG):assert (data['timeline_start_year'],data['timeline_end_year'],data['timeline_basis'])==(1818,1899,'life')
  else:assert AID in r.text and '1854' in r.text
  public.append(dict(url=r.url,status=r.status_code,seconds=round(time.monotonic()-started,3)))
 m.save(RUN/'verification.json',dict(at=m.now(),artist_id=NEW,artwork_id=AID,new_artist_verified=True,old_person_unchanged=True,artwork_metadata_and_media_preserved=True,local_baseline_equal=True,local_readonly_counts=local,public=public));print('Verified Sharpe identity, unchanged artwork fields and public routes',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply','verify']);args=p.parse_args();globals()[args.action]()
