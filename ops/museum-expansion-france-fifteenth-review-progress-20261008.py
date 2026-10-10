"""Freeze source research and 360 provisional object reviews; no catalogue mutation."""
import hashlib,importlib.util,json,runpy
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-fifteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
f=i.f;m=f.m;RUN=f.RUN
def main():
 dest=RUN/'review-progress-checkpoint-001.json';snapshot=RUN/'working-notes-through-360-001.py';decisions=RUN/'provisional-decisions-001.json.gz'
 assert not any(p.exists() for p in [dest,snapshot,decisions])
 working=Path(__file__).with_name('museum-expansion-france-fifteenth-working-notes-20261008.py');notes=runpy.run_path(str(working))
 assert set(notes['SOURCE_NOTES']).isdisjoint(notes['HOLDS']) and set(notes['SOURCE_NOTES'])|set(notes['HOLDS'])==set(range(1,361))
 candidates=RUN/'native-candidates-001.json.gz';rows=m.load(candidates)['rows'];assert len(rows)==650
 for dep in m.load(candidates)['dependencies']+[m.load(candidates)['parser_reference']]:f.checked(dep)
 for p in sorted((RUN/'current-001').glob('batch-*.json.gz')):f.body(m.load(p))
 native=m.load(RUN/'paris-object-context-checked-001.json.gz');assert len(native['rows'])==150 and all(v['inventory_equal'] for v in native['rows'])
 for dep in native['dependencies']:f.checked(dep)
 initial=m.load(RUN/'initial-scope-001.json.gz')
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'];counts=i.counts(db);assert counts==initial['counts']
 snapshot.write_bytes(working.read_bytes())
 out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes['SOURCE_NOTES'] else 'editorial_hold',basis=notes['SOURCE_NOTES'].get(r['number'],notes['HOLDS'].get(r['number'])),specific_pending=notes['PENDING'].get(r['number']),required_creator_qualification=notes['QUALIFIED'].get(r['number'])) for r in rows[:360]]
 m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(candidates),database_writes=0,policy='Initial individual source and comparison review only. Native role reconciliation, supplemental identity and within-batch physical-unit decisions remain before any import.'))
 paths={p for p in RUN.rglob('*') if p.is_file() and p.name!='README.md'}
 paths|={p.resolve() for p in (m.ROOT/'ops').glob('*france*fifteenth*20261008.py') if p!=working}
 prior=m.RUN/'native/france-fourteenth-minimum-20261008/delivery-checkpoint-001.json';paths|={prior,m.ROOT/'AGENTS.md'}
 logs=sorted(Path('/Users/vadimdulub/Library/Logs').glob('artline-france-fifteenth-*-20261008.log'))
 ix=m.load(RUN/'native-identity-001.json.gz');cx=m.load(RUN/'identity-citations-001.json.gz')
 m.save(dest,dict(at=m.now(),state='progress_not_delivered',goal_complete=False,database_writes=0,new_additions=0,reviewed_objects=360,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),remaining_individual_reviews=290,source_candidates=650,current_source_records=650,checked_native_object_pages=150,identity_scope_artworks=len(ix['state']['artworks']),identity_citations=len(cx['citations']),protected_initial_records=len(initial['scoped_ids']),initial_scope_unchanged=True,counts=counts,tests_passed=29,references=[f.ref(p) for p in sorted(paths)],external_references=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in logs],source_access_holds=[dict(url='https://www.ville-bourges.fr/site/autour-des-indelicats',status=403,policy='No retry or bypass; independent collection catalogue and auction format resources captured separately.')],pending_work=['Review Cognacq-Jay361-510 using verified native detail pages; preserve current/former/after creator relationships.', 'Review Ecouen511-650 with precise state assignment/deposit and Cluny/Louvre provenance preserved.', 'Resolve specific pending comparisons, former makers, translated short titles and native canonical URLs with a fresh read-only identity scope.', 'Reconcile within-batch object units and parenthetic accession subnumbers; shared physical sheets cannot count twice.', 'Build final review plan only after individual decisions and guards; apply authorised supported local review additions, exact readback and zero-write replay.', 'Continue all-museum100-200 objective; this preparation does not complete it.'],policy='Research progress only. Previous delivery remains frozen. No images, publication, artist authority, existing metadata or current-display changes.'))
 print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=360,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),remaining=290,native_pages=150,baseline_records_unchanged=len(initial['scoped_ids']),database_writes=0)),flush=True)
if __name__=='__main__':main()
