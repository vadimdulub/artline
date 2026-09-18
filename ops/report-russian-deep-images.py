#!/usr/bin/env python3
"""Build the cited result and verified recovery archive after image checks pass."""
import collections,hashlib,importlib.util,json,tarfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-russian-deep-images.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
RUN=r.RUN;ROOT=r.ROOT;core=r.core
def main():
 final=json.loads((RUN/'final-verification.json').read_bytes());assert not final['pending_attachment']
 before=json.loads((RUN/'local-before.json').read_bytes());works={w['id']:w for w in before['works']};selected=[json.loads(p.read_bytes()) for p in (RUN/'images/selected').glob('*/*.json')];receipts=[json.loads(p.read_bytes()) for p in (RUN/'images/images').glob('*/*.json')]
 q=json.loads((RUN/'quality-review/final-image.json').read_bytes());selected=[q if s['artwork_id']==q['artwork_id'] else s for s in selected];receipts=[q if s['artwork_id']==q['artwork_id'] else s for s in receipts]
 completed={json.loads(line)['artwork_id'] for line in (RUN/'images/events.jsonl').read_text().splitlines() if json.loads(line)['outcome']=='complete'};receipts=[s for s in receipts if s['artwork_id'] in completed]
 sources=collections.Counter(s['provider'] for s in receipts);artists=collections.Counter(s['artist'] for s in receipts);types=collections.Counter(works[s['artwork_id']]['work_type'] for s in receipts);rights=collections.Counter(s['license_label'] for s in receipts)
 searches=[RUN,RUN/'accession-deeper'];pages={};identities=[];deferred=[];truncated=0
 for path in searches:
  pages.update(json.loads((path/'accession-search-files.json').read_bytes()));identities+=json.loads((path/'new-commons-identity-matches.json').read_bytes());deferred+=json.loads((path/'new-commons-rights-deferred.json').read_bytes());truncated+=sum(json.loads(p.read_bytes())['truncated'] for p in (path/'accession-search-batches').glob('*.json'))
 photos=json.loads((RUN/'photographs-verified-aliases/new-commons-selection.json').read_bytes());museum_targets=json.loads((RUN/'direct-museum-targets.json').read_bytes());museum_selected=json.loads((RUN/'direct-museum-selection.json').read_bytes())
 coverage=final['targets']['local']['fixed_cohort_coverage'][0];backup=json.loads((RUN/'backups.json').read_bytes())
 lines=['# Russian artwork image research — 13 September 2026','',f"**{len(receipts)} additional images were verified in both the local and production catalogues.** They cover {len(artists)} existing creator labels/profiles and {len(types)} artwork types. All added reproductions are JPEGs of at most 100,000 bytes; the largest is {final['largest_image_bytes']:,} bytes. Artwork review/publication states, dates, creator attributions and holdings remain unchanged.",'',
 '## Results and coverage','',
 '| Measure | Result |','| --- | ---: |',f"| Selected images | {len(selected)} |",f"| Attached and verified in both databases | {len(receipts)} |",f"| Remaining selected images awaiting download | {len(final['pending_preparation'])} |",f"| Prepared images awaiting attachment | {len(final['pending_attachment'])} |",f"| Fixed Russian research cohort | {before['summary']['works']:,} works |",f"| Images before this pass | {before['summary']['with_images']} |",f"| Images after this pass | {coverage['with_images']} |",f"| Remaining eligible image gaps in this cohort | {coverage['eligible_gaps']:,} |",'',
 'These figures describe this pass and a fixed catalogue cohort. They do not count the images added by the preceding Danish/Russian pass as new additions, and they do not claim complete coverage of Russian painting. The file-by-file result, original source pages, licenses and existing museum identifiers are in [IMAGE-INVENTORY.md](IMAGE-INVENTORY.md). Database and delivered-byte checks are recorded in [final-verification.json](final-verification.json).','',
 '## Research scope','',
 'The baseline includes 519 existing artist profiles with an explicit Russian cultural-affiliation record, plus Alexej von Jawlensky and six existing icons whose object-level cultural context explicitly identifies Russian icon painting. Russian affiliation can coexist with another national tradition; it is not a claim of exclusive nationality. Holding country and birthplace alone did not determine scope. Jawlensky is explicitly described as Russian by both [NGA](https://www.nga.gov/artists/1418-alexej-von-jawlensky) and [MoMA](https://www.moma.org/artists/2896-alexei-jawlensky); his catalogue country metadata was preserved. See [scope-supplement-evidence.json](scope-supplement-evidence.json).','',
 'Only existing, non-archived works with backend-confirmed selection evidence and eligible creation dates were candidates. Unknown dates and ranges crossing 1970 were not assigned substitute years. Anonymous Russian icon records retained their object-level creator labels. The Greek attribution on the separate Theophanes icon did not become a Russian artist authority through its Moscow holding.','',
 '## Search depth and identity evidence','',
 f"The pass resumed 174 previously researched Russian candidates, then searched another 2,400 missing Russian Museum objects in two disjoint groups of 1,200. These searches retrieved {len(pages):,} distinct Commons file records. The exact creator/accession path confirmed {len(identities)} additional object identities before rights selection. A separate photograph path selected {len(photos)} images using exact official museum-object links. Another {len(museum_targets)} existing objects were checked against Met, NGA, Cleveland and Chicago data; {len(museum_selected)} supplied explicitly reusable primary images.",'',
 'Museum URL inventory hints were discovery terms only. The detailed Russian Museum page had to confirm the actual accession, title and creator-authority link. A Commons file then needed the same accession and institution with a creator match, or an exact official object URL in an independent photograph record. Similar titles, initials alone and repeated accession numbers across institutions were insufficient. The initial Kremlin search, for example, returned a Jan van Scorel painting for Ж-760; it was rejected as a different institution and object.','',
 'Commons sometimes places the photographer in its exported Artist field. The independent-photograph path therefore uses exact museum object URLs and separate creator verification. Shakko photographs retain “Photo: Wikipedia / Shakko (Sofia Bagdasarova)” and the explicit CC BY-SA 4.0 license. Gallery frames and surrounding material are retained where present; no automatic cropping, generative filling or restoration was performed.','',
 f"The search was bounded: {truncated} accession batches returned a continuation marker, which was recorded instead of treated as an exhaustive result. Files without inventory metadata, alternate spellings, inaccessible records and unsearched works can still contain valid images. Metadata discovery was broader than the selected image downloads. Raw API responses, revision identifiers, museum captures and checksums remain with this research.",'',
 '## Rights and source disagreements','',
 'Commons rights were checked per file, including license, copyright flags, restrictions, source credit and dispute markers. A public-domain painting did not automatically clear every museum photograph. Russian Museum website reproductions with unresolved source-permission conflicts were deferred. Independent photographs needed a reusable photographic license and evidence for the underlying artwork; this pass retained the licensed file credit rather than inventing a photographer. See the rights deferral files beside each search result.','',
 'Museum image eligibility was checked against explicit object/image flags. [The Met API](https://metmuseum.github.io/) exposes object IDs and public-domain image fields. [NGA](https://www.nga.gov/artworks/free-images-and-open-access) distinguishes its open-access image programme from its catalogue data; the existing revision-pinned image table was filtered to the selected object IDs, primary views and open-access flag. [Cleveland](https://www.clevelandart.org/open-access) identifies eligible images with CC0 metadata. [Chicago API documentation](https://api.artic.edu/docs/) supports exact object retrieval and image-rights fields; none of the checked Chicago gaps supplied an image meeting this pass’s conditions.','',
 'The Kremlin icon *Mother of God of Tenderness* was matched through [official object 9679](https://collectiononline.kreml.ru/entity/OBJECT/9679), accession Ж-267, and the [source record cited by Commons](https://www.icon-art.info/masterpiece.php?mst_id=189). The [Commons file](https://commons.wikimedia.org/wiki/File:Umilenie_Uspenskiy_01.jpg) identifies a faithful public-domain reproduction, the same subject, Novgorod tradition and Dormition Cathedral context. The official museum dates it to the middle of the 12th century; the linked bibliography also records other scholarly dating. The official catalogue interval was preserved. Neither a current display claim nor a named maker was inferred. The other five scoped icon gaps remain unresolved.','',
 '## Verification and practical limits','',
 'Every completed image was decoded and checked for dimensions, SHA-256 and the 100,000-byte ceiling. Stored GCS objects were checked against the local bytes using size and MD5. Both databases were queried through the exact artwork identifier; media association, source checksum, license, credit and unchanged artwork metadata were verified. Representative authenticated preview API responses and served image bytes were checked for every image provider. Visual observations are retained in visual-review.json.','',
 'The image client now identifies Artline with a contact URL, follows a single paced Commons download stream and records provider cooldowns without an early retry. These follow [Wikimedia’s published API guidance](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits); they do not guarantee immunity from operational rate limits.','',
 'The query-plan evidence concerns indexed object lookups in the actual catalogue. It is not a 10-million-row load test or a claim about global browsing performance. No application deployment or publication was required for these catalogue media attachments.','',
 '## Source and evidence inventory','',
 '- [Local baseline](local-before.json) and [production baseline](production-before.json): fixed cohort and metadata before mutation.',
 '- [First accession search](accession-search-targets.json), [second accession search](accession-deeper/accession-search-targets.json), and their file/capture directories: bounded discovery and exact object verification.',
 '- [Photograph matches](photographs-verified-aliases/new-commons-identity-matches.json): official object URLs, independent source and image credits.',
 '- [Museum targets](direct-museum-targets.json), [selected museum images](direct-museum-selection.json), [museum deferrals](direct-museum-deferred.json), and [NGA scoped data](nga-scoped-open-images.json).',
 '- [Icon selection and unresolved cases](kremlin-icon-selection.json), official saved museum record and linked scholarly source capture.',
 '- images/selected: immutable identity and rights decisions before downloading; images/images: immutable compressed-file and source-byte receipts; images/events.jsonl: preparation/application outcomes.',
 '- [Database research citations](commons-research-database-receipt.json), [final verification](final-verification.json), [query plans](final-query-plans.json), and [backup receipt](backups.json).','']
 (RUN/'RESEARCH.md').write_text('\n'.join(lines))
 with (RUN/'RESEARCH.md').open('a') as f:f.write('\nA visual quality correction replaced one photograph added during this pass with a separately licensed, unobstructed view of the same painting. The previous media and decision remain in the evidence archive; the replacement was conditional on the old media belonging to this pass. See [quality-review/database-receipt.json](quality-review/database-receipt.json). A stalled local development server was restarted before delivery checks were repeated; see [local-web-recovery.json](local-web-recovery.json).\n')
 inventory=['# Added Russian artwork images','', '| Artist / creator label | Artwork | Catalogue identifier | Image source | License | Result |','| --- | --- | --- | --- | --- | --- |']
 clean=lambda s:str(s).replace('|','\\|').replace('\n',' ')
 for s in sorted(selected,key=lambda s:(s['artist'],s['title'])):
  w=works[s['artwork_id']];e=next(e for e in w['identifiers'] if e['scheme']==s['scheme'] and e['id']==s['external_id'])
  inventory.append(f"| {clean(s['artist'])} | {clean(s['title'])} | [{clean(e['id'])}]({e['url']}) | [Source]({s['page']}) | {clean(s['license_label'])} | {'Verified in both DBs' if s['artwork_id'] in completed else 'Awaiting download'} |")
 (RUN/'IMAGE-INVENTORY.md').write_text('\n'.join(inventory)+'\n')
 readme=f"""# Russian image pass — completion receipt

{len(receipts)} new images verified in local and production; {len(final['pending_preparation'])} selected images still await preparation. No prepared attachments remain pending.

Read [RESEARCH.md](RESEARCH.md) for the cited findings and [IMAGE-INVENTORY.md](IMAGE-INVENTORY.md) for every selected artwork.

Providers: {dict(sources)}. Types: {dict(types)}. Licenses: {dict(rights)}.

Recovery: local custom-format dump `{backup['local']['path']}` ({backup['local']['bytes']:,} bytes, SHA-256 `{backup['local']['sha256']}`); managed Cloud SQL backup `{backup['production']['id']}`, verified SUCCESSFUL. pg_restore --list passed; no full restore rehearsal was performed.

Scripts: ops/research-russian-deep-images.py (read-only baseline and metadata research), ops/select-russian-deep-images.py (pin identity and rights), ops/apply-russian-deep-images.py (prepare/apply/evidence), ops/verify-russian-deep-images.py (read-only verification), ops/report-russian-deep-images.py (report/archive). Use `/tmp/artline-images-venv/bin/python` and `PYTHONPYCACHEPREFIX=/tmp/artline-deep-pycache`. Completed selections and receipts are immutable; create a new research run to change them. Preparation and application skip existing receipts. Check provider cooldown evidence before resuming a pending download.

No new artworks, biographies, creation years or current-display claims were manufactured. Existing review/publication states are unchanged. No commits or deployment.
"""
 (RUN/'README.md').write_text(readme)
 paths={p for p in RUN.rglob('*') if p.is_file() and p.name!='archive-receipt.json'}
 paths.update(ROOT/'ops'/s for s in ['research-russian-deep-images.py','select-russian-deep-images.py','apply-russian-deep-images.py','verify-russian-deep-images.py','report-russian-deep-images.py','correct-russian-image-quality.py','resolve-danish-russian-images.py','enrich-artwork-images.py'])
 paths.update(ROOT/'apps/web/public'/s['path'].lstrip('/') for s in receipts)
 old=json.loads((RUN/'images/images/russian-deep-commons'/(q['artwork_id']+'.json')).read_bytes());paths.add(ROOT/'apps/web/public'/old['path'].lstrip('/'))
 def referenced(value):
  if isinstance(value,dict):
   for k,v in value.items():
    if k in ('museum_capture','selection_file','capture') and isinstance(v,str) and v.startswith(('docs/','content/')):
     p=ROOT/v
     if p.is_file():paths.add(p)
    referenced(v)
  elif isinstance(value,list):
   for v in value:referenced(v)
 for s in selected:referenced(s['raw'])
 icon=ROOT/'content/imports/icons-primary-20260910/4fcce5642e6f1f87e13cf91f2ae75b8ed14efc980920e414da48e2f0a58ea131.html'
 paths.update([icon,Path(str(icon)+'.snapshot.json')])
 manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':core.sha(p.read_bytes())} for p in sorted(paths)}
 core.save_new(RUN/'archive-manifest.json',manifest);paths.add(RUN/'archive-manifest.json');archive=r.BACKUP/'completed-russian-image-pass.tar.gz';assert not archive.exists()
 with tarfile.open(archive,'w:gz') as t:
  for p in sorted(paths):t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 with tarfile.open(archive,'r:gz') as t:
  for name,record in manifest.items():
   data=t.extractfile(name).read();assert len(data)==record['bytes'] and core.sha(data)==record['sha256']
 core.save_new(RUN/'archive-receipt.json',{'path':str(archive),'bytes':archive.stat().st_size,'sha256':core.sha(archive.read_bytes()),'verified_files':len(manifest),'verified_images':len(receipts),'at':core.now()})
 print('Report and checksum-verified archive complete',len(receipts),flush=True)
if __name__=='__main__':main()
