#!/usr/bin/env python3
"""Verify the47th campaign wave and intentionally supersede backed-up status documents."""
import csv,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-hamburg-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def main():
 priorpath=a.RUN/'research-checkpoint-001.json';assert hashlib.sha256(priorpath.read_bytes()).hexdigest()=='c7196c29913fe7ca1f659de5aa8f9387457ea32c6815cb0f7fd604599506463e'
 prior=m.load(priorpath);assert len(prior['artifacts'])==6571
 for ref in prior['artifacts']:a.checked_reference(ref)
 other=prior['other_job_status_reference'];a.checked_reference(other)
 summary=m.load(m.RUN/'verification-after-wave-47.json');minimum=m.load(a.RUN/'minimum-100-verification.json');plan,digest=a.validate_plan()
 assert summary['verified_new_artworks']==5006 and summary['verified_existing_artworks_linked']==765
 assert summary['institutions_with_new_records_or_reconciled_holdings']==159 and summary['source_pass_museums']==342 and summary['source_pass_institutions']==343
 assert summary['after']['museums_below_100']==1200 and summary['after']['museums_below_200']==1290
 assert minimum['current_counts']==dict(linked=108,eligible=108) and minimum['verified_new_records']==84 and minimum['plan_sha256']==digest
 with m.connect() as db:assert a.verify(db,plan,digest)=={k:v for k,v in minimum.items() if k not in ['at','plan_sha256']}
 counts={}
 for name,n in [('added-artworks-after-wave-47.csv',5006),('reconciled-artworks-after-wave-47.csv',765),('museum-coverage-after-wave-47.csv',1491),('gac-date-enrichments-after-wave-47.csv',6)]:
  with (m.RUN/name).open(newline='') as f:rows=list(csv.DictReader(f))
  assert len(rows)==n;counts[name]=n
  if name.startswith('added-artworks-'):assert len({r['artwork_id'] for r in rows})==n and sum(r['museum_slug']=='hamburger-kunsthalle' for r in rows)==84
  if name.startswith('museum-coverage-'):
   assert sum(int(r['added_this_campaign']) for r in rows)==5006 and sum(int(r['existing_artworks_linked_this_campaign']) for r in rows)==765
 all_log=Path('/tmp/artline-museum-tests-20261007-hamburg.log').read_text();local_log=Path('/tmp/artline-hamburg-final-tests-20261007.log').read_text();replay=Path('/tmp/artline-hamburg-replay-20261007.log').read_text()
 assert re.search(r'Ran 731 tests in [\d.]+s\n\nOK\n$',all_log) and re.search(r'Ran 35 tests in [\d.]+s\n\nOK\n$',local_log) and 'zero inserts' in replay
 root=m.RUN/'README.md';local=a.RUN/'README.md';old_root=root.read_text();old_local=local.read_text();assert not (a.RUN/'delivery-checkpoint-001.json').exists()
 text=old_root
 for before,after in [('after-wave-46','after-wave-47'),('4,922','5,006'),('across 155 local museums','across 156 local museums'),('expand 158 institutions','expand 159 institutions'),('1,201','1,200'),('106,470','106,394'),('232,384','232,300'),('110,329','110,253'),('238,371','238,287'),('**156 collections**','**157 collections**'),('All 50 import batches','All 51 import batches'),('The 696 offline policy tests','The 731 offline policy tests'),('covered 341 museums','covered 342 museums'),('Yale University Art Gallery and 17 Italian museums','Yale University Art Gallery, Hamburger Kunsthalle and 17 Italian museums'),('institution total to 342','institution total to 343')]:
  assert before in text,before;text=text.replace(before,after)
 row='| Yale University Art Gallery — official LUX metadata | 99 | 1 |';assert row in text;text=text.replace(row,row+'\n| Hamburger Kunsthalle — reviewed Wikidata and public source evidence | 84 | 1 |')
 row='| Yale University Art Gallery | 34 → 133 | 30 → 129 |';assert row in text;text=text.replace(row,row+'\n| Hamburger Kunsthalle | 24 → 108 | 24 → 108 |')
 text+='''

## Hamburger Kunsthalle additions

The [Hamburg pass](native/hamburg/README.md) adds **84 eligible review records**, taking the museum from 24 to **108 linked and eligible artworks**. All 25 previously associated records and 28 citations remain unchanged. Replay inserted zero rows. Another 92 eligible artworks are needed for the preferred 200 target.

Bounded Wikidata discovery captured 260 distinct artwork entities and retained 143 source candidates. Object/version review approved 84; the follow-up queue keeps 117 source holds, 19 existing-identity reconciliations and 40 editorial holds. The 23 official collection captions comprise four corroborations of selected works and 19 separate follow-ups, not another 23 added objects. Original claims, qualifiers, unknowns, rights and source references remain evidence. Independent public references resolve two erroneous dimensions, and Kirchner's 1926 reworking remains explicit. The denied native catalogue was not bypassed. All 35 Hamburg checks passed within 731 campaign tests; the successor report revalidates 51 addition batches and preserves the 765 separate existing-work reconciliations.
'''
 local_text='''# Hamburger Kunsthalle — 84 additions verified, 7 October 2026

The museum now has **108 linked artworks with eligible creation dates**, up from 24. The [pinned plan](hamburg-reviewed-additions-001-plan.json.gz) added **84 real local review records** and their source-backed holding assertions. All 25 previously associated records, 28 citations and existing relationships remain unchanged. No images, painter links, publication or current-display claims were added. [Readback verification](minimum-100-verification.json) checks every inserted field and source record; replay inserted zero rows. Another **92 eligible artworks** are needed for the preferred 200 target.

Two bounded Wikidata index captures supplied 260 distinct objects. The [source triage](wikidata-candidates-002.json.gz) retained 143 candidates and 117 source holds. The [explicit editorial selection](editorial-reviewed-001.json.gz) approves 84 additions at 80% editorial museum confidence, which is not a calibrated probability. All original Wikidata claims, ranks, qualifiers and references are preserved. Its unfetched native-catalogue URLs remain references, not claims of native verification. Of the additions, 68 have known inventories; unknown inventories, materials and dimensions remain null where unsupported.

The [follow-up queue](followup-queue-001.json.gz) contains 117 source holds, 19 existing-identity reconciliations, 40 editorial holds, 19 official-caption follow-ups and four corroborating captions. Those 199 queue rows are evidence records, not a count of distinct unadded physical artworks. Existing Calderon, Runge and Francke identities must be reconciled before adding or linking them. Close-sized Waldmüller, Abildgaard, Bredael and Avercamp versions remain held. Broad creation ranges that may reflect artist activity or lifespan require object-specific evidence. The whole Grabow altar caption and its component-size measurements remain unresolved.

The [official department captions](main-site-leads-001.json.gz) independently corroborate the selected Liebermann hotel terrace, Klee viaducts, Beckmann Odysseus and Kirchner Painter and Model. [Captured independent public references](supplemental-public-pages-003.json.gz) resolve Beckmann's dimensions to 150 × 115.5 cm using catalogue raisonné646/inventory2887, and Anita Rée's half-nude dimensions to 66 × 53.5 cm using Kulturstiftung's caption. The conflicting Wikidata values and Beckmann's conflicting department caption are retained. Kirchner's source “1910 (überarbeitet 1926)” is preserved with a1910–1926creation/reworking envelope, not silently reduced to1910. Wasmann's source1930–1931date conflicts with the official artist lifespan1805–1886and remains held without a guessed correction.

The separate native online catalogue returned Anubis access denial. No challenge bypass or alternate technical route into that catalogue was attempted. Four accessible museum collection pages and selected independent public references supplied context. The Wanderer caption retains its explicit permanent-loan credit. The DDB reference associated with WikidataKerstingQ50110119currently describes the Berlin work A I931,circa1812,53.5×41cm; it is not Hamburg holding proof. Museum connection never establishes current display, custody or legal ownership.

All **35 Hamburg tests** and the **731-test campaign suite** passed without database fixtures. The [wave47report](../../verification-after-wave-47.json) revalidates51addition batches. Its first read-only report attempt exceeded the filesystem filename limit because inherited labels grew too long; the retained failure receipt documents this and the successful report uses a shorter root. Catalogue writes were unaffected. The campaign now totals **5,006 new artworks and765existing-work holding reconciliations**, kept separate from the unrelated minimum100job.
'''
 backups=[]
 for p,old,new,name in [(root,old_root,text,'hamburg-root-readme-before-001.json.gz'),(local,old_local,local_text,'hamburg-local-readme-before-001.json.gz')]:
  backup=m.BACKUP/name;assert not backup.exists();oldhash=hashlib.sha256(p.read_bytes()).hexdigest();m.save(backup,dict(at=m.now(),path=str(p),sha256=oldhash,text=old));p.write_text(new)
  backups.append(dict(path=str(p.relative_to(m.ROOT)),before_sha256=oldhash,after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest()))
 m.save(a.RUN/'validation-001.json',dict(at=m.now(),database_test_fixtures=False,tests_passed=731,hamburg_tests_passed=35,all_command="python -B -m unittest discover -s ops -p 'test_museum_expansion_*.py'",all_output=all_log,local_output=local_log,apply_output=Path('/tmp/artline-hamburg-apply-20261007.log').read_text(),replay_output=replay,report_output=Path('/tmp/artline-hamburg-report-002-20261007.log').read_text(),csv_counts=counts,limitation='Offline policy/evidence tests and real read-only verification; not representative ten-million-row load testing.'))
 m.save(a.RUN/'prior-checkpoint-verification-002.json',dict(at=m.now(),prior_checkpoint=a.reference(priorpath),prior_artifacts_verified=6571,intentional_supersessions=backups,other_job_status_reference=other,other_job_totals_separate=True))
 superseded={b['path']:b for b in backups};refs={}
 for ref in prior['artifacts']:
  p=m.ROOT/ref['path']
  if ref['path'] in superseded:
   b=superseded[ref['path']];assert ref['sha256']==b['before_sha256'];assert hashlib.sha256(m.load(Path(b['backup_path']))['text'].encode()).hexdigest()==b['before_sha256'];refs[ref['path']]=a.reference(p)
  else:a.checked_reference(ref);refs[ref['path']]=ref
 paths=[priorpath]+[p for root in (m.RUN/'native').glob('hamburg*') if root.is_dir() for p in root.rglob('*') if p.is_file()]+list((m.ROOT/'ops').glob('*hamburg*20261007.py'))+[p for p in m.RUN.glob('*after-wave-47*') if p.is_file()]+[p for p in m.RUN.glob('*h47*') if p.is_file()]
 for p in paths:refs[str(p.relative_to(m.ROOT))]=a.reference(p)
 for ref in refs.values():a.checked_reference(ref)
 result=dict(at=m.now(),local_only=True,goal_complete=False,campaign_new_artworks=5006,campaign_existing_links=765,institutions_with_new_records_or_reconciled_holdings=159,source_pass_museums=342,source_pass_institutions=343,hamburg_added=84,hamburg_counts=minimum['current_counts'],hamburg_verification=minimum,remaining_to_preferred_200=92,queue_rows=199,museums_below_100=1200,tests_passed=731,hamburg_tests_passed=35,plan_sha256=digest,csv_counts_verified=counts,artifacts=sorted(refs.values(),key=lambda x:x['path']),prior_checkpoint_reference=a.reference(priorpath),prior_artifacts_verified=6569,intentional_supersessions=backups,other_job_status_reference=other,other_job_totals_separate=True,next_work='Continue museum coverage. Madrid Thyssen-Bornemisza fresh scope has30linked/28eligible;32official masterpiece cards include31pre1971research leads and one1971exclusion. Collection search403is retained without bypass. Carmen leased collection and Málaga institution remain separate. Hamburg needs92more for200and has version/date reconciliation leads.',notes='All51addition batches revalidated through report chain; all10prior holding/date operations preserved. No production changes,images,publication,deployment or commits. Thyssen research is not counted as a completed source pass or additions.')
 out=a.RUN/'delivery-checkpoint-001.json';m.save(out,result);print(json.dumps(dict(artifacts=len(refs),checkpoint=a.reference(out),campaign_new_artworks=5006,hamburg_counts=minimum['current_counts'],museums_below_100=1200)))
if __name__=='__main__':main()
