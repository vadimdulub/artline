#!/usr/bin/env python3
"""Verify wave48, preserve status-document preimages, and pin the delivery."""
import csv,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-thyssen-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;RUN=a.RUN
def main():
 priorpath=RUN/'research-checkpoint-001.json';assert hashlib.sha256(priorpath.read_bytes()).hexdigest()=='6b5610a12c4a03c446513870e733f3bcfa6e20ed9e05bc481b4444fc2f404b9e'
 prior=m.load(priorpath);assert len(prior['artifacts'])==6815
 for ref in prior['artifacts']:a.checked_reference(ref)
 other=prior['other_job_status_reference'];a.checked_reference(other)
 summary=m.load(m.RUN/'verification-after-wave-48.json');plan,digest=a.validate_plan();assert a.PLAN.name=='thyssen-reviewed-additions-001-plan-003.json.gz' and m.load(RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 assert summary['verified_new_artworks']==5178 and summary['verified_existing_artworks_linked']==765
 assert summary['institutions_with_new_records_or_reconciled_holdings']==160 and summary['source_pass_museums']==343 and summary['source_pass_institutions']==344
 assert summary['after']['museums_below_100']==1199 and summary['after']['museums_below_200']==1289
 with m.connect() as db:verified=a.verify(db,plan,digest)
 assert verified['current_counts']==dict(linked=202,eligible=200) and verified['verified_new_records']==172 and verified['existing_artworks_unchanged']==32
 counts={}
 for name,total in [('added-artworks-after-wave-48.csv',5178),('reconciled-artworks-after-wave-48.csv',765),('museum-coverage-after-wave-48.csv',1491),('gac-date-enrichments-after-wave-48.csv',6)]:
  with (m.RUN/name).open(newline='') as stream:rows=list(csv.DictReader(stream))
  assert len(rows)==total;counts[name]=total
  if name.startswith('added-artworks-'):assert len({r['artwork_id'] for r in rows})==total and sum(r['museum_slug']=='museo-thyssen-bornemisza' for r in rows)==172
  if name.startswith('museum-coverage-'):assert sum(int(r['added_this_campaign']) for r in rows)==5178 and sum(int(r['existing_artworks_linked_this_campaign']) for r in rows)==765
 log=Path('/tmp/artline-museum-campaign-tests-thyssen-003-20261007.log').read_text();replay=Path('/tmp/artline-thyssen-replay-20261007.log').read_text()
 assert re.search(r'Ran 762 tests in [\d.]+s\n\nOK\n$',log) and 'zero inserts' in replay
 root=m.RUN/'README.md';local=RUN/'README.md';old_root=root.read_text();old_local=local.read_text();assert not (RUN/'delivery-checkpoint-001.json').exists()
 text=old_root
 for before,after in [('after-wave-47','after-wave-48'),('5,006','5,178'),('across 156 local museums','across 157 local museums'),('expand 159 institutions','expand 160 institutions'),('1,200','1,199'),('1,290','1,289'),('106,394','106,324'),('232,300','232,130'),('110,253','110,181'),('238,287','238,115'),('**157 collections**','**158 collections**'),('All 51 import batches','All 52 import batches'),('The 731 offline policy tests','The 762 offline policy tests'),('covered 342 museums','covered 343 museums'),('Hamburger Kunsthalle and 17 Italian museums','Hamburger Kunsthalle, Museo Nacional Thyssen-Bornemisza and 17 Italian museums'),('institution total to 343','institution total to 344')]:
  assert before in text,before;text=text.replace(before,after)
 row='| Hamburger Kunsthalle — reviewed Wikidata and public source evidence | 84 | 1 |';assert row in text;text=text.replace(row,row+'\n| Museo Nacional Thyssen-Bornemisza — official catalogue metadata | 172 | 1 |')
 row='| Hamburger Kunsthalle | 24 → 108 | 24 → 108 |';assert row in text;text=text.replace(row,row+'\n| Museo Nacional Thyssen-Bornemisza | 30 → 202 | 28 → 200 |')
 text+='''

## Museo Nacional Thyssen-Bornemisza additions

The [Madrid Thyssen pass](native/thyssen/README.md) adds **172 eligible review records**, taking the museum from 30 linked records and 28 eligible dates to **202 linked records and 200 eligible dates**. All 32 previously associated records and their relationships remain unchanged; replay inserted zero rows. The preferred target of 200 eligible records is reached for this museum.

The selection follows 267 public artwork pages linked from the museum's masterpieces page and bounded related-work cards. Of 209 source candidates, 172 were approved; 15 existing identities and 22 unresolved physical versions remain held, along with 58 source-credit holds. Loans, Barcelona deposits and the separate Málaga Carmen Thyssen museum are not merged into Madrid holdings. A Byzantine anonymous triptych and a grisaille diptych each count once, as does a sheet with a verso study. Qualified workshop/joint creators, literal dates, physical facts, unknown rights labels and original HTML remain evidence. All 31 Thyssen checks passed within 762 campaign tests; the successor report revalidates 52 addition batches and preserves 765 existing-work reconciliations.
'''
 local_text=f'''# Museo Nacional Thyssen-Bornemisza — 172 additions verified, 7 October 2026

The Madrid museum now has **202 linked artworks, including 200 with eligible creation dates**, up from 30 linked / 28 eligible. The [pinned applied plan](thyssen-reviewed-additions-001-plan-003.json.gz) adds 172 real local catalogue records in review. The preferred target of 200 eligible records is reached. [Readback verification](preferred-200-verification.json) confirms every inserted field, identifier, citation and holding assertion, and preserves all 32 older associated records and {verified['old_citations_unchanged']} citations. Replay inserted zero rows. No images, painter links, publication or current-display claims were added.

The [editorial review](editorial-reviewed-001.json.gz) accounts for 267 selected native artwork pages: 172 additions, 15 existing identities held for reconciliation, 22 version holds and 58 source-credit holds. Museum assignments have 90% editorial confidence, not a calibrated probability. The [source candidates](native-candidates-002.json.gz) preserve all literal titles, qualified creators, source creation dates, inventories, media, dimensions, narrative, credits, parsed unknowns and raw HTML. Native artist identities were used for comparison, without creating painter authorities. Eleven bounded Wikidata URL matches provide secondary translation/ID leads only; no Wikidata metadata replaces the native facts.

The independently accessible public masterpieces page supplied 31 pre-1971 leads and one 1971 exclusion. Bounded related-work selections captured 105 and 131 additional pages. Every object has a hashed card-to-detail source chain. The permanent-collection search returned 403 and was not bypassed. Separate comparison captures from the Met were rate-limited and Toledo/MoMA returned 403; failures and earlier web-tool summaries are retained as such. The independently accessible Art Institute Homer essay was captured successfully. Source access failures never become native verification claims.

The anonymous Venetian triptych retains its explicitly documented Byzantine iconography and historical attributions; it counts once. Van Eyck's two-panel grisaille diptych likewise counts once. Grosz's recto/verso sheet and Beurer's portrait panel each receive one record. Pater's near-identical Met title is a separately documented pendant; Kupka I and II are explicitly distinguished by the museum despite equal sizes. Picasso's dedicated first-edition print is distinguished from 1913 impressions. Unknown normalized types for Work on paper and Relief remain unknown, with their literal source forms preserved in citations. The restricted catalogue object-form field remains null for these unmapped labels.

The 95 held source objects remain research evidence, not new holdings. They include Barcelona MNAC deposits, bare Carmen/private credits, duplicate reverse sides, translated existing titles and close-sized physical versions. Dalí's native 1947 date and the existing 1944 date are both retained; no duplicate was added and no existing date rewritten. Carmen Thyssen Museum Málaga remains a separate institution. Holding evidence does not establish legal title, present custody, a room or current display.

All **31 Thyssen checks** passed in the **762-test campaign suite**, without test databases or catalogue fixtures. The [first supersession](plan-supersession-001.json) retains an unapplied plan and a test correction that preserves an unknown rights label. The [second supersession](plan-supersession-002.json) and [rollback check](failed-plan-002-rollback-verification.json) document a rejected source-form value and complete transaction rollback. The third plan preserves original facts separately and stores unsupported object-form labels as null, without inventing a subtype or changing the schema. Backups are under the configured Artline Library directory.

The [wave 48 report](../../verification-after-wave-48.json) revalidates 52 addition batches and all prior holding/date operations. This campaign now totals 5,178 new artworks and 765 existing-work museum links, separate from the unrelated minimum-100 job. The overall museum goal remains unfinished.
'''
 backups=[]
 for path,old,new,name in [(root,old_root,text,'thyssen-root-readme-before-001.json.gz'),(local,old_local,local_text,'thyssen-local-readme-before-001.json.gz')]:
  backup=m.BACKUP/name;assert not backup.exists();oldsha=hashlib.sha256(path.read_bytes()).hexdigest();m.save(backup,dict(at=m.now(),path=str(path),sha256=oldsha,text=old));path.write_text(new)
  backups.append(dict(path=str(path.relative_to(m.ROOT)),before_sha256=oldsha,after_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest()))
 m.save(RUN/'preferred-200-verification.json',dict(at=m.now(),plan_sha256=digest,**verified))
 logs={p.name:p.read_text() for p in Path('/tmp').glob('artline-thyssen*20261007.log') if p.is_file()}
 m.save(RUN/'validation-001.json',dict(at=m.now(),database_test_fixtures=False,tests_passed=762,thyssen_tests_passed=31,all_command="python -B -m unittest discover -s ops -p 'test_museum_expansion*py'",all_output=log,retained_logs=logs,csv_counts=counts,limitation='Offline policy/evidence checks and real catalogue readback; not representative ten-million-row load testing. Failed direct HTTP responses are retained; source text available only through earlier web discovery is labelled.'))
 m.save(RUN/'prior-checkpoint-verification-002.json',dict(at=m.now(),prior_checkpoint=a.reference(priorpath),prior_artifacts_verified=6815,intentional_supersessions=backups,other_job_status_reference=other,other_job_totals_separate=True))
 superseded={b['path']:b for b in backups};refs={}
 for ref in prior['artifacts']:
  path=m.ROOT/ref['path']
  if ref['path'] in superseded:
   b=superseded[ref['path']];assert ref['sha256']==b['before_sha256'];assert hashlib.sha256(m.load(Path(b['backup_path']))['text'].encode()).hexdigest()==b['before_sha256'];refs[ref['path']]=a.reference(path)
  else:a.checked_reference(ref);refs[ref['path']]=ref
 paths=[priorpath]+[p for root in (m.RUN/'native').glob('thyssen*') if root.is_dir() for p in root.rglob('*') if p.is_file()]+list((m.ROOT/'ops').glob('*thyssen*20261007.py'))+[p for p in m.RUN.glob('*after-wave-48*') if p.is_file()]+[p for p in m.RUN.glob('*t48*') if p.is_file()]
 paths+=[a.checked_reference(ref) for ref in plan['evidence']]
 for path in paths:refs[str(path.relative_to(m.ROOT))]=a.reference(path)
 for ref in refs.values():a.checked_reference(ref)
 result=dict(at=m.now(),local_only=True,goal_complete=False,campaign_new_artworks=5178,campaign_existing_links=765,institutions_with_new_records_or_reconciled_holdings=160,source_pass_museums=343,source_pass_institutions=344,thyssen_added=172,thyssen_counts=verified['current_counts'],thyssen_verification=verified,remaining_to_preferred_200=0,held_objects=95,museums_below_100=1199,tests_passed=762,thyssen_tests_passed=31,plan_sha256=digest,csv_counts_verified=counts,artifacts=sorted(refs.values(),key=lambda x:x['path']),prior_checkpoint_reference=a.reference(priorpath),prior_artifacts_verified=6815,intentional_supersessions=backups,other_job_status_reference=other,other_job_totals_separate=True,next_work='Continue museum-by-museum review from the coverage register, prioritizing museums below 100 and preserving held identity/provenance evidence. Thyssen preferred 200 eligible reached; held cases remain separate reconciliation work.',notes='All 52 addition batches and 10 prior holding/date operations revalidated. No production changes,images,publication,deployment,commits or database fixtures.')
 out=RUN/'delivery-checkpoint-001.json';m.save(out,result);print(json.dumps(dict(artifacts=len(refs),checkpoint=a.reference(out),campaign_new_artworks=5178,thyssen_counts=verified['current_counts'],museums_below_100=1199)),flush=True)
if __name__=='__main__':main()
