# Proposed follow-up batches

Research only. This is an ordered work queue, not authorization to mutate the catalogue, download collections, publish, or deploy.

## 1. Identity and duplicate reconciliation

Review the two MuMa and two Orsay institution records; confirm stable Muséofile, Wikidata and official-site identity evidence. Review missing geography for MAM Paris/Petit Palais and independent institutions. Preserve all citations and holding assertions. Do not merge physical artwork versions solely because titles or accession prefixes match.

Resolve all 35 accession leads in `bounded-candidates-with-local-leads.json` before calling these candidates new. Some may be actual duplicate leads; some may be multi-object inventories. Re-check global artwork identifiers and source URLs with bounded indexed queries, including institution-unlinked works. Preserve the seven research-only geography mappings as proposals until validated.

## 2. Eight Paris Musées CC0 painting records

Scope: PPP439, PPP488, AMVP 1712, AMVP 1057, PPP3048, PPP3045, PPP2101, PPP377.

For each, determine whether to enrich an existing record or propose a new review record. Capture the selected image's explicit licence, attribution, asset URL, dimensions, source record revision and checksum in an approved acquisition workflow. One object can have several visual assets; select a reproduction, not a frame/detail or unrelated image. Do not change a drawing's type merely to fit this batch.

API automation needs the legitimate Paris Musées token and compliance with its published terms; no token is present in this research packet. A user-supplied credential must stay outside committed research files.

## 3. MuMa: 25–40 objects, bounded by specific source IDs

Start with Monet 994.01 / Joconde 07200000523 and the Dufy final/oil-study/drawing distinction. Then reconcile the existing 52 dated paintings across aliases before expanding selected Boudin/Dufy/Monet/Marquet/Friesz and Senn-collection records. Keep supplied anonymous or qualified attributions in research, with explicit attribution-model work if needed.

Limit an initial image pilot to 10 individually cleared works, using exact museum accession/object identifiers. Do not treat the 240 Boudin studies sharing an inventory number as a single painting, or automatically expand the entire artist corpus. Photograph reuse needs its own evidence.

## 4. Dieppe: 20–30 objects

Begin with Pissarro 07120002591 and Renoir 000PE015361, then review the bounded Sickert, maritime and Northern-school leads. Record Orsay ownership versus Dieppe deposit where applicable. Use no current-display assertions unless freshly documented. The Pissarro alternative photo needs licence/revision and visual QA before download/attachment.

## 5. Nice and nearby national museums: 40–60 mixed-type objects

Separate sub-batches: Chéret, Matisse, MAMAC, Chagall; then Léger/Biot and Picasso/Vallauris. For Matisse compare supplied inventory and full dates; for MAMAC separate creation, acquisition and signature dates; for Chagall map final paintings to preparatory studies by accession, medium and dimensions. Preserve cut paper, prints, drawings and mixed media instead of flattening them to painting.

The image-permission and blocked-PDF issues can leave metadata review complete while media remains pending. Do not invent image permissions or treat all artwork by a pre-1970 artist as date-eligible. Mark ranges crossing 1970 and incomplete dates for editorial review.

## 6. Louvre and Pompidou native-catalogue pilots

Louvre: 25–50 selected paintings from museum-designated highlights or documented holdings, each with ARK/JSON and accession identity, retaining approximate/range dates and source updates. Reuse open metadata within its terms; choose image route separately.

Pompidou: establish museum identity and test a bounded 25-work set from the native painting catalogue/masterpiece list. The empty Joconde painting feed must not block this. Verify native object IDs, deposits/loans, media rights and date cutoff; post-1970 work remains out of automatic eligibility.

## 7. Regional expansion, balanced rather than Paris-only

Run one 20–30-object museum pilot per region using `regional-inventory.md`. Give early attention to Grenoble, Lyon, Rouen, Caen, Reims, Strasbourg, Lille/LaM/La Piscine, Dijon/Besançon, Nantes/Angers, Rennes/Quimper, Bordeaux/Bayonne, Montpellier/Toulouse/Céret, Tours/Orléans, Palais Fesch and Léon-Dierx. Choose represented women artists and Russian/Greek/Byzantine holdings when documented; do not infer authorship or omit anonymous traditions just to simplify ingestion.

## Acceptance checklist for any later write

- Explicit import/image-acquisition authorization and a clearly bounded ID manifest.
- Backup in the approved Application Support/Artline backup location before material database changes, not in Documents.
- Read-only preflight against real catalogue; no disposable fixtures or tests written there.
- Exact object/variant identity, documented institution role, preserved unknowns and attribution qualifiers.
- Creation end at/before 1970 with source-supported date semantics; uncertain dates retained for review.
- Separate museum-highlight designation from personal editorial selection.
- Per-file image rights, photographer credit, source URL, asset identity, checksum and visual quality checks.
- Records stay in review until explicitly validated/published; holdings never imply current display.
- Go/PostgreSQL retain filtering/counting/pagination; return bounded data to Next.js. No whole-collection browser downloads or per-artwork request loops.
- Query-plan and representative-scale tests are a separate engineering task. This research audit does not satisfy 10-million-row performance verification.
