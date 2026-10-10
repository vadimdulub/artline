#!/usr/bin/env python3
"""Pin wave50 additions, partial source queues and historical policy evidence."""
import csv,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-next-samples-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;RUN=a.RUN
def main():
 out=RUN/'delivery-checkpoint-001.json';assert not out.exists();priorpath=m.RUN/'native/nelson/delivery-checkpoint-001.json';assert hashlib.sha256(priorpath.read_bytes()).hexdigest()=='7c53544f14b3d79859b286514de8b28483c281a705f790d7ec8d97b40020d900';prior=m.load(priorpath)
 for ref in prior['artifacts']:
  if ref['path']=='AGENTS.md':a.h.checked_policy(ref)
  else:a.checked_reference(ref)
 a.checked_reference(prior['other_job_status_reference']);plan,digest=a.validate_plan();assert digest=='aae29496a833d49bd99c9b095669d363c6e0acb1806d3a148d2ba5637521ee6d'
 with m.connect() as db:verified=a.verify(db,plan,digest)
 summary=m.load(m.RUN/'verification-after-wave-50.json');assert summary['verified_new_artworks']==5329 and summary['verified_existing_artworks_linked']==765 and summary['source_pass_museums']==347 and summary['institutions_with_new_records_or_reconciled_holdings']==163
 totals={}
 for name,count in [('added-artworks-after-wave-50.csv',5329),('reconciled-artworks-after-wave-50.csv',765),('museum-coverage-after-wave-50.csv',1491),('gac-date-enrichments-after-wave-50.csv',6)]:
  with (m.RUN/name).open(newline='') as f:rows=list(csv.DictReader(f))
  assert len(rows)==count;totals[name]=count
  if name.startswith('added-artworks'):assert len({r['artwork_id'] for r in rows})==count
  if name.startswith('museum-coverage'):assert sum(int(r['added_this_campaign']) for r in rows)==5329 and sum(int(r['existing_artworks_linked_this_campaign']) for r in rows)==765
 testlog=Path('/tmp/artline-museum-campaign-tests-next-samples-002-20261007.log').read_text();assert re.search(r'Ran 799 tests in [\d.]+s\n\nOK\n$',testlog);assert 'zero inserts' in Path('/tmp/artline-next-samples-replay-20261007.log').read_text()
 root=m.RUN/'README.md';old=root.read_text();text=old
 replacements=[('after-wave-49','after-wave-50'),('5,327','5,329'),('across 158 local museums','across 160 local museums'),('expand 161 institutions','expand 163 institutions'),('**159 collections**','**161 collections**'),('106,224','106,222'),('231,981','231,979'),('110,081','110,079'),('237,966','237,964'),('covered 344 museums','covered 347 museums'),('Nelson-Atkins Museum of Art and 17 Italian museums','Nelson-Atkins Museum of Art, Art Gallery of Ontario, Detroit Institute of Arts, Saint Louis Art Museum and 17 Italian museums'),('institution total to 345','institution total to 348'),('All 53 import batches','All 54 import batches'),('The 788 offline policy tests','The 799 offline policy tests')]
 for before,after in replacements:assert before in text,before;text=text.replace(before,after)
 marker='| Nelson-Atkins Museum of Art — official catalogue extracts | 149 | 1 |';assert marker in text;text=text.replace(marker,marker+'\n| AGO and Detroit — two complete official collection records | 2 | 2 |')
 marker='| Nelson-Atkins Museum of Art | 0 → 149 | 0 → 149 |';assert marker in text;text=text.replace(marker,marker+'\n| Art Gallery of Ontario | 0 → 1 | 0 → 1 |\n| Detroit Institute of Arts | 0 → 1 | 0 → 1 |')
 text+='''

## AGO, Detroit and Saint Louis source passes

The [next museum pass](native/next-samples/README.md) adds two complete, individually reviewed records: George Theodore Berthon’s *The Three Robinson Sisters* (1846, AGO inventory 2007/33) and Josefa de Óbidos’s *Reading the Fate of the Christ Child* (1667, Detroit inventory 2020.15). Both museums move from zero to one linked, eligible review record. Their 19 older pending artworks and 38 citations are unchanged; replay inserts zero records. These museums remain below the requested minimum.

The saved indexes contain 172 date-screened AGO leads and 118 Detroit leads, including Russian and Greek priorities. After the one AGO addition, 289 queue entries remain unapproved; the Detroit addition came from a separately captured highlight. Another 25 indexed leads have unresolved or ineligible source dates. Saint Louis returned HTTP403. AGO direct requests returned HTTP403, and seven of eight attempted object extracts timed out. Detroit supplied four general index pages and two priority filters before HTTP429 stopped requests. Failures and incomplete captures are retained; quotas never turn these leads into approved artwork facts.

Wave50 freshly verifies all 54 addition batches and the ten prior holding/date operations. All 799 offline checks pass with the explicit historical-policy adapter. During this pass, AGENTS.md gained the additive local-image-delivery paragraph; its prior exact bytes were preserved in the Library backup directory, while the current policy governs new work. The unchanged historical tests initially rejected the changed policy file, so the audit now verifies both exact versions instead of changing old plans or weakening source checks. No images, existing catalogue metadata or publication states changed in this batch.
'''
 backup=m.BACKUP/'next-samples-root-readme-before-001.json.gz';assert not backup.exists();oldsha=hashlib.sha256(root.read_bytes()).hexdigest();m.save(backup,dict(at=m.now(),path=str(root),sha256=oldsha,text=old));root.write_text(text)
 supersession=dict(path=str(root.relative_to(m.ROOT)),before_sha256=oldsha,after_sha256=hashlib.sha256(root.read_bytes()).hexdigest(),backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 docs={
  'next-samples':'''# Two complete museum records added — 7 October 2026

Added **two actual review records**: AGO’s *The Three Robinson Sisters* (George Theodore Berthon, 1846, 2007/33) and Detroit’s *Reading the Fate of the Christ Child* (Josefa de Óbidos, 1667, 2020.15). Each museum now has one linked artwork with eligible creation dates. The [pinned plan](next-samples-reviewed-additions-001-plan.json.gz) and [readback](verification-001.json) preserve all metadata, identifiers, citations and accepted holding assertions. The 19 older pending artworks and 38 citations remain unchanged. Replay inserts zero records. There are no new artist authorities, painter links, images, publication or display claims.

AGO supplies a complete line-numbered web extract and indexed selection chain; original object HTTP bytes were unavailable. Detroit supplies original official HTML, linked JSON metadata and capture receipts. The three sisters form one group portrait. The small Detroit copper differs from the tall Lisbon Saint Joseph composition; existing Nativity and Salvator Mundi identities remain separate. The primary Detroit sources agree on accession 2020.15 and an unqualified creator label. A secondary licensed-image entry says “attributed to” and a book-preview result prints 2020.14; both discrepancies remain in the review audit, without silently changing sources.

Read-only scopes inspected 21 AGO-related catalogue records and 33 Detroit-related records by creators, aliases, titles, inventories and native source identifiers. No source-ID, title or accession duplicate was found for either approved object. Other Berthon surname matches describe different artists and subjects.

The larger [AGO](../ago/README.md) and [Detroit](../detroit/README.md) queues still contain **289 unapproved entries**, plus 25 index-date holds across the two museums. The Detroit highlight is separate from its 118-entry queue. [Saint Louis](../slam/README.md) remains on a source-access hold. All three museums remain below 100, and the overall goal is unfinished.

All **11 new checks** passed within the **799-test campaign suite**. The historical-policy adapter verifies the exact old AGENTS.md snapshot and exact current additive update; other changed evidence is rejected normally. The initial unadapted suite failure is retained in validation evidence. The [wave50 report](../../verification-after-wave-50.json) freshly checks 54 addition batches and ten prior holding/date operations. Campaign totals are **5,329 additions and 765 existing-work museum links**, separate from the unrelated minimum-100 job. **1,198 museums remain below 100 linked records**. These checks do not establish ten-million-row performance.
''',
  'ago':'''# Art Gallery of Ontario — partial source pass

One complete record was added in review: *The Three Robinson Sisters*, George Theodore Berthon, 1846, inventory 2007/33. The museum now has one linked record with eligible dates. Its two older pending MacDonald records and four citations remain unchanged.

The [selected queue](selected-official-queue-001.json) contains 172 date-screened painting/drawing leads; 171 remain unapproved after this addition. Seventeen further leads have date holds, and 81 decorative/sculpture entries were outside this bounded painting/drawing selection. Those work types are not globally excluded. Two repeated indexes were deduplicated. Canadian, Modern, Indigenous and Thomson indexes supplied the leads; European and filtered routes failed. The three Indigenous painting highlights fall after 1970 and were not selected.

Direct collection requests returned HTTP403. Eight selected object extracts were attempted: one complete, seven timeouts. Two canonical-URL retries also failed. The [partial capture receipt](partial-capture-001.json) records 164 unattempted selected objects. An ad-hoc “429” substring detector matched object ID34295; AGO did not actually return HTTP429. Original object HTTP bytes are unavailable, and this limitation remains explicit. No images were downloaded. Further work needs usable object evidence and fresh duplicate checks; indexed leads are not approved additions.
''',
  'detroit':'''# Detroit Institute of Arts — partial source pass

One complete highlight record was added in review: *Reading the Fate of the Christ Child*, Josefa de Óbidos, 1667, accession 2020.15. Official HTML and linked JSON agree on identity, 23 × 29 cm dimensions, oil-on-copper medium and the museum purchase credit. The museum now has one linked record with eligible dates; 17 older pending artworks and 34 citations remain unchanged.

The [separate selected queue](selected-official-queue-001.json) contains 118 date-screened leads from four 30-row European Painting pages and explicit Russian/Greek filters. Native IDs deduplicate these to 126 indexed works: 118 selected, eight date holds. Source selection alone does not resolve qualified creators, artist-lifespan date errors, versions or possible group identities. None of these 118 queued details was captured in this pass; the added highlight was captured separately before the rate limit.

The fifth general index request returned HTTP429, and direct requests stopped. The [partial receipt](partial-capture-001.json) retains the failed HTTP body and all successful captures. The inherited downloader did not retain Retry-After headers. Do not bypass the rate limit through another transport or blindly restart the queue. Any later native continuation must document its cooldown, retain the failed preimage, record fresh request timing and use a slower cadence that respects server guidance. No images were fetched, and source gallery labels were not promoted to current-display claims.
''',
  'slam':'''# Saint Louis Art Museum — source access hold

The fresh local scope has zero linked records and two pending artwork associations. Both official collection overview/search web requests returned HTTP403. The [source hold](source-hold-001.json) and original tool output are preserved. No artwork, association, image or metadata was changed. The museum still needs at least 100 eligible, individually verified records; an access failure does not establish a lack of eligible artworks.
'''}
 for key,content in docs.items():
  p=m.RUN/'native'/key/'README.md';assert not p.exists();p.write_text(content)
 m.save(RUN/'verification-001.json',dict(at=m.now(),plan_sha256=digest,**verified))
 logs={p.name:p.read_text() for p in Path('/tmp').glob('artline-next-samples*20261007.log') if p.is_file()};logs['unadapted-suite']=Path('/tmp/artline-museum-campaign-tests-next-samples-20261007.log').read_text()
 m.save(RUN/'validation-001.json',dict(at=m.now(),tests_passed=799,new_tests_passed=11,test_database=False,command='python -B ops/museum-expansion-next-samples-tests-20261007.py',output=testlog,retained_logs=logs,csv_counts=totals,limitation='Offline evidence/policy checks and real-catalogue readback, not representative large-scale load testing.'))
 m.save(RUN/'prior-checkpoint-verification-002.json',dict(at=m.now(),prior_checkpoint=a.reference(priorpath),prior_artifacts_verified=8360,intentional_supersessions=[supersession,m.load(a.h.RECEIPT)],other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True))
 refs={}
 for ref in prior['artifacts']:
  if ref['path']==supersession['path']:assert ref['sha256']==oldsha;refs[ref['path']]=a.reference(root)
  elif ref['path']=='AGENTS.md':a.h.checked_policy(ref);refs[ref['path']]=a.reference(m.ROOT/'AGENTS.md')
  else:a.checked_reference(ref);refs[ref['path']]=ref
 paths=[priorpath]+[p for key in ['ago','detroit','slam','next-samples'] for p in (m.RUN/'native'/key).rglob('*') if p.is_file()]+[p for p in (m.ROOT/'ops').glob('*20261007.py') if any(key in p.name for key in ['next-samples','next_samples','ago-','detroit-','policy-history'])]+list(m.RUN.glob('*after-wave-50*'))+list(m.RUN.glob('*s50*'))+[a.checked_reference(ref) for ref in plan['evidence']]
 for p in paths:refs[str(p.relative_to(m.ROOT))]=a.reference(p)
 for ref in refs.values():a.checked_reference(ref)
 checkpoint=dict(at=m.now(),goal_complete=False,local_only=True,campaign_new_artworks=5329,campaign_existing_links=765,institutions_with_new_records_or_reconciled_holdings=163,source_pass_museums=347,source_pass_institutions=348,new_additions=2,verification=verified,museums_below_100=1198,unapproved_queue_entries=289,index_date_holds=25,tests_passed=799,new_tests_passed=11,plan_sha256=digest,csv_counts_verified=totals,artifacts=sorted(refs.values(),key=lambda x:x['path']),prior_checkpoint_reference=a.reference(priorpath),prior_artifacts_verified=8360,intentional_supersessions=[supersession,m.load(a.h.RECEIPT)],other_job_status_reference=prior['other_job_status_reference'],other_job_totals_separate=True,next_work='Continue toward100–200per museum. Preserve AGO and SaintLouis access holds. A later Detroit native continuation must use documented cooldown and slower cadence, retain prior429, and honor any fresh Retry-After. MFA Boston is another untouched museum below100 with official collection filters; web discovery only, no scope or captures yet. Use historical-policy adapter for old plans; current AGENTS governs new work.')
 m.save(out,checkpoint);print(json.dumps(dict(artifacts=len(refs),checkpoint=a.reference(out),campaign_new_artworks=5329,museums_below_100=1198)),flush=True)
if __name__=='__main__':main()
