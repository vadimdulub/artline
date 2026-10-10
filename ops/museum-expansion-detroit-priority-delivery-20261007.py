#!/usr/bin/env python3
"""Pin wave51 and an explicit partial checkpoint of the ongoing native capture."""
import csv,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-detroit-priority-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;RUN=a.RUN
def main():
 out=RUN/'delivery-checkpoint-001.json';assert not out.exists();priorpath=m.RUN/'native/next-samples/delivery-checkpoint-001.json';assert hashlib.sha256(priorpath.read_bytes()).hexdigest()=='c17aac8fd1a0947ad96b076f5a15418e5e0cf1ca9e4b06e77d79c8286f72ba82';prior=m.load(priorpath)
 for ref in prior['artifacts']:a.checked_reference(ref)
 a.checked_reference(prior['other_job_status_reference']);plan,digest=a.validate_plan();assert digest=='1300cfc3605c4d2ccd2ef16b4dec70daaaead11c77a5b35bd1a930ef74b031bf'
 with m.connect() as db:verified=a.verify(db,plan,digest)
 summary=m.load(m.RUN/'verification-after-wave-51.json');assert summary['verified_new_artworks']==5334 and summary['verified_existing_artworks_linked']==765 and summary['source_pass_museums']==348 and summary['institutions_with_new_records_or_reconciled_holdings']==163
 totals={}
 for name,count in [('added-artworks-after-wave-51.csv',5334),('reconciled-artworks-after-wave-51.csv',765),('museum-coverage-after-wave-51.csv',1491),('gac-date-enrichments-after-wave-51.csv',6)]:
  with (m.RUN/name).open(newline='') as f:rows=list(csv.DictReader(f))
  assert len(rows)==count;totals[name]=count
  if name.startswith('added-artworks'):assert len({r['artwork_id'] for r in rows})==count
  if name.startswith('museum-coverage'):assert sum(int(r['added_this_campaign']) for r in rows)==5334 and sum(int(r['existing_artworks_linked_this_campaign']) for r in rows)==765
 testlog=Path('/tmp/artline-museum-campaign-tests-detroit-priority-20261007.log').read_text();assert re.search(r'Ran 811 tests in [\d.]+s\n\nOK\n$',testlog);assert 'zero inserts' in Path('/tmp/artline-detroit-priority-replay-20261007.log').read_text()
 completed=sorted((a.f.RUN/'objects-001').glob('*.json.gz'));captures=[]
 for p in completed:
  x=m.load(p);a.f.d.body(x['capture']);a.checked_reference(x['queue_reference']);captures.append(dict(number=x['number'],source_id=x['index']['source_id'],object_reference=a.reference(p),body_reference=a.reference(m.ROOT/x['capture']['body_path']),receipt_reference=a.reference(a.f.RUN/'captures'/('object-%03d.json'%x['number']))))
 assert len(captures)==len({r['source_id'] for r in captures});ps=subprocess.run(['ps','-axo','pid=,command='],capture_output=True,text=True,check=True).stdout;workers=[line.strip() for line in ps.splitlines() if line.strip().endswith('Python -B ops/museum-expansion-detroit-resume-after-timeout-20261007.py')];assert len(workers)<=1
 errors=[a.reference(p) for p in sorted((a.f.RUN/'errors').glob('*.json'))]
 capture_state=dict(at=m.now(),state='active' if workers else 'stopped_or_complete_requires_receipt_review',worker=workers,tool_session_id=19735 if workers else None,log_path='/tmp/artline-detroit-after-timeout-20261007.log',selected=118,complete_captures=len(captures),latest_completed_number=max(v['number'] for v in captures),added=5,complete_unapproved=len(captures)-5,uncaptured=118-len(captures),unapproved_total=113,errors=errors,captures=captures,policy='Snapshot of completed immutable captures only. Worker may create later files outside this checkpoint. Do not start a second worker or restart a stopped source request blindly. Object5 remains uncaptured; object2 remains held because its location is unknown since1951. Current capture alone is not approval.')
 m.save(a.f.RUN/'capture-checkpoint-001.json',capture_state)
 root=m.RUN/'README.md';before=root.read_text();text=before
 for old,new in [('after-wave-50','after-wave-51'),('5,329','5,334'),('106,222','106,217'),('231,979','231,974'),('110,079','110,074'),('237,964','237,959'),('covered 347 museums','covered 348 museums'),('Saint Louis Art Museum and 17 Italian museums','Saint Louis Art Museum, Museum of Fine Arts Boston and 17 Italian museums'),('institution total to 348','institution total to 349'),('All 54 import batches','All 55 import batches'),('The 799 offline policy tests','The 811 offline policy tests'),('| Detroit Institute of Arts | 0 → 1 | 0 → 1 |','| Detroit Institute of Arts | 0 → 6 | 0 → 6 |')]:assert old in text,old;text=text.replace(old,new)
 marker='| AGO and Detroit — two complete official collection records | 2 | 2 |';assert marker in text;text=text.replace(marker,marker+'\n| Detroit — reviewed Russian and Greek painted panels | 5 | 1 continuation |')
 text+='''

## Detroit Russian and Greek continuation; MFA Boston access hold

The [Detroit priority batch](native/detroit-priority/README.md) adds five paintings: *The Intercession of the Virgin*, *Virgin Annunciate*, *The Creation of the World*, *Saint George and the Dragon* and *Saint Mercurius*. Detroit now has six linked records with eligible creation dates. Its 18 earlier records and 35 citations are unchanged. Russian and Greek cultural labels and the Moscow, Stroganov and Novgorod school labels remain literal object labels. No artist profiles or links were invented.

The source says the *New Testament Trinity* has been unlocated since 1951, so it remains excluded from the current collection additions. *Annunciatory Angel* timed out and remains uncaptured. A qualified *Madonna and Child* needs further version checks. Matching inventories at other museums and similar saint subjects were individually distinguished, including Toledo’s French Saint George panel with superficially similar dimensions. The read-only identity scope covered 274 catalogue records and retained 559 citations.

Detroit’s native continuation resumed after the documented rate-limit cooldown, using one request per 25 seconds at most. A later transport timeout stopped the worker; after review and another wait, other selected objects continued without retrying the failed object or changing transport. The [capture checkpoint](native/detroit-resume/capture-checkpoint-001.json) explicitly separates completed captures from unapproved and uncaptured leads. Further work is ongoing; none of those leads is counted as an addition merely because it was captured.

[MFA Boston](native/mfa/README.md) returned a collection-site robot-verification gate. Its official search guide was readable, and explicitly describes some formerly owned objects and incoming loans in the catalogue. No challenge was bypassed, no artwork was added, and the 15 earlier pending records remain unchanged. This is a new source pass, not an expanded museum.

Wave51 verifies all 55 addition batches and ten previous holding/date operations. All 811 offline checks pass, including 12 new priority-source checks. The two wave50 records are rechecked unchanged by an explicit successor verifier that accounts for the five later Detroit additions when checking museum totals. The overall goal remains unfinished: 1,198 museums still have fewer than 100 linked records.
'''
 backup=m.BACKUP/'detroit-priority-root-readme-before-001.json.gz';assert not backup.exists();oldsha=hashlib.sha256(root.read_bytes()).hexdigest();m.save(backup,dict(at=m.now(),path=str(root),sha256=oldsha,text=before));root.write_text(text);supersession=dict(path=str(root.relative_to(m.ROOT)),before_sha256=oldsha,after_sha256=hashlib.sha256(root.read_bytes()).hexdigest(),backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 docs={
 RUN/'README.md':'''# Detroit priority batch — five additions

Five Russian and Greek paintings were added to the real local catalogue in review, bringing Detroit to six linked, eligible records. The [reviewed plan](detroit-priority-reviewed-additions-001-plan.json.gz) and [verification](verification-001.json) preserve exact source facts, source dates, accession numbers, credits, school/cultural labels and unknown copyright. The 18 earlier artwork records and 35 citations are unchanged. Replay inserts zero records. No new artist authority, painter link, image, publication or current-display claim was created.

The additions are The Intercession of the Virgin (65.300), Virgin Annunciate (39.607), The Creation of the World (23.2), Saint George and the Dragon (38.69) and Saint Mercurius (89.8). Primary source provenance explicitly records gifts, bequests or purchases by Detroit. Museum-specific accession collisions and related subjects were reviewed across 274 catalogue records and 559 citations. The Toledo Saint George panel is French and has a separate Libbey acquisition; similar frame dimensions do not merge it with the Novgorod panel.

New Testament Trinity (43.420) remains held because the source states its location has been unknown since 1951. Annunciatory Angel remains uncaptured after a timeout. School of Fabriano’s Madonna and Child remains held for version checks. Other selected captures are outside this five-record approval.

The campaign now has 5,334 additions and 765 existing-work museum links. All 811 checks pass, including 12 new offline checks. These are source-policy and database-readback checks, not ten-million-row load tests. The goal remains unfinished, with 1,198 canonical museums below 100 linked records. The unrelated minimum-100 job remains separate and unchanged.
''',
 a.f.RUN/'README.md':'''# Detroit native continuation — partial capture

The [checkpoint](capture-checkpoint-001.json) records the exact completed objects, source receipts, worker status and remaining selected queue at this snapshot. Later immutable captures may exist outside that snapshot. Do not start a second worker while session19735 is active. The source cadence is at most one direct request every25seconds; stop on a new source error and inspect its receipt before deciding what can continue.

The first continuation waited more than30minutes after the retained HTTP429. Four object pages succeeded; object5 (Annunciatory Angel) then timed out without an HTTP response. That failure was preserved and not retried. After at least5minutes, the reviewed successor continued to other already-selected public URLs on the same host and transport. No verification challenge or rate limit was bypassed.

Five Russian/Greek objects have since been [added in review](../detroit-priority/README.md). New Testament Trinity is held for its explicitly unknown location since1951. Qualified Fabriano attribution, a small Flemish triptych with former attributions, two companion Florentine panels, former Foppa attribution, and an apparent artist-lifespan creation range remain documented in the preliminary follow-up notes. Use the v2 facts parser for later objects; it also flags creation bounds that match differently formatted artist life dates. Later identity scopes must include historical creator names and Claude Lorrain alongside Claude Gellée.

The pre-addition scope and preliminary identity001/002 files belong to the five-panel batch. Before adding further objects, take a fresh museum scope reflecting six linked artworks and rerun scoped duplicate checks; do not reuse the one-linked-record baseline as if it were current.
''',
 m.RUN/'native/mfa/README.md':'''# Museum of Fine Arts Boston — source access hold

The official European paintings collection index returned a robot-verification page requiring JavaScript. The [original tool result](web-discovery-001.json) is retained; no challenge bypass, alternate transport or object capture was attempted. The official search guide was readable and notes that the catalogue can include former holdings and incoming loans, so catalogue presence alone must not establish a current holding.

No additions or catalogue changes were made. The real local scope has zero linked records and 15 pending artwork associations, all unchanged. Eligible object research remains necessary toward the100–200target; this access failure does not establish a lack of artworks.
'''}
 for p,content in docs.items():assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
 m.save(RUN/'verification-001.json',dict(at=m.now(),plan_sha256=digest,**verified));m.save(RUN/'validation-001.json',dict(at=m.now(),tests_passed=811,new_tests_passed=12,test_database=False,output=testlog,retained_logs={p.name:p.read_text() for p in Path('/tmp').glob('artline-detroit-priority*20261007.log') if p.is_file()},csv_counts=totals))
 m.save(RUN/'prior-checkpoint-verification-001.json',dict(at=m.now(),prior_checkpoint=a.reference(priorpath),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=[supersession],other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True))
 refs={r['path']:(a.reference(root) if r['path']==supersession['path'] else r) for r in prior['artifacts']}
 paths=[priorpath]+[p for directory in [RUN,m.RUN/'native/mfa'] for p in directory.rglob('*') if p.is_file()]+[p for p in a.f.RUN.glob('*') if p.is_file()]+[p for p in (a.f.RUN/'errors').glob('*.json')]+[p for p in (m.ROOT/'ops').glob('*detroit*20261007.py')]+list(m.RUN.glob('*after-wave-51*'))+list(m.RUN.glob('*d51*'))+[a.checked_reference(r) for r in plan['evidence']]
 for row in captures:
  paths += [a.checked_reference(row[k]) for k in ['object_reference','body_reference','receipt_reference']]
 for p in paths:refs[str(p.relative_to(m.ROOT))]=a.reference(p)
 for ref in refs.values():a.checked_reference(ref)
 checkpoint=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5334,campaign_existing_links=765,institutions_with_new_records_or_reconciled_holdings=163,source_pass_museums=348,source_pass_institutions=349,new_additions=5,verification=verified,museums_below_100=1198,detroit_unapproved_queue_entries=113,tests_passed=811,new_tests_passed=12,plan_sha256=digest,csv_counts_verified=totals,artifacts=sorted(refs.values(),key=lambda x:x['path']),prior_checkpoint_reference=a.reference(priorpath),prior_artifacts_verified=len(prior['artifacts']),intentional_supersessions=[supersession],other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True,capture_checkpoint_reference=a.reference(a.f.RUN/'capture-checkpoint-001.json'),next_work='Continue Detroit remaining113selected leads. Reuse the live capture session19735; do not restart. Check new failures. Take a new museum scope after the five additions, use the v2 lifespan flag, source former-attribution evidence and fresh identity checks. Preserve MFA,AGO,SaintLouis holds. Do not count Detroit as a new distinct museum/source pass again.')
 m.save(out,checkpoint);print(json.dumps(dict(artifacts=len(refs),checkpoint=a.reference(out),campaign_new_artworks=5334,museums_below_100=1198,capture_state=capture_state['state'],complete_captures=len(captures))),flush=True)
if __name__=='__main__':main()
