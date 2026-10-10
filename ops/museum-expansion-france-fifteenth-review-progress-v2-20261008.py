"""Freeze the completed individual first review; no catalogue mutation."""
import hashlib, importlib.util, json, runpy
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-fifteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
f=i.f;m=f.m;RUN=f.RUN
def main():
 prior=RUN/'review-progress-checkpoint-002.json';cp=m.load(prior)
 assert f.ref(prior)['sha256']=='0db7aac92654b9a71ae5d4d70dfded8d6c48bb1ea7eea4c4028bf918e465249b'
 for dep in cp['references']:f.checked(dep)
 for dep in cp['external_references']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 dest=RUN/'review-progress-checkpoint-003.json';snapshot=RUN/'working-notes-through-650-001.py';decisions=RUN/'provisional-decisions-002.json.gz'
 assert not any(p.exists() for p in [dest,snapshot,decisions])
 working=Path(__file__).with_name('museum-expansion-france-fifteenth-working-notes-20261008.py');notes=runpy.run_path(str(working))
 assert set(notes['SOURCE_NOTES']).isdisjoint(notes['HOLDS']) and set(notes['SOURCE_NOTES'])|set(notes['HOLDS'])==set(range(1,651))
 initial=m.load(RUN/'initial-scope-001.json.gz')
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'];counts=i.counts(db);assert counts==initial['counts']
 snapshot.write_bytes(working.read_bytes())
 rows=m.load(RUN/'native-candidates-001.json.gz')['rows']
 out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes['SOURCE_NOTES'] else 'editorial_hold',basis=notes['SOURCE_NOTES'].get(r['number'],notes['HOLDS'].get(r['number'])),specific_pending=notes['PENDING'].get(r['number']),required_creator_qualification=notes['NATIVE_QUALIFIED'].get(r['number'],notes['QUALIFIED'].get(r['number']))) for r in rows]
 m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(RUN/'native-candidates-001.json.gz'),database_writes=0,policy='Individual source review complete. Supplemental identity and physical-unit questions remain; provisional support is not an import approval.'))
 paths={p for p in RUN.rglob('*') if p.is_file() and p.name!='README.md'}|{Path(__file__).resolve()}
 m.save(dest,dict(at=m.now(),state='progress_not_delivered',goal_complete=False,database_writes=0,new_additions=0,reviewed_objects=650,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),remaining_individual_reviews=0,pending_specific_questions=len(notes['PENDING']),native_creator_qualifications=len(notes['NATIVE_QUALIFIED']),protected_initial_records=len(initial['scoped_ids']),initial_scope_unchanged=True,counts=counts,previous_checkpoint=f.ref(prior),references=[f.ref(p) for p in sorted(paths)],external_references=cp['external_references'],pending_work=['Supplemental title, former-maker, native-URL, historical/related-inventory identity scope.', 'Resolve remaining physical units and sparse primary comparators; preserve holds where evidence is insufficient.', 'Prepare and apply only final supported records with backup, exact readback and zero-write replay.', 'Continue all-museum 100-200 objective.'],policy='Does not pin its own live output log. Prior checkpoints and source captures remain unchanged.'))
 print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=650,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),database_writes=0)),flush=True)
if __name__=='__main__':main()
