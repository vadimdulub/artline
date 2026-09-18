Artline research results — 2026-09-15

The 100-row START_HERE_images_100.csv assignment was researched. All 100 rows and all existing fields/IDs are retained unchanged; only proposal and evidence fields are filled. The full multi-batch queue was not treated as an additional assignment. These are proposals for reviewed import; no database changes or image uploads were performed.

Results

- 100 artworks attempted; 0 unvisited artwork rows.
- 9 verified_image: Dürer’s young woman, Bronzino’s Eleonora, Caravaggio’s Bacchus, Cimabue’s Santa Trinita Maestà, Fra Angelico’s main Glorification panel, Goya’s Goicoechea portrait, Uccello’s Uffizi San Romano panel, Titian’s Flora, and the London Van Gogh Wheatfield.
- 71 verified_metadata_only: returned object facts are supported, but an approved reproduction was not established.
- 11 needs_review and 9 blocked. 80 rows therefore have a verified outcome; 20 still need source, object, date or rights resolution.
- The initial image objective is complete for 9 works. Exactly 91 still need an approved image or resolution of the recorded issue. Their task IDs and next actions are in remaining_artwork_tasks.csv. A metadata-only result is useful research, not a completed image task.
- Image rights: 9 approved, 9 restricted and 82 unresolved. Seven approved files carry PDM 1.0; two photographs carry CC0 1.0. Exact file pages, original image URLs, licence links, credits, dimensions, visual observations and UTC checks are recorded in the CSV.

Painter countries

All 88 assigned painter rows are preserved. Eight painters with missing affiliations were researched: Claude Lorrain (FR), Giorgione (IT), Perugino (IT), and Paolo Uccello (IT) have explicit institutional country evidence. NGA’s Venetian and Umbrian labels remain in the evidence. Van Dyck and Rubens are documented as Flemish, and Bosch as Netherlandish; no unsupported modern code is substituted. Sofonisba’s Brera record supports Cremonese practice but explicit country wording remains to be corroborated. Four country rows need review; 80 painter rows were not revisited. Exact slugs and states are in remaining_painter_tasks.csv. Existing affiliations were not removed or freshly certified by implication.

Additional museum works and duplicate checking

Five physical-artwork candidates are returned separately, all status=review and action=new_artwork: NGA 573 (Van Dyck, Portrait of a Flemish Lady), 41590 (Giorgione, The Holy Family), 43721 (Rubens, Decius Mus Addressing the Legions), 71349 (Rubens, The Fall of Phaeton), and Met 438028 (Uccello, The Crucifixion). Their exact accessions/object IDs and Wikidata crosswalks had no match in all 236,156 active/archived index rows; 545 redirects and nearby creator/title results were also checked. This is a finding relative to the supplied snapshot, not a claim that another catalogue cannot contain the objects.

Among 35 additional NGA paintings sought for six researched painters, 30 already matched existing records, four became candidates and one virtual aggregate was excluded because its three physical panels are already indexed. The Uccello triptych is counted once with its three painted components described. A Met search for Sofonisba returned one inaccessible object and two print/book objects by other makers; these were not misclassified as her paintings. The 39-entry duplicate_check_audit.csv records those results. New candidates have no proposed images; four require date-normalization review, and all five still need image research.

Important corrections and review points

- Dürer: Städel calls the sitter an unknown young woman and the medium watercolour on canvas. The later Fürleger crest does not establish the sitter’s identity.
- Ghirlandaio: the inspected image matches the correct 1487 tondo, but includes a three-dimensional frame and a copyright watermark despite its Commons PDM claim. It is withheld.
- Fra Angelico: the approved photograph shows the complete main painted panel, including gilded upper ornament, but excludes the separately catalogued predella reunited with it in 2024. It must not be presented as a photograph of the entire reassembled ensemble.
- Bosch: the Berlin source combines recto and verso; its PDM credit was located, but that composite was not visually checked. No image URL is proposed.
- Vermeer: Commons PDM and the museum’s non-commercial download conditions conflict for the museum-sourced reproduction. Image withheld.
- Botticelli: Pushkin’s page discusses paired shutters and probable pupil execution despite its Botticelli heading. Exact panel coverage and creator role need review.
- Bronzino’s Lorenzo Lenzi: the regional catalogue retains competing Bronzino/Pontormo attribution and alternative dates. Mixed circa/before wording is retained without invented bounds.
- The Canaletto Pushkin page contains conflicting holding references. Giorgione’s Tempesta discusses competing dates and conflicting acquisition histories. Neither is silently normalized.
- Borghese’s David preserves competing date ranges. The Doré battle’s historical event date is not used as a creation date. Rembrandt’s Late 1650s remains a qualified decade. The current Hamburger Kunsthalle date for the Wanderer is circa 1817.
- Fragonard’s dimensions conflict; the proposed dimension field stays empty. Met/AIC metadata licences and per-object public-domain flags were not treated as automatic permission for unverified images. Munch’s exact photograph is CC BY-NC-SA 4.0 and is excluded.

Access and scope limitations

Direct access failed for NGA object pages, several Lombardia records, some Tate URLs, the Tretyakov lead, and a Pushkin collection endpoint. The NGA official open dataset recovered four assigned objects; public web retrieval recovered the Tiepolo, Lorenzo Lenzi and Vermeer records. Other rows retain exact obstacles and URLs. source_access_log.csv records fetch attempts; successful public-web recoveries are explained in the result rows. The initial 8 MB NGA download was incomplete and was not used for discovery; the complete 82,364,723-byte objects file was obtained before selection and duplicate checks.

The image search was bounded: nine selected reproductions were inspected, and the rejected Ghirlandaio photograph was also inspected. Source-access checks covered all 100 starter works, but alternate-image searching was not exhaustive for every metadata-only work. Unviewed candidates were not marked visually verified. No not_found result is used for an unvisited row. Unknown facts remain blank. No current-display, ownership, masterpiece, publication or import claim is inferred from collection membership.

Validation

The three requested CSVs round-trip as UTF-8 with BOM and exactly the original headers: artwork 100 × 77 columns; painter 88 × 37; new candidates 5 × 45. All original identity/context cells, including distinct production/local UUIDs and embedded JSON, compare equal. Task/candidate IDs are unique. Date/type/role/outcome/rights enums, UTC timestamps, country codes, CSV quoting, Unicode and formula-like proposal cells pass validation. All nine verified_image rows have the required object, image, visual, licence and attribution evidence. All other rows have blank direct image and thumbnail fields. validation_report.json records the checks.

Files

- completed_artwork_research.csv
- completed_painter_research.csv
- new_artwork_candidates.csv
- remaining_artwork_tasks.csv
- remaining_painter_tasks.csv
- duplicate_check_audit.csv
- source_access_log.csv
- validation_report.json
