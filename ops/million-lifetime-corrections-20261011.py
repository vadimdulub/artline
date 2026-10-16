#!/usr/bin/env python3
"""Individually evidenced creator correction; no artwork dates or lives inferred."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('bulk',Path(__file__).with_name('million-bulk-import-20261010.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);m=b.m;n=b.n
RUN=m.RUN/'lifetime-followup-20261011'
AID='a09c8e0e-036d-581c-bed6-c53b2bfe64d1';OLD='6b1e6211-1af9-53b7-ae05-92835ed17df0';NEW='c2ddf083-77db-500c-abea-fae00147a206'
def snapshot(db):
 return dict(artwork=db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=%s',(AID,)).fetchone()['v'],creators=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artwork_artists a WHERE artwork_id=%s ORDER BY artist_id',(AID,))],media=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artwork_media a WHERE artwork_id=%s ORDER BY media_id',(AID,))],identifiers=[r['v'] for r in db.execute("SELECT to_jsonb(a) v FROM external_identifiers a WHERE entity_type='artwork' AND entity_id=%s ORDER BY id",(AID,))])
def main():
 receipt=RUN/'frey-applied.json'
 if receipt.exists():return
 path=RUN/'frey-evidence.json'
 if not path.exists():
  m.save(path,dict(checked_at=m.now(),method='Primary collection and authority pages read with the web research tool; summaries below are editorial observations, not raw page copies.',sources=[
   dict(url='https://www.metmuseum.org/art/collection/search/628087',facts='Met object 628087, accession 53.600.2269, is a 1731 engraving after Guercino: the Burial of Saint Petronilla. Its creator biography incorrectly supplies the later Frey lifespan 1813–1865. Trimmed sheet 62.6 × 34.5 cm.'),
   dict(url='https://www.rijksmuseum.nl/nl/collectie/object/Graflegging-en-hemelvaart-van-H-Petronilla--9b491bab4b9e225815daa29f6ec80695',native_uri='https://id.rijksmuseum.nl/200394128',facts='Rijks accession RP-P-OB-67.305 describes the burial and assumption of Saint Petronilla, dated 1731, naming Jakob Frey I as printmaker after Guercino. Plate 630 × 360 mm. The record cites the catalogue Jakob Frey (1681–1752), number 150. This is a separate physical impression; holdings and object identities are not merged.'),
   dict(url='https://www.getty.edu/vow/ULANFullDisplay?find=Pierfrancesco+Mola&nation=&role=&subjectid=500056707',facts='Getty ULAN 500056707 identifies Jakob/Johann Jakob Frey I, the elder, as the Swiss printmaker 1681–1752 and supplies Wikidata Q1679017. The nineteenth-century painter is a separate person.')],decision='Replace only the wrong primary creator link with the existing elder Frey record. Preserve the Met raw attribution, old link and all object metadata in citations and backup. Dates, status, images and museum holdings remain unchanged.'))
 evidence=m.load(path)
 backup=m.BACKUP/'lifetime-followup-20261011/frey-before.json.gz'
 with m.m.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(AID,)).fetchone();before=snapshot(db)
  existing=db.execute("SELECT 1 FROM citations WHERE id=%s",(m.uid('lifetime-followup/frey'),)).fetchone()
  if existing:
   assert len(before['creators'])==1 and before['creators'][0]['artist_id']==NEW
   saved=m.load(backup);assert all(before[k]==saved[k] for k in ['artwork','media','identifiers'])
   m.save(receipt,dict(at=m.now(),artwork_id=AID,old_artist_id=OLD,new_artist_id=NEW,recovered=True));return
  assert before['artwork']['status']=='review' and before['artwork']['creation_year_start']==1731
  assert len(before['creators'])==1 and before['creators'][0]['artist_id']==OLD and before['creators'][0]['attribution_role']=='primary'
  person=db.execute('SELECT birth_year,death_year FROM artists WHERE id=%s',(NEW,)).fetchone();assert (person['birth_year'],person['death_year'])==(1681,1752)
  assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id='Q1679017'",(NEW,)).fetchone()
  m.save(backup,before)
  source=next(r for r in m.load(m.RUN/'met/002/plan.json.gz')['new_artworks'] if r['artwork_id']==AID)
  note=dict(evidence=evidence,previous_creator_link=before['creators'][0],original_native_creators=source['creators'],original_native_object=source['raw'])
  n.copy_rows(db,'citations',[dict(id=m.uid('lifetime-followup/frey'),entity_type='artwork',entity_id=AID,field_name='million_lifetime_identity_review',source_id=m.uid('source/met'),source_record_id='628087',source_url=source['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
  db.execute("UPDATE artwork_artists SET artist_id=%s,attribution_note=%s WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(NEW,'Identity reviewed 11 October 2026: Jakob Frey I (1681–1752), supported by Rijksmuseum RP-P-OB-67.305 and Getty ULAN 500056707. Met biography for the later namesake is preserved in the correction citation.',AID,OLD))
  after=snapshot(db);assert all(after[k]==before[k] for k in ['artwork','media','identifiers'])
  assert len(after['creators'])==1 and after['creators'][0]['artist_id']==NEW
  db.commit()
 m.save(receipt,dict(at=m.now(),artwork_id=AID,old_artist_id=OLD,new_artist_id=NEW,source_evidence_sha256=m.sha(path.read_bytes()),metadata_and_media_preserved=True));print('Corrected one confirmed Frey homonym link',flush=True)
if __name__=='__main__':main()
