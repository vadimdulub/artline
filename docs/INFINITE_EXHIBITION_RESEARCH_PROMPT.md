# Continuous exhibition research and production enrichment prompt

Work in `/Users/vadimdulub/Documents/vadim-dulub-git/artline`.

Build and run a continuously resumable Artline exhibition research and production enrichment programme. Discover and add verified exhibitions, participating artists, exhibited artworks, authentic images, venues and their documented connections. Continue across bounded batches without asking me to type “continue.”

## Read first

- `AGENTS.md`
- `/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv`
- `docs/ARTLINE_IMAGE_USE.md`
- `docs/LOCAL_DATA_LOCATIONS.md`
- Existing exhibition schemas, ingestion tools, research evidence and checkpoints.
- Existing continuous-research supervisor and its locks.

## Authorization and boundaries

- I authorize validated production additions and enrichment for exhibitions, artists, artworks, authentic images, venues and documented exhibition connections.
- Use Google Cloud SQL and Storage only through the established production workflow, including necessary authentication, secret access, proxies, backups and verification.
- Cloud Translation remains disabled and prohibited. Do not enable it, call it or silently substitute another paid translation service.
- Keep the real local Artline database read-only.
- Do not delete records, bulk rewrite historical statuses, commit, push, deploy or apply infrastructure changes.
- Do not modify or interrupt the separate artwork research programme.
- Reuse existing catalogue entities wherever possible. Never create duplicate artists, artworks, museums or exhibitions to increase totals.

## Establish the exhibition scope

- Inspect the existing exhibition-specific date, eligibility and review rules before selecting records.
- Do not apply artwork creation cutoffs to exhibition opening dates.
- Preserve the through-1970 artwork scope and documented exceptions when creating main-catalogue artworks.
- Do not generalize the Museum of Russian Impressionism’s museum-specific exceptions to other institutions.
- If no general exhibition-date scope is documented, research historical, current and announced exhibitions, preserve their actual dates and keep uncertain cases in review. Do not invent a cutoff.

## Sources, including Arthive

- Use the 111-source registry for discovery and institution identities, following each provider’s permitted access method.
- **Arthive is explicitly permitted as an additional exhibition research source: <https://arthive.com/exhibitions>.** Use its directory, archive and individual exhibition pages to discover and document exhibitions, dates, venues, named participants and explicitly identified exhibited works. It supplements the original registry; do not silently rewrite the original CSV.
- Retain each exact Arthive exhibition URL and native identifier, original wording, retrieval date and source capture. Distinguish Arthive assertions from corroborating institutional evidence.
- Prefer official exhibition pages, museum archives, dated catalogues, checklists, annual reports and institutional publications for exhibition facts. Cross-check Arthive dates, venues and object participation against these sources where available; preserve discrepancies and uncertainty when corroboration is unavailable.
- Do not treat every artwork or artist linked near an Arthive exhibition as a confirmed participant. Require an explicit exhibition-level statement or documented checklist connection.
- Arthive source acceptance does not automatically license every hosted image or extend WikiArt-specific image approvals to Arthive. Preserve image-specific rights and credits and follow the existing applicable image policy.
- Supplement with authoritative library catalogue records and documented archival sources.
- Preserve source URLs, retrieval dates, captures and checksums.
- A search snippet, image caption, artwork collection page or artist biography alone does not prove participation in a particular exhibition.
- Respect provider access holds, authentication requirements and rate limits.
- Preserve actual source rights labels separately from user approval. Apply source-specific image approvals only within their documented scope.

## Exhibition records

- Record the original title, supported translated titles, organizer, venue, city, country, opening and closing dates, exhibition type, source identifiers and evidence.
- Preserve unknown fields and qualified or conflicting dates.
- Distinguish announced, held, underway, postponed and cancelled exhibitions. Do not infer that an announced event actually occurred.
- Record date-status assessments with the date they were checked.
- Distinguish exhibition organizers, host venues, lenders, sponsors and catalogue publishers.
- Reconcile exhibitions by title variants, dates, organizer, venue and source identity.
- Model travelling exhibitions as a shared exhibition with separately dated venue stops where the existing schema supports this.
- Do not count each venue stop, translated title or catalogue edition as another distinct exhibition.
- Distinguish collection displays, temporary exhibitions, biennial editions, fairs and retrospective exhibitions using the source’s actual description.

## Artists and artworks

- Add artist participation only when supported by explicit exhibition evidence.
- Reconcile creator names, aliases and authority identifiers before creating new artist records.
- Preserve qualified attributions, collective creators, workshops and anonymous labels.
- Attach an existing artwork to an exhibition only after matching the exact object/version using accession, title, creator, date, dimensions, provenance or catalogue number as needed.
- Distinguish copies, studies, casts, editions, print impressions, components and alternate versions.
- Preserve catalogue numbers, lender credits and the wording of exhibition checklists.
- Do not infer that every work by a participating artist appeared in the exhibition.
- Do not infer museum ownership or permanent holdings from temporary exhibition participation or a loan.
- Do not infer current display from a historical exhibition record.
- Preserve partial checklists explicitly; never describe selected documented works as the complete exhibition.
- If an exhibited object is outside the main artwork scope or cannot be securely reconciled, use an existing documentary-entry workflow where available. Otherwise retain a research candidate rather than forcing it into the catalogue.

## Images and documents

- Find authentic exhibition posters, installation views, catalogue covers and reproductions of documented exhibited artworks.
- Label each image by its actual role. An exhibition poster or installation photograph is not an artwork’s primary reproduction.
- Identify depicted works individually before linking them from installation views.
- Do not use generated pictures, unrelated works, merchandise or another version as substitutes.
- Verify exact artwork identity and apply the established image-matching threshold where applicable.
- Preserve actual rights labels, photographer credits, source URLs and any applicable user approval.
- Follow the existing full-frame, proportional resizing and 100,000-byte application-derivative policy where applicable.
- Archive originals and research documents in the established locations outside Documents.
- Technically validate every downloaded image. Record actual visual review and inspect flagged cases individually.
- Do not claim unsampled images were individually viewed.
- Preserve catalogues as evidence with page references; do not upload complete copyrighted publications merely because they are accessible online.

## Production delivery

- Inspect and reuse the established exhibition ingestion workflow.
- Verify the production target before every write.
- Use immutable, checksum-pinned plans, transactional writes, audit history, backups and idempotent recovery.
- Coordinate with existing ingestion locks to avoid racing the artwork programme.
- Keep new records in the appropriate review state and preserve existing editorial statuses.
- Validate exhibition-to-venue, exhibition-to-artist and exhibition-to-artwork relationships independently.
- Verify uploaded files, database associations and public delivery afterward.
- If the schema cannot represent a documented relationship accurately, retain the evidence and record the schema gap. Do not invent a substitute relationship or deploy an unrequested migration.

## Persistence

- Establish a separate durable exhibition queue, checkpoint directory and supervisor identity.
- Verify there is no existing exhibition worker before starting another.
- Execute one bounded batch per worker invocation. The supervisor owns continuation.
- Save source cursors, research outcomes, selected objects, holds, import manifests and verification receipts after every batch.
- Reconcile interrupted writes against live production before retrying.
- Continue indefinitely until I explicitly stop this programme, subject to available authentication, storage and configured spending/account limits.
- Report the 100-hour milestone without treating it as a stopping point.
- Never invent a spending budget or bypass limits.
- Use bounded retries and backoff. Move to another eligible source when a provider is held.
- If a genuine infrastructure blocker persists, save the checkpoint and report it rather than repeatedly making unchanged failed calls.
- Never claim background execution without verifying that the supervisor and worker are running.

## Reporting

- Report distinct new exhibitions, venue stops, new artists, new catalogue artworks, documentary entries, artist participation links, exact artwork participation links and images separately.
- Separate new records from enrichment of existing records.
- Separate discovered, prepared, imported and verified results.
- Count only verified production changes attributable to this programme.
- Preserve the distinction between complete and partial exhibition checklists.
- Produce hourly progress summaries with source coverage, outstanding holds and the next queue.
- Do not attribute another concurrent job’s changes to this programme.

Begin now: inspect the exhibition workflows and scope, establish and verify durable continuation, then execute the first validated production batch. Do not stop at returning another plan or prompt.
