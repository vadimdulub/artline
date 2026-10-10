# National Museum of Serbia research

Applied checkpoint, 7 October 2026. **115 selected works have been added to the local catalogue**, bringing the National Museum of Serbia from **one to 116 linked artworks with eligible dates**. All additions remain in review. The [post-apply verification](progress-verification-001.json) confirms every new metadata field and source/holding record, plus unchanged complete prior artwork, citation and institution records. The earlier [research verification](research-verification-001.json) remains an immutable pre-import snapshot.

The evidence contains **134 dated candidates**, of which [editorial triage](editorial-triage-001.json) selected **115 for the now-applied [pinned plan](../../serbia-001-current-plan.json.gz)** and retained **19 duplicate, version, medium or impression cases needing follow-up**. All 134 proposed intervals are eligible under the database date classifier; identity and holding checks are separate requirements. The 115 applied records passed both source validation and fresh database identity checks.

The additions comprise 57 paintings, ten sculptures, ten metalwork objects, five drawings, two prints, one fresco, one ceramic object and 29 unknown types. Twenty-one carry literal museum inventories. Local gallery-image fingerprints and virtual-object IDs are research identifiers, not invented accession numbers. No artists, images, publication or current-display claims were added. Replaying the pinned batch inserted zero rows.

| Source selection | Entries examined | Dated candidates | Source-level holds/overlaps |
| --- | ---: | ---: | ---: |
| Nine official collection gallery pages | 107 | 83 | 24 |
| Museum-linked Bukovac and Paja Jovanović virtual exhibitions | 46 | 30 | 16 |
| One inventory-bearing page of the 2015 annual report | 24 | 21 | 3 |
| Total | 177 | 134 | 43 |

The source counts include repeated representations of objects. They must not be reported as 177 distinct artworks. A further [twelve-object foreign-art virtual exhibition](vr-foreign-exhibition-001.json) is retained as an unprocessed discovery source; it overlaps the gallery selection and is outside the candidate totals above.

## Evidence and review

The [gallery queue](caption-queue-001.json) preserves literal Cyrillic captions and their page captures. Image URLs are retained only to locate entries; no artwork image files were requested. Those URLs are not accession numbers. Anonymous Byzantine and post-Byzantine objects retain unknown makers and literal source origins. Modern fresco copies lack creation dates and remain held; their medieval subjects do not date the copies. Miroslav Gospel page 149 and two similarly titled double-icon views require physical-object scope review.

The museum’s [official virtual-exhibition index capture](vr-official-index-001.json) links the exact Bukovac and Paja exhibitions. Their embedded metadata was parsed as JSON without executing scripts. Thirty selected object pages agree with their exhibition entries on creator identity, title, physical format, material and creation fields. Bukovac’s curatorial introduction explicitly identifies its twenty-three paintings as the museum collection. Paja records require either their individual collection label or a matching specific title in the museum’s annual report; exhibition membership alone is insufficient.

The two Queen Natalie paintings are a preparatory bust study (82 × 66 cm) and a full portrait (214 × 131 cm). The full portrait also appears in the gallery and is counted once in triage. Bukovac’s Father retains the source’s `Oko 1900` approximation even though a structured year field says 1900. The 1901 Alexander Obrenović entry is held because its attached narrative describes the different 1922 Karađorđević portrait. The two Icarus diptych components and unbounded “after” dates remain held. Jovanović’s Izdajica retains its own 1925 date and the note that it replicates an 1884 work.

The [2015 annual report](annual-report-2015.pdf) has a [retrieval receipt](annual-report-2015.receipt.json). Printed pages 47 and 55 (PDF pages 48 and 56) were rendered and visually checked. The former corroborates named Paja works from the museum collection; its inventory numbers remain comparison leads where a title alone cannot establish the physical version. The latter provides twenty-four individual outgoing-loan entries. Twenty-one dated, non-overlapping entries become candidates; the unbounded “after 1840” portrait and two gallery/virtual overlaps remain held. Borrowing venues are not assigned as holding museums. The evidence explicitly remains dated 2015 and makes no fresh display claim.

All twenty-one report candidates retain unknown individual object type, medium and dimensions. This includes Queen Draga, whose type must not be inferred from its creator or collection heading. The Uroš Knežević question mark and the Popović title’s “after Đurković” wording remain literal. Missing metadata is not replaced with invented values.

The final [creator/name search](creator-identity-review-003.json.gz) retains 24 artist-profile leads, ten aliases, 11,459 linked-artwork rows, 617 unlinked-label rows and 2,077 exact-title leads. These are duplicate-search scopes, not approved artist links. The [per-candidate comparisons](creator-title-comparison-leads-003.json.gz) cover all 134 records. An earlier search missed the accented Paja spelling in virtual records; the second and third snapshots correct that, while earlier evidence remains unchanged. The Bruegel Jan spelling probe remains relevant to the held flower painting.

Nadežda Petrović’s 1907 Self Portrait has an existing same-work lead and must be reconciled rather than inserted again. Other held cases include the Monet cathedral and Pissarro square versions, generic Cassatt and Tintoretto records, and Dürer, Callot, Gauguin and Kandinsky impression identities. Specific reasons and comparison IDs are in the triage file.

## Application and remaining work

The [application review](application-review-001.json) pins the plan and isolated importer. Current creator pools, title leads, source URLs, inventories and the prior record were rechecked inside the atomic transaction. Backups and the reviewed plan are under `/Users/vadimdulub/Library/Application Support/Artline/backups/museum-expansion-20261006/`. The shared campaign importer remains unchanged while another live campaign depends on its pinned hash. A separate report adapter revalidates the previous batches and combines this verified batch into the [after-wave-23 campaign report](../../verification-after-wave-23.json).

The museum still needs **84 additional eligible linked works for 200**. The [follow-up queue](followup-queue-002.json) preserves all 62 unadded source entries, including duplicates and version holds, plus the additional unprocessed virtual-exhibition lead. Resolve the existing Nadežda Petrović identity as an existing-record holding question, rather than creating another artwork. Do not assume every discovery key represents a separate physical work.

Nineteen offline Serbia tests and **161 campaign tests** pass, using retained real sources without database fixtures. The final evidence and code hashes are recorded in the second delivery checkpoint. This research does not test large-database query performance.
