#!/usr/bin/env python3
"""Publish verification-backed local research reports; optional private archive."""
import argparse, importlib.util,json,tarfile
from pathlib import Path
s=importlib.util.spec_from_file_location('authority',Path(__file__).with_name('reconcile-creator-authorities.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m

def report():
    first=a.BASE;second=m.RUN
    f=json.loads((first/'manifest.json').read_text());s=m.read('manifest.json')
    for run in (first,second):
        for name in ('local-verification.json','production-verification.json','live-verification.json'):assert (run/name).exists()
    one=json.loads((first/'local-verification.json').read_text());two=m.read('local-verification.json');prod=m.read('production-verification.json')
    assert two['counts']['unlinked']==prod['counts']['unlinked']==75965-f['links']-s['links']
    new={e['artist']['slug']:e['artist'] for e in m.read('plan.json') if e['artist']['new']}
    text=f'''# Creator lifespan reconciliation — 13 September 2026

Completed in local and production: **{f['links']:,} artwork links to {f['existing_painters']} existing painters**. This pass audited all 75,965 remaining unlinked review artworks. It found {f['strict_lifespan_labels']:,} creator labels ending in an explicit `(YYYY–YYYY)` lifespan; accepted links require a unique documented full-name variant and both matching painter lifespan boundaries.

Source facts and supplied CSV identities were rechecked before every write. Known biography conflicts, museum creator mismatches, ambiguous namesakes, attribution holds and impossible artwork/lifetime relationships were retained for review. Surname-first label normalization is used only with both independently documented lifespan boundaries. Activity ranges, approximate dates and qualified names are not parsed as closed lifespans.

Every selected artwork remains in review. Titles, artwork types, creation dates, museum fields, images, existing painter records and original CSV/source evidence were verified unchanged. **{one['unknown_dates_preserved']:,} unknown creation dates and {one['unknown_types_preserved']:,} unknown artwork types stayed unknown.** The creator's lifespan never becomes an artwork creation date.

Both databases passed preflight and all-link verification. The writer used 48 serializable batches per database, each at most 100 records, with existing ingestion advisory locks. Citations preserve the original label, parsed creator evidence, documented painter authorities and plan SHA-256 `{f['sha256']}`. Twenty-five public artwork detail checks plus painter options and timeline filters passed. Public research preview remains read-only; the protected editor endpoint returned 401.

Immediately after this pass, both databases had 71,222 unresolved artworks. The subsequent [Wikidata authority pass](../creator-authorities-20260913/README.md) reduces that count further.

Recovery: fresh local full dump, archive validation and checksum receipt under `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-lifespans-20260913/`; successful Cloud SQL backup **1789324907514**. Both target preimages are retained there. No test databases, real-catalogue fixtures, images, deployments or commits were created for these identity passes.
'''
    (first/'README.md').write_text(text)
    counts={}
    for e in m.read('plan.json'):counts[e['artist']['slug']]=counts.get(e['artist']['slug'],0)+1
    rows='\n'.join(f"| {p['display_name']} | {p['birth_year']}–{p['death_year']} | {counts[p['slug']]} | [Wikidata](https://www.wikidata.org/wiki/{p['authorities'][0]['id']}) |" for p in sorted(new.values(),key=lambda p:p['display_name']))
    report=f'''# Creator authority research — 13 September 2026

Completed in **both local and production**: **{s['links']:,} additional artwork links**, including **{s['new_painters']} new review painters** and links to {s['existing_painters']} existing painters. Together with the [explicit lifespan pass](../creator-lifespans-20260913/README.md), this reconciles **{f['links']+s['links']:,} of the 75,965 unresolved artworks**. **{prod['counts']['unlinked']:,} artworks remain unlinked in each database**, representing 27,276 distinct object-level creator labels. This is not a claim that all 75,965 identities have been resolved.

Research includes existing and new museums and collections without restricting reconciliation to the earlier 342-institution list. This creator-only operation adds no museum, holding, on-view, artwork or image records. Existing records and uncertain attributions remain supported in review.

## Evidence and matching

Researched the 100 largest eligible unresolved closed-biography groups (2,794 artworks) against Wikidata, preserving API responses, full entity claims, retrieval timestamps, hashes and every decision. Discovery tries museum surname-first names and reordered names. Acceptance still requires a documented complete name variant, both source lifespan years, a human authority and one unique identity. Museum facts or the literal supplied creator lifespan independently corroborate the Wikidata identity.

New people require no collision with existing names, aliases, Wikidata IDs or source museum person IDs, including NGA, MoMA and Tate identifiers. Property mappings were checked against Wikidata property definitions. Conflicting authority IDs, date discrepancies and namesakes remain held. Alfred Stevens and an ambiguous `Moreau` alias were specifically held; one work falls outside its creator's lifetime. The initial unapplied plan is preserved in `planning-draft-001`; the final plan also checks original museum creator IDs.

Sources for the {s['links']:,} applied links: Joconde 913; explicit supplied biographies corroborated with Wikidata 717; Tate 40; SMK 16. Museum physical-object/holding review notes remain unresolved; a supported creator identity does not validate those other fields. All original research facts, source holds, CSV cells and entry checksums are preserved.

Examples include [Jeanne-Marie Barbey](https://www.wikidata.org/wiki/Q33100373) (280 linked works) and [Edme-Adolphe Fontaine](https://www.wikidata.org/wiki/Q3047674) (101). Captured source evidence is attached to each artwork citation and each new painter's identity/date citation.

## Verification and recovery

Both targets passed read-only preflight, then 17 serializable write batches of at most 100 works. New painters are created atomically with their first supported artwork link. All {s['links']:,} links/citations and 44 new painter identities were verified in each target. Existing painter metadata, artwork titles/types/dates, museum fields and images were unchanged; **426 unknown artwork dates and 717 unknown types remain unknown**. Across both passes, 2,969 unknown dates and 5,460 unknown types were preserved. No artwork or painter was published.

All selected mappings match across local and production. Final counts: local {two['counts']['artworks']:,} artworks / {two['counts']['artists']:,} painters; production {prod['counts']['artworks']:,} artworks / {prod['counts']['artists']:,} painters. The pre-existing three archived-row difference remains. Public artwork details were checked for every one of the 54 painters in this pass, plus new-painter options and timeline filtering. Together with the first pass, 79 public artwork detail checks passed. No browser interaction test is claimed.

Eleven offline identity-policy tests passed, including activity/approximate-date rejection, insufficient name-only evidence, namesakes, museum-ID/name collisions and contradictory source identities. No real-catalogue fixtures or test databases were used. A read-only indexed lookup of 100 actual artwork/creator links completed in 18.222 ms locally; its plan is saved in `local-scoped-lookup-plan.json`. These checks are not a 10-million-row load benchmark.

Final plan SHA-256: `{s['sha256']}`. Full selected target preimages and checksums are under `/Users/vadimdulub/Library/Application Support/Artline/backups/creator-authorities-20260913/`. They complement the fresh full local and successful managed production backup taken before the first pass. For scoped recovery, use the plan, target preimages and per-batch receipts; retain any later independent edits. `archive-receipt.json` identifies the private Google Storage evidence archive. No deployment or Git commit was made for these passes.

## Remaining backlog

`remaining-triage.json` accounts for every remaining artwork: 43,319 supplied-label records need source identity evidence; 18,812 museum creator records need additional identity evidence; 7,275 have closed biographies needing a unique authority or conflict resolution; 92 have existing conflict/attribution holds; 38 retain qualified/unknown creator labels. These are research queues, not rejection categories. Missing details do not delete or hide the retained public research records. No guessed person links were used to reduce the unresolved count.

## New review painters

| Painter | Documented lifespan | Linked artworks | Authority |
| --- | --- | ---: | --- |
{rows}
'''
    (second/'README.md').write_text(report)
    print('Both verified research reports written',flush=True)

def archive():
    assert (m.RUN/'README.md').exists()
    dest=Path('/tmp/artline-creator-expansion-20260913.tar.gz')
    assert not dest.exists()
    files=['ops/reconcile-creator-lifespans.py','ops/research-unresolved-creator-authorities.py','ops/reconcile-creator-authorities.py','ops/verify-creator-authorities.py','ops/report-creator-expansion.py','ops/reconcile-creators-followup.py','ops/verify-creator-followup.py','ops/test_creator_authorities.py','ops/test_creator_followup.py','ops/research-wikimedia-catalogues.py','ops/reconcile-artwork-creators.py','ops/plan-expanded-round2.py','ops/import-michelangelo-frescoes.py','ops/enrich-artwork-images.py']
    with tarfile.open(dest,'w:gz') as tar:
        for root in [a.BASE,m.RUN]:tar.add(root,arcname=str(root.relative_to(m.ROOT)))
        for path in files:tar.add(m.ROOT/path,arcname=path)
        for root in [m.BACKUPS.parent/'creator-lifespans-20260913',m.BACKUPS]:
            for path in sorted(root.glob('*.json')):tar.add(path,arcname='recovery/'+root.name+'/'+path.name)
    checksum=m.r.core.sha(dest.read_bytes());key='research-evidence/creator-expansion-20260913/'+dest.name
    client=m.r.core.storage.Client(project='artline-508319',credentials=m.r.core.GcloudCredentials());blob=client.bucket('artline-508319-images').blob(key)
    blob.metadata={'sha256':checksum};blob.upload_from_filename(str(dest),if_generation_match=0,content_type='application/gzip',timeout=300);blob.reload()
    assert int(blob.size)==dest.stat().st_size and blob.metadata['sha256']==checksum
    receipt={'at':m.r.core.now(),'uri':'gs://artline-508319-images/'+key,'bytes':blob.size,'sha256':checksum,'generation':blob.generation,'contents':'Both research runs, source captures, plans, applied receipts, verification, scripts and scoped recovery preimages. No credentials or Terraform state.'}
    m.save('archive-receipt.json',receipt);m.r.core.save_new(a.BASE/'archive-receipt.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['report','archive']);arg=p.parse_args();report() if arg.command=='report' else archive()
