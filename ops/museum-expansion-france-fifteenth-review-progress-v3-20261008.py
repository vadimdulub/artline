"""Freeze supplemental identity progress with source and unchanged-DB verification."""
import gzip,hashlib,importlib.util,json,runpy
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-fifteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
f=i.f;m=f.m;RUN=f.RUN
def main():
 prior=RUN/'review-progress-checkpoint-003.json';cp=m.load(prior);assert f.ref(prior)['sha256']=='46ab50784308bc81329c5b5a643f70332e58eaac04f6a4dfe628b734b0e39582'
 for dep in cp['references']:f.checked(dep)
 for dep in cp['external_references']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
 dest=RUN/'review-progress-checkpoint-004.json';snapshot=RUN/'working-notes-supplement-through-397-001.py';decisions=RUN/'provisional-decisions-003.json.gz'
 assert not any(p.exists() for p in [dest,snapshot,decisions])
 working=Path(__file__).with_name('museum-expansion-france-fifteenth-working-notes-20261008.py');notes=runpy.run_path(str(working));assert set(notes['SOURCE_NOTES']).isdisjoint(notes['HOLDS']) and set(notes['SOURCE_NOTES'])|set(notes['HOLDS'])==set(range(1,651))
 old=m.load(RUN/'native-identity-001.json.gz')['comparisons'];new=m.load(RUN/'native-identity-002.json.gz')['comparisons'];coverage=[]
 for num,(a,b) in enumerate(zip(old,new),1):
  seen={r['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for r in a[k]}
  delta=sorted({r['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits'] for r in b[k]}-seen)
  needed=bool(delta or b['object_alias_hits'] or b['related_inventory_hits'])
  if num<=397 and num in notes['SOURCE_NOTES'] and needed:assert num in notes['SUPPLEMENTAL_REVIEW'],num
  coverage.append(dict(number=num,new_comparison_ids=delta,supplemental_review_needed=needed,supplemental_basis=notes['SUPPLEMENTAL_REVIEW'].get(num),specific_pending=notes['PENDING'].get(num),held=num in notes['HOLDS']))
 native=m.load(RUN/'paris-comparators-checked-001.json.gz');assert len(native['rows'])==9
 for row in native['rows']:
  receipt=m.load(f.checked(row['receipt_reference']));raw=gzip.decompress(f.checked(row['body_reference']).read_bytes());assert receipt['status']==200 and hashlib.sha256(raw).hexdigest()==receipt['sha256']
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style','noscript']):tag.decompose()
  text=soup.get_text('\n',strip=True);assert text==f.checked(row['text_reference']).read_text()
  assert text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]==row['literal_detail_text']
 validation=m.load(RUN/'identity-recomputed-002.json');assert validation['comparisons_recomputed_equal'] and validation['candidates_reparsed_equal']==650
 initial=m.load(RUN/'initial-scope-001.json.gz')
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'];counts=i.counts(db);assert counts==initial['counts']
 snapshot.write_bytes(working.read_bytes());rows=m.load(RUN/'native-candidates-001.json.gz')['rows']
 out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes['SOURCE_NOTES'] else 'editorial_hold',basis=notes['SOURCE_NOTES'].get(r['number'],notes['HOLDS'].get(r['number'])),supplemental_basis=notes['SUPPLEMENTAL_REVIEW'].get(r['number']),specific_pending=notes['PENDING'].get(r['number']),required_creator_qualification=notes['NATIVE_QUALIFIED'].get(r['number'],notes['QUALIFIED'].get(r['number']))) for r in rows]
 m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(RUN/'native-candidates-001.json.gz'),coverage=coverage,database_writes=0,policy='Supplemental lead review through397, not final import approval. Explicit pending impressions, generic titles and source conflicts remain.'))
 paths={p for p in RUN.rglob('*') if p.is_file() and p.name!='README.md'}|{p.resolve() for p in (m.ROOT/'ops').glob('*france*fifteenth*20261008.py') if p!=working}
 ownlog=Path('/Users/vadimdulub/Library/Logs/artline-france-fifteenth-review-progress-004-20261008.log')
 logs=[p for p in sorted(Path('/Users/vadimdulub/Library/Logs').glob('artline-france-fifteenth-*-20261008.log')) if p!=ownlog]
 m.save(dest,dict(at=m.now(),state='progress_not_delivered',goal_complete=False,database_writes=0,new_additions=0,reviewed_objects=650,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),supplemental_lead_review_through=397,supplemental_notes=len(notes['SUPPLEMENTAL_REVIEW']),remaining_supplemental_number_range=[398,650],pending_specific_questions=len(notes['PENDING']),protected_initial_records=len(initial['scoped_ids']),initial_scope_unchanged=True,counts=counts,tests_passed=34,current_national_records=650,candidate_native_pages=150,additional_existing_portrait_pages=9,targeted_municipal_louvre_pages=3,identity_artworks=67824,identity_citations=148704,physical_primary_records=2475,previous_checkpoint=f.ref(prior),references=[f.ref(p) for p in sorted(paths)],external_references=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in logs],pending_work=['Finish supplemental physical comparisons398–650, especially generic portrait titles and English aliases.', 'Resolve remaining same-plate impressions and primary metadata for sparse comparators; retain explicit holds where evidence is insufficient.', 'Complete full generic exact-title audit, within-batch physical groups, historical Louvre OA aliases and qualified native creator labels.', 'Build final reviewed plan, backup, apply supported local review records, verify exact readback and zero-write replay.', 'Continue all-museum100–200 goal.'],policy='Research checkpoint only. Original source fields and previous delivery unchanged. No image, artist-authority, publication or current-display mutation. Own live output log excluded.'))
 print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=650,provisional_supported=len(notes['SOURCE_NOTES']),held=len(notes['HOLDS']),supplemental_through=397,protected_initial_records=len(initial['scoped_ids']),database_writes=0)),flush=True)
if __name__=='__main__':main()
