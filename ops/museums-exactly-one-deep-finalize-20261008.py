#!/usr/bin/env python3
"""Final object/version decisions, retained separately from discovery plans."""
import argparse,copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museums-exactly-one-artefact-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
d=a.d;RUN=a.RUN;ROOT=a.ROOT

HOLDS={
 '5f3414a63c3e063cf91095b5':'Illustrated album / author-role identity requires clarification; do not treat Evarnitsky as the painting creator.',
 '60bf6684adb09e32c40829f6':'Source creator heading Abram Yefimov conflicts with own object narrative naming Abram Arkhipov.',
 '5d274d938383a67c60f1e802':'Nicholas Mas likely denotes Nicolaes Maes; review against existing Maes portrait versions before adding.',
 '5faa8a5aa44e956c1dc52568':'Raffaelli study for Boulevard Saint-Michel; compare existing creator records and versions individually.',
 '5df0fc57de44bc629d5e8347':'Own source displays incompatible dimensions 80.6 x 98.4 and 65.3 x 54.5; clarify object/version before adding.',
 '642e8359f3f1ca0338fec005':'Same Zhukovsky 1918 Summer Morning as English native record 5952628a5a93481c74b378c9: identical creator, museum and 91.3 x 122.6 cm. Retain one artwork and both source identities.',
}
NOTES={
 '5d31adceed60240267a85d96':'Source describes A Bad Joke as a study (circa 1904). Preserve this version identity; do not identify it with a finished work. No matching 1904 existing Fechin object was found in the creator-scoped comparison.',
 '5ddf81fb19c40046f8a7d04d':'Source identifies the museum object as the 1867 replica of the 1862 composition. This record denotes the documented 1867 version, not the 1862 original.',
}
def write_wave(source,wave,holds,notes=None):
 folder=RUN/'waves'/source;plan=d.load(folder/'plan.json.gz');original=copy.deepcopy(plan);keep=[]
 for r in plan['records']:
  key=r['source_record_id']
  if key in holds:plan['held'].append(dict(source_record_id=key,artwork_id=r['artwork_id'],museum_id=r['museum']['id'],title=r['facts']['title'],reason='individual_version_review_hold',basis=holds[key]));continue
  if key in (notes or {}):r['remaining_uncertainty']+=' '+notes[key];r['raw_source_record']['editorial_version_review']=notes[key]
  if key=='5952628a5a93481c74b378c9':
   duplicate=next(v for v in original['records']if v['source_record_id']=='642e8359f3f1ca0338fec005')
   r['raw_source_record']['duplicate_native_source']=duplicate
   r['remaining_uncertainty']+=' '+HOLDS['642e8359f3f1ca0338fec005']
   r['alternate_native_urls']=sorted(set(r.get('alternate_native_urls',[])+[duplicate['facts']['source_url']]))
  keep.append(r)
 plan['records']=keep
 for summary in plan['museums']:
  rows=[r for r in keep if r['museum']['id']==summary['museum_id']]
  summary.update(new_artworks=sum(r['action']=='create'for r in rows),new_links=sum(r['action']=='link'for r in rows),projected_eligible=summary['before']['eligible']+len(rows),projected_linked=summary['before']['linked']+len(rows),available_after_identity_review=len(rows))
 plan['parent_plan']=dict(path=str((folder/'plan.json.gz').relative_to(ROOT)),sha256=d.sha((folder/'plan.json.gz').read_bytes()))
 plan['individual_editorial_review']=dict(at=d.now(),holds=holds,version_notes=notes or {},basis='Retain original source facts; individually distinguish physical objects, versions, source creator roles and native duplicates. Similarity is discovery only.')
 dest=RUN/'waves'/wave
 for name in ['sample.json','source-verified.json.gz','identity-query-plan.json']:d.save(dest/name,d.load(folder/name))
 plan['sample_sha256']=d.sha((dest/'sample.json').read_bytes());d.save(dest/'plan.json.gz',plan)
 d.save(Path.home()/'Library/Application Support/Artline/backups'/a.m.OP/wave/'plan-and-preimages.json.gz',plan)
 print(wave,len(keep),'new artworks',flush=True)

def prepare():
 write_wave('artefact-reviewed','artefact-delivery',HOLDS,NOTES)
 write_wave('missing-authorities-reviewed','wikidata-reviewed',{'Q94657450':'Braque still-life creator/date comparison remains unresolved; do not create until individually compared with existing versions.'})

def apply_artefact():
 assert d.load(RUN/'backups.json')['production']['status']=='SUCCESSFUL'
 a.configure('artefact-delivery').apply()

def duplicate_identifier():
 delivery=a.configure('artefact-delivery');plan=d.load(RUN/'waves/artefact-delivery/plan.json.gz');receipt=d.load(RUN/'waves/artefact-delivery/applied.json')
 assert receipt['plan_sha256']==d.sha((RUN/'waves/artefact-delivery/plan.json.gz').read_bytes())
 row=next(r for r in plan['records']if r['source_record_id']=='5952628a5a93481c74b378c9');other=row['raw_source_record']['duplicate_native_source'];a.check_body(row,{});a.check_body(other,{})
 assert row['museum']['id']==other['museum']['id'] and row['facts']['first']==other['facts']['first']==1918
 assert row['facts']['creator_label']==other['facts']['creator_label']=='Stanislav Zhukovsky'
 with delivery.connect(readonly=False)as db,db.transaction():
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  old=db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=%s FOR UPDATE',(row['artwork_id'],)).fetchone()['v']
  assert old['current_institution_id']==row['museum']['id'] and old['status']=='review' and old['title']==row['facts']['title']
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme='artefact-object' AND external_id=%s",(other['source_record_id'],)).fetchone()
  assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=%s",(other['facts']['source_url'],)).fetchone()
  # One external identifier per scheme/entity is enforced by the catalogue.
  # The second official record is a citation, which native identity discovery
  # also indexes by exact source URL. No invented provider scheme is created.
  preimage=delivery.BACKUP/'duplicate-source-citation-preimage.json'
  if preimage.exists():assert d.load(preimage)['artwork']==old
  else:d.save(preimage,dict(at=d.now(),artwork=old,citation=None,secondary_source=other))
  source_id=db.execute('SELECT id::text FROM sources WHERE slug=%s',(delivery.OP,)).fetchone()['id']
  new=dict(id=delivery.uid('secondary-citation/'+row['artwork_id']),entity_type='artwork',entity_id=row['artwork_id'],field_name='additional_native_object_identity',source_record_id=other['source_record_id'],source_url=other['facts']['source_url'],source_id=source_id,retrieved_at=other['source_receipt']['retrieved_at'],created_by=delivery.ACTOR,evidence_note=json.dumps(dict(basis=HOLDS[other['source_record_id']],source=other,primary_source_id=row['source_record_id']),ensure_ascii=False))
  delivery.insert(db,'citations',new)
  assert db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=%s',(row['artwork_id'],)).fetchone()['v']==old
 d.save(RUN/'waves/artefact-delivery/secondary-source-applied.json',dict(at=d.now(),citation=new,basis=HOLDS[other['source_record_id']],prior_attempt='Second external identifier was rolled back by the one-identifier-per-scheme constraint; retained the second native identity as an exact-source-URL citation.'))
 print('Attached second source identity to the same Zhukovsky artwork',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();globals()[x.phase]()
